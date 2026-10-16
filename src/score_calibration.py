"""Per-agent score normalization, fitted on attack-free train scores"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class AgentScoreCalibrator:
    """Divides each agent's score by its train 99th percentile, so 1.0 means 'train tail'"""

    refs: dict[str, float] = field(default_factory=dict)  # agent name - train q99

    def fit(self, agent_name: str, train_scores: np.ndarray) -> None:
        scores = np.asarray(train_scores, dtype=float)
        scores = scores[np.isfinite(scores)]
        if scores.size == 0:
            self.refs[agent_name] = 1.0
            return

        q99 = float(np.quantile(scores, 0.99))
        # Flat scores (for example an IF decision function near zero) fall back to the tail
        if q99 <= 1e-6:
            q99 = max(float(np.quantile(scores, 0.999)), float(scores.max()), 1e-6)
        self.refs[agent_name] = q99

    def normalize(self, agent_name: str, scores: np.ndarray) -> np.ndarray:
        if agent_name not in self.refs:
            raise KeyError(f"No calibration reference for agent '{agent_name}'")
        return np.asarray(scores, dtype=float) / self.refs[agent_name]
