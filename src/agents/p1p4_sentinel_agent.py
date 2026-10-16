from __future__ import annotations

import numpy as np
import pandas as pd

from src.thresholding import EVTThresholdResult, apply_threshold, fit_evt_threshold

from .base_agent import AgentOutput, BaseAgent


class P1P4SentinelAgent(BaseAgent):
    """Watches P1 and P4 on their own: how far each variable is from its long rolling mean"""

    def __init__(
        self,
        variables: list[str],
        window_seconds: int = 600,
        long_window_seconds: int = 3600,
        use_evt_threshold: bool = True,
        evt_init_level: float = 0.99,
        evt_tail_prob: float = 1e-4,
        evt_min_exceedances: int = 50,
        evt_fallback_quantile: float = 0.9999,
    ):
        super().__init__("P1P4SentinelAgent", variables)
        self.window_seconds = int(window_seconds)
        self.long_window_seconds = int(long_window_seconds)
        self.use_evt_threshold = use_evt_threshold
        self.evt_init_level = evt_init_level
        self.evt_tail_prob = evt_tail_prob
        self.evt_min_exceedances = evt_min_exceedances
        self.evt_fallback_quantile = evt_fallback_quantile

        self.global_mean_: pd.Series | None = None
        self.global_std_: pd.Series | None = None
        self.score_threshold_: float | None = None
        self.evt_info_: EVTThresholdResult | None = None

    def _rolling_z(self, x: pd.DataFrame) -> np.ndarray:
        """Max over variables of |x - long rolling mean| / global std"""
        long_mean = x.rolling(
            window=self.long_window_seconds,
            min_periods=max(60, self.long_window_seconds // 6),
        ).mean()
        long_mean = long_mean.fillna(self.global_mean_)
        std_floor = (self.global_std_ * 0.1).clip(lower=1e-6)
        scale = self.global_std_.combine(std_floor, np.maximum)
        z = ((x - long_mean) / scale).abs()
        return z.fillna(0).max(axis=1).values

    def fit(self, train: pd.DataFrame) -> "P1P4SentinelAgent":
        x = self._select_data(train)
        self.global_mean_ = x.mean()
        self.global_std_ = x.std().replace(0, 1e-6)

        if self.use_evt_threshold:
            train_scores = self._rolling_z(x)
            self.evt_info_ = fit_evt_threshold(
                train_scores,
                init_level=self.evt_init_level,
                tail_prob=self.evt_tail_prob,
                min_exceedances=self.evt_min_exceedances,
                fallback_quantile=self.evt_fallback_quantile,
            )
            self.score_threshold_ = self.evt_info_.threshold
            print(
                f"  P1P4SentinelAgent EVT threshold={self.score_threshold_:.6f} "
                f"({self.evt_info_.method}, exceedances={self.evt_info_.n_exceedances})"
            )

        return self

    def predict(self, test: pd.DataFrame) -> AgentOutput:
        x = self._select_data(test)
        scores = self._rolling_z(x)

        if self.use_evt_threshold and self.score_threshold_ is not None:
            flags = apply_threshold(scores, self.score_threshold_)
        else:
            flags = (scores > 3.0).astype(int)

        return AgentOutput(
            name=self.name,
            flags=flags,
            scores=np.asarray(scores, dtype=float),
            variables=self.available_vars,
        )
