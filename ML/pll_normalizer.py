# =============================================================================
# File: pll_normalizer.py
# Purpose: Piecewise Linear-Log normalizer — fit on train only, transform val/test.
# Updated: 2026-05-25
# =============================================================================

from __future__ import annotations

import numpy as np
import pickle
from typing import Any

# ─── PLL group configuration for 3D tensor features (data_loader.py)
# Feature indices in the 20-dim 3D tensor: price, direction, front, back,
# strong, break, reverse, power, count, impulse, up_12, dn_12, up_24, dn_24,
# up_48, dn_48, ATR_ratio, hour_sin, hour_cos, time_pos

PLL_GROUPS_3D: dict[str, list[int]] = {
    "price": [0],
    "front_back": [2, 3],
    "impulse": [9],
    "power": [7],
    "count": [8],
    "updn_h12": [10, 11],
    "updn_h24": [12, 13],
    "updn_h48": [14, 15],
}

# Feature indices that are NOT PLL-normalized
NO_NORM_INDICES_3D: list[int] = [1, 4, 5, 6, 16, 17, 18, 19]
# direction(1), strong(4), break(5), reverse(6), ATR_ratio(16), hour_sin/cos(17-18), time_pos(19)

# Break index for pre-normalization clipping
BREAK_IDX_3D: int = 5
BREAK_CLIP_MAX: int = 5


