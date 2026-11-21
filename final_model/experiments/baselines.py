"""Run the frozen OWLv2 or Qwen comparison with its recorded settings."""

import argparse
import json
import math
import os
import re
import time
from pathlib import Path

from PIL import Image, ImageOps

from predict import iter_images, write_jsonl


def load_owl(settings):
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    import torch
    from transformers import Owlv2ForObjectDetection, Owlv2Processor

    model_id = settings["model"]
    revision = settings["revision"]
    device = settings["device"]
    processor = Owlv2Processor.from_pretrained(model_id, revision=revision)
    model = Owlv2ForObjectDetection.from_pretrained(
        model_id, revision=revision, dtype=getattr(torch, settings["dtype"]), use_safetensors=True
    ).to(device).eval()
    text = processor(text=[settings["prompts"]], return_tensors="pt").to(device)

    @torch.inference_mode()
    def detect(image, photo_id):
        width, height = image.size
        pixels = processor.image_processor(images=image, return_tensors="pt").pixel_values
        outputs = model(pixel_values=pixels.to(device, model.dtype), **text)
        outputs.logits = outputs.logits.float().cpu()
        outputs.pred_boxes = outputs.pred_boxes.float().cpu()
        if not (torch.isfinite(outputs.logits).all() and torch.isfinite(outputs.pred_boxes).all()):
            raise ValueError(f"Non-finite model output for {photo_id}")
        result = processor.image_processor.post_process_object_detection(
            outputs, threshold=settings["score_floor"], target_sizes=[(height, width)]
        )[0]
        boxes = (result["boxes"] / torch.tensor([width, height, width, height])).clamp(0, 1)
        detections = []
        for (left, top, right, bottom), score in zip(boxes.tolist(), result["scores"].tolist()):
            if left < right and top < bottom:
                detections.append(dict(left=left, top=top, width=right - left, height=bottom - top, score=score))
        return sorted(detections, key=lambda item: item["score"], reverse=True)

    return detect


def parse_qwen(answer):
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", answer.strip(), re.DOTALL | re.IGNORECASE)
    items = json.loads(fenced.group(1) if fenced else answer)
    if not isinstance(items, list):
        raise ValueError("Expected an array of boxes")
    detections = []
    for item in items:
        box = item.get("bbox_2d") if isinstance(item, dict) else item
        if not isinstance(box, list) or len(box) != 4:
            raise ValueError(f"Expected four coordinates: {box!r}")
        if not all(type(x) in (int, float) and math.isfinite(x) for x in box):
            raise ValueError(f"Non-numeric coordinates: {box!r}")
        left, top, right, bottom = box
        if not (0 <= left < right <= 1000 and 0 <= top < bottom <= 1000):
            raise ValueError(f"Invalid coordinates: {box!r}")
        detections.append(dict(left=left / 1000, top=top / 1000, width=(right - left) / 1000,
                               height=(bottom - top) / 1000, score=1.0))
    return detections


def log_failure(path, photo_id, exc, **details):
    record = dict(photo_id=photo_id, error=f"{type(exc).__name__}: {exc}", **details)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_qwen(settings, failure_log):
    import mlx.core as mx
    from huggingface_hub import snapshot_download
    from mlx_vlm import generate, load
    from mlx_vlm.prompt_utils import apply_chat_template
    from mlx_vlm.utils import load_config

    mx.random.seed(0)
    path = snapshot_download(settings["model"], revision=settings["revision"], token=False,
                             allow_patterns=["*.json", "*.jinja", "*.txt", "*.safetensors"])
    model, processor = load(path)
    config = load_config(path)
    prompts = [apply_chat_template(processor, config, settings[key], num_images=1)
               for key in ("prompt", "retry_prompt")]
    limits = [settings["max_tokens"], settings["retry_max_tokens"]]

    def detect(image, photo_id):
        image.thumbnail((settings["max_side"], settings["max_side"]), Image.Resampling.LANCZOS)
        for attempt, (prompt, limit) in enumerate(zip(prompts, limits), 1):
            answer = generate(model, processor, prompt, [image], max_tokens=limit,
                              temperature=settings["temperature"], verbose=False).text
            try:
                return parse_qwen(answer)
            except ValueError as exc:
                if attempt == len(prompts):
                    raise ValueError(f"Invalid final Qwen response: {answer!r}") from exc
                log_failure(failure_log, photo_id, exc, attempt=attempt, raw_response=answer)

    return detect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=["owl", "qwen"])
    parser.add_argument("manifest", type=Path)
    parser.add_argument("images", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    prefix = {"owl": "owlv2_base", "qwen": "qwen4bit"}[args.model]
    config = Path(__file__).resolve().parents[1] / "results" / f"{prefix}_raw.jsonl.config.json"
    settings = json.loads(config.read_text())
    failure_log = args.output.with_suffix(args.output.suffix + ".failures.jsonl")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    detect = load_owl(settings) if args.model == "owl" else load_qwen(settings, failure_log)

    def rows():
        for photo_id, path in iter_images(args.manifest, args.images):
            started = time.perf_counter()
            try:
                with Image.open(path) as source:
                    image = ImageOps.exif_transpose(source).convert("RGB")
                boxes = detect(image, photo_id)
            except Exception as exc:
                log_failure(failure_log, photo_id, exc)
                raise
            elapsed = time.perf_counter() - started
            yield dict(photo_id=photo_id, detections=boxes, elapsed_s=elapsed, error=None)

    write_jsonl(args.output, rows())


if __name__ == "__main__":
    main()
