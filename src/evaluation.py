from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def compute_sample_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "attack_samples": int(y_true.sum()),
        "predicted_attack_samples": int(y_pred.sum()),
        "total_samples": int(len(y_true)),
    }


def find_intervals(binary: np.ndarray) -> list[tuple[int, int]]:
    binary = np.asarray(binary).astype(int)

    intervals = []
    in_interval = False
    start = 0

    for i, value in enumerate(binary):
        if value == 1 and not in_interval:
            start = i
            in_interval = True
        elif value == 0 and in_interval:
            intervals.append((start, i - 1))
            in_interval = False

    if in_interval:
        intervals.append((start, len(binary) - 1))

    return intervals


def _overlap(a: tuple[int, int], b: tuple[int, int]) -> int:
    left = max(a[0], b[0])
    right = min(a[1], b[1])
    return max(0, right - left + 1)


def compute_interval_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    true_intervals = find_intervals(y_true)
    pred_intervals = find_intervals(y_pred)

    detected_true = 0
    for t in true_intervals:
        if any(_overlap(t, p) > 0 for p in pred_intervals):
            detected_true += 1

    useful_pred = 0
    for p in pred_intervals:
        if any(_overlap(t, p) > 0 for t in true_intervals):
            useful_pred += 1

    interval_recall = detected_true / len(true_intervals) if true_intervals else 0.0
    interval_precision = useful_pred / len(pred_intervals) if pred_intervals else 0.0

    if interval_precision + interval_recall == 0:
        interval_f1 = 0.0
    else:
        interval_f1 = (
            2 * interval_precision * interval_recall
            / (interval_precision + interval_recall)
        )

    return {
        "true_intervals": int(len(true_intervals)),
        "predicted_intervals": int(len(pred_intervals)),
        "detected_true_intervals": int(detected_true),
        "useful_predicted_intervals": int(useful_pred),
        "false_alarm_intervals": int(len(pred_intervals) - useful_pred),
        "interval_precision": interval_precision,
        "interval_recall": interval_recall,
        "interval_f1": interval_f1,
    }


def save_metrics(metrics: dict[str, Any], output_file: str | Path) -> None:
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([metrics]).to_csv(output_file, index=False)


def save_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    scores: np.ndarray | None,
    output_file: str | Path,
    extra: dict[str, np.ndarray] | None = None,
) -> None:
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({
        "label": np.asarray(y_true).astype(int),
        "prediction": np.asarray(y_pred).astype(int),
    })

    if scores is not None:
        df["score"] = np.asarray(scores)

    if extra:
        for name, values in extra.items():
            df[name] = np.asarray(values)

    df.to_csv(output_file, index=False)


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, title: str, output_file: str | Path) -> None:
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm)

    ax.set_title(title)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Normal", "Attack"])
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Normal", "Attack"])

    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center")

    fig.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig(output_file, dpi=200)
    plt.close()


