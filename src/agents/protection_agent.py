import numpy as np
import pandas as pd

from .base_agent import AgentOutput, BaseAgent


class ProtectionAgent(BaseAgent):
    """Rules on the protection system: changed trip limits, vibration over its limit, unusual trip status"""

    PARAMETER_VARS = [
        "P2_RTR",
        "P2_VTR01",
        "P2_VTR02",
        "P2_VTR03",
        "P2_VTR04",
    ]

    STATUS_VARS = [
        "P2_Emerg",
        "P2_TripEx",
    ]

    VIBRATION_PAIRS = [
        ("P2_VIBTR01", "P2_VTR01"),
        ("P2_VIBTR02", "P2_VTR02"),
        ("P2_VIBTR03", "P2_VTR03"),
        ("P2_VIBTR04", "P2_VTR04"),
    ]

    def __init__(self, variables: list[str]):
        super().__init__("ProtectionAgent", variables)

        self.param_median_: dict[str, float] = {}
        self.param_tol_: dict[str, float] = {}
        self.status_mode_: dict[str, int] = {}

    def fit(self, train: pd.DataFrame) -> "ProtectionAgent":
        x = self._select_data(train)

        for var in self.PARAMETER_VARS:
            if var in x.columns:
                median = float(x[var].median())
                std = float(x[var].std())
                tolerance = max(5.0 * std, 1e-6, 0.001 * abs(median))
                self.param_median_[var] = median
                self.param_tol_[var] = tolerance

        for var in self.STATUS_VARS:
            if var in x.columns:
                mode = int(x[var].mode().iloc[0])
                self.status_mode_[var] = mode

        train_check = self.predict(train)
        n_train = int(train_check.flags.sum())
        print(
            f"  ProtectionAgent train activations: {n_train} "
            f"(expect ~0 on attack-free data)"
        )

        return self

    def predict(self, test: pd.DataFrame) -> AgentOutput:
        x = self._select_data(test)

        n = len(x)
        flags = np.zeros(n, dtype=int)
        scores = np.zeros(n, dtype=float)

        # 1. Protection parameter deviation
        for var, median in self.param_median_.items():
            if var not in x.columns:
                continue

            tol = self.param_tol_[var]
            deviation_score = (x[var].values - median).astype(float)
            deviation_score = np.abs(deviation_score) / tol

            flags = flags | (deviation_score > 1.0).astype(int)
            scores = np.maximum(scores, deviation_score)

        # 2. Vibration exceeding threshold
        for vib_var, threshold_var in self.VIBRATION_PAIRS:
            if vib_var not in x.columns or threshold_var not in x.columns:
                continue

            vib = np.abs(x[vib_var].values.astype(float))
            threshold = np.abs(x[threshold_var].values.astype(float))

            valid = threshold > 1e-9
            exceed_score = np.zeros(n, dtype=float)
            exceed_score[valid] = vib[valid] / threshold[valid]

            flags = flags | (exceed_score > 1.0).astype(int)
            scores = np.maximum(scores, exceed_score)

        # 3. Emergency/trip status deviation from normal mode
        for var, mode in self.status_mode_.items():
            if var not in x.columns:
                continue

            status_changed = (x[var].values.astype(int) != mode).astype(int)
            flags = flags | status_changed
            scores = np.maximum(scores, status_changed.astype(float))

        return AgentOutput(
            name=self.name,
            flags=flags.astype(int),
            scores=scores.astype(float),
            variables=self.available_vars,
        )