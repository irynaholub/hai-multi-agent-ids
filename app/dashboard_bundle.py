"""Load the saved predictions and build the numbers and events shown in the dashboard"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.ui_labels import AGENT_COLS
from src import config
from src.anomaly_event import AnomalyEvent
from src.evaluation import build_inscope_keep_mask, compute_etapr, find_intervals

# SetpointAgent -> SetpointAgent_norm_score
SCORE_COLS = {c.removesuffix("_flag"): c.replace("_flag", "_norm_score") for c in AGENT_COLS}

# Used only when the test CSV has no timestamps
TEST_START = datetime(2020, 2, 3, 0, 0, 0)


def _as_path_list(files) -> list[Path]:
    if files is None:
        return []
    if isinstance(files, (str, Path)):
        return [Path(files)]
    return [Path(f) for f in files]


def _load_test_timestamps(expected_len: int) -> np.ndarray | None:
    """Timestamps of all test files in the same order as the predictions"""
    test_files = config.TEST_FILES if config.USE_MULTIPLE_FILES else config.TEST_FILE
    stamps = []

    for path in _as_path_list(test_files):
        if not path.exists():
            continue
        df = pd.read_csv(path, usecols=lambda c: str(c).strip() == "timestamp")
        if "timestamp" not in df.columns:
            return None
        stamps.append(df["timestamp"].astype(str).values)

    if not stamps:
        return None

    out = np.concatenate(stamps, axis=0)
    if len(out) < expected_len:
        return None
    return out[:expected_len]


def row_to_ts(row: int, timestamps: np.ndarray | None = None) -> str:
    if timestamps is not None and 0 <= int(row) < len(timestamps):
        return str(timestamps[int(row)])
    return (TEST_START + timedelta(seconds=int(row))).strftime("%Y-%m-%d %H:%M:%S")


def load_detection_bundle() -> dict[str, Any]:
    cr_path = config.RESULTS_DIR / "multi_agent_cross_residual_predictions.csv.gz"
    cc_path = config.RESULTS_DIR / "multi_agent_orchestrator_final_predictions.csv"
    baseline_path = config.RESULTS_DIR / "baseline_predictions.csv"
    mask_path = config.RESULTS_DIR / "p2_target_attacks_mask.csv"

    if not cr_path.exists():
        raise FileNotFoundError(f"Missing {cr_path}, run run_multi_agent.py first")

    cr = pd.read_csv(cr_path)
    y_true = cr["label"].values.astype(int)
    target_mask = pd.read_csv(mask_path)["label"].values.astype(int)

    bundle: dict[str, Any] = {
        "cr": cr,
        "y_true": y_true,
        "timestamps": _load_test_timestamps(len(y_true)),
        "target_mask": target_mask,
        "keep": build_inscope_keep_mask(target_mask, y_true),
        "pred_cc": None,
        "pred_baseline": None,
    }

    if cc_path.exists():
        bundle["pred_cc"] = pd.read_csv(cc_path)["prediction"].values.astype(int)
    if baseline_path.exists():
        bundle["pred_baseline"] = pd.read_csv(baseline_path)["prediction"].values.astype(int)

    return bundle


def etapr_p2_target(y_true: np.ndarray, pred: np.ndarray, keep: np.ndarray) -> dict[str, float]:
    return compute_etapr(y_true[keep], np.asarray(pred).astype(int)[keep], theta_p=0.5, theta_r=0.1)


def _touches_target(y_true: np.ndarray, target_mask: np.ndarray, start: int, end: int) -> bool:
    return bool(np.any(y_true[start : end + 1].astype(bool) & target_mask[start : end + 1].astype(bool)))


def false_alarm_count(pred: np.ndarray, y_true: np.ndarray, target_mask: np.ndarray) -> int:
    """Predicted intervals that do not touch any target attack"""
    pred = np.asarray(pred).astype(int)
    return sum(1 for ps, pe in find_intervals(pred) if not _touches_target(y_true, target_mask, ps, pe))


def _flag_active(seg: pd.DataFrame, col: str) -> bool:
    return bool(seg[col].mean() > 0.1) if col in seg else False


def build_events(
    pred: np.ndarray,
    cr: pd.DataFrame,
    y_true: np.ndarray,
    target_mask: np.ndarray,
    timestamps: np.ndarray | None = None,
) -> list[AnomalyEvent]:
    events = []
    for ps, pe in find_intervals(np.asarray(pred).astype(int)):
        seg = cr.iloc[ps : pe + 1]
        active = [
            col.replace("_flag", "")
            for col in AGENT_COLS
            if col in seg.columns and seg[col].mean() > 0.1
        ]
        scores = {
            name: float(seg[col].mean())
            for name, col in SCORE_COLS.items()
            if col in seg.columns
        }
        events.append(
            AnomalyEvent(
                start_row=ps,
                end_row=pe,
                timestamp_start=row_to_ts(ps, timestamps),
                timestamp_end=row_to_ts(pe, timestamps),
                active_agents=active,
                agent_scores=scores,
                chain_flag=_flag_active(seg, "chain_flag"),
                residual_flag=_flag_active(seg, "residual_flag"),
                vote_flag=_flag_active(seg, "vote_flag"),
                extra={
                    "plant_zone": "P2 (турбіна + контур тиску)",
                    "is_true_positive": str(_touches_target(y_true, target_mask, ps, pe)),
                    "duration_sec": str(pe - ps + 1),
                },
            )
        )
    return events


def interval_label(event: AnomalyEvent) -> str:
    tag = "TP" if event.extra.get("is_true_positive") == "True" else "FP"
    return f"[{tag}] {event.timestamp_start} — {event.timestamp_end} ({event.duration_sec}s)"
