"""Baseline: a single Isolation Forest on the same variables as the multi-agent system"""

import sys
from pathlib import Path

import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config
from src.data_loader import load_hai_data
from src.evaluation import (
    compute_interval_metrics,
    compute_sample_metrics,
    plot_binary_timeline,
    plot_confusion_matrix,
    plot_score_timeline,
    save_metrics,
    save_predictions,
)


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

    scaler = MinMaxScaler()
    train_scaled = scaler.fit_transform(data.train)
    test_scaled = scaler.transform(data.test)

    model = IsolationForest(
        n_estimators=config.BASELINE_IF_N_ESTIMATORS,
        contamination=config.BASELINE_IF_CONTAMINATION,
        random_state=config.RANDOM_STATE,
        n_jobs=-1,
    )
    print("\nTraining Isolation Forest...")
    model.fit(train_scaled)

    y_pred = (model.predict(test_scaled) == -1).astype(int)
    # Higher score = more anomalous
    scores = -model.decision_function(test_scaled)

    metrics = {
        "method": "IsolationForest_baseline",
        "variables_used": len(data.available_vars),
        "n_estimators": config.BASELINE_IF_N_ESTIMATORS,
        "contamination": config.BASELINE_IF_CONTAMINATION,
        **compute_sample_metrics(data.labels, y_pred),
        **compute_interval_metrics(data.labels, y_pred),
    }

    print("\nSample-wise metrics:")
    for k in ["precision", "recall", "f1", "accuracy", "tp", "fp", "fn", "tn"]:
        print(f"  {k}: {metrics[k]}")

    print("\nInterval-based metrics:")
    for k in ["interval_precision", "interval_recall", "interval_f1", "true_intervals", "predicted_intervals"]:
        print(f"  {k}: {metrics[k]}")

    save_metrics(metrics, config.RESULTS_DIR / "baseline_metrics.csv")
    save_predictions(
        y_true=data.labels,
        y_pred=y_pred,
        scores=scores,
        output_file=config.RESULTS_DIR / "baseline_predictions.csv",
    )

    plot_confusion_matrix(
        y_true=data.labels,
        y_pred=y_pred,
        title="Isolation Forest baseline confusion matrix",
        output_file=config.FIGURES_DIR / "baseline_confusion_matrix.png",
    )
    plot_binary_timeline(
        y_true=data.labels,
        y_pred=y_pred,
        title="Isolation Forest baseline: predictions vs labels",
        output_file=config.FIGURES_DIR / "baseline_predictions_vs_labels.png",
    )
    plot_score_timeline(
        y_true=data.labels,
        scores=scores,
        title="Isolation Forest anomaly scores vs labels",
        output_file=config.FIGURES_DIR / "baseline_scores_vs_labels.png",
    )

    joblib.dump(
        {"scaler": scaler, "model": model, "variables": data.available_vars},
        config.MODELS_DIR / "baseline_isolation_forest.pkl",
    )
    print(f"\nSaved results to {config.RESULTS_DIR} and {config.FIGURES_DIR}")


if __name__ == "__main__":
    main()
