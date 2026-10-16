"""Build the ground-truth mask for the 5 P2 attack scenarios (A224, A225, A228, A232, A233) in test2"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config
from src.evaluation import find_intervals

# Attack list from the HAI 23.05 technical details (test2_index is 1-based, as in data/summary_label2.txt)
TARGET_ATTACKS = [
    {"scenario": "A224", "ap": "AP14 + AP26", "p2_targets": "P2_AutoSD",
     "support_targets": "P1_B3004", "test2_index": 24, "expected_length_s": 107},
    {"scenario": "A225", "ap": "AP16 + AP32", "p2_targets": "P2_VTR01",
     "support_targets": "P1_LCV01D", "test2_index": 25, "expected_length_s": 60},
    {"scenario": "A228", "ap": "AP05 + AP30", "p2_targets": "P2_SCO, P2_SIT01",
     "support_targets": "P1_PCV01D, P1_PIT01", "test2_index": 28, "expected_length_s": 155},
    {"scenario": "A232", "ap": "AP45 + AP27", "p2_targets": "P2_AutoSD, P2_SIT01",
     "support_targets": "P1_B4002", "test2_index": 32, "expected_length_s": 153},
    {"scenario": "A233", "ap": "AP44 + AP47", "p2_targets": "P2_VTR02",
     "support_targets": "P1_LCV01D, P1_LIT01", "test2_index": 33, "expected_length_s": 2051},
]

# Labelled windows can differ from the official durations by a second or two
LENGTH_TOLERANCE_SECONDS = 5


def _read_labels() -> list[np.ndarray]:
    parts = []
    for path in map(Path, config.LABEL_FILES):
        if not path.exists():
            raise FileNotFoundError(f"Label file not found: {path}")
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        parts.append(df["label"].astype(int).values)
    return parts


def main() -> None:
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    parts = _read_labels()
    if len(parts) < 2:
        raise RuntimeError("Need both label files (test1 and test2) in config.LABEL_FILES")

    test1_size = len(parts[0])
    total_n = sum(len(p) for p in parts)
    test1_intervals = find_intervals(parts[0])
    test2_intervals = find_intervals(parts[1])
    print(f"Attack intervals: test1={len(test1_intervals)}, test2={len(test2_intervals)}")

    if len(test2_intervals) < 33:
        raise RuntimeError(f"Expected at least 33 intervals in test2, found {len(test2_intervals)}")

    mask = np.zeros(total_n, dtype=int)
    rows = []
    for entry in TARGET_ATTACKS:
        start, end = test2_intervals[entry["test2_index"] - 1]
        start += test1_size
        end += test1_size
        length = end - start + 1
        ok = abs(length - entry["expected_length_s"]) <= LENGTH_TOLERANCE_SECONDS
        mask[start : end + 1] = 1

        rows.append({
            "scenario": entry["scenario"],
            "ap": entry["ap"],
            "p2_targets": entry["p2_targets"],
            "support_targets": entry["support_targets"],
            "test2_index_1based": entry["test2_index"],
            "concat_index_1based": len(test1_intervals) + entry["test2_index"],
            "start_idx": start,
            "end_idx": end,
            "length_samples": length,
            "expected_length_s": entry["expected_length_s"],
            "length_ok": ok,
        })
        status = "OK" if ok else "LENGTH MISMATCH"
        print(f"  {entry['scenario']}: rows {start}..{end}, {length} s (expected {entry['expected_length_s']}) {status}")

    print(f"Mask: {int(mask.sum())} samples, {mask.mean() * 100:.3f}% of test data")

    pd.DataFrame({"label": mask}).to_csv(config.RESULTS_DIR / "p2_target_attacks_mask.csv", index=False)
    pd.DataFrame(rows).to_csv(config.RESULTS_DIR / "p2_target_attacks_summary.csv", index=False)


if __name__ == "__main__":
    main()
