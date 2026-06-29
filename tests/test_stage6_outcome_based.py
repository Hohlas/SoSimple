import numpy as np
import pandas as pd
import pytest

import ML.baseline.benchmark_stage6_outcome_based as s6


def test_stage6_config_is_fixed_and_narrow():
    cfg = s6.STAGE6_0_CONFIG

    assert cfg.horizon_bars == 24
    assert cfg.stop_offset_atr == 0.5
    assert cfg.take_profit_atr == 2.0
    assert cfg.entry_lag_bars == 1
    assert cfg.same_bar_policy == "sl_first"
    assert cfg.primary_profile == "clock_shift_back"
    assert cfg.disclosure_profiles == ("clock_shift_back_impulse",)


def test_stage6_target_columns_are_denied_from_features():
    target_cols = set(s6.stage6_target_columns())
    denylist = set(s6.stage6_feature_denylist())

    assert "stage6_tp_vs_rest_flag" in target_cols
    assert "stage6_pnl_r" in target_cols
    assert target_cols <= denylist
    assert all(col.startswith("stage6_") for col in target_cols)