class PLLGroupScaler:
    """Piecewise Linear-Log scaler for a single feature group.

    All features in the group share one min/max/percentile computed from
    the pooled values of all group features across the full train set.

    Algorithm (from lib_PIC.mqh PiecewiseNormalize):
      - x <= percentile_val: linear map to [0, P]
      - x >  percentile_val: log compression to [P, 1.0]
      - P defaults to 0.95
    """

    def __init__(self, percentile: float = 0.95):
        if not 0.0 < percentile < 1.0:
            raise ValueError(f"percentile must be in (0, 1), got {percentile}")
        self.percentile = float(percentile)
        self.min_val: float = 0.0
        self.max_val: float = 1.0
        self.pctl_val: float = 0.95
        self.fitted: bool = False

    def fit(self, X: np.ndarray) -> PLLGroupScaler:
        """Fit min/max/percentile from pooled group values.

        Args:
            X: 1D array of all finite values from all features in this group
               across the entire train set.
        """
        finite = X[np.isfinite(X)]
        if len(finite) == 0:
            return self

        self.min_val = float(np.min(finite))
        self.max_val = float(np.max(finite))
        self.pctl_val = float(np.percentile(finite, self.percentile * 100))

        if self.max_val <= self.min_val:
            self.max_val = self.min_val + 1.0
            self.pctl_val = self.min_val + 0.5 * self.percentile

        self.fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply PLL transform.

        Args:
            X: Values to normalize (any shape, float).

        Returns:
            Normalized values in [0, 1], same shape as X.
        """
        if not self.fitted:
            raise RuntimeError("PLLGroupScaler.fit() must be called before transform()")

        result = np.zeros_like(X, dtype=np.float32)
        finite_mask = np.isfinite(X)
        if not finite_mask.any():
            return result

        x = X[finite_mask].astype(np.float64)
        out = np.zeros(len(x), dtype=np.float64)

        linear = x <= self.pctl_val
        log_mask = x > self.pctl_val

        denom_linear = max(self.pctl_val - self.min_val, 1e-12)
        out[linear] = self.percentile * (x[linear] - self.min_val) / denom_linear

        if log_mask.any():
            x_log = x[log_mask]
            denom_tail = max(self.max_val - self.pctl_val, 1e-12)
            z = 1.0 + 9.0 * (x_log - self.pctl_val) / denom_tail
            z = np.clip(z, 1.0, 10.0)
            tail = np.log(z) / np.log(10.0)
            out[log_mask] = self.percentile + (1.0 - self.percentile) * tail

        result[finite_mask] = out.astype(np.float32)
        return result


class PLLFeatureNormalizer:
    """Per-group PLL normalizer for 3D fractal feature tensors.

    Fit on train, transform on val/test. Clip break > 5 before normalization.
    """

    def __init__(
        self,
        groups: dict[str, list[int]] | None = None,
        no_norm_indices: list[int] | None = None,
        break_idx: int | None = None,
        break_clip: int = 5,
        percentile: float = 0.95,
    ):
        self.groups = groups or PLL_GROUPS_3D
        self.no_norm = no_norm_indices or NO_NORM_INDICES_3D
        self.break_idx = break_idx if break_idx is not None else BREAK_IDX_3D
        self.break_clip = break_clip
        self.percentile = float(percentile)
        self.scalers: dict[str, PLLGroupScaler] = {}
        self._all_indices: set[int] = set()

    def fit(self, X_train: np.ndarray) -> PLLFeatureNormalizer:
        """Fit all group scalers on train data.

        Args:
            X_train: shape (n_samples, n_fractals, n_features).
        """
        n_features = X_train.shape[2]
        all_grouped = set()
        for indices in self.groups.values():
            all_grouped.update(indices)
        self._all_indices = all_grouped | set(self.no_norm)

        for group_name, indices in self.groups.items():
            pooled = X_train[:, :, indices].ravel()
            pooled = pooled[np.isfinite(pooled)]
            self.scalers[group_name] = PLLGroupScaler(percentile=self.percentile).fit(pooled)

        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Apply PLL normalization, copying non-normalized features as-is.

        Args:
            X: shape (n_samples, n_fractals, n_features).

        Returns:
            Normalized X, same shape, dtype float32.
        """
        result = np.zeros_like(X, dtype=np.float32)

        result[:, :, self.break_idx] = np.clip(
            X[:, :, self.break_idx].astype(np.float32), 0, self.break_clip
        )

        for group_name, indices in self.groups.items():
            scaler = self.scalers[group_name]
            pooled = X[:, :, indices].ravel()
            normalized = scaler.transform(pooled)
            result[:, :, indices] = normalized.reshape(X.shape[0], X.shape[1], len(indices))

        for idx in self.no_norm:
            if idx != self.break_idx:
                result[:, :, idx] = X[:, :, idx].astype(np.float32)

        return result

    def fit_transform(self, X_train: np.ndarray) -> np.ndarray:
        self.fit(X_train)
        return self.transform(X_train)

    def save(self, path: str) -> None:
        state = {
            "groups": self.groups,
            "no_norm": self.no_norm,
            "break_idx": self.break_idx,
            "break_clip": self.break_clip,
            "percentile": self.percentile,
            "_all_indices": self._all_indices,
            "scalers": {
                name: {
                    "percentile": s.percentile,
                    "min_val": s.min_val,
                    "max_val": s.max_val,
                    "pctl_val": s.pctl_val,
                    "fitted": s.fitted,
                }
                for name, s in self.scalers.items()
            },
        }
        with open(path, "wb") as f:
            pickle.dump(state, f)

    @classmethod
    def load(cls, path: str) -> PLLFeatureNormalizer:
        with open(path, "rb") as f:
            state = pickle.load(f)

        obj = cls(
            groups=state["groups"],
            no_norm_indices=state["no_norm"],
            break_idx=state["break_idx"],
            break_clip=state["break_clip"],
            percentile=state["percentile"],
        )
        obj._all_indices = state["_all_indices"]
        for name, sdata in state["scalers"].items():
            s = PLLGroupScaler(percentile=sdata["percentile"])
            s.min_val = sdata["min_val"]
            s.max_val = sdata["max_val"]
            s.pctl_val = sdata["pctl_val"]
            s.fitted = sdata["fitted"]
            obj.scalers[name] = s
        return obj

    def summary(self) -> dict[str, dict[str, float]]:
        return {
            name: {
                "min": s.min_val,
                "max": s.max_val,
                "pctl": s.pctl_val,
            }
            for name, s in self.scalers.items()
        }
