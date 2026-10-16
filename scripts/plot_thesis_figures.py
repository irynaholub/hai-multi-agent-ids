"""Plots saved to results/figures (fig1-fig5), the dashboard sidebar shows them"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

from src import config
from src.evaluation import build_inscope_keep_mask, compute_etapr, find_intervals

OUT = config.RESULTS_DIR / "figures"
OUT.mkdir(parents=True, exist_ok=True)

C_OLD = "#5B8DB8"    # baseline
C_NEW = "#3E9B6C"    # orchestrator
C_GT = "#D94F3D"     # ground truth
C_SHADE = "#F0F4FA"  # attack window background

AGENT_COLORS = ["#5B8DB8", "#E8A838", "#3E9B6C", "#D94F3D", "#9B59B6", "#1ABC9C"]
LABEL_BASELINE = "Базова модель\nIsolation Forest"
LABEL_PROPOSED = "Оркестратор"

AGENT_LABELS = {
    "SetpointAgent_flag": "Агент уставок",
    "ControlOutputAgent_flag": "Керуючі виходи",
    "LSTMAutoencoderAgent_flag": "LSTM-автоенкодер",
    "ProtectionAgent_flag": "Захист P2",
    "ConsistencyAgent_flag": "Узгодженість P1/P2/P4",
    "P1P4SentinelAgent_flag": "Sentinel P1/P4",
}
agent_cols = list(AGENT_LABELS.keys())

# Data
cr_df = pd.read_csv(config.RESULTS_DIR / "multi_agent_cross_residual_predictions.csv.gz")
cc_df = pd.read_csv(config.RESULTS_DIR / "multi_agent_orchestrator_final_predictions.csv")
bl_path = config.RESULTS_DIR / "baseline_predictions.csv"
bl_df = pd.read_csv(bl_path) if bl_path.exists() else None

y_true = cr_df["label"].values.astype(int)
target_mask = pd.read_csv(config.RESULTS_DIR / "p2_target_attacks_mask.csv")["label"].values
keep = build_inscope_keep_mask(target_mask, y_true)

pred_cc = cc_df["prediction"].values.astype(int)
pred_bl = bl_df["prediction"].values.astype(int) if bl_df is not None else None

target_intervals = find_intervals(target_mask)


def etapr_n(pred):
    pred = np.asarray(pred).astype(int)
    return compute_etapr(y_true[keep], pred[keep], theta_p=0.5, theta_r=0.1)


res_bl = etapr_n(pred_bl) if pred_bl is not None else None
res_cc = etapr_n(pred_cc)


def fig1_comparison():
    """eTaF1 / eTaP / eTaR bars for the baseline and the orchestrator"""
    methods, colors, values = [], [], []
    if res_bl is not None:
        methods.append(LABEL_BASELINE)
        colors.append(C_OLD)
        values.append([res_bl["eta_f1"], res_bl["eta_precision"], res_bl["eta_recall"]])
    methods.append(LABEL_PROPOSED)
    colors.append(C_NEW)
    values.append([res_cc["eta_f1"], res_cc["eta_precision"], res_cc["eta_recall"]])
    metrics = ["eTaF1", "eTaP", "eTaR"]

    x = np.arange(len(metrics))
    width = 0.24
    fig, ax = plt.subplots(figsize=(9, 5.5))
    fig.patch.set_facecolor("white")

    for i, (method, color, vals) in enumerate(zip(methods, colors, values)):
        offset = (i - 1) * width
        bars = ax.bar(x + offset, vals, width, label=method, color=color,
                      edgecolor="white", linewidth=0.8, zorder=3)
        for bar, v in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.014,
                f"{v:.3f}",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
                color=color,
                clip_on=False,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=13, fontweight="bold")
    ax.set_ylabel("Score", fontsize=12)
    ax.set_xlabel("Metric", fontsize=12)
    ax.set_title("Цільові P2-атаки: eTaPR за методами\n(θ_p = 0.5, θ_r = 0.1)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_ylim(0, 1.14)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(
        fontsize=9.5,
        framealpha=0.9,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.0),
        ncol=2,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUT / "fig1_method_comparison.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("  [saved] fig1_method_comparison.png")


def fig2_agent_heatmap():
    """Mean flag of every agent inside each target attack window"""
    attack_names = [f"A{i + 1}" for i in range(len(target_intervals))]
    n_attacks = len(target_intervals)
    n_agents = len(agent_cols)
    heatmap = np.zeros((n_agents, n_attacks))

    for j, (s, e) in enumerate(target_intervals):
        seg = cr_df.iloc[s:e + 1]
        for i, col in enumerate(agent_cols):
            if col in seg.columns:
                heatmap[i, j] = seg[col].mean()

    fig, ax = plt.subplots(figsize=(max(6, n_attacks * 1.3), 4.5))
    fig.patch.set_facecolor("white")
    im = ax.imshow(heatmap, aspect="auto", cmap="YlOrRd", vmin=0, vmax=1,
                   interpolation="nearest")

    for i in range(n_agents):
        for j in range(n_attacks):
            val = heatmap[i, j]
            color = "white" if val > 0.55 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=9, color=color, fontweight="bold")

    ax.set_xticks(range(n_attacks))
    ax.set_xticklabels(attack_names, fontsize=10, fontweight="bold")
    ax.set_yticks(range(n_agents))
    ax.set_yticklabels([AGENT_LABELS[c] for c in agent_cols], fontsize=10)
    ax.set_xlabel("Attack scenario", fontsize=11)
    ax.set_ylabel("Agent", fontsize=11)
    ax.set_title("Середня активність агентів у вікні кожної цільової P2-атаки",
                 fontsize=12, fontweight="bold", pad=10)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Mean flag (0 = silent, 1 = always active)", fontsize=9)

    plt.tight_layout()
    plt.savefig(OUT / "fig2_agent_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("  [saved] fig2_agent_heatmap.png")


def fig3_per_attack():
    """Recall and precision of the orchestrator for each target attack"""
    attack_names = [f"Attack {i + 1}" for i in range(len(target_intervals))]
    summary_path = config.RESULTS_DIR / "p2_target_attacks_summary.csv"
    if summary_path.exists():
        summary_df = pd.read_csv(summary_path)
        if "scenario" in summary_df.columns and len(summary_df) >= len(target_intervals):
            attack_names = summary_df["scenario"].astype(str).tolist()[: len(target_intervals)]

    recalls = []
    precisions = []
    pred_ints = find_intervals(pred_cc)

    for s, e in target_intervals:
        atk_len = e - s + 1
        # Share of the attack covered by predictions
        covered = sum(
            max(0, min(e, pe) - max(s, ps) + 1)
            for ps, pe in pred_ints
        )
        recalls.append(min(1.0, covered / atk_len))

        # For each predicted interval touching the attack: overlap / interval length
        prec_parts = []
        for ps, pe in pred_ints:
            ovl = max(0, min(e, pe) - max(s, ps) + 1)
            if ovl > 0:
                prec_parts.append(ovl / (pe - ps + 1))
        precisions.append(float(np.mean(prec_parts)) if prec_parts else 0.0)

    x = np.arange(len(attack_names))
    width = 0.35
    fig, ax = plt.subplots(figsize=(max(7.5, len(attack_names) * 1.7), 5.6))
    fig.patch.set_facecolor("white")

    br = ax.bar(x - width / 2, recalls, width, label="Recall (coverage)",
                color=C_NEW, edgecolor="white", zorder=3)
    bp = ax.bar(x + width / 2, precisions, width, label="Precision (purity)",
                color=C_OLD, edgecolor="white", zorder=3)

    label_dy = 0.022

    def _bar_label(bar, value: float, color: str, y: float) -> None:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=color,
            clip_on=False,
        )

    for bar_r, bar_p, rec, prec in zip(br, bp, recalls, precisions):
        y_r = bar_r.get_height() + label_dy
        y_p = bar_p.get_height() + label_dy
        # Move the blue label up if it would overlap the green one
        if abs(y_p - y_r) < 0.055:
            y_p = y_r + 0.055
        _bar_label(bar_r, rec, C_NEW, y_r)
        _bar_label(bar_p, prec, C_OLD, y_p)

    ax.axhline(0.5, color="grey", linestyle="--", linewidth=1,
               label="θ_p = θ detection = 0.5", zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels(attack_names, fontsize=11, fontweight="bold")
    ax.set_ylabel("Score", fontsize=12)
    ax.set_xlabel("Сценарій атаки (цільові P2)", fontsize=12)
    ax.set_ylim(0, 1.08)
    ax.yaxis.grid(True, linestyle="--", alpha=0.45, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.suptitle(
        "Покриття recall та precision по атаках\n(оркестратор)",
        fontsize=12,
        fontweight="bold",
        y=1.02,
    )
    ax.legend(
        fontsize=9,
        framealpha=0.95,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.0),
        ncol=3,
        columnspacing=1.2,
        handletextpad=0.5,
    )

    fig.subplots_adjust(top=0.82, bottom=0.14, left=0.10, right=0.98)
    plt.savefig(
        OUT / "fig3_per_attack_coverage.png",
        dpi=200,
        bbox_inches="tight",
        pad_inches=0.22,
    )
    plt.close()
    print("  [saved] fig3_per_attack_coverage.png")


def fig4_timeline():
    """Ground truth, predictions and every agent flag around the longest target attack"""
    atk_idx = int(np.argmax([e - s for s, e in target_intervals]))
    s_raw, e_raw = target_intervals[atk_idx]
    margin = 600
    s = max(0, s_raw - margin)
    e = min(len(y_true) - 1, e_raw + margin)

    x = np.arange(e - s + 1)

    rows = ["Еталон", LABEL_PROPOSED.replace("\n", " ")]
    signals = [y_true[s:e + 1].astype(float), pred_cc[s:e + 1].astype(float)]
    row_colors = [C_GT, C_NEW]
    if pred_bl is not None:
        rows.insert(2, LABEL_BASELINE.replace("\n", " "))
        signals.insert(2, pred_bl[s:e + 1].astype(float))
        row_colors.insert(2, C_OLD)
    rows += [AGENT_LABELS[c] for c in agent_cols]
    signals += [cr_df[c].values[s:e + 1].astype(float) for c in agent_cols]
    row_colors += AGENT_COLORS

    n_rows = len(rows)
    fig = plt.figure(figsize=(14, 2.2 * n_rows))
    fig.patch.set_facecolor("white")
    gs = GridSpec(n_rows, 1, hspace=0.12, figure=fig)

    for idx, (row, sig, col) in enumerate(zip(rows, signals, row_colors)):
        ax = fig.add_subplot(gs[idx])
        ax.axvspan(s_raw - s, e_raw - s, color=C_SHADE, zorder=1, label="attack window")
        ax.fill_between(x, 0, sig, color=col, alpha=0.82, step="post", zorder=2)
        ax.set_yticks([0, 1])
        ax.set_yticklabels(["0", "1"], fontsize=7)
        ax.set_ylim(-0.08, 1.35)
        ax.set_ylabel(row, fontsize=8.5, rotation=0, ha="right", va="center",
                      labelpad=62)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        if idx < n_rows - 1:
            ax.set_xticks([])
        else:
            ax.set_xlabel("Time offset (seconds)", fontsize=11)
            ax.xaxis.set_tick_params(labelsize=9)

    fig.axes[0].set_title(
        f"Таймлайн агентів: цільова P2-атака #{atk_idx + 1} (±{margin} с)",
        fontsize=12, fontweight="bold", pad=8)

    handles = [
        mpatches.Patch(color=C_SHADE, label="Ground-truth attack window"),
        mpatches.Patch(color=C_GT, label="Ground truth"),
        mpatches.Patch(color=C_NEW, label=LABEL_PROPOSED.replace("\n", " ")),
        mpatches.Patch(color=C_OLD, label=LABEL_BASELINE.replace("\n", " ")),
    ]
    fig.legend(handles=handles, loc="upper right", fontsize=8.5,
               framealpha=0.9, ncol=2, bbox_to_anchor=(0.99, 0.99))

    plt.savefig(OUT / "fig4_timeline.png", dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  [saved] fig4_timeline.png  (attack #{atk_idx + 1}, rows={s_raw}:{e_raw})")


def fig5_false_alarms():
    """Number of predicted intervals that touch no target attack"""
    def fa_count(pred):
        pred = np.asarray(pred).astype(int)
        return sum(
            1 for ps, pe in find_intervals(pred)
            if not np.any(y_true[ps:pe + 1].astype(bool) & target_mask[ps:pe + 1].astype(bool))
        )

    methods, fa_vals, colors = [], [], []
    if pred_bl is not None:
        methods.append(LABEL_BASELINE)
        fa_vals.append(fa_count(pred_bl))
        colors.append(C_OLD)
    methods.append(LABEL_PROPOSED)
    fa_vals.append(fa_count(pred_cc))
    colors.append(C_NEW)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    fig.patch.set_facecolor("white")
    bars = ax.bar(methods, fa_vals, color=colors, edgecolor="white",
                  linewidth=0.8, width=0.5, zorder=3)

    for bar, v in zip(bars, fa_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                str(v), ha="center", va="bottom", fontsize=14, fontweight="bold")

    ax.set_ylabel("Number of false-alarm intervals", fontsize=12)
    ax.set_xlabel("Method", fontsize=12)
    ax.set_title("Кількість хибних інтервалів\n(цільові P2-атаки)",
                 fontsize=12, fontweight="bold", pad=10)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(OUT / "fig5_false_alarms.png", dpi=200, bbox_inches="tight")
    plt.close()
    print("  [saved] fig5_false_alarms.png")


if __name__ == "__main__":
    print(f"Saving figures to {OUT}")
    fig1_comparison()
    fig2_agent_heatmap()
    fig3_per_attack()
    fig4_timeline()
    fig5_false_alarms()