def plot_binary_timeline(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    title: str,
    output_file: str | Path,
    max_points: int = 8000,
) -> None:
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)

    step = max(1, len(y_true) // max_points)
    x = np.arange(0, len(y_true), step)

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(x, y_true[::step], linewidth=0.8, label="Ground truth")
    ax.plot(x, y_pred[::step] + 1.2, linewidth=0.8, label="Prediction")

    ax.set_yticks([0, 1, 1.2, 2.2])
    ax.set_yticklabels(["Normal", "Attack", "Pred normal", "Pred attack"])
    ax.set_xlabel("Sample index")
    ax.set_title(title)
    ax.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(output_file, dpi=200)
    plt.close()


def plot_score_timeline(
    y_true: np.ndarray,
    scores: np.ndarray,
    title: str,
    output_file: str | Path,
    max_points: int = 8000,
) -> None:
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    y_true = np.asarray(y_true).astype(int)
    scores = np.asarray(scores)

    step = max(1, len(y_true) // max_points)
    x = np.arange(0, len(y_true), step)

    fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

    axes[0].plot(x, scores[::step], linewidth=0.6)
    axes[0].set_ylabel("Anomaly score")
    axes[0].set_title(title)

    axes[1].plot(x, y_true[::step], linewidth=0.6)
    axes[1].set_ylabel("Ground truth")
    axes[1].set_xlabel("Sample index")
    axes[1].set_yticks([0, 1])

    plt.tight_layout()
    plt.savefig(output_file, dpi=200)
    plt.close()


def plot_agent_timeline(
    y_true: np.ndarray,
    final_pred: np.ndarray,
    agent_flags: dict[str, np.ndarray],
    output_file: str | Path,
    max_points: int = 8000,
) -> None:
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    y_true = np.asarray(y_true).astype(int)
    final_pred = np.asarray(final_pred).astype(int)

    step = max(1, len(y_true) // max_points)
    x = np.arange(0, len(y_true), step)

    rows = 2 + len(agent_flags)
    fig, axes = plt.subplots(rows, 1, figsize=(14, 2.0 * rows), sharex=True)

    axes[0].plot(x, y_true[::step], linewidth=0.7)
    axes[0].set_ylabel("Label")
    axes[0].set_yticks([0, 1])
    axes[0].set_title("Agent-based detection timeline")

    axes[1].plot(x, final_pred[::step], linewidth=0.7)
    axes[1].set_ylabel("Orchestrator")
    axes[1].set_yticks([0, 1])

    for idx, (name, flags) in enumerate(agent_flags.items(), start=2):
        flags = np.asarray(flags).astype(int)
        axes[idx].plot(x, flags[::step], linewidth=0.7)
        axes[idx].set_ylabel(name)
        axes[idx].set_yticks([0, 1])

    axes[-1].set_xlabel("Sample index")

    plt.tight_layout()
    plt.savefig(output_file, dpi=200)
    plt.close()


def hysteresis_expand(
    flags: np.ndarray,
    anchor_score: np.ndarray,
    low_threshold: float,
    max_extend: int = 1500,
    extend_left: bool = True,
    extend_right: bool = True,
) -> np.ndarray:
    """
    Stretch each predicted interval to the left/right while anchor_score stays
    above low_threshold. max_extend limits how far one interval can grow
    """
    flags = np.asarray(flags).astype(int).copy()
    anchor_score = np.asarray(anchor_score, dtype=float)

    if len(flags) != len(anchor_score):
        raise ValueError(
            f"hysteresis_expand: flags and anchor_score length mismatch "
            f"({len(flags)} vs {len(anchor_score)})"
        )

    n = len(flags)
    expanded = flags.copy()

    intervals = find_intervals(flags)

    for start, end in intervals:
        if extend_left:
            i = start - 1
            steps = 0
            while i >= 0 and anchor_score[i] > low_threshold and steps < max_extend:
                if expanded[i] == 1:
                    break
                expanded[i] = 1
                i -= 1
                steps += 1

        if extend_right:
            i = end + 1
            steps = 0
            while i < n and anchor_score[i] > low_threshold and steps < max_extend:
                if expanded[i] == 1:
                    break
                expanded[i] = 1
                i += 1
                steps += 1

    return expanded.astype(int)


def compute_etapr(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    theta_p: float = 0.5,
    theta_r: float = 0.1,
    delta: float = 0.0,
) -> dict[str, float]:
    """eTaPR from the official HAI package (wshw4ng/eTaPR); 0 = normal, 1 = attack"""
    from eTaPR_pkg import etapr

    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)

    true_intervals = find_intervals(y_true)
    pred_intervals = find_intervals(y_pred)

    result = etapr.evaluate_w_streams(
        y_true.tolist(),
        y_pred.tolist(),
        theta_p=theta_p,
        theta_r=theta_r,
        delta=delta,
    )

    detected = result.get("Detected_Anomalies") or []
    correct = result.get("Correct_Predictions") or []

    return {
        "theta_p": theta_p,
        "theta_r": theta_r,
        "delta": delta,
        "true_intervals": len(true_intervals),
        "predicted_intervals": len(pred_intervals),
        "detected_true_intervals": len(detected),
        "useful_predicted_intervals": len(correct),
        "false_alarm_intervals": int(result.get("N False Alarm", 0)),
        "eta_precision": float(result["eTaP"]),
        "eta_recall": float(result["eTaR"]),
        "eta_f1": float(result["f1"]),
        "eta_precision_detection": float(result["eTaPd"]),
        "eta_precision_portion": float(result["eTaPp"]),
        "eta_recall_detection": float(result["eTaRd"]),
        "eta_recall_portion": float(result["eTaRp"]),
        "point_precision": float(result.get("precision", 0.0)),
        "point_recall": float(result.get("recall", 0.0)),
        "point_adjust_precision": float(result.get("point_adjust_precision", 0.0)),
        "point_adjust_recall": float(result.get("point_adjust_recall", 0.0)),
    }


def build_inscope_keep_mask(target_mask: np.ndarray, full_labels: np.ndarray) -> np.ndarray:
    """Keep target attacks and normal data; other attacks are left out (not counted as FP)"""
    target_mask = np.asarray(target_mask).astype(int)
    full_labels = np.asarray(full_labels).astype(int)
    in_target = target_mask == 1
    is_normal = full_labels == 0
    return in_target | is_normal