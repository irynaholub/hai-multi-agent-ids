"""Streamlit dashboard: metrics, agent timeline and GPT incident reports"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from app.dashboard_bundle import (
    build_events,
    etapr_p2_target,
    false_alarm_count,
    interval_label,
    load_detection_bundle,
)
from app.ui_labels import AGENT_COLS, AGENT_DISPLAY
from src import config
from src.llm_judge import LLMJudge

METHOD_BASELINE = "Базова модель Isolation Forest"
METHOD_PROPOSED = "Оркестратор"
TARGET_ATTACKS_TOTAL = 5
LLM_MODEL = "gpt-4o-mini"
TIMELINE_MARGIN = 400

GREEN, BLUE, PURPLE, RED, AMBER = "#3E9B6C", "#5B8DB8", "#9B59B6", "#D94F3D", "#E8A838"
AGENT_COLORS = [BLUE, AMBER, GREEN, RED, PURPLE, "#1ABC9C"]

PLOTLY_STATIC = {
    "staticPlot": True,
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False,
}

st.set_page_config(
    page_title="HAI Multi-Agent IDS",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .kpi-box {
        border-radius: 10px;
        padding: 0.9rem 1rem;
        color: white;
        margin-bottom: 0.6rem;
    }
    .kpi-title { font-size: 0.9rem; opacity: 0.95; }
    .kpi-value { font-size: 1.6rem; font-weight: 700; }
    .delta-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(120px, 1fr));
        gap: 10px;
        margin: 8px 0 14px 0;
    }
    .delta-card {
        border-radius: 10px;
        padding: 0.8rem;
        color: white;
        text-align: center;
    }
    .delta-label { font-size: 0.9rem; opacity: 0.95; }
    .delta-value { font-size: 1.3rem; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Завантаження результатів...")
def cached_bundle():
    return load_detection_bundle()


def show_plotly(fig: go.Figure) -> None:
    fig.update_layout(dragmode=False)
    st.plotly_chart(fig, width="stretch", config=PLOTLY_STATIC)


def format_report_body(text: str) -> str:
    """Drop the [SEVERITY: ...] line, the badge shows it instead"""
    lines = [line for line in text.splitlines() if "[SEVERITY:" not in line.upper()]
    return "\n".join(lines).strip()


def severity_badge(severity: str) -> str:
    colors = {"HIGH": RED, "MEDIUM": AMBER, "LOW": GREEN}
    c = colors.get(severity.upper(), BLUE)
    return (
        f'<span style="background:{c};color:white;padding:4px 10px;'
        f'border-radius:4px;font-weight:600;">{severity}</span>'
    )


def plot_timeline(
    cr: pd.DataFrame,
    y_true: np.ndarray,
    pred: np.ndarray,
    start: int,
    end: int,
    title: str,
) -> go.Figure:
    s = max(0, start - TIMELINE_MARGIN)
    e = min(len(y_true) - 1, end + TIMELINE_MARGIN)
    x = np.arange(s, e + 1)

    rows = [f"Прогноз ({METHOD_PROPOSED})"] + [
        AGENT_DISPLAY.get(c.replace("_flag", ""), c) for c in AGENT_COLS
    ]
    fig = make_subplots(
        rows=len(rows),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        subplot_titles=rows,
    )

    fig.add_trace(
        go.Scatter(x=x, y=pred[s : e + 1], mode="lines", line=dict(color=GREEN, width=1),
                   showlegend=False),
        row=1, col=1,
    )

    for i, col in enumerate(AGENT_COLS):
        if col not in cr.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=x,
                y=cr[col].values[s : e + 1],
                mode="lines",
                line=dict(color=AGENT_COLORS[i % len(AGENT_COLORS)], width=1),
                showlegend=False,
            ),
            row=2 + i,
            col=1,
        )

    # Highlight the detected interval (not the ground truth)
    fig.add_vrect(
        x0=start, x1=end, fillcolor="rgba(91,141,184,0.15)",
        line_width=0, row="all", col=1,
    )

    fig.update_yaxes(title_text="Прапорець (0/1)", tickvals=[0, 1], row=1, col=1)
    for r in range(2, len(rows) + 1):
        fig.update_yaxes(tickvals=[0, 1], row=r, col=1)

    fig.update_xaxes(title_text="Час (індекс зразка, 1 Гц = 1 с)", row=len(rows), col=1)
    fig.update_layout(
        height=180 * len(rows),
        title=title,
        showlegend=False,
        margin=dict(l=40, r=20, t=50, b=40),
        dragmode=False,
    )
    return fig


def render_overview(y_true, keep, target_mask, pred_cc, pred_baseline) -> None:
    methods = []
    if pred_baseline is not None:
        methods.append((METHOD_BASELINE, pred_baseline, BLUE))
    methods.append((METHOD_PROPOSED, pred_cc, GREEN))

    results = {
        name: (etapr_p2_target(y_true, pred, keep), false_alarm_count(pred, y_true, target_mask))
        for name, pred, _ in methods
    }
    m_final, fa_final = results[METHOD_PROPOSED]

    kpis = [
        ("Фінальний eTaF1", f"{m_final['eta_f1']:.3f}", GREEN),
        ("Фінальний eTaP", f"{m_final['eta_precision']:.3f}", BLUE),
        ("Фінальний eTaR", f"{m_final['eta_recall']:.3f}", PURPLE),
        ("Хибні інтервали", f"{fa_final}", RED),
    ]
    for col, (title, value, color) in zip(st.columns(4), kpis):
        col.markdown(
            f'<div class="kpi-box" style="background:{color};">'
            f'<div class="kpi-title">{title}</div>'
            f'<div class="kpi-value">{value}</div></div>',
            unsafe_allow_html=True,
        )

    metrics_rows = []
    for col, (name, _, _) in zip(st.columns(len(methods)), methods):
        m, fa = results[name]
        with col:
            st.subheader(name)
            st.metric("eTaF1", f"{m['eta_f1']:.3f}")
            st.metric("eTaP (precision)", f"{m['eta_precision']:.3f}")
            st.metric("eTaR (recall)", f"{m['eta_recall']:.3f}")
            st.metric("Цільові P2-атаки", f"{m['detected_true_intervals']}/{TARGET_ATTACKS_TOTAL}")
            st.metric("Хибні інтервали", fa)
        metrics_rows.append({
            "Метод": name,
            "eTaF1": m["eta_f1"],
            "eTaP": m["eta_precision"],
            "eTaR": m["eta_recall"],
            "Виявлено": m["detected_true_intervals"],
            "FA": fa,
        })

    st.divider()
    st.subheader("Порівняння eTaPR (цільові P2-атаки)")
    st.dataframe(
        pd.DataFrame(metrics_rows).style.format({"eTaF1": "{:.3f}", "eTaP": "{:.3f}", "eTaR": "{:.3f}"}),
        width="stretch",
        hide_index=True,
    )

    fig_cmp = go.Figure()
    for name, _, color in methods:
        m, _ = results[name]
        values = [m["eta_f1"], m["eta_precision"], m["eta_recall"]]
        fig_cmp.add_trace(go.Bar(
            name=name,
            x=["eTaF1", "eTaP", "eTaR"],
            y=values,
            marker_color=color,
            text=[f"{v:.3f}" for v in values],
            textposition="outside",
        ))
    fig_cmp.update_layout(
        barmode="group",
        yaxis_title="Оцінка eTaPR",
        xaxis_title="Метрика",
        yaxis=dict(range=[0, 1.08]),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        dragmode=False,
    )
    show_plotly(fig_cmp)

    if pred_baseline is None:
        return

    m_base, fa_base = results[METHOD_BASELINE]
    d_f1 = m_final["eta_f1"] - m_base["eta_f1"]
    d_p = m_final["eta_precision"] - m_base["eta_precision"]
    d_r = m_final["eta_recall"] - m_base["eta_recall"]
    d_fa = fa_final - fa_base

    st.subheader("Покращення запропонованого методу відносно baseline")
    # (label, shown value, is it an improvement)
    deltas = [
        ("Δ eTaF1", f"{d_f1:+.3f}", d_f1 >= 0),
        ("Δ eTaP", f"{d_p:+.3f}", d_p >= 0),
        ("Δ eTaR", f"{d_r:+.3f}", d_r >= 0),
        ("Δ FA", f"{d_fa:+d}", d_fa <= 0),
    ]
    cards = "".join(
        f'<div class="delta-card" style="background:{GREEN if good else RED}">'
        f'<div class="delta-label">{label}</div><div class="delta-value">{value}</div></div>'
        for label, value, good in deltas
    )
    st.markdown(f'<div class="delta-grid">{cards}</div>', unsafe_allow_html=True)
    for col, (label, value, _) in zip(st.columns(4), deltas):
        col.metric(label, value)

    gains = [d_f1, d_p, d_r]
    fig_gain = go.Figure(go.Bar(
        x=["eTaF1", "eTaP", "eTaR"],
        y=gains,
        marker_color=[GREEN if v >= 0 else RED for v in gains],
        text=[f"{v:+.3f}" for v in gains],
        textposition="outside",
    ))
    fig_gain.update_layout(
        height=320,
        xaxis_title="Метрика",
        yaxis_title="Δ (proposed − baseline)",
        yaxis=dict(zeroline=True, zerolinewidth=1),
        dragmode=False,
    )
    show_plotly(fig_gain)


def render_timeline(events, tp_events, cr, y_true, pred_cc) -> None:
    if not events:
        st.warning("Немає детектованих інтервалів.")
        return

    show_fp = st.checkbox(
        "Показувати хибні спрацювання (FP)",
        value=False,
        help="За замовчуванням — лише цільові P2-атаки (TP).",
    )
    timeline_events = events if show_fp else (tp_events or events)
    if not show_fp and tp_events:
        st.caption("Відображаються інтервали з перетином цільових P2-атак.")

    labels = [interval_label(e) for e in timeline_events]
    idx = st.selectbox(
        "Інтервал детекції",
        range(len(timeline_events)),
        format_func=lambda i: labels[i],
    )
    ev = timeline_events[idx]
    agents_ua = ", ".join(AGENT_DISPLAY.get(a, a) for a in ev.active_agents) or "—"
    st.write(
        f"**Активні агенти:** {agents_ua}  ·  "
        f"ланцюг={ev.chain_flag}  залишок={ev.residual_flag}  голосування={ev.vote_flag}"
    )
    show_plotly(plot_timeline(cr, y_true, pred_cc, ev.start_row, ev.end_row, title=f"Таймлайн: {labels[idx]}"))

    if not ev.agent_scores:
        return

    sc = pd.DataFrame([
        {"Агент": AGENT_DISPLAY.get(k, k), "Середня нормована оцінка": v}
        for k, v in sorted(ev.agent_scores.items(), key=lambda x: -x[1])
    ])
    fig_sc = go.Figure(go.Bar(
        x=sc["Середня нормована оцінка"],
        y=sc["Агент"],
        orientation="h",
        marker_color=BLUE,
        text=sc["Середня нормована оцінка"].round(2),
        textposition="outside",
    ))
    fig_sc.update_layout(
        title="Аномальні оцінки агентів у вікні",
        xaxis_title="Нормована оцінка",
        yaxis_title="Агент",
        height=280,
        dragmode=False,
    )
    show_plotly(fig_sc)


def render_llm_report(tp_events) -> None:
    st.subheader("Аналіз події")
    st.caption("Звіт для оператора лише по **цільових P2-атаках**.")

    if not tp_events:
        st.warning("Немає істинних інтервалів (цільові P2-атаки) для аналізу.")
        return

    idx = st.selectbox(
        "Оберіть інтервал",
        range(len(tp_events)),
        format_func=lambda i: interval_label(tp_events[i]),
        key="llm_interval",
    )
    ev = tp_events[idx]

    c1, c2 = st.columns(2)
    c1.metric("Початок", ev.timestamp_start)
    c2.metric("Кінець", ev.timestamp_end)

    if st.button("Згенерувати звіт", type="primary", width="stretch"):
        with st.spinner("Генерація звіту…"):
            try:
                report = LLMJudge(model=LLM_MODEL).explain(ev)
            except Exception as e:
                st.error(str(e))
                st.info("Перевірте баланс OpenAI та ключ у файлі `.env`.")
                st.stop()

        st.markdown(severity_badge(report.severity), unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(format_report_body(report.text))


def main() -> None:
    st.title("HAI Multi-Agent IDS — панель оператора")
    st.caption("Мультиагентна детекція · baseline vs proposed · аналіз подій")

    try:
        bundle = cached_bundle()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    cr = bundle["cr"]
    y_true = bundle["y_true"]
    pred_cc = bundle["pred_cc"]

    if pred_cc is None:
        st.warning(
            "Немає прогнозів оркестратора. Запустіть: "
            "`python scripts/apply_orchestrator_final.py`"
        )
        st.stop()

    events = build_events(pred_cc, cr, y_true, bundle["target_mask"], bundle.get("timestamps"))
    tp_events = [e for e in events if e.extra.get("is_true_positive") == "True"]

    with st.sidebar:
        st.header("Інформація")
        st.markdown("**Порівняння методів**")
        st.markdown(f"- **{METHOD_PROPOSED}** — запропонований підхід")
        st.markdown(f"- **{METHOD_BASELINE}**")
        fig_dir = config.RESULTS_DIR / "figures"
        if fig_dir.exists() and any(fig_dir.glob("fig*.png")):
            st.divider()
            st.markdown("**Збережені графіки**")
            for p in sorted(fig_dir.glob("fig*.png")):
                st.image(str(p), caption=p.stem, width="stretch")

    tab_overview, tab_timeline, tab_llm = st.tabs(
        ["Огляд метрик", "Таймлайн агентів", "Аналіз події"]
    )
    with tab_overview:
        render_overview(y_true, bundle["keep"], bundle["target_mask"], pred_cc, bundle["pred_baseline"])
    with tab_timeline:
        render_timeline(events, tp_events, cr, y_true, pred_cc)
    with tab_llm:
        render_llm_report(tp_events)


if __name__ == "__main__":
    main()
