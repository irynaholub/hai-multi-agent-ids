"""Final step: cut the chain at the end of the vote, add the residual, compute eTaPR"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src import config
from src.evaluation import (
    build_inscope_keep_mask,
    compute_etapr,
    find_intervals,
    hysteresis_expand,
)

CROSS_RESIDUAL_CSV = "multi_agent_cross_residual_predictions.csv.gz"
OUTPUT_CSV = "multi_agent_orchestrator_final_predictions.csv"


def cap_chain_at_vote_end(chain: np.ndarray, vote: np.ndarray) -> np.ndarray:
    """Cut every chain interval right after its last overlap with a vote interval"""
    out = chain.copy().astype(int)
    vote_intervals = find_intervals(vote.astype(bool))

    for cs, ce in find_intervals(chain.astype(bool)):
        last_vote_end = cs - 1
        for vs, ve in vote_intervals:
            if ve >= cs and vs <= ce:
                last_vote_end = max(last_vote_end, min(ve, ce))

        if cs <= last_vote_end < ce:
            out[last_vote_end + 1 : ce + 1] = 0

    return out


def main() -> None:
    results = config.RESULTS_DIR
    target_mask = pd.read_csv(results / "p2_target_attacks_mask.csv")["label"].values

    cr = pd.read_csv(results / CROSS_RESIDUAL_CSV)
    y_true = cr["label"].values.astype(int)
    keep = build_inscope_keep_mask(target_mask, y_true)

    chain = cr["chain_flag"].values.astype(int)
    residual = cr["residual_flag"].values.astype(int)
    vote = cr["vote_flag"].values.astype(int)

    pred = np.clip(cap_chain_at_vote_end(chain, vote) + residual, 0, 1).astype(int)

    if config.USE_FINAL_ORCHESTRATOR_HYSTERESIS:
        anchor_col = f"{config.HYSTERESIS_ANCHOR_AGENT}_norm_score"
        if anchor_col in cr.columns:
            pred = hysteresis_expand(
                pred,
                cr[anchor_col].values.astype(float),
                low_threshold=config.HYSTERESIS_LOW_THRESHOLD,
                max_extend=config.FINAL_HYSTERESIS_MAX_EXTEND,
                extend_left=True,
                extend_right=config.FINAL_HYSTERESIS_EXTEND_RIGHT,
            ).astype(int)
        else:
            print(f"  [warn] {anchor_col} missing, hysteresis skipped")

    strict = compute_etapr(y_true[keep], pred[keep], theta_p=0.5, theta_r=0.1)
    relaxed = compute_etapr(y_true[keep], pred[keep], theta_p=0.1, theta_r=0.1)

    # A predicted interval is a false alarm if it touches no target attack
    false_alarms = sum(
        1
        for s, e in find_intervals(pred)
        if not np.any(y_true[s : e + 1].astype(bool) & target_mask[s : e + 1].astype(bool))
    )

    print("=" * 70)
    print("ОРКЕСТРАТОР — фінальний результат")
    print("=" * 70)
    print("\n  Цільові P2-атаки (theta_p=0.5):")
    print(f"    eTaF1      = {strict['eta_f1']:.4f}")
    print(
        f"    eTaP       = {strict['eta_precision']:.4f}  "
        f"(detection={strict['eta_precision_detection']:.4f}  "
        f"portion={strict['eta_precision_portion']:.4f})"
    )
    print(
        f"    eTaR       = {strict['eta_recall']:.4f}  "
        f"(detection={strict['eta_recall_detection']:.4f}  "
        f"portion={strict['eta_recall_portion']:.4f})"
    )
    print(f"    виявлено   = {strict['detected_true_intervals']}/{strict['true_intervals']}")
    print(f"    хибні інтервали = {false_alarms}")
    print(f"    інтервалів прогнозу = {len(find_intervals(pred))}")
    print("\n  Цільові P2-атаки (theta_p=0.1, relaxed):")
    print(
        f"    eTaF1      = {relaxed['eta_f1']:.4f}  "
        f"P={relaxed['eta_precision']:.4f}  R={relaxed['eta_recall']:.4f}"
    )

    print("\n  Порівняння з baseline / cross_residual:")
    for filename, label in [
        ("baseline_predictions.csv", "Базова модель Isolation Forest"),
        (CROSS_RESIDUAL_CSV, "cross_residual (проміжний)"),
    ]:
        path = results / filename
        if not path.exists():
            continue
        df = pd.read_csv(path)
        y_pred = df["prediction"].values.astype(int)
        r = compute_etapr(
            df["label"].values.astype(int)[keep], y_pred[keep], theta_p=0.5, theta_r=0.1
        )
        print(
            f"    {label:42s}: eTaF1={r['eta_f1']:.3f}  "
            f"виявлено={r['detected_true_intervals']}/{r['true_intervals']}"
        )

    out_df = cr[["label"]].copy()
    out_df["prediction"] = pred
    # Not a model score: a rough number for the dashboard timeline, chain counts more than vote
    out_df["score"] = chain.astype(float) * 0.6 + vote.astype(float) * 0.4

    out_path = results / OUTPUT_CSV
    out_df.to_csv(out_path, index=False)
    print(f"\n  Збережено: {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
