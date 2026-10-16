from __future__ import annotations

import numpy as np
import pandas as pd

from src.agents.base_agent import AgentOutput
from src.orchestrator_physics import OrchestratorPhysics
from src.score_calibration import AgentScoreCalibrator


class Orchestrator:
    """Final flag = group vote (>= min_votes) OR cross residual; the chain is only saved for the final step"""

    def __init__(
        self,
        min_votes: int = 2,
        vote_exclude_agents: list[str] | None = None,
        vote_agent_groups: dict[str, list[str]] | None = None,
        lstm_agent: str = "LSTMAutoencoderAgent",
    ):
        self.min_votes = min_votes
        self.vote_exclude_agents = vote_exclude_agents or []
        self.vote_agent_groups = vote_agent_groups
        self.lstm_agent = lstm_agent

    def _vote_flags(
        self,
        flags: np.ndarray,
        agent_names: list[str],
    ) -> tuple[np.ndarray, np.ndarray]:
        """Binary vote flag and the number of votes per sample"""
        exclude = self.vote_exclude_agents
        n_samples = flags.shape[1]

        if self.vote_agent_groups:
            votes = np.zeros(n_samples, dtype=float)
            for members in self.vote_agent_groups.values():
                indices = [
                    agent_names.index(name)
                    for name in members
                    if name in agent_names and name not in exclude
                ]
                if not indices:
                    continue
                votes += (flags[indices].sum(axis=0) >= 1).astype(float)
        else:
            keep = [i for i, name in enumerate(agent_names) if name not in exclude]
            votes = flags[keep].sum(axis=0) if keep else flags.sum(axis=0)

        final = (votes >= self.min_votes).astype(int)
        return final, votes.astype(float)

    def aggregate(
        self,
        outputs: list[AgentOutput],
        calibrator: AgentScoreCalibrator | None,
        test_df: pd.DataFrame,
        physics: OrchestratorPhysics,
    ) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        if not outputs:
            raise ValueError("No agent outputs provided to orchestrator")

        flags = np.vstack([o.flags.astype(int) for o in outputs])
        scores = np.vstack([o.scores.astype(float) for o in outputs])
        agent_names = [o.name for o in outputs]
        n = flags.shape[1]

        norm_scores = scores.copy()
        if calibrator is not None:
            for idx, name in enumerate(agent_names):
                norm_scores[idx] = calibrator.normalize(name, scores[idx])

        vote_flags, vote_scores = self._vote_flags(flags, agent_names)

        chain = np.zeros(n, dtype=int)
        residual = np.zeros(n, dtype=int)
        lstm_norm = np.zeros(n, dtype=float)
        if self.lstm_agent in agent_names:
            lstm_norm = norm_scores[agent_names.index(self.lstm_agent)]
            setpoint_flag = (
                flags[agent_names.index("SetpointAgent")]
                if "SetpointAgent" in agent_names
                else np.zeros(n, dtype=int)
            )
            chain = physics.evidence_chain(setpoint_flag, lstm_norm)
            residual = physics.cross_residual(test_df, lstm_norm)

        final_flags = np.clip(vote_flags + residual, 0, 1).astype(int)
        final_scores = np.maximum(vote_scores, lstm_norm * residual)

        details = pd.DataFrame({
            "orchestrator_prediction": final_flags,
            "orchestrator_score": final_scores,
            "vote_flag": vote_flags.astype(int),
            "chain_flag": chain.astype(int),
            "residual_flag": residual.astype(int),
        })
        for output in outputs:
            details[f"{output.name}_flag"] = output.flags.astype(int)
            details[f"{output.name}_score"] = output.scores.astype(float)
            if calibrator is not None and output.name in calibrator.refs:
                details[f"{output.name}_norm_score"] = calibrator.normalize(
                    output.name, output.scores,
                )

        return final_flags, final_scores, details
