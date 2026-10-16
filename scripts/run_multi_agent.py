"""Train the six agents, run the orchestrator and save metrics, plots and the model"""

import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config
from src.agents import (
    ConsistencyAgent,
    ControlOutputAgent,
    LSTMAutoencoderAgent,
    P1P4SentinelAgent,
    ProtectionAgent,
    SetpointAgent,
)
from src.data_loader import load_hai_data
from src.evaluation import (
    compute_interval_metrics,
    compute_sample_metrics,
    plot_agent_timeline,
    plot_binary_timeline,
    plot_confusion_matrix,
    plot_score_timeline,
    save_metrics,
    save_predictions,
)
from src.orchestrator import Orchestrator
from src.orchestrator_physics import OrchestratorPhysics
from src.score_calibration import AgentScoreCalibrator

NAME = "multi_agent_cross_residual"


def _evt_kwargs() -> dict:
    return {
        "use_evt_threshold": config.USE_EVT_THRESHOLD,
        "evt_init_level": config.EVT_INIT_LEVEL,
        "evt_tail_prob": config.EVT_TAIL_PROB,
        "evt_min_exceedances": config.EVT_MIN_EXCEEDANCES,
        "evt_fallback_quantile": config.EVT_FALLBACK_QUANTILE,
    }


def build_agents() -> list:
    agents = [
        SetpointAgent(
            variables=config.SETPOINT_AGENT_VARS,
            z_threshold=config.SETPOINT_Z_THRESHOLD,
            residual_quantile=config.SETPOINT_RESIDUAL_QUANTILE,
            drift_short_window=config.SETPOINT_DRIFT_SHORT_WINDOW,
            drift_long_window=config.SETPOINT_DRIFT_LONG_WINDOW,
            **_evt_kwargs(),
        ),
        ControlOutputAgent(
            variables=config.CONTROL_OUTPUT_AGENT_VARS,
            n_estimators=config.CONTROL_AGENT_IF_N_ESTIMATORS,
            contamination=config.CONTROL_AGENT_IF_CONTAMINATION,
            random_state=config.RANDOM_STATE,
            **_evt_kwargs(),
        ),
    ]

    if config.USE_LSTM_AGENT:
        agents.append(
            LSTMAutoencoderAgent(
                variables=config.LSTM_AGENT_VARS,
                window_size=config.LSTM_WINDOW_SIZE,
                train_stride=config.LSTM_TRAIN_STRIDE,
                prediction_stride=config.LSTM_PREDICTION_STRIDE,
                hidden_dim=config.LSTM_HIDDEN_DIM,
                epochs=config.LSTM_EPOCHS,
                batch_size=config.LSTM_BATCH_SIZE,
                learning_rate=config.LSTM_LEARNING_RATE,
                threshold_quantile=config.LSTM_THRESHOLD_QUANTILE,
                max_train_windows=config.LSTM_MAX_TRAIN_WINDOWS,
                random_state=config.RANDOM_STATE,
                **_evt_kwargs(),
            )
        )

    agents += [
        ProtectionAgent(variables=config.PROTECTION_AGENT_VARS),
        ConsistencyAgent(
            variables=config.CONSISTENCY_AGENT_VARS,
            residual_quantile=config.CONSISTENCY_RESIDUAL_QUANTILE,
            **_evt_kwargs(),
        ),
        P1P4SentinelAgent(
            variables=config.P1P4_SENTINEL_AGENT_VARS,
            window_seconds=config.P1P4_SENTINEL_WINDOW_SECONDS,
            long_window_seconds=config.P1P4_SENTINEL_LONG_WINDOW_SECONDS,
            **_evt_kwargs(),
        ),
    ]
    return agents


def evaluate_and_save(y_true, y_pred, scores, details) -> dict:
    metrics = {
        "method": NAME,
        **compute_sample_metrics(y_true, y_pred),
        **compute_interval_metrics(y_true, y_pred),
    }
    save_metrics(metrics, config.RESULTS_DIR / f"{NAME}_metrics.csv")

    extra = {
        col: details[col].values
        for col in details.columns
        if col not in ["orchestrator_prediction", "orchestrator_score"]
    }
    save_predictions(
        y_true=y_true,
        y_pred=y_pred,
        scores=scores,
        output_file=config.RESULTS_DIR / f"{NAME}_predictions.csv.gz",
        extra=extra,
    )

    plot_confusion_matrix(
        y_true=y_true,
        y_pred=y_pred,
        title=f"{NAME} confusion matrix",
        output_file=config.FIGURES_DIR / f"{NAME}_confusion_matrix.png",
    )
    plot_binary_timeline(
        y_true=y_true,
        y_pred=y_pred,
        title=f"{NAME}: predictions vs labels",
        output_file=config.FIGURES_DIR / f"{NAME}_predictions_vs_labels.png",
    )
    plot_score_timeline(
        y_true=y_true,
        scores=scores,
        title=f"{NAME}: orchestrator scores vs labels",
        output_file=config.FIGURES_DIR / f"{NAME}_scores_vs_labels.png",
    )
    return metrics


