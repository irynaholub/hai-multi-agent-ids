"""Physics-based signals for the orchestrator: causal chain and P4_ST_PO residual"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def _clean_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df[cols].copy()
    out = out.apply(pd.to_numeric, errors="coerce")
    return out.ffill().bfill().fillna(0.0)


def _rise_events(flag: np.ndarray) -> np.ndarray:
    x = np.asarray(flag).astype(int)
    prev = np.concatenate(([0], x[:-1]))
    return ((x == 1) & (prev == 0)).astype(int)


def _persistent_runs(above: np.ndarray, min_run: int) -> list[tuple[int, int]]:
    x = np.asarray(above).astype(bool)
    n = len(x)
    runs: list[tuple[int, int]] = []
    i = 0
    while i < n:
        if not x[i]:
            i += 1
            continue
        j = i
        while j < n and x[j]:
            j += 1
        if (j - i) >= min_run:
            runs.append((i, j - 1))
        i = j
    return runs


@dataclass
class OrchestratorPhysics:
    """Thresholds and the P4_ST_PO model, fitted on attack-free train data"""

    po_model: LinearRegression | None
    po_predictors: list[str]
    po_residual_thr: float  # normalised residual score (same scale as ConsistencyAgent)

    chain_lag_seconds: int
    lstm_min_run_seconds: int
    lstm_norm_threshold: float

    @classmethod
    def fit(
        cls,
        train: pd.DataFrame,
        *,
        chain_lag_seconds: int = 120,
        lstm_min_run_seconds: int = 30,
        lstm_norm_threshold: float = 1.0,
        po_residual_quantile: float = 0.99,
    ) -> "OrchestratorPhysics":
        po_predictors = [c for c in ["P2_SIT01", "P4_ST_GOV", "P4_ST_PS"] if c in train.columns]
        po_model: LinearRegression | None = None
        po_residual_thr = 1.0

        if "P4_ST_PO" in train.columns and po_predictors:
            x = _clean_numeric(train, po_predictors + ["P4_ST_PO"])
            po_model = LinearRegression()
            po_model.fit(x[po_predictors].values, x["P4_ST_PO"].values)
            pred = po_model.predict(x[po_predictors].values)
            resid = np.abs(x["P4_ST_PO"].values - pred)
            base = np.maximum(np.abs(pred), 1e-6)
            resid_norm = resid / base
            po_residual_thr = float(np.quantile(resid_norm, po_residual_quantile))
            po_residual_thr = max(po_residual_thr, 1e-6)

        return cls(
            po_model=po_model,
            po_predictors=po_predictors,
            po_residual_thr=po_residual_thr,
            chain_lag_seconds=chain_lag_seconds,
            lstm_min_run_seconds=lstm_min_run_seconds,
            lstm_norm_threshold=lstm_norm_threshold,
        )

    def evidence_chain(
        self,
        setpoint_flag: np.ndarray,
        lstm_norm: np.ndarray,
    ) -> np.ndarray:
        """After a setpoint spike, mark the first sustained LSTM segment within the lag window"""
        n = len(setpoint_flag)
        out = np.zeros(n, dtype=int)
        lstm_above = np.asarray(lstm_norm, dtype=float) >= self.lstm_norm_threshold
        min_run = self.lstm_min_run_seconds
        max_wait = self.chain_lag_seconds

        for t0 in np.where(_rise_events(setpoint_flag))[0]:
            search_end = min(n, t0 + max_wait + 1)
            i = int(t0)
            while i < search_end:
                if not lstm_above[i]:
                    i += 1
                    continue
                j = i
                while j < n and lstm_above[j]:
                    j += 1
                run_len = j - i
                if run_len >= min_run:
                    out[i:j] = 1
                    break
                i = j
        return out

    def cross_residual(self, test: pd.DataFrame, lstm_norm: np.ndarray) -> np.ndarray:
        """Sustained LSTM together with a large P4_ST_PO residual"""
        n = len(test)
        out = np.zeros(n, dtype=int)
        if self.po_model is None or "P4_ST_PO" not in test.columns:
            return out

        cols = self.po_predictors + ["P4_ST_PO"]
        x = _clean_numeric(test, cols)
        pred = self.po_model.predict(x[self.po_predictors].values)
        actual = x["P4_ST_PO"].values
        resid_norm = np.abs(actual - pred) / np.maximum(np.abs(pred), 1e-6)

        lstm_sustained = np.zeros(n, dtype=int)
        for rs, re in _persistent_runs(
            np.asarray(lstm_norm, dtype=float) >= self.lstm_norm_threshold,
            self.lstm_min_run_seconds,
        ):
            lstm_sustained[rs : re + 1] = 1

        return (lstm_sustained & (resid_norm >= self.po_residual_thr)).astype(int)
