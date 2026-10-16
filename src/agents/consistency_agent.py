import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from src.thresholding import EVTThresholdResult, apply_threshold, fit_evt_threshold

from .base_agent import AgentOutput, BaseAgent


class ConsistencyAgent(BaseAgent):
    """Linear regressions between P1, P4 and P2, fitted on train; a large residual is an anomaly"""

    def __init__(
        self,
        variables: list[str],
        residual_quantile: float = 0.995,
        use_evt_threshold: bool = True,
        evt_init_level: float = 0.99,
        evt_tail_prob: float = 1e-4,
        evt_min_exceedances: int = 50,
        evt_fallback_quantile: float = 0.9999,
    ):
        super().__init__("ConsistencyAgent", variables)
        self.residual_quantile = residual_quantile
        self.use_evt_threshold = use_evt_threshold
        self.evt_init_level = evt_init_level
        self.evt_tail_prob = evt_tail_prob
        self.evt_min_exceedances = evt_min_exceedances
        self.evt_fallback_quantile = evt_fallback_quantile
        self.checks_: list[dict] = []
        self.score_threshold_: float | None = None
        self.evt_info_: EVTThresholdResult | None = None

    def _add_check(
        self,
        train: pd.DataFrame,
        target: str,
        predictors: list[str],
        name: str,
    ) -> None:
        predictors = [p for p in predictors if p in train.columns]

        if target not in train.columns or not predictors:
            return

        x = train[predictors].values
        y = train[target].values

        model = LinearRegression()
        model.fit(x, y)

        residual = np.abs(y - model.predict(x))
        threshold = float(np.quantile(residual, self.residual_quantile))
        threshold = max(threshold, 1e-9)

        self.checks_.append({
            "name": name,
            "target": target,
            "predictors": predictors,
            "model": model,
            "threshold": threshold,
        })

    def _compute_scores(self, x: pd.DataFrame) -> np.ndarray:
        n = len(x)
        scores = np.zeros(n, dtype=float)

        for check in self.checks_:
            target = check["target"]
            predictors = check["predictors"]
            model = check["model"]
            threshold = check["threshold"]

            if target not in x.columns or not all(p in x.columns for p in predictors):
                continue

            pred = model.predict(x[predictors].values)
            residual = np.abs(x[target].values - pred)
            residual_score = residual / threshold
            scores = np.maximum(scores, residual_score)

        return scores

    def fit(self, train: pd.DataFrame) -> "ConsistencyAgent":
        x = self._select_data(train)

        self._add_check(
            train=x,
            target="P4_ST_PT01",
            predictors=["P1_PIT01", "P1_PCV01D", "P1_PCV01Z"],
            name="P1_pressure_to_P4_pressure",
        )

        self._add_check(
            train=x,
            target="P4_ST_TT01",
            predictors=[
                "P1_TIT01", "P1_TIT02", "P1_TIT03",
                "P1_FCV01D", "P1_FCV02D", "P1_FT02",
            ],
            name="P1_temperature_to_P4_temperature",
        )

        self._add_check(
            train=x,
            target="P2_SIT01",
            predictors=[
                "P2_AutoSD", "P2_SCO", "P2_SCST",
                "P4_ST_PS", "P4_ST_GOV", "P4_ST_PT01", "P4_ST_TT01",
            ],
            name="P4_P2_context_to_turbine_speed",
        )

        self._add_check(
            train=x,
            target="P2_SCO",
            predictors=["P2_AutoSD", "P2_SIT01", "P2_SCST", "P4_ST_PS", "P4_ST_GOV"],
            name="P4_P2_context_to_control_output",
        )

        if not self.checks_:
            raise ValueError(
                "ConsistencyAgent: no consistency checks could be built. "
                "Check selected variables."
            )

        if self.use_evt_threshold:
            train_scores = self._compute_scores(x)
            self.evt_info_ = fit_evt_threshold(
                train_scores,
                init_level=self.evt_init_level,
                tail_prob=self.evt_tail_prob,
                min_exceedances=self.evt_min_exceedances,
                fallback_quantile=self.evt_fallback_quantile,
            )
            self.score_threshold_ = self.evt_info_.threshold
            print(
                f"  ConsistencyAgent EVT threshold={self.score_threshold_:.6f} "
                f"({self.evt_info_.method}, exceedances={self.evt_info_.n_exceedances})"
            )

        return self

    def predict(self, test: pd.DataFrame) -> AgentOutput:
        x = self._select_data(test)
        scores = self._compute_scores(x)

        if self.use_evt_threshold and self.score_threshold_ is not None:
            flags = apply_threshold(scores, self.score_threshold_)
        else:
            flags = (scores > 1.0).astype(int)

        return AgentOutput(
            name=self.name,
            flags=flags.astype(int),
            scores=scores.astype(float),
            variables=self.available_vars,
        )