def main() -> None:
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if config.USE_MULTIPLE_FILES:
        train_arg, test_arg, label_arg = config.TRAIN_FILES, config.TEST_FILES, config.LABEL_FILES
    else:
        train_arg, test_arg, label_arg = config.TRAIN_FILE, config.TEST_FILE, config.LABEL_FILE

    data = load_hai_data(
        train_file=train_arg,
        test_file=test_arg,
        label_file=label_arg,
        selected_vars=config.FINAL_SELECTED_VARS,
    )

    print(f"Train samples: {len(data.train)}")
    print(f"Test samples:  {len(data.test)}")
    print(f"Attack samples in test: {int(data.labels.sum())}")
    print(f"Variables: {len(data.available_vars)}")

    if data.missing_vars:
        print("Missing variables ignored:")
        for var in data.missing_vars:
            print(f"  - {var}")

    agents = build_agents()
    outputs = []
    train_outputs = []

    for agent in agents:
        print(f"\nAgent: {agent.name}")
        agent.fit(data.train)
        train_outputs.append(agent.predict(data.train))
        output = agent.predict(data.test)
        outputs.append(output)
        print(f"  variables used: {len(output.variables)}")
        print(f"  predicted anomaly samples: {int(output.flags.sum())}")

    print("\nIndividual agent metrics:")
    agent_rows = []
    for output in outputs:
        row = {
            "method": output.name,
            "variables_used": len(output.variables),
            **compute_sample_metrics(data.labels, output.flags),
            **compute_interval_metrics(data.labels, output.flags),
        }
        agent_rows.append(row)
        print(
            f"  {output.name}: precision={row['precision']:.3f} recall={row['recall']:.3f} "
            f"f1={row['f1']:.3f} interval_f1={row['interval_f1']:.3f}"
        )
    pd.DataFrame(agent_rows).to_csv(config.RESULTS_DIR / "individual_agent_metrics.csv", index=False)

    # Each agent score is divided by its q99 on train, so scores become comparable
    calibrator = AgentScoreCalibrator()
    for out in train_outputs:
        calibrator.fit(out.name, out.scores)

    physics = OrchestratorPhysics.fit(
        data.train,
        chain_lag_seconds=config.EVIDENCE_CHAIN_LAG_SECONDS,
        lstm_min_run_seconds=config.EVIDENCE_LSTM_MIN_RUN_SECONDS,
        lstm_norm_threshold=config.EVIDENCE_LSTM_NORM_THRESHOLD,
        po_residual_quantile=config.EVIDENCE_PO_RESIDUAL_QUANTILE,
    )

    # The output of this step is the input of apply_orchestrator_final.py
    orchestrator = Orchestrator(
        min_votes=config.ORCHESTRATOR_MIN_VOTES,
        vote_exclude_agents=config.VOTE_EXCLUDE_AGENTS,
        vote_agent_groups=config.VOTE_AGENT_GROUPS if config.USE_VOTE_AGENT_GROUPS else None,
    )
    y_pred, scores, details = orchestrator.aggregate(outputs, calibrator, data.test, physics)
    metrics = evaluate_and_save(data.labels, y_pred, scores, details)

    plot_agent_timeline(
        y_true=data.labels,
        final_pred=y_pred,
        agent_flags={output.name: output.flags for output in outputs},
        output_file=config.FIGURES_DIR / f"{NAME}_agent_timeline.png",
    )

    joblib.dump(
        {
            "agents": agents,
            "variables": data.available_vars,
            "calibrator": calibrator,
            "train_agent_outputs": {
                out.name: {"scores": out.scores, "flags": out.flags} for out in train_outputs
            },
            "physics": physics,
        },
        config.MODELS_DIR / "multi_agent_system.pkl",
    )

    print(f"\nOrchestrator: interval_f1={metrics['interval_f1']:.4f}, fp={metrics['fp']}")


if __name__ == "__main__":
    main()
