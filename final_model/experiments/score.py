"""Reproduce the team leaderboard and threshold experiment from saved detections."""

import argparse
import json
from pathlib import Path

from predict import final_boxes, iou, read_rows


THRESHOLDS = (
    .01, .02, .03, .04, .05, .075, .10, .125, .15, .175, .20, .225, .25,
    .275, .30, .325, .35, .375, .40, .425, .45, .475, .50, .55, .60, .65,
    .70, .75, .80,
)
MODELS = ("grounding_tiny", "grounding_base", "owlv2_base", "qwen4bit", "grounding_base_contrast")


def matches(overlaps, cutoff):
    """Count the largest one-to-one matching between predicted and true boxes."""
    owners = {}

    def assign(prediction, seen):
        for target, overlap in enumerate(overlaps[prediction]):
            if overlap < cutoff or target in seen:
                continue
            seen.add(target)
            if target not in owners or assign(owners[target], seen):
                owners[target] = prediction
                return True
        return False

    return sum(assign(prediction, set()) for prediction in range(len(overlaps)))


def metrics(raw, truth, ids, threshold):
    tp50 = tp75 = predicted = expected = fp_empty = 0
    for photo_id in ids:
        boxes = final_boxes(raw[photo_id]["detections"], threshold)
        targets = truth[photo_id]["boxes"]
        overlaps = [[iou(box, target) for target in targets] for box in boxes]
        tp50 += matches(overlaps, .5)
        tp75 += matches(overlaps, .75)
        predicted += len(boxes)
        expected += len(targets)
        if not targets:
            fp_empty += len(boxes)
    return {
        "threshold": threshold,
        "f1_50": 2 * tp50 / max(1, predicted + expected),
        "f1_75": 2 * tp75 / max(1, predicted + expected),
        "precision": tp50 / max(1, predicted),
        "recall": tp50 / max(1, expected),
        "boxes_on_empty": fp_empty,
    }


def compare(truth, folder):
    calibration = read_rows(folder / "calibration.jsonl")
    holdout = read_rows(folder / "holdout.jsonl")
    if calibration.keys() & holdout.keys() or calibration.keys() | holdout.keys() != truth.keys():
        raise ValueError("Calibration and holdout must partition the golden set")

    rows = []
    for name in MODELS:
        raw = read_rows(folder / f"{name}_raw.jsonl")
        if raw.keys() != truth.keys():
            raise ValueError(f"{name}: predictions and golden set have different photo IDs")
        errors = [pid for pid, row in raw.items() if row["error"] is not None]
        if errors:
            raise ValueError(f"{name}: inference failed on {len(errors)} photos, including {errors[0]}")

        grid = (metrics(raw, truth, calibration, threshold) for threshold in THRESHOLDS)
        best = max(grid, key=lambda r: (r["f1_50"], r["f1_75"], r["precision"], -abs(r["threshold"] - .25)))
        calibrated = metrics(raw, truth, truth, best["threshold"])
        reference = metrics(raw, truth, truth, .10 if name == "owlv2_base" else .25)
        chosen = reference if reference["f1_50"] > calibrated["f1_50"] else calibrated
        rows.append({
            "model": name,
            "all": chosen,
            "holdout": metrics(raw, truth, holdout, chosen["threshold"]),
            "all_reference_threshold": reference,
            "all_at_calibration_threshold": calibrated,
            "elapsed_s": sum(raw[pid]["elapsed_s"] for pid in truth),
            "errors": len(errors),
        })
    rows.sort(key=lambda row: (-row["all"]["f1_50"], row["elapsed_s"]))
    return {"selected": rows[0]["model"], "models": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold", type=Path)
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(read_rows(args.gold), args.results), indent=2))
