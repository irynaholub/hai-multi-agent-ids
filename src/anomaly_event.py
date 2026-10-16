"""One detected anomaly interval (used by the dashboard and LLM report)"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AnomalyEvent:
    start_row: int
    end_row: int
    timestamp_start: str
    timestamp_end: str
    active_agents: list[str]
    agent_scores: dict[str, float] = field(default_factory=dict)
    chain_flag: bool = False
    residual_flag: bool = False
    vote_flag: bool = False
    extra: dict = field(default_factory=dict)

    @property
    def duration_sec(self) -> int:
        return self.end_row - self.start_row + 1
