"""Score thresholds from attack-free train data: Peaks Over Threshold (EVT) with a quantile fallback"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import genpareto


@dataclass
class EVTThresholdResult:
    threshold: float
    init_level: float
    init_u: float
    tail_prob: float
    n_samples: int
    n_exceedances: int
    gpd_shape: float | None
    gpd_scale: float | None
    method: str


def fit_evt_threshold(
    scores: np.ndarray,
    init_level: float = 0.99,
    tail_prob: float = 5e-4,
    min_exceedances: int = 50,
    fallback_quantile: float = 0.9999,
) -> EVTThresholdResult:
    """Fit a Generalized Pareto tail above the `init_level` quantile and pick the
    threshold with exceedance probability `tail_prob`

    With too few exceedances or a bad fit it falls back to `fallback_quantile`
    """
    scores = np.asarray(scores, dtype=float)
    scores = scores[np.isfinite(scores)]

    def result(thr, method, u, n, n_exc, shape=None, scale=None) -> EVTThresholdResult:
        return EVTThresholdResult(
            threshold=float(thr),
            init_level=init_level,
            init_u=u,
            tail_prob=tail_prob,
            n_samples=n,
            n_exceedances=n_exc,
            gpd_shape=shape,
            gpd_scale=scale,
            method=method,
        )

    if scores.size == 0:
        return result(0.0, "empty", 0.0, 0, 0)

    sorted_scores = np.sort(scores)
    n = len(sorted_scores)
    u_idx = min(max(int(np.floor(init_level * n)), 0), n - 1)
    u = float(sorted_scores[u_idx])
    exceedances = sorted_scores[u_idx:] - u
    n_exc = int(exceedances.size)

    fallback = float(np.quantile(scores, fallback_quantile))
    if n_exc < min_exceedances or np.all(exceedances <= 0):
        return result(fallback, "quantile_fallback", u, n, n_exc)

    try:
        shape, _, scale = genpareto.fit(exceedances, floc=0)
        scale = float(max(scale, 1e-12))
        shape = float(shape)
        nu = n_exc / n

        if abs(shape) < 1e-8:
            thr = u - scale * np.log(max(tail_prob / nu, 1e-300))
        else:
            thr = u + (scale / shape) * ((tail_prob / nu) ** (-shape) - 1.0)

        if not np.isfinite(thr) or thr <= u:
            raise ValueError("invalid EVT threshold")

        # Do not go above the empirical (1 - tail_prob) quantile
        method = "evt_pot"
        cap = float(np.quantile(scores, 1.0 - tail_prob))
        if thr > cap:
            thr = cap
            method = "evt_pot_capped"

        return result(thr, method, u, n, n_exc, shape, scale)
    except Exception:
        return result(fallback, "quantile_fallback", u, n, n_exc)


def apply_threshold(scores: np.ndarray, threshold: float) -> np.ndarray:
    """Binary flags (1 = anomaly)"""
    return (np.asarray(scores, dtype=float) > threshold).astype(int)
