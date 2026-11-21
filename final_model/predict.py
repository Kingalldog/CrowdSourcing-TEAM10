"""Detect adult butterflies and moths with the team's frozen Grounding DINO setup."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
import hashlib
import json
import os
import shutil
import tempfile
import time
from functools import partial
from multiprocessing import get_context
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen


RESULTS = Path(__file__).parent / "results"
WINNER = "grounding_base_contrast"
FIELDS = ("left", "top", "width", "height")


def read_rows(path):
    rows = {}
    with path.open(encoding="utf-8") as source:
        for line in source:
            if line.strip():
                row = json.loads(line)
                pid = row["photo_id"]
                if type(pid) is not int or pid in rows:
                    raise ValueError(f"{path}: invalid or duplicate photo_id {pid}")
                rows[pid] = row
    if not rows:
        raise ValueError(f"Empty file: {path}")
    return rows


@contextmanager
def atomic_file(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            yield stream
            stream.close()
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)


def write_jsonl(path, rows):
    with atomic_file(path) as stream:
        for row in rows:
            stream.write((json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n").encode())


def iter_images(manifest, images):
    from PIL import Image

    for pid, row in read_rows(manifest).items():
        path = images / f"{pid}.jpg"
        if not path.exists():
            url = urlsplit(row["photo_url"])
            if (url.scheme, url.netloc) != ("https", "inaturalist-open-data.s3.amazonaws.com") or not url.path.startswith(f"/photos/{pid}/original."):
                raise ValueError(f"Unexpected iNaturalist URL for {pid}")
            with atomic_file(path) as temp, urlopen(url.geturl(), timeout=30) as response:
                shutil.copyfileobj(response, temp)
                temp.seek(0)
                with Image.open(temp) as img:
                    img.verify()
        yield pid, path


def iou(a, b):
    ax, ay, aw, ah = (a[k] for k in FIELDS)
    bx, by, bw, bh = (b[k] for k in FIELDS)
    ar, ab, br, bb = ax + aw, ay + ah, bx + bw, by + bh
    width = max(0, min(ar, br) - max(ax, bx))
    height = max(0, min(ab, bb) - max(ay, by))
    overlap = width * height
    return overlap / ((ar - ax) * (ab - ay) + (br - bx) * (bb - by) - overlap)


def final_boxes(detections, threshold):
    kept = []
    for box in sorted(detections, key=lambda b: b["score"], reverse=True):
        score = box["score"]
        x, y, w, h = (box[k] for k in FIELDS)
        if not (0 <= score <= 1 and w > 0 and h > 0 and 0 <= x < x + w <= 1.000001 and 0 <= y < y + h <= 1.000001):
            raise ValueError(f"Invalid detection: {box}")
        if score >= threshold and all(iou(box, other) <= 0.55 for other in kept):
            kept.append({key: box[key] for key in FIELDS})
    return kept


def detect_batch(items, *, config, device, model_dir):
    import torch
    from PIL import Image, ImageOps
    from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

    model = model_dir or config["model"]
    processor = AutoProcessor.from_pretrained(model, revision=config["revision"])
    processor.image_processor.size = config["resize"]
    detector = AutoModelForZeroShotObjectDetection.from_pretrained(
        model, revision=config["revision"], dtype=torch.float32, use_safetensors=True, disable_custom_kernels=True
    ).to(device).eval()
    target = config["prompt"]
    caption = (target + " " + config.get("distractors", "")).strip()
    tokens = processor.tokenizer(caption, return_offsets_mapping=True)
    target_ids, competitor_ids = [], []
    for index, (start, end) in enumerate(tokens["offset_mapping"]):
        if any(c.isalnum() for c in caption[start:end]):
            group = target_ids if end <= len(target) else competitor_ids
            group.append(index)

    rows = []
    with torch.inference_mode():
        for pid, path in items:
            start_time = time.monotonic()
            try:
                with Image.open(path) as source:
                    image = ImageOps.exif_transpose(source).convert("RGB")
                inputs = processor(images=image, text=caption, return_tensors="pt").to(device)
                output = detector(**inputs)
                probabilities = output.logits[0].float().sigmoid()
                scores = probabilities.amax(-1)
                if competitor_ids:
                    target_scores = probabilities[:, target_ids].amax(-1)
                    competitor_scores = probabilities[:, competitor_ids].amax(-1)
                    scores = torch.where(target_scores >= competitor_scores, target_scores, 0.0)
                centers = output.pred_boxes[0].float().cpu()
                scores = scores.cpu()
                if not torch.isfinite(centers).all() or not torch.isfinite(scores).all():
                    raise ValueError("Non-finite detector output")
                selected = scores > config["score_floor"]
                detections = []
                for (cx, cy, w, h), score in zip(centers[selected].tolist(), scores[selected].tolist()):
                    left, top = max(0., cx - w / 2), max(0., cy - h / 2)
                    right, bottom = min(1., cx + w / 2), min(1., cy + h / 2)
                    if right > left and bottom > top:
                        detections.append(dict(left=left, top=top, width=right-left, height=bottom-top, score=score))
                detections.sort(key=lambda box: box["score"], reverse=True)
                rows.append(dict(photo_id=pid, detections=detections, elapsed_s=time.monotonic()-start_time, error=None))
            except Exception as exc:
                raise RuntimeError(f"photo_id={pid}: {exc}") from exc
            if device == "mps" and len(rows) % 5 == 0:
                torch.mps.empty_cache()
    return rows


def run_detector(args):
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    import torch

    name = args.raw or WINNER
    config = json.loads((RESULTS / f"{name}_raw.jsonl.config.json").read_text())
    if args.model_dir and config.get("weights_sha256"):
        with (args.model_dir / "model.safetensors").open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != config["weights_sha256"]:
                raise ValueError("Local weights differ from the recorded checkpoint")
    device = args.device or ("mps" if torch.backends.mps.is_available() else "cpu")
    detect = partial(detect_batch, config=config, device=device, model_dir=args.model_dir)
    images = list(iter_images(args.manifest, args.images))
    if device == "mps" and len(images) > 40:
        # A fresh process every 40 photos releases MPS graphs for previous image sizes.
        for start in range(0, len(images), 40):
            with ProcessPoolExecutor(max_workers=1, mp_context=get_context("spawn")) as pool:
                rows = pool.submit(detect, images[start:start + 40]).result()
            yield from rows
    else:
        yield from detect(images)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--images", type=Path, default=Path("images"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--from-raw", type=Path, help="Export saved detections without loading a model")
    mode.add_argument("--raw", choices=(WINNER, "grounding_base", "grounding_tiny"), help="Save scored boxes for comparison")
    parser.add_argument("--device", choices=("cpu", "mps", "cuda"))
    parser.add_argument("--model-dir", type=Path, help="Use an existing copy of the pinned model")
    args = parser.parse_args()
    if args.from_raw:
        ids = read_rows(args.manifest)
        raw = read_rows(args.from_raw)
        if ids.keys() != raw.keys():
            parser.error("Manifest and saved predictions have different photo IDs")
        rows = (raw[pid] for pid in ids)
    else:
        rows = run_detector(args)

    def output_rows():
        for row in rows:
            if row["error"] is not None:
                raise ValueError(f"photo_id={row['photo_id']}: {row['error']}")
            yield row if args.raw else dict(photo_id=row["photo_id"], boxes=final_boxes(row["detections"], 0.25), error=None)

    try:
        write_jsonl(args.output, output_rows())
    except Exception as exc:
        with Path(str(args.output) + ".errors.jsonl").open("a", encoding="utf-8") as log:
            print(json.dumps(dict(time=time.time(), error=str(exc))), file=log)
        raise


if __name__ == "__main__":
    main()
