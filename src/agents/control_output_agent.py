import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler

from src.thresholding import EVTThresholdResult, apply_threshold, fit_evt_threshold

from .base_agent import AgentOutput, BaseAgent


class ControlOutputAgent(BaseAgent):
    """Isolation Forest on the 4 variables of the P2 speed loop (the joint pattern)"""

    def __init__(
        self,
        variables: list[str],
        n_estimators: int = 150,
        contamination: float = 0.01,
        random_state: int = 42,
        use_evt_threshold: bool = True,
        evt_init_level: float = 0.99,
        evt_tail_prob: float = 1e-4,
        evt_min_exceedances: int = 50,
        evt_fallback_quantile: float = 0.9999,
    ):
        super().__init__("ControlOutputAgent", variables)
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.use_evt_threshold = use_evt_threshold
        self.evt_init_level = evt_init_level
        self.evt_tail_prob = evt_tail_prob
        self.evt_min_exceedances = evt_min_exceedances
        self.evt_fallback_quantile = evt_fallback_quantile

        self.scaler = MinMaxScaler()
        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.score_threshold_: float | None = None
        self.evt_info_: EVTThresholdResult | None = None

    def _anomaly_scores(self, x_scaled: np.ndarray) -> np.ndarray:
        return -self.model.decision_function(x_scaled)

    def fit(self, train: pd.DataFrame) -> "ControlOutputAgent":
        x = self._select_data(train)
        x_scaled = self.scaler.fit_transform(x)
        self.model.fit(x_scaled)

        if self.use_evt_threshold:
            train_scores = self._anomaly_scores(x_scaled)
            self.evt_info_ = fit_evt_threshold(
                train_scores,
                init_level=self.evt_init_level,
                tail_prob=self.evt_tail_prob,
                min_exceedances=self.evt_min_exceedances,
                fallback_quantile=self.evt_fallback_quantile,
            )
            self.score_threshold_ = self.evt_info_.threshold
            print(
                f"  ControlOutputAgent EVT threshold={self.score_threshold_:.6f} "
                f"({self.evt_info_.method}, exceedances={self.evt_info_.n_exceedances})"
            )

        return self

    def predict(self, test: pd.DataFrame) -> AgentOutput:
        x = self._select_data(test)
        x_scaled = self.scaler.transform(x)
        scores = self._anomaly_scores(x_scaled)

        if self.use_evt_threshold and self.score_threshold_ is not None:
            flags = apply_threshold(scores, self.score_threshold_)
        else:
            raw_pred = self.model.predict(x_scaled)
            flags = (raw_pred == -1).astype(int)

        return AgentOutput(
            name=self.name,
            flags=flags,
            scores=np.asarray(scores, dtype=float),
            variables=self.available_vars,
        )
