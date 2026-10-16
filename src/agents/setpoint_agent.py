import numpy as np
import pandas as pd

from src.thresholding import EVTThresholdResult, apply_threshold, fit_evt_threshold

from .base_agent import AgentOutput, BaseAgent


class SetpointAgent(BaseAgent):
    """Setpoint manipulation: max of jump z-score, level z-score, slow drift and the AutoSD/SIT01 gap"""

    def __init__(
        self,
        variables: list[str],
        z_threshold: float = 4.0,
        residual_quantile: float = 0.995,
        use_evt_threshold: bool = True,
        evt_init_level: float = 0.99,
        evt_tail_prob: float = 1e-4,
        evt_min_exceedances: int = 50,
        evt_fallback_quantile: float = 0.9999,
        drift_short_window: int = 30,
        drift_long_window: int = 600,
    ):
        super().__init__("SetpointAgent", variables)
        self.z_threshold = z_threshold
        self.residual_quantile = residual_quantile
        self.use_evt_threshold = use_evt_threshold
        self.evt_init_level = evt_init_level
        self.evt_tail_prob = evt_tail_prob
        self.evt_min_exceedances = evt_min_exceedances
        self.evt_fallback_quantile = evt_fallback_quantile
        self.drift_short_window = drift_short_window
        self.drift_long_window = drift_long_window

        self.diff_mean_: pd.Series | None = None
        self.diff_std_: pd.Series | None = None
        self.level_mean_: pd.Series | None = None
        self.level_std_: pd.Series | None = None
        self.residual_threshold_: float | None = None
        self.score_threshold_: float | None = None
        self.evt_info_: EVTThresholdResult | None = None

    def fit(self, train: pd.DataFrame) -> "SetpointAgent":
        x = self._select_data(train)

        diffs = x.diff().fillna(0)
        self.diff_mean_ = diffs.mean()
        self.diff_std_ = diffs.std().replace(0, 1e-9)
        self.level_mean_ = x.mean()
        self.level_std_ = x.std().replace(0, 1e-9)

        if "P2_AutoSD" in x.columns and "P2_SIT01" in x.columns:
            residual = (x["P2_SIT01"] - x["P2_AutoSD"]).abs()
            self.residual_threshold_ = float(residual.quantile(self.residual_quantile))
            self.residual_threshold_ = max(self.residual_threshold_, 1e-9)
        else:
            self.residual_threshold_ = None

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
                f"  SetpointAgent EVT threshold={self.score_threshold_:.6f} "
                f"({self.evt_info_.method}, exceedances={self.evt_info_.n_exceedances})"
            )

        return self

    def _compute_scores(self, x: pd.DataFrame) -> np.ndarray:
        diffs = x.diff().fillna(0)
        z = ((diffs - self.diff_mean_) / self.diff_std_).abs()
        max_z = z.max(axis=1).values

        score = max_z.copy()

        if self.level_mean_ is not None and self.level_std_ is not None:
            level_z = ((x - self.level_mean_) / self.level_std_).abs()
            level_score = level_z.max(axis=1).values
            score = np.maximum(score, level_score)

        if self.level_std_ is not None and self.drift_short_window > 0:
            short_mean = x.rolling(
                window=self.drift_short_window,
                min_periods=max(2, min(self.drift_short_window, 10)),
            ).mean()
            long_mean = x.shift(self.drift_short_window).rolling(
                window=max(self.drift_long_window, self.drift_short_window + 1),
                min_periods=max(2, min(self.drift_short_window, 10)),
            ).mean()
            drift = ((short_mean - long_mean) / self.level_std_).abs()
            drift_score = drift.fillna(0).max(axis=1).values
            score = np.maximum(score, drift_score)

        if self.residual_threshold_ is not None:
            residual = (x["P2_SIT01"] - x["P2_AutoSD"]).abs().values
            residual_score = residual / self.residual_threshold_
            score = np.maximum(score, residual_score)

        return score.astype(float)

    def predict(self, test: pd.DataFrame) -> AgentOutput:
        x = self._select_data(test)
        score = self._compute_scores(x)

        if self.use_evt_threshold and self.score_threshold_ is not None:
            flags = apply_threshold(score, self.score_threshold_)
        else:
            flags = (score > self.z_threshold).astype(int)
            if self.residual_threshold_ is not None:
                residual = (x["P2_SIT01"] - x["P2_AutoSD"]).abs().values
                residual_score = residual / self.residual_threshold_
                flags = flags | (residual_score > 1.0).astype(int)

        return AgentOutput(
            name=self.name,
            flags=flags.astype(int),
            scores=score.astype(float),
            variables=self.available_vars,
        )
