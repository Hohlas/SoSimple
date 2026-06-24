# =============================================================================
# File: ML/baseline/benchmark_stage5_transformer_breach.py
# Purpose: Stage 5.0 runner + diagnostic sub-stages 5.0a-5.0f:
#          feature preflight, transform audit, profile screening,
#          and signal stationarity diagnostics
# Input: DATA/Nero_XAUUSD_*_labeled.csv
# Output: ML/reports/stage5_transformer_breach.json,
#         ML/reports/stage5_0a_feature_preflight.json,
#         ML/reports/stage5_0a_feature_stats_normalized.csv,
#         ML/reports/stage5_0a_feature_stats_per_position.csv,
#         ML/reports/stage5_0a_profile_summary.csv,
#         ML/reports/stage5_0a_transform_comparison.json,
#         ML/reports/stage5_0d_diagnostic_screening.json,
#         ML/reports/stage5_0f_signal_stationarity.json
# Language: Python 3.10+
# Created: 2026-06-17
# Updated: 2026-06-24
# =============================================================================

import argparse, json, os, sys, time
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset
import xgboost as xgb

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ML.models.fractal_breach_transformer import FractalBreachTransformer, TokenSelector

# ===========================================================================
# Constants
# ===========================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'DATA'
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'

TRAIN_FILE = DATA_DIR / 'Nero_XAUUSD_train_labeled.csv'
VAL_FILE = DATA_DIR / 'Nero_XAUUSD_validation_labeled.csv'
TEST_FILE = DATA_DIR / 'Nero_XAUUSD_test_labeled.csv'
OHLC_FILE = DATA_DIR / 'XAUUSD_H1_OHLC.csv'

CSV_SEP = ';'
FRACTAL_SEP = ':'
N_FRACTALS = 100

TARGET_COLUMN = 'sell_stop_broken_H6_off05_flag'


def find_buy_stop_target_columns(df: pd.DataFrame) -> list[str]:
    return sorted([
        col for col in df.columns
        if col.startswith("buy_stop_broken_") and col.endswith("_flag")
    ])


def summarize_target_contract(df_by_split: dict[str, pd.DataFrame], target_col: str) -> dict:
    splits = {}
    for split_name, df in df_by_split.items():
        if target_col not in df.columns:
            splits[split_name] = {"exists": False}
            continue
        series = pd.to_numeric(df[target_col], errors="coerce")
        non_null = series.dropna()
        splits[split_name] = {
            "exists": True,
            "n_rows": int(len(series)),
            "n_non_null": int(len(non_null)),
            "null_rate": float(series.isna().mean()) if len(series) else None,
            "positive_rate": float((non_null == 1).mean()) if len(non_null) else None,
            "unique_values": sorted([_safe(v) for v in non_null.unique().tolist()]),
        }
    return {"target": target_col, "splits": splits}

# Split years
TRAIN_MAX_YEAR = 2020
VAL_STOP_YEARS = {2021, 2022}
HOLDOUT_MIN_YEAR = 2023

# Base10 feature indices in fractal string (0-indexed)
# Format: time:price:dir:front:back:strong:break:reverse:power:count:impulse:...
BASE10_INDICES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
BASE10_NAMES = ['price', 'direction', 'front', 'back', 'strong', 'break',
                'reverse', 'power', 'count', 'impulse']
NO_PRICE_TOKEN_FIELDS = ['direction', 'front', 'back', 'strong', 'break',
                         'reverse', 'power', 'count', 'impulse']
TIME_ONLY_ROW_FIELDS = ['hour_sin', 'hour_cos', 'dow_sin', 'dow_cos']
TIME_PLUS_ATR_ROW_FIELDS = ['ATR', 'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos']

# Full29 feature indices (matching data_loader.py)
# CSV fields 1-20 are fractal features, plus computed features
# For the benchmark we use fields 1-20 as token features
FULL29_INDICES = list(range(1, 21))

# Training budget
SEEDS = [42, 77, 123]
MAX_EPOCHS = 60
EARLY_STOPPING_PATIENCE = 8
BATCH_SIZE = 256
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4

# Model architecture
D_MODEL = 64
NHEAD = 4
DIM_FEEDFORWARD = 128
DROPOUT = 0.15
NUM_LAYERS = 2

# Gate thresholds
PHASE1_STOP_GAP = 0.03  # halt if Transformer val AUC trails XGBoost by >0.03
HOLDOUT_AUC_DELTA = 0.02  # must beat XGBoost by at least 0.02
HOLDOUT_TIME_AUC_DELTA = 0.04  # must beat time_only by at least 0.04
HOLDOUT_LIFT_DELTA = 0.10  # lift_bottom30 must improve by at least 0.10
YEARLY_AUC_MIN = 0.55
MIN_VALID_YEARS = 3

# Corridor thresholds
CORRIDOR_LOW_COVERAGE_PCT_EMPTY = 0.05
CORRIDOR_LOW_COVERAGE_MEDIAN = 3
CORRIDOR_REJECTED_PCT_EMPTY = 0.20
CORRIDOR_REJECTED_MEDIAN = 2

# JSON report path
JSON_REPORT_PATH = REPORTS_DIR / 'stage5_transformer_breach.json'
STAGE5_0B_JSON_REPORT_PATH = REPORTS_DIR / "stage5_0b_asinh_rerun.json"
STAGE5_0F_TARGETS = [
    "sell_stop_broken_H6_off05_flag",
    "buy_stop_broken_H6_off05_flag",
]
STAGE5_0F_PROFILE_KEYS = [
    "base_raw_plus_time",
    "structure_only",
    "time_only",
    "all100_relative_price_time",
]
STAGE5_0F_SEEDS = [42, 77, 123]
STAGE5_0F_DECISION_YEARS = [2023, 2024, 2025]
STAGE5_0F_LOW_N_YEAR = 2026
STAGE5_0F_ROLLING_WINDOW_YEARS = 8
STAGE5_0F_BOOTSTRAP_N = 1000
STAGE5_0F_JSON_REPORT_PATH = REPORTS_DIR / "stage5_0f_signal_stationarity.json"
STAGE5_1_JSON_REPORT_PATH = REPORTS_DIR / "stage5_1_structural_field_ablation.json"
STAGE5_1_TARGETS = [
    "sell_stop_broken_H6_off05_flag",
    "buy_stop_broken_H6_off05_flag",
]
STAGE5_1_FIELDS = NO_PRICE_TOKEN_FIELDS.copy()
STAGE5_1_PROFILE_KEYS = (
    ["time_only", "structure_full"]
    + [f"drop_{field}" for field in STAGE5_1_FIELDS]
    + [f"add_{field}" for field in STAGE5_1_FIELDS]
)
STAGE5_1_SEEDS = [42, 77, 123]
STAGE5_1_VAL_YEARS = [2021, 2022]
STAGE5_1_HOLDOUT_YEARS = [2023, 2024, 2025]
STAGE5_1_LOW_N_YEAR = 2026
STAGE5_1_BOOTSTRAP_N = 1000

# ===========================================================================
# Profile definitions
# ===========================================================================

PROFILE_DEFS = [
    {
        "name": "all100_base10_time",
        "selection": "all100",
        "order": "freshness",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 5,
    },
    {
        "name": "all100_base10_no_time",
        "selection": "all100",
        "order": "freshness",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 1,
    },
    {
        "name": "newest20_base10_time",
        "selection": "newest",
        "order": "freshness",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 20,
        "token_dim": 10,
        "row_dim": 5,
        "n": 20,
    },
    {
        "name": "nearest40_base10_time",
        "selection": "nearest",
        "order": "price_distance",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 40,
        "token_dim": 10,
        "row_dim": 5,
        "k": 40,
    },
    {
        "name": "corridor_10atr_base10_time",
        "selection": "corridor",
        "order": "price_distance",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 40,
        "token_dim": 10,
        "row_dim": 5,
        "corridor_atr": 10.0,
    },
    # Phase 3 — conditional
    {
        "name": "corridor_5atr_base10_time",
        "selection": "corridor",
        "order": "price_distance",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 30,
        "token_dim": 10,
        "row_dim": 5,
        "corridor_atr": 5.0,
    },
    {
        "name": "corridor_15atr_base10_time",
        "selection": "corridor",
        "order": "price_distance",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 50,
        "token_dim": 10,
        "row_dim": 5,
        "corridor_atr": 15.0,
    },
    # Phase 4 — optional
    {
        "name": "all100_full29_time",
        "selection": "all100",
        "order": "freshness",
        "token_fields": None,  # uses Full29 extraction
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 100,
        "token_dim": 20,
        "row_dim": 5,
        "full29": True,
    },
    {
        "name": "all100_base10_no_price_time",
        "selection": "all100",
        "order": "freshness",
        "token_fields": ["direction", "front", "back", "strong", "break",
                         "reverse", "power", "count", "impulse"],
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 100,
        "token_dim": 9,
        "row_dim": 5,
    },
    # Diagnostic: relative_price = (fractal_price - fractal0_price) / ATR
    {
        "name": "all100_base10_relative_price_time",
        "selection": "all100",
        "order": "freshness",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 5,
        "relative_price": True,
    },
    {
        "name": "nearest40_base10_relative_price_time",
        "selection": "nearest",
        "order": "price_distance",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 40,
        "token_dim": 10,
        "row_dim": 5,
        "k": 40,
        "relative_price": True,
    },
    {
        "name": "corridor_10atr_base10_relative_price_time",
        "selection": "corridor",
        "order": "price_distance",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": ["ATR", "hour_sin", "hour_cos", "dow_sin", "dow_cos"],
        "uses_time": True,
        "seq_len": 40,
        "token_dim": 10,
        "row_dim": 5,
        "corridor_atr": 10.0,
        "relative_price": True,
    },
    # Stage 5.0a preflight profiles
    {
        "name": "time_only_clean",
        "selection": "row_only",
        "selector": "no token selector",
        "order": "none",
        "token_order": "none",
        "token_fields": [],
        "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 0,
        "token_dim": 0,
        "row_dim": 4,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
    },
    {
        "name": "atr_only",
        "selection": "row_only",
        "selector": "no token selector",
        "order": "none",
        "token_order": "none",
        "token_fields": [],
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 0,
        "token_dim": 0,
        "row_dim": 1,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
    },
    {
        "name": "time_plus_atr",
        "selection": "row_only",
        "selector": "no token selector",
        "order": "none",
        "token_order": "none",
        "token_fields": [],
        "row_fields": TIME_PLUS_ATR_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 0,
        "token_dim": 0,
        "row_dim": 5,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
    },
    {
        "name": "all100_absolute_price_time",
        "selection": "all100",
        "selector": "fractal0..fractal99",
        "order": "freshness",
        "token_order": "freshness: fractal0, fractal1, ...",
        "token_fields": BASE10_NAMES.copy(),
        "row_fields": TIME_PLUS_ATR_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 5,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
    },
    {
        "name": "all100_no_price_time",
        "selection": "all100",
        "selector": "fractal0..fractal99",
        "order": "freshness",
        "token_order": "freshness: fractal0, fractal1, ...",
        "token_fields": NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": TIME_PLUS_ATR_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 100,
        "token_dim": 9,
        "row_dim": 5,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
    },
    {
        "name": "all100_relative_price_no_time",
        "selection": "all100",
        "selector": "fractal0..fractal99",
        "order": "freshness",
        "token_order": "freshness: fractal0, fractal1, ...",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 1,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "relative_price": True,
    },
    {
        "name": "all100_relative_price_time",
        "selection": "all100",
        "selector": "fractal0..fractal99",
        "order": "freshness",
        "token_order": "freshness: fractal0, fractal1, ...",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": TIME_PLUS_ATR_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 5,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "relative_price": True,
    },
    {
        "name": "all100_absolute_price_atr_scaled_time_raw",
        "selection": "all100",
        "selector": "fractal0..fractal99",
        "order": "freshness",
        "token_order": "freshness: fractal0, fractal1, ...",
        "token_fields": ['price_atr_scaled'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": TIME_PLUS_ATR_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 5,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "absolute_price_atr_scaled": True,
        "price_atr_scaled_transform": "raw",
        "diagnostic_only": True,
    },
    {
        "name": "all100_absolute_price_atr_scaled_time_asinh",
        "selection": "all100",
        "selector": "fractal0..fractal99",
        "order": "freshness",
        "token_order": "freshness: fractal0, fractal1, ...",
        "token_fields": ['price_atr_scaled'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": TIME_PLUS_ATR_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 5,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "absolute_price_atr_scaled": True,
        "price_atr_scaled_transform": "asinh",
        "diagnostic_only": True,
    },
    {
        "name": "corridor_5atr_relative_price_no_time",
        "selection": "corridor",
        "selector": "levels within +/-5 ATR from fractal0.price",
        "order": "price_distance_with_anchor_first",
        "token_order": "anchor first, then ascending absolute distance to anchor",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 40,
        "token_dim": 10,
        "row_dim": 1,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "corridor_atr": 5.0,
        "relative_price": True,
    },
    {
        "name": "corridor_10atr_relative_price_no_time",
        "selection": "corridor",
        "selector": "levels within +/-10 ATR from fractal0.price",
        "order": "price_distance_with_anchor_first",
        "token_order": "anchor first, then ascending absolute distance to anchor",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 40,
        "token_dim": 10,
        "row_dim": 1,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "corridor_atr": 10.0,
        "relative_price": True,
    },
    {
        "name": "corridor_5atr_relative_price_no_time_full",
        "selection": "corridor",
        "selector": "levels within +/-5 ATR from fractal0.price",
        "order": "price_distance_with_anchor_first",
        "token_order": "anchor first, then ascending absolute distance to anchor",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": [],
        "uses_time": False,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 0,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "corridor_atr": 5.0,
        "relative_price": True,
        "diagnostic_only": True,
    },
    {
        "name": "corridor_10atr_relative_price_no_time_full",
        "selection": "corridor",
        "selector": "levels within +/-10 ATR from fractal0.price",
        "order": "price_distance_with_anchor_first",
        "token_order": "anchor first, then ascending absolute distance to anchor",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": [],
        "uses_time": False,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 0,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "corridor_atr": 10.0,
        "relative_price": True,
        "diagnostic_only": True,
    },
    {
        "name": "corridor_5atr_relative_price_atr_full",
        "selection": "corridor",
        "selector": "levels within +/-5 ATR from fractal0.price",
        "order": "price_distance_with_anchor_first",
        "token_order": "anchor first, then ascending absolute distance to anchor",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 1,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "corridor_atr": 5.0,
        "relative_price": True,
    },
    {
        "name": "corridor_10atr_relative_price_atr_full",
        "selection": "corridor",
        "selector": "levels within +/-10 ATR from fractal0.price",
        "order": "price_distance_with_anchor_first",
        "token_order": "anchor first, then ascending absolute distance to anchor",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 1,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "corridor_atr": 10.0,
        "relative_price": True,
    },
    {
        "name": "corridor_5atr_price_unit_atr_full",
        "selection": "corridor",
        "selector": "levels within +/-5 ATR from fractal0.price",
        "order": "price_distance_with_anchor_first",
        "token_order": "anchor first, then ascending absolute distance to anchor",
        "token_fields": ['price_coord_unit'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 1,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "corridor_atr": 5.0,
        "corridor_price_unit": True,
        "diagnostic_only": True,
    },
    {
        "name": "corridor_10atr_price_unit_atr_full",
        "selection": "corridor",
        "selector": "levels within +/-10 ATR from fractal0.price",
        "order": "price_distance_with_anchor_first",
        "token_order": "anchor first, then ascending absolute distance to anchor",
        "token_fields": ['price_coord_unit'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 100,
        "token_dim": 10,
        "row_dim": 1,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "corridor_atr": 10.0,
        "corridor_price_unit": True,
        "diagnostic_only": True,
    },
    {
        "name": "corridor_15atr_relative_price_no_time",
        "selection": "corridor",
        "selector": "levels within +/-15 ATR from fractal0.price",
        "order": "price_distance_with_anchor_first",
        "token_order": "anchor first, then ascending absolute distance to anchor",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 40,
        "token_dim": 10,
        "row_dim": 1,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "corridor_atr": 15.0,
        "relative_price": True,
    },
    {
        "name": "corridor_10atr_relative_price_time",
        "selection": "corridor",
        "selector": "levels within +/-10 ATR from fractal0.price",
        "order": "price_distance_with_anchor_first",
        "token_order": "anchor first, then ascending absolute distance to anchor",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": TIME_PLUS_ATR_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 40,
        "token_dim": 10,
        "row_dim": 5,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "corridor_atr": 10.0,
        "relative_price": True,
    },
    {
        "name": "nearest40_relative_price_no_time",
        "selection": "nearest",
        "selector": "40 closest levels to fractal0.price, excluding anchor from K",
        "order": "price_distance_excluding_anchor",
        "token_order": "ascending absolute distance to anchor; tie-breaker by freshness",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": ["ATR"],
        "uses_time": False,
        "seq_len": 40,
        "token_dim": 10,
        "row_dim": 1,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "k": 40,
        "relative_price": True,
        "exclude_anchor_from_k": True,
    },
    {
        "name": "nearest40_relative_price_time",
        "selection": "nearest",
        "selector": "40 closest levels to fractal0.price, excluding anchor from K",
        "order": "price_distance_excluding_anchor",
        "token_order": "ascending absolute distance to anchor; tie-breaker by freshness",
        "token_fields": ['price_coord_atr'] + NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": TIME_PLUS_ATR_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 40,
        "token_dim": 10,
        "row_dim": 5,
        "padding_value": 0.0,
        "mask_semantics": "1=real token, 0=padding",
        "k": 40,
        "relative_price": True,
        "exclude_anchor_from_k": True,
    },
]


def define_profiles():
    return PROFILE_DEFS


def find_profile(name: str):
    for p in PROFILE_DEFS:
        if p["name"] == name:
            return p
    return None


def get_profile_contract(profile: dict) -> dict:
    return {
        "name": profile["name"],
        "selection": profile["selection"],
        "selector": profile.get("selector", profile["selection"]),
        "token_fields": list(profile.get("token_fields", [])),
        "row_fields": list(profile.get("row_fields", [])),
        "token_order": profile.get("token_order", profile.get("order", "unknown")),
        "seq_len": int(profile.get("seq_len", 0)),
        "padding_value": float(profile.get("padding_value", 0.0)),
        "mask_semantics": profile.get("mask_semantics", "1=real token, 0=padding"),
        "diagnostic_only": bool(profile.get("diagnostic_only", False)),
    }


def get_profile_seq_len(profile: dict, train_df: pd.DataFrame = None,
                        val_stop_df: pd.DataFrame = None) -> int:
    """Return seq_len, optionally adjusted from corridor validation (Phase 3)."""
    if profile.get("selection") == "corridor" and train_df is not None:
        combined = pd.concat([train_df, val_stop_df], ignore_index=True)
        stats = compute_corridor_stats(combined, profile)
        n_median = stats["n_fractals_median"]
        declared_seq = profile["seq_len"]
        p80 = stats.get("n_fractals_p80", declared_seq)
        if p80 < declared_seq:
            return max(int(p80), 3)
        return declared_seq
    return profile["seq_len"]


# ===========================================================================
# Feature extraction
# ===========================================================================

def extract_base10_fields(fractal_str: str) -> np.ndarray:
    """Extract base10 features from a single fractal string."""
    parts = fractal_str.split(FRACTAL_SEP)
    result = np.zeros(10, dtype=np.float32)
    if len(parts) < 23:
        return result
    for j, idx in enumerate(BASE10_INDICES):
        try:
            result[j] = float(parts[idx])
        except (ValueError, IndexError):
            result[j] = 0.0
    if np.isnan(result).any():
        result = np.nan_to_num(result, nan=0.0)
    return result


def extract_full29_fields(fractal_str: str) -> np.ndarray:
    """Extract Full29 (first 20 fields) from a single fractal string."""
    parts = fractal_str.split(FRACTAL_SEP)
    result = np.zeros(20, dtype=np.float32)
    if len(parts) < 21:
        return result
    for j, idx in enumerate(FULL29_INDICES):
        try:
            result[j] = float(parts[idx])
        except (ValueError, IndexError):
            result[j] = 0.0
    if np.isnan(result).any():
        result = np.nan_to_num(result, nan=0.0)
    return result


def _base10_name_to_index() -> dict:
    return {name: idx for idx, name in enumerate(BASE10_NAMES)}


BASE10_NAME_TO_INDEX = _base10_name_to_index()


def project_token_fields(base_features: np.ndarray, profile: dict) -> np.ndarray:
    token_fields = profile.get("token_fields", [])
    if not token_fields:
        return np.zeros((base_features.shape[0], 0), dtype=np.float32)

    projected = np.zeros((base_features.shape[0], len(token_fields)), dtype=np.float32)
    for out_idx, field_name in enumerate(token_fields):
        source_name = "price" if field_name in {
            "price_coord_atr",
            "price_coord_unit",
            "price_atr_scaled",
        } else field_name
        source_idx = BASE10_NAME_TO_INDEX[source_name]
        projected[:, out_idx] = base_features[:, source_idx]
    return projected


def _signed_log1p(x: np.ndarray) -> np.ndarray:
    """A7: signed-log transform for signed values with long tails
    (signed distance, signed return, signed price coordinate).
    sign(x) * log1p(abs(x)); x=0 -> 0; compresses |x|>1 tails monotonically.
    """
    return np.sign(x) * np.log1p(np.abs(x))


def _asinh_transform(x: np.ndarray) -> np.ndarray:
    """Soft tail compression: near zero it is almost linear, tails are log-like."""
    return np.arcsinh(x)


def _fit_piecewise_tail_params(values: np.ndarray, lower_q: float = 5, upper_q: float = 95) -> dict:
    """Fit piecewise tail-compression thresholds on train values only."""
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    clean = arr[np.isfinite(arr)]
    if len(clean) == 0:
        lower = upper = 0.0
    else:
        lower, upper = np.percentile(clean, [lower_q, upper_q])
        if upper < lower:
            lower, upper = upper, lower
    return {
        "lower": float(lower),
        "upper": float(upper),
        "lower_q": float(lower_q),
        "upper_q": float(upper_q),
        "fit_split": "train",
    }


def _apply_piecewise_tail_transform(x: np.ndarray, params: dict) -> np.ndarray:
    """Keep the middle interval linear; compress values below/above thresholds."""
    arr = np.asarray(x, dtype=np.float32)
    lower = float(params.get("lower", 0.0))
    upper = float(params.get("upper", lower))
    if upper <= lower:
        return arr.copy()
    out = arr.copy()
    lower_mask = out < lower
    upper_mask = out > upper
    out[lower_mask] = lower - np.log1p(lower - out[lower_mask])
    out[upper_mask] = upper + np.log1p(out[upper_mask] - upper)
    return out.astype(np.float32)


def _transform_atr_values(values: np.ndarray, transform_variant: str = "current",
                          transform_params: dict | None = None) -> np.ndarray:
    if transform_variant == "identity":
        return np.asarray(values, dtype=np.float32)
    variant = TRANSFORM_VARIANTS.get(transform_variant, TRANSFORM_VARIANTS["current"])
    method = variant.get("row_atr", "log1p")
    vals = np.asarray(values, dtype=np.float32)
    if method == "log1p":
        return np.log1p(np.clip(vals, 0.0, None)).astype(np.float32)
    if method == "asinh":
        return _asinh_transform(np.clip(vals, 0.0, None)).astype(np.float32)
    if method == "piecewise_tail":
        params = (transform_params or {}).get("ATR")
        if params is None:
            params = _fit_piecewise_tail_params(np.clip(vals, 0.0, None))
        return _apply_piecewise_tail_transform(np.clip(vals, 0.0, None), params)
    raise ValueError(f"Unknown ATR transform method: {method}")


def _transform_price_coord_values(values: np.ndarray, transform_variant: str = "current",
                                  transform_params: dict | None = None) -> np.ndarray:
    if transform_variant == "identity":
        return np.asarray(values, dtype=np.float32)
    variant = TRANSFORM_VARIANTS.get(transform_variant, TRANSFORM_VARIANTS["current"])
    method = variant.get("price_coord_atr", "signed_log1p")
    vals = np.asarray(values, dtype=np.float32)
    if method == "signed_log1p":
        return _signed_log1p(vals).astype(np.float32)
    if method == "asinh":
        return _asinh_transform(vals).astype(np.float32)
    if method == "piecewise_tail":
        params = (transform_params or {}).get("price_coord_atr")
        if params is None:
            params = _fit_piecewise_tail_params(vals)
        return _apply_piecewise_tail_transform(vals, params)
    raise ValueError(f"Unknown price_coord_atr transform method: {method}")


def _post_process_price_fields(tokens: np.ndarray, mask: np.ndarray, token_fields: list,
                               f0_prices: np.ndarray, atr_vals: np.ndarray, profile: dict,
                               transform_variant: str = "current",
                               transform_params: dict | None = None) -> None:
    """Replace raw price placeholder fields with ATR-scaled diagnostic values."""
    safe_atr = np.maximum(np.asarray(atr_vals, dtype=np.float32), 0.001)
    if "price_coord_atr" in token_fields or (profile.get("relative_price", False) and "price" in token_fields):
        price_idx = token_fields.index("price_coord_atr") if "price_coord_atr" in token_fields else token_fields.index("price")
        price_col = tokens[:, :, price_idx]
        raw_coord = (price_col - f0_prices[:, None]) / safe_atr[:, None]
        tokens[:, :, price_idx] = _transform_price_coord_values(
            raw_coord, transform_variant, transform_params)

    if "price_coord_unit" in token_fields:
        price_idx = token_fields.index("price_coord_unit")
        price_col = tokens[:, :, price_idx]
        corridor_atr = max(float(profile.get("corridor_atr", 1.0)), 0.001)
        raw_coord = (price_col - f0_prices[:, None]) / safe_atr[:, None]
        tokens[:, :, price_idx] = (raw_coord / corridor_atr).astype(np.float32)

    if "price_atr_scaled" in token_fields:
        price_idx = token_fields.index("price_atr_scaled")
        price_col = tokens[:, :, price_idx]
        scaled = price_col / safe_atr[:, None]
        method = profile.get("price_atr_scaled_transform", "raw")
        if method == "raw":
            tokens[:, :, price_idx] = scaled.astype(np.float32)
        elif method == "asinh":
            tokens[:, :, price_idx] = _asinh_transform(scaled).astype(np.float32)
        else:
            raise ValueError(f"Unknown price_atr_scaled transform method: {method}")

    tokens[~mask] = 0.0


def fit_transform_params_for_profile(train_df: pd.DataFrame, parsed_train: dict,
                                     profile: dict, transform_variant: str) -> dict:
    """Fit train-only parameters for transforms that need quantile thresholds."""
    variant = TRANSFORM_VARIANTS.get(transform_variant, TRANSFORM_VARIANTS["current"])
    if not variant.get("fit_params", False):
        return {}

    lower_q = float(variant.get("lower_q", 5))
    upper_q = float(variant.get("upper_q", 95))
    params = {}

    if "ATR" in profile.get("row_fields", []):
        atr_vals = pd.to_numeric(train_df["ATR"], errors="coerce").fillna(0.0).clip(lower=0.0).values
        params["ATR"] = _fit_piecewise_tail_params(atr_vals, lower_q, upper_q)

    if profile.get("relative_price", False) and "price_coord_atr" in profile.get("token_fields", []):
        raw_tokens, _, raw_mask, _ = build_profile_features_from_parsed(
            train_df, parsed_train, profile, transform_variant="identity")
        price_idx = profile["token_fields"].index("price_coord_atr")
        raw_coords = raw_tokens[:, :, price_idx][raw_mask]
        params["price_coord_atr"] = _fit_piecewise_tail_params(raw_coords, lower_q, upper_q)

    return params


def build_row_features(df: pd.DataFrame, profile: dict, transform_variant: str = "current",
                       transform_params: dict | None = None) -> np.ndarray:
    """Build row-level features: ATR + optional time features."""
    row_fields = profile["row_fields"]
    n_rows = len(df)
    result = np.zeros((n_rows, len(row_fields)), dtype=np.float32)
    col_map = {}
    for j, field in enumerate(row_fields):
        if field == "ATR":
            col_map[j] = "ATR"
        elif field == "hour_sin":
            col_map[j] = "hour_sin"
        elif field == "hour_cos":
            col_map[j] = "hour_cos"
        elif field == "dow_sin":
            col_map[j] = "dow_sin"
        elif field == "dow_cos":
            col_map[j] = "dow_cos"

    for j, csv_col in col_map.items():
        if csv_col == "ATR":
            # A7 feature-distribution-audit: ATR is non-negative with a long right
            # tail and holdout regime shift; log1p before StandardScaler compresses
            # the tail (ATR=0 -> 0, ATR>0 monotonic). price_coord_atr keeps raw ATR
            # as denominator (handled in build_profile_features_from_parsed).
            vals = pd.to_numeric(df["ATR"], errors="coerce").fillna(0.0).clip(lower=0.0).values
            result[:, j] = _transform_atr_values(vals, transform_variant, transform_params)
        elif csv_col.startswith("hour_") or csv_col.startswith("dow_"):
            times = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce")
            if csv_col == "hour_sin":
                result[:, j] = np.sin(2 * np.pi * times.dt.hour.fillna(0).values / 24).astype(np.float32)
            elif csv_col == "hour_cos":
                result[:, j] = np.cos(2 * np.pi * times.dt.hour.fillna(0).values / 24).astype(np.float32)
            elif csv_col == "dow_sin":
                result[:, j] = np.sin(2 * np.pi * times.dt.dayofweek.fillna(0).values / 7).astype(np.float32)
            elif csv_col == "dow_cos":
                result[:, j] = np.cos(2 * np.pi * times.dt.dayofweek.fillna(0).values / 7).astype(np.float32)

    if np.isnan(result).any():
        result = np.nan_to_num(result, nan=0.0)
    return result


def build_profile_features(df: pd.DataFrame, profile: dict, transform_variant: str = "current",
                           transform_params: dict | None = None):
    """Build token tensor, row_features, and mask for a profile.

    Returns:
        tokens: (n_samples, seq_len, token_dim)
        row_features: (n_samples, row_dim)
        mask: (n_samples, seq_len)
        selection_meta: raw coverage before seq_len cap
    """
    n_samples = len(df)
    seq_len = profile["seq_len"]
    token_dim = profile["token_dim"]
    selection = profile["selection"]
    is_full29 = profile.get("full29", False)
    token_fields = profile.get("token_fields", [])

    tokens = np.zeros((n_samples, seq_len, token_dim), dtype=np.float32)
    mask = np.zeros((n_samples, seq_len), dtype=bool)

    if selection == "row_only" or seq_len == 0 or token_dim == 0:
        row_features = build_row_features(df, profile, transform_variant, transform_params)
        if np.isnan(row_features).any():
            row_features = np.nan_to_num(row_features, nan=0.0)
        selection_meta = {
            "candidate_count_before_cap": np.zeros(n_samples, dtype=np.int32),
            "selected_count_after_cap": np.zeros(n_samples, dtype=np.int32),
            "is_truncated": np.zeros(n_samples, dtype=bool),
        }
        return tokens.astype(np.float32), row_features.astype(np.float32), mask, selection_meta

    candidate_count_before_cap = np.zeros(n_samples, dtype=np.int32)
    selected_count_after_cap = np.zeros(n_samples, dtype=np.int32)
    is_truncated = np.zeros(n_samples, dtype=bool)

    # Pre-parse all fractal columns
    for sample_idx in range(n_samples):
        # Parse all available fractal prices and features
        prices = np.zeros(N_FRACTALS, dtype=np.float32)
        raw_base10 = np.zeros((N_FRACTALS, len(BASE10_NAMES)), dtype=np.float32)
        raw_features = np.zeros((N_FRACTALS, token_dim), dtype=np.float32)
        valid_fractals = np.zeros(N_FRACTALS, dtype=bool)
        valid_count = 0

        for f_idx in range(N_FRACTALS):
            col = f"fractal{f_idx}"
            if col not in df.columns:
                break
            fstr = str(df[col].iloc[sample_idx])
            if fstr and fstr != "nan":
                if is_full29:
                    raw_features[f_idx] = extract_full29_fields(fstr)
                else:
                    raw_base10[f_idx] = extract_base10_fields(fstr)
                    raw_features[f_idx] = project_token_fields(raw_base10[[f_idx]], profile)[0]
                # Extract price for selection
                parts = fstr.split(FRACTAL_SEP)
                try:
                    prices[f_idx] = float(parts[1])
                except (ValueError, IndexError):
                    prices[f_idx] = 0.0
                # Check if this fractal is valid (not all zeros)
                if np.any(raw_features[f_idx] != 0):
                    valid_fractals[f_idx] = True
                    valid_count += 1

        if valid_count == 0:
            mask[sample_idx, :] = False
            continue

        valid_prices = prices[valid_fractals]
        valid_features = raw_features[valid_fractals]
        valid_indices = np.where(valid_fractals)[0]

        raw_candidate_count = valid_count
        if selection == "all100":
            selected_idx, m = TokenSelector.all_fractals(valid_count, seq_len)
        elif selection == "newest":
            n_val = int(profile.get("n", seq_len))
            selected_idx, m = TokenSelector.newest_n(n_val, valid_count, seq_len)
            raw_candidate_count = min(valid_count, n_val)
        elif selection == "nearest":
            k_val = int(profile.get("k", seq_len))
            selected_idx, m, _ = TokenSelector.by_nearest(
                valid_prices, prices[0], k_val, seq_len,
                exclude_anchor=profile.get("exclude_anchor_from_k", False),
                anchor_valid_position=0,
            )
            excluded_anchor = 1 if profile.get("exclude_anchor_from_k", False) and valid_count > 0 else 0
            raw_candidate_count = min(max(valid_count - excluded_anchor, 0), k_val)
        elif selection == "corridor":
            corridor_atr_val = profile.get("corridor_atr", 10.0)
            atr_val = pd.to_numeric(df["ATR"].iloc[sample_idx], errors="coerce")
            atr_val = atr_val if atr_val > 0 else 1.0
            corridor_threshold = corridor_atr_val * atr_val
            raw_candidate_count = int(np.sum(np.abs(valid_prices - prices[0]) <= corridor_threshold))
            selected_idx, m, _ = TokenSelector.by_corridor(
                valid_prices, prices[0], atr_val, corridor_atr_val, seq_len)
        else:
            selected_idx, m = TokenSelector.all_fractals(valid_count, seq_len)

        candidate_count_before_cap[sample_idx] = max(int(raw_candidate_count), 0)
        selected_count_after_cap[sample_idx] = int(m.sum())
        is_truncated[sample_idx] = candidate_count_before_cap[sample_idx] > seq_len

        # Map selected_idx (into valid_fractals) back to valid_indices and then into feature array
        for t in range(min(len(selected_idx), seq_len)):
            if m[t]:
                mapped_idx = selected_idx[t]
                if mapped_idx < len(valid_features):
                    tokens[sample_idx, t] = valid_features[mapped_idx]
                    mask[sample_idx, t] = True

    row_features = build_row_features(df, profile, transform_variant, transform_params)

    if profile.get("relative_price", False) or any(
        field in token_fields for field in ["price_coord_unit", "price_atr_scaled"]
    ):
        f0_prices = np.zeros(n_samples, dtype=np.float32)
        atr_vals = np.zeros(n_samples, dtype=np.float32)
        for sample_idx in range(n_samples):
            fstr = str(df["fractal0"].iloc[sample_idx])
            try:
                f0_prices[sample_idx] = float(fstr.split(FRACTAL_SEP)[1])
            except (ValueError, IndexError):
                f0_prices[sample_idx] = 0.0
            atr_raw = pd.to_numeric(df["ATR"].iloc[sample_idx], errors="coerce")
            atr_vals[sample_idx] = max(float(atr_raw) if not pd.isna(atr_raw) else 1.0, 0.001)
        _post_process_price_fields(
            tokens, mask, token_fields, f0_prices, atr_vals, profile,
            transform_variant, transform_params)

    if np.isnan(tokens).any():
        tokens = np.nan_to_num(tokens, nan=0.0)
    if np.isnan(row_features).any():
        row_features = np.nan_to_num(row_features, nan=0.0)

    selection_meta = {
        "candidate_count_before_cap": candidate_count_before_cap,
        "selected_count_after_cap": selected_count_after_cap,
        "is_truncated": is_truncated,
    }
    return tokens.astype(np.float32), row_features.astype(np.float32), mask, selection_meta


def parse_split_fractals(df: pd.DataFrame) -> dict:
    n_samples = len(df)
    prices = np.zeros((n_samples, N_FRACTALS), dtype=np.float32)
    base10 = np.zeros((n_samples, N_FRACTALS, len(BASE10_NAMES)), dtype=np.float32)
    valid = np.zeros((n_samples, N_FRACTALS), dtype=bool)

    available_cols = [f"fractal{i}" for i in range(N_FRACTALS) if f"fractal{i}" in df.columns]
    for sample_idx in range(n_samples):
        for f_idx, col in enumerate(available_cols):
            fstr = str(df[col].iloc[sample_idx])
            if not fstr or fstr == "nan":
                continue
            base10[sample_idx, f_idx] = extract_base10_fields(fstr)
            try:
                prices[sample_idx, f_idx] = float(fstr.split(FRACTAL_SEP)[1])
            except (ValueError, IndexError):
                prices[sample_idx, f_idx] = 0.0
            if np.any(base10[sample_idx, f_idx] != 0):
                valid[sample_idx, f_idx] = True
    return {"prices": prices, "base10": base10, "valid": valid}


def build_profile_features_from_parsed(df: pd.DataFrame, parsed: dict, profile: dict,
                                       transform_variant: str = "current",
                                       transform_params: dict | None = None):
    n_samples = len(df)
    seq_len = profile["seq_len"]
    token_dim = profile["token_dim"]
    selection = profile["selection"]
    token_fields = profile.get("token_fields", [])
    tokens = np.zeros((n_samples, seq_len, token_dim), dtype=np.float32)
    mask = np.zeros((n_samples, seq_len), dtype=bool)

    if selection == "row_only" or seq_len == 0 or token_dim == 0:
        selection_meta = {
            "candidate_count_before_cap": np.zeros(n_samples, dtype=np.int32),
            "selected_count_after_cap": np.zeros(n_samples, dtype=np.int32),
            "is_truncated": np.zeros(n_samples, dtype=bool),
        }
        return (
            np.zeros((n_samples, 0, 0), dtype=np.float32),
            build_row_features(df, profile, transform_variant, transform_params),
            np.zeros((n_samples, 0), dtype=bool),
            selection_meta,
        )

    prices_all = parsed["prices"]
    valid_all = parsed["valid"]
    base10_all = parsed["base10"]
    candidate_count_before_cap = np.zeros(n_samples, dtype=np.int32)
    selected_count_after_cap = np.zeros(n_samples, dtype=np.int32)
    is_truncated = np.zeros(n_samples, dtype=bool)

    for sample_idx in range(n_samples):
        valid_mask = valid_all[sample_idx]
        valid_count = int(valid_mask.sum())
        if valid_count == 0:
            continue
        valid_prices = prices_all[sample_idx, valid_mask]
        valid_base10 = base10_all[sample_idx, valid_mask]
        valid_features = project_token_fields(valid_base10, profile)

        raw_candidate_count = valid_count
        if selection == "all100":
            selected_idx, m = TokenSelector.all_fractals(valid_count, seq_len)
        elif selection == "newest":
            n_val = int(profile.get("n", seq_len))
            selected_idx, m = TokenSelector.newest_n(n_val, valid_count, seq_len)
            raw_candidate_count = min(valid_count, n_val)
        elif selection == "nearest":
            k_val = int(profile.get("k", seq_len))
            selected_idx, m, _ = TokenSelector.by_nearest(
                valid_prices, prices_all[sample_idx, 0], k_val, seq_len,
                exclude_anchor=profile.get("exclude_anchor_from_k", False),
                anchor_valid_position=0,
            )
            excluded_anchor = 1 if profile.get("exclude_anchor_from_k", False) and valid_count > 0 else 0
            raw_candidate_count = min(max(valid_count - excluded_anchor, 0), k_val)
        elif selection == "corridor":
            atr_val = pd.to_numeric(df["ATR"].iloc[sample_idx], errors="coerce")
            atr_val = atr_val if atr_val > 0 else 1.0
            corridor_threshold = profile.get("corridor_atr", 10.0) * atr_val
            raw_candidate_count = int(np.sum(np.abs(valid_prices - prices_all[sample_idx, 0]) <= corridor_threshold))
            selected_idx, m, _ = TokenSelector.by_corridor(
                valid_prices, prices_all[sample_idx, 0], atr_val, profile.get("corridor_atr", 10.0), seq_len
            )
        else:
            selected_idx, m = TokenSelector.all_fractals(valid_count, seq_len)

        candidate_count_before_cap[sample_idx] = max(int(raw_candidate_count), 0)
        selected_count_after_cap[sample_idx] = int(m.sum())
        is_truncated[sample_idx] = candidate_count_before_cap[sample_idx] > seq_len

        for t in range(min(len(selected_idx), seq_len)):
            if m[t] and selected_idx[t] < len(valid_features):
                tokens[sample_idx, t] = valid_features[selected_idx[t]]
                mask[sample_idx, t] = True

    row_features = build_row_features(df, profile, transform_variant, transform_params)
    if profile.get("relative_price", False) or any(
        field in token_fields for field in ["price_coord_unit", "price_atr_scaled"]
    ):
        f0_prices = prices_all[:, 0].copy()
        atr_vals = pd.to_numeric(df["ATR"], errors="coerce").fillna(1.0).clip(lower=0.001).values.astype(np.float32)
        _post_process_price_fields(
            tokens, mask, token_fields, f0_prices, atr_vals, profile,
            transform_variant, transform_params)

    if np.isnan(tokens).any():
        tokens = np.nan_to_num(tokens, nan=0.0)
    if np.isnan(row_features).any():
        row_features = np.nan_to_num(row_features, nan=0.0)
    selection_meta = {
        "candidate_count_before_cap": candidate_count_before_cap,
        "selected_count_after_cap": selected_count_after_cap,
        "is_truncated": is_truncated,
    }
    return tokens.astype(np.float32), row_features.astype(np.float32), mask, selection_meta


# ===========================================================================
# Normalization (fit on train valid positions only; apply to all splits)
# ===========================================================================

def normalize_profile_features(tokens_train, row_feat_train, mask_train,
                                tokens_val, row_feat_val, mask_val,
                                tokens_hold, row_feat_hold, mask_hold):
    """Fit StandardScaler on train valid positions only. Transform all splits.

    Token scaler: fit only on valid token positions (mask=True). Padding stays 0.
    Row scaler: fit on all train rows.
    """
    n_samples, seq_len, token_dim = tokens_train.shape

    valid_train_tokens = tokens_train[mask_train] if token_dim > 0 else np.zeros((0, 0), dtype=np.float32)
    token_scaler = StandardScaler()
    if token_dim == 0:
        token_scaler.mean_ = np.zeros(0)
        token_scaler.scale_ = np.ones(0)
    elif len(valid_train_tokens) > 0:
        token_scaler.fit(valid_train_tokens)
    else:
        token_scaler.mean_ = np.zeros(token_dim)
        token_scaler.scale_ = np.ones(token_dim)

    def _transform_tokens(tok, m):
        out = tok.copy()
        for d in range(token_dim):
            std = float(token_scaler.scale_[d])
            if std > 1e-8:
                out[:, :, d] = (out[:, :, d] - float(token_scaler.mean_[d])) / std
            else:
                out[:, :, d] = out[:, :, d] - float(token_scaler.mean_[d])
        out[~m] = 0.0
        return out

    tokens_train_n = _transform_tokens(tokens_train, mask_train)
    tokens_val_n = _transform_tokens(tokens_val, mask_val)
    tokens_hold_n = _transform_tokens(tokens_hold, mask_hold)

    row_scaler = StandardScaler()
    if row_feat_train.shape[1] == 0:
        row_scaler.mean_ = np.zeros(0)
        row_scaler.scale_ = np.ones(0)
        row_feat_train_n = row_feat_train.astype(np.float32)
        row_feat_val_n = row_feat_val.astype(np.float32)
        row_feat_hold_n = row_feat_hold.astype(np.float32)
    else:
        row_scaler.fit(row_feat_train)
        row_feat_train_n = row_scaler.transform(row_feat_train).astype(np.float32)
        row_feat_val_n = row_scaler.transform(row_feat_val).astype(np.float32)
        row_feat_hold_n = row_scaler.transform(row_feat_hold).astype(np.float32)

    scaler_stats = {
        "token_scaler": {
            "mean": [float(x) for x in token_scaler.mean_],
            "std": [float(x) for x in token_scaler.scale_],
            "n_valid_train_positions": int(mask_train.sum()),
        },
        "row_scaler": {
            "mean": [float(x) for x in row_scaler.mean_],
            "std": [float(x) for x in row_scaler.scale_],
        },
    }

    return (tokens_train_n, row_feat_train_n,
            tokens_val_n, row_feat_val_n,
            tokens_hold_n, row_feat_hold_n), scaler_stats


# ===========================================================================
# Normalized feature distribution audit
# ===========================================================================

def _per_feature_stats(values: np.ndarray, mask: np.ndarray = None) -> list[dict]:
    """Compute per-feature percentiles, tail fractions, NaN/Inf.

    Supports 2D (N, F) and 3D (N, S, F) arrays. Iterates the last axis as features.
    If mask is provided (same shape as values, bool), only masked=True positions are used.
    Returns a list of dicts, one per feature column (last axis).
    """
    if values.ndim == 3:
        n_feat = values.shape[2]
    else:
        n_feat = values.shape[1]
    result = []
    for f in range(n_feat):
        if values.ndim == 3:
            col = values[:, :, f]
        else:
            col = values[:, f]
        if mask is not None:
            col = col[mask]
        n = len(col)
        if n == 0:
            result.append({"n": 0})
            continue
        col = col.astype(np.float64)
        n_nan = int(np.isnan(col).sum())
        n_inf = int(np.isinf(col).sum())
        clean = col[~(np.isnan(col) | np.isinf(col))]
        n_clean = len(clean)
        tail3 = (np.abs(clean) > 3).sum() / n_clean if n_clean > 0 else 0.0
        tail5 = (np.abs(clean) > 5).sum() / n_clean if n_clean > 0 else 0.0
        tail10 = (np.abs(clean) > 10).sum() / n_clean if n_clean > 0 else 0.0
        tail20 = (np.abs(clean) > 20).sum() / n_clean if n_clean > 0 else 0.0
        zero_pct = float(np.mean(clean == 0.0)) if n_clean > 0 else 0.0
        pvals = np.percentile(clean, [0, 1, 5, 25, 50, 75, 95, 99, 100]) if n_clean > 0 else [np.nan] * 9
        result.append({
            "n": int(n),
            "n_nan": n_nan,
            "n_inf": n_inf,
            "missing_pct": round(float((n - n_clean) / max(n, 1)), 6),
            "zero_pct": round(zero_pct, 6),
            "mean": round(float(np.mean(clean)), 4) if n_clean > 0 else None,
            "std": round(float(np.std(clean)), 4) if n_clean > 0 else None,
            "p0": round(float(pvals[0]), 4) if n_clean > 0 else None,
            "p1": round(float(pvals[1]), 4) if n_clean > 0 else None,
            "p5": round(float(pvals[2]), 4) if n_clean > 0 else None,
            "p25": round(float(pvals[3]), 4) if n_clean > 0 else None,
            "p50": round(float(pvals[4]), 4) if n_clean > 0 else None,
            "p75": round(float(pvals[5]), 4) if n_clean > 0 else None,
            "p95": round(float(pvals[6]), 4) if n_clean > 0 else None,
            "p99": round(float(pvals[7]), 4) if n_clean > 0 else None,
            "p100": round(float(pvals[8]), 4) if n_clean > 0 else None,
            "frac_abs_gt3": round(float(tail3), 6),
            "frac_abs_gt5": round(float(tail5), 6),
            "frac_abs_gt10": round(float(tail10), 6),
            "frac_abs_gt20": round(float(tail20), 6),
            "has_nan": bool(n_nan > 0),
            "has_inf": bool(n_inf > 0),
        })
    return result


def compute_per_position_token_stats(tokens: np.ndarray, mask: np.ndarray,
                                     token_fields: list[str]) -> list[dict]:
    """A7 Feature Distribution Audit: per-position token statistics.

    For sequence profiles where token order has meaning (corridor/nearest/all100),
    aggregate-over-positions stats can hide position-specific tails, padding drift
    or a single extreme position. This computes per-feature stats for each token
    position 0..seq_len-1, using only valid (mask=True) samples at that position.

    Unlike flatten_audit_to_rows, fully-padded positions (n_valid=0) are KEPT,
    because position coverage is itself an A7 diagnostic (padding% per position).

    Returns rows in the same column schema as flatten_audit_to_rows token rows,
    without profile/split keys (added by the caller).
    """
    rows = []
    if tokens.ndim != 3 or tokens.shape[1] == 0 or tokens.shape[2] == 0:
        return rows
    n_samples, seq_len, token_dim = tokens.shape
    if len(token_fields) != token_dim:
        token_fields = [f"t{i}" for i in range(token_dim)]
    for t in range(seq_len):
        pos_mask = mask[:, t] if mask is not None else np.ones(n_samples, dtype=bool)
        pos_tokens = tokens[:, t, :][pos_mask]
        stats = _per_feature_stats(pos_tokens)
        for f_idx, fname in enumerate(token_fields):
            s = stats[f_idx]
            flags = []
            if s.get("n", 0) > 0:
                if s.get("frac_abs_gt10", 0) > 0.01:
                    flags.append("TAIL_GT10")
                if s.get("frac_abs_gt20", 0) > 0.0:
                    flags.append("TAIL_GT20")
                if s.get("has_nan"):
                    flags.append("NAN")
                if s.get("has_inf"):
                    flags.append("INF")
            status = ("ERROR" if ("NAN" in flags or "INF" in flags)
                      else "WARNING" if flags
                      else "OK" if s.get("n", 0) > 0 else "EMPTY")
            rows.append({
                "feature_group": "token",
                "feature_name": fname,
                "token_position": t,
                "n_valid": s.get("n"),
                "missing_pct": s.get("missing_pct"),
                "zero_pct": s.get("zero_pct"),
                "mean": s.get("mean"),
                "std": s.get("std"),
                "min": s.get("p0"),
                "p1": s.get("p1"),
                "p5": s.get("p5"),
                "p25": s.get("p25"),
                "p50": s.get("p50"),
                "p75": s.get("p75"),
                "p95": s.get("p95"),
                "p99": s.get("p99"),
                "max": s.get("p100"),
                "frac_abs_gt3": s.get("frac_abs_gt3"),
                "frac_abs_gt5": s.get("frac_abs_gt5"),
                "frac_abs_gt10": s.get("frac_abs_gt10"),
                "frac_abs_gt20": s.get("frac_abs_gt20"),
                "nan_count": s.get("n_nan"),
                "inf_count": s.get("n_inf"),
                "status": status,
                "flags": ";".join(flags),
            })
    return rows


def audit_normalized_distribution(
    tokens_train, mask_train,
    tokens_val, mask_val,
    tokens_hold, mask_hold,
    rf_train, rf_val, rf_hold,
    token_fields: list[str] | None = None,
    row_fields: list[str] | None = None,
) -> dict:
    """Audit normalized feature distributions across splits.

    Checks:
      - Per-feature percentiles and tail fractions
      - abs(x) > 10 frequently → warning
      - abs(x) > 20 any → warning
      - holdout p95 vs train p95 → regime shift warning
      - padding != 0 → error
      - NaN/Inf in any split → error

    Returns a dict suitable for JSON serialization.
    """
    splits = {
        "train": (tokens_train, mask_train, rf_train),
        "val_stop": (tokens_val, mask_val, rf_val),
        "holdout": (tokens_hold, mask_hold, rf_hold),
    }

    token_fields = token_fields or [f"t{i}" for i in range(tokens_train.shape[2])]
    row_fields = row_fields or [f"r{i}" for i in range(rf_train.shape[1])]

    by_split = {}
    flags = []

    for split_name, (tok, tk_mask, rf) in splits.items():
        # Token features: per-feature stats on valid (masked) positions
        tok_stats = _per_feature_stats(tok, tk_mask)
        # Row features: per-feature stats (all rows)
        rf_stats = _per_feature_stats(rf)

        by_split[split_name] = {
            "token_features": {token_fields[i]: tok_stats[i] for i in range(len(tok_stats))},
            "row_features": {row_fields[i]: rf_stats[i] for i in range(len(rf_stats))},
        }

        # NaN/Inf check
        for feat_name, s in by_split[split_name]["token_features"].items():
            if s.get("has_nan"):
                flags.append(f"NaN in {split_name}.{feat_name} (token)")
            if s.get("has_inf"):
                flags.append(f"Inf in {split_name}.{feat_name} (token)")
        for feat_name, s in by_split[split_name]["row_features"].items():
            if s.get("has_nan"):
                flags.append(f"NaN in {split_name}.{feat_name} (row)")
            if s.get("has_inf"):
                flags.append(f"Inf in {split_name}.{feat_name} (row)")

    # Padding check: masked=False positions must be exactly zero
    ALLOWED_PADDING_DEVIATION = 1e-6
    for split_name, (tok, tk_mask, _) in splits.items():
        padding = tok[~tk_mask]
        if len(padding) > 0:
            padding_abs_max = float(np.max(np.abs(padding)))
            if padding_abs_max > ALLOWED_PADDING_DEVIATION:
                flags.append(f"PADDING_NOT_ZERO in {split_name}: max_abs={padding_abs_max:.2e}")

    # Tail warnings: fraction of abs(x) > 10 across valid positions
    for split_name, (tok, tk_mask, rf) in splits.items():
        for feat_name, s in by_split[split_name]["token_features"].items():
            f10 = s.get("frac_abs_gt10", 0) or 0
            if f10 > 0.01:
                flags.append(f"TAIL_GT10 in {split_name}.{feat_name} (token): frac={f10:.4f}")
            f20 = s.get("frac_abs_gt20", 0) or 0
            if f20 > 0:
                flags.append(f"TAIL_GT20 in {split_name}.{feat_name} (token): frac={f20:.6f}")
        for feat_name, s in by_split[split_name]["row_features"].items():
            f10 = s.get("frac_abs_gt10", 0) or 0
            if f10 > 0.01:
                flags.append(f"TAIL_GT10 in {split_name}.{feat_name} (row): frac={f10:.4f}")
            f20 = s.get("frac_abs_gt20", 0) or 0
            if f20 > 0:
                flags.append(f"TAIL_GT20 in {split_name}.{feat_name} (row): frac={f20:.6f}")

    # Regime shift: holdout p95 vs train p95 delta
    if "train" in by_split and "holdout" in by_split:
        for feat_name in by_split["train"]["token_features"]:
            t_p95 = by_split["train"]["token_features"].get(feat_name, {}).get("p95")
            h_p95 = by_split["holdout"]["token_features"].get(feat_name, {}).get("p95")
            if t_p95 is not None and h_p95 is not None and abs(t_p95) < 100:
                delta = abs(h_p95 - t_p95)
                if delta > 3.0:
                    flags.append(f"REGIME_SHIFT in {feat_name} (token): train_p95={t_p95:.2f} holdout_p95={h_p95:.2f} delta={delta:.2f}")
        for feat_name in by_split["train"]["row_features"]:
            t_p95 = by_split["train"]["row_features"].get(feat_name, {}).get("p95")
            h_p95 = by_split["holdout"]["row_features"].get(feat_name, {}).get("p95")
            if t_p95 is not None and h_p95 is not None and abs(t_p95) < 100:
                delta = abs(h_p95 - t_p95)
                if delta > 3.0:
                    flags.append(f"REGIME_SHIFT in {feat_name} (row): train_p95={t_p95:.2f} holdout_p95={h_p95:.2f} delta={delta:.2f}")

    status = "OK"
    if any("PADDING_NOT_ZERO" in f or "NaN" in f or "Inf" in f for f in flags):
        status = "ERROR"
    elif any("TAIL_GT20" in f for f in flags):
        status = "WARNING"
    elif any("TAIL_GT10" in f for f in flags):
        status = "WARNING"
    elif any("REGIME_SHIFT" in f for f in flags):
        status = "WARNING"

    return {
        "status": status,
        "flags": sorted(set(flags)),
        "by_split": by_split,
        "padding_check": {
            "allowed_deviation": ALLOWED_PADDING_DEVIATION,
            "comment": "Padding (mask=False) must be exactly 0.0",
        },
        "thresholds": {
            "abs_gt10_warn_if_fraction": 0.01,
            "abs_gt20_warn_if_any": True,
            "regime_shift_p95_delta": 3.0,
            "comment": "Pre-training guard: if tails are long, consider RobustScaler or clipping [-8,8] before any holdout viewing.",
        },
    }


def compute_profile_coverage(tokens: np.ndarray, mask: np.ndarray, profile: dict,
                             selection_meta: dict | None = None) -> dict:
    counts = mask.sum(axis=1).astype(np.int32) if mask.size > 0 else np.zeros(tokens.shape[0], dtype=np.int32)
    if len(counts) == 0:
        counts = np.array([0], dtype=np.int32)
    pvals = np.percentile(counts, [5, 25, 50, 75, 95]) if len(counts) > 0 else [0] * 5
    raw_counts = None
    truncation_flags = None
    if selection_meta is not None:
        raw_counts = np.asarray(selection_meta.get("candidate_count_before_cap", []), dtype=np.int32)
        truncation_flags = np.asarray(selection_meta.get("is_truncated", []), dtype=bool)
    if raw_counts is None or raw_counts.size == 0:
        raw_counts = counts
    if truncation_flags is None or truncation_flags.size == 0:
        truncation_flags = raw_counts > int(profile.get("seq_len", 0))
    raw_pvals = np.percentile(raw_counts, [5, 25, 50, 75, 95]) if len(raw_counts) > 0 else [0] * 5
    truncation = float(np.mean(truncation_flags)) if len(truncation_flags) > 0 else 0.0
    price_bounds = {}
    token_fields = profile.get("token_fields", [])
    if "price_coord_atr" in token_fields and mask.sum() > 0:
        price_idx = token_fields.index("price_coord_atr")
        valid_prices = tokens[:, :, price_idx][mask]
        if len(valid_prices) > 0:
            # A7 corridor bounds check requires RAW price_coord_atr = (price-f0)/ATR.
            # relative_price profiles apply signed-log transform to tokens, so recover
            # raw bounds via the exact inverse for extrema: raw = sign(x)*expm1(abs(x)).
            if profile.get("relative_price", False):
                vp_min = float(np.min(valid_prices))
                vp_max = float(np.max(valid_prices))
                raw_min = float(np.sign(vp_min) * np.expm1(abs(vp_min)))
                raw_max = float(np.sign(vp_max) * np.expm1(abs(vp_max)))
            else:
                raw_min = float(np.min(valid_prices))
                raw_max = float(np.max(valid_prices))
            price_bounds = {
                "min_price_coord_atr": raw_min,
                "max_price_coord_atr": raw_max,
            }
    return {
        "valid_tokens_p5": float(pvals[0]),
        "valid_tokens_p25": float(pvals[1]),
        "valid_tokens_p50": float(pvals[2]),
        "valid_tokens_p75": float(pvals[3]),
        "valid_tokens_p95": float(pvals[4]),
        "candidate_count_before_cap_p5": float(raw_pvals[0]),
        "candidate_count_before_cap_p25": float(raw_pvals[1]),
        "candidate_count_before_cap_p50": float(raw_pvals[2]),
        "candidate_count_before_cap_p75": float(raw_pvals[3]),
        "candidate_count_before_cap_p95": float(raw_pvals[4]),
        "selected_count_after_cap_p5": float(pvals[0]),
        "selected_count_after_cap_p25": float(pvals[1]),
        "selected_count_after_cap_p50": float(pvals[2]),
        "selected_count_after_cap_p75": float(pvals[3]),
        "selected_count_after_cap_p95": float(pvals[4]),
        "pct_empty": float(np.mean(counts == 0)),
        "pct_single": float(np.mean(counts == 1)),
        "pct_two": float(np.mean(counts == 2)),
        "pct_three_plus": float(np.mean(counts >= 3)),
        "pct_truncation_true": truncation,
        "pct_candidate_count_ge_40": float(np.mean(raw_counts >= 40)),
        "pct_candidate_count_ge_90": float(np.mean(raw_counts >= 90)),
        "pct_candidate_count_eq_100": float(np.mean(raw_counts == 100)),
        "pct_selected_count_ge_90": float(np.mean(counts >= 90)),
        **price_bounds,
    }


def flatten_audit_to_rows(profile_name: str, profile: dict, split_name: str, audit_split: dict, coverage: dict) -> list[dict]:
    rows = []
    for feature_group_key, feature_group_name in [("token_features", "token"), ("row_features", "row")]:
        for feature_name, stats in audit_split.get(feature_group_key, {}).items():
            if stats.get("n", 0) == 0:
                continue
            flags = []
            if stats.get("frac_abs_gt10", 0) > 0.01:
                flags.append("TAIL_GT10")
            if stats.get("frac_abs_gt20", 0) > 0.0:
                flags.append("TAIL_GT20")
            if stats.get("has_nan"):
                flags.append("NAN")
            if stats.get("has_inf"):
                flags.append("INF")
            rows.append({
                "profile": profile_name,
                "split": split_name,
                "feature_group": feature_group_name,
                "feature_name": feature_name,
                "token_position": "",
                "n_valid": stats.get("n"),
                "missing_pct": stats.get("missing_pct"),
                "zero_pct": stats.get("zero_pct"),
                "mean": stats.get("mean"),
                "std": stats.get("std"),
                "min": stats.get("p0"),
                "p1": stats.get("p1"),
                "p5": stats.get("p5"),
                "p25": stats.get("p25"),
                "p50": stats.get("p50"),
                "p75": stats.get("p75"),
                "p95": stats.get("p95"),
                "p99": stats.get("p99"),
                "max": stats.get("p100"),
                "frac_abs_gt3": stats.get("frac_abs_gt3"),
                "frac_abs_gt5": stats.get("frac_abs_gt5"),
                "frac_abs_gt10": stats.get("frac_abs_gt10"),
                "frac_abs_gt20": stats.get("frac_abs_gt20"),
                "nan_count": stats.get("n_nan"),
                "inf_count": stats.get("n_inf"),
                "status": "ERROR" if ("NAN" in flags or "INF" in flags) else ("WARNING" if flags else "OK"),
                "flags": ";".join(flags),
            })
    for key, value in coverage.items():
        rows.append({
            "profile": profile_name,
            "split": split_name,
            "feature_group": "coverage",
            "feature_name": key,
            "token_position": "",
            "n_valid": None,
            "missing_pct": None,
            "zero_pct": None,
            "mean": value,
            "std": None,
            "min": None,
            "p1": None,
            "p5": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p95": None,
            "p99": None,
            "max": None,
            "frac_abs_gt3": None,
            "frac_abs_gt5": None,
            "frac_abs_gt10": None,
            "frac_abs_gt20": None,
            "nan_count": None,
            "inf_count": None,
            "status": "OK",
            "flags": "",
        })
    return rows


# ===========================================================================
# OHLC label verification
# ===========================================================================

def _parse_breach_target(target_col: str) -> dict:
    parts = target_col.split("_")
    if len(parts) < 5 or parts[1:3] != ["stop", "broken"] or not target_col.endswith("_flag"):
        raise ValueError(f"Unsupported breach target: {target_col}")
    side = parts[0]
    horizon = int(parts[3][1:])
    offset = int(parts[4][3:]) / 10.0
    if side not in {"buy", "sell"}:
        raise ValueError(f"Unsupported breach side: {side}")
    return {"side": side, "horizon": horizon, "offset": offset}


def verify_breach_labels_against_ohlc(holdout_df: pd.DataFrame, ohlc_path: str = None,
                                       n_sample: int = 50, random_seed: int = 123,
                                       target_col: str = TARGET_COLUMN) -> dict:
    """Verify a stop-breach target against OHLC for random holdout rows.

    Fixed seed for reproducibility. Checks:
      - Core: does stored label match OHLC-computed breach over next H bars?
      - Boundary: max High in window within 0.1*ATR of stop — near-miss check.
    """
    if ohlc_path is None:
        ohlc_path = str(OHLC_FILE)

    from datetime import datetime, timezone

    ohlc_df = pd.read_csv(ohlc_path, sep=CSV_SEP)
    ohlc_df["_dt"] = pd.to_datetime(ohlc_df["time"], format="%Y.%m.%d %H:%M",
                                     errors="coerce", utc=True)
    ohlc_df = ohlc_df.dropna(subset=["_dt"]).sort_values("_dt").reset_index(drop=True)
    time_to_idx = {dt: i for i, dt in enumerate(ohlc_df["_dt"])}
    n_ohlc = len(ohlc_df)
    spec = _parse_breach_target(target_col)
    expected_fractal_dir = -1 if spec["side"] == "buy" else 1
    expected_signal = 1 if spec["side"] == "buy" else -1
    horizon = spec["horizon"]
    offset = spec["offset"]

    target_rows = holdout_df[pd.to_numeric(holdout_df[target_col], errors="coerce").notna()]
    signal_rows = target_rows[target_rows["signal"].astype(int) == expected_signal]
    if len(signal_rows) > 0:
        target_rows = signal_rows
    n_sample = min(n_sample, len(target_rows))
    rng = np.random.RandomState(random_seed)
    sample_indices = rng.choice(len(target_rows), size=n_sample, replace=False)
    sample = target_rows.iloc[sample_indices]

    mismatches = []
    near_misses = []
    matches = 0
    skipped = 0
    mismatch_examples = []
    near_miss_examples = []
    fractal_dir_counts = {1: 0, -1: 0, 0: 0}

    for orig_idx, row in sample.iterrows():
        try:
            row_dt = datetime.strptime(str(row["time"]), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except (ValueError, KeyError):
            skipped += 1
            continue

        idx0 = time_to_idx.get(row_dt)
        if idx0 is None or idx0 + horizon >= n_ohlc:
            skipped += 1
            continue

        try:
            f0 = str(row["fractal0"])
            parts = f0.split(FRACTAL_SEP)
            fractal_price = float(parts[1])
            fractal_dir = int(parts[2])
        except (ValueError, IndexError, KeyError):
            skipped += 1
            continue

        atr = float(row.get("ATR", 0))
        if atr <= 0 or fractal_dir == 0:
            skipped += 1
            continue

        fractal_dir_counts[fractal_dir] = fractal_dir_counts.get(fractal_dir, 0) + 1

        stop_offset = offset * atr
        if fractal_dir == 1:  # SELL: стоп выше пика
            stop_price = fractal_price + stop_offset
            highs = [ohlc_df.iloc[k]["high"] for k in range(idx0 + 1, min(idx0 + 1 + horizon, n_ohlc))]
            breached = any(h >= stop_price for h in highs)
            max_high = max(highs)
            near_boundary = abs(max_high - stop_price) < 0.1 * atr and not breached
        elif fractal_dir == -1:  # BUY: стоп ниже впадины
            stop_price = fractal_price - stop_offset
            lows = [ohlc_df.iloc[k]["low"] for k in range(idx0 + 1, min(idx0 + 1 + horizon, n_ohlc))]
            breached = any(l <= stop_price for l in lows)
            min_low = min(lows)
            near_boundary = abs(min_low - stop_price) < 0.1 * atr and not breached
        else:
            skipped += 1
            continue

        stored = row.get(target_col)
        stored_val = int(stored) if not pd.isna(stored) else None
        computed_val = 1 if breached else 0

        info = {
            "df_row": int(orig_idx) if not isinstance(orig_idx, np.integer) else int(orig_idx),
            "time": str(row.get("time", "")),
            "fractal_price": round(fractal_price, 2),
            "atr": round(atr, 4),
            "stop_offset": round(stop_offset, 2),
            "stop_price": round(stop_price, 2),
            "stored_label": stored_val,
            "computed_label": computed_val,
            "n_future_bars": min(horizon, n_ohlc - idx0 - 1),
        }

        if stored_val == computed_val:
            matches += 1
            if near_boundary:
                near_misses.append(info)
                if len(near_miss_examples) < 5:
                    near_miss_examples.append(info)
        else:
            mismatches.append(info)
            if len(mismatch_examples) < 10:
                mismatch_examples.append(info)

    return {
        "random_seed": random_seed,
        "target": target_col,
        "n_sampled": n_sample,
        "n_checked": matches + len(mismatches),
        "n_skipped": skipped,
        "n_matches": matches,
        "n_mismatches": len(mismatches),
        "n_near_boundary": len(near_misses),
        "mismatch_examples": mismatch_examples,
        "near_miss_examples": near_miss_examples,
        "fractal_dir_counts": fractal_dir_counts,
        "fractal_dir_ok": fractal_dir_counts.get(expected_fractal_dir, 0) > 0 and fractal_dir_counts.get(0, 0) == 0,
        "status": "PASS" if len(mismatches) == 0 and matches >= 10 else (
            "MISMATCH" if len(mismatches) > 0 else "LOW_VALID_COUNT"
        ),
        "verdict": (
            "Labels confirmed — 0 mismatches, sufficient for Stage 5.0"
            if len(mismatches) == 0 and matches >= 10
            else f"{len(mismatches)} mismatches found — investigation required before training"
        ),
    }


def compute_corridor_stats(df: pd.DataFrame, profile: dict) -> dict:
    """Compute corridor population statistics."""
    corridor_atr = profile.get("corridor_atr", 10.0)
    n_rows = len(df)
    counts = []

    for i in range(min(n_rows, 5000)):
        atr_val = pd.to_numeric(df["ATR"].iloc[i], errors="coerce")
        atr_val = float(atr_val) if float(atr_val) > 0 else 1.0
        threshold = corridor_atr * atr_val
        try:
            f0_str = str(df["fractal0"].iloc[i])
            f0_price = float(f0_str.split(FRACTAL_SEP)[1])
        except (ValueError, IndexError):
            f0_price = 0.0

        cnt = 0
        for j in range(N_FRACTALS):
            col = f"fractal{j}"
            if col not in df.columns:
                break
            fstr = str(df[col].iloc[i])
            if not fstr or fstr == "nan":
                continue
            try:
                price = float(fstr.split(FRACTAL_SEP)[1])
            except (ValueError, IndexError):
                continue
            if abs(price - f0_price) <= threshold:
                cnt += 1
        counts.append(cnt)

    counts = np.array(counts, dtype=np.float64)
    pcts = np.percentile(counts, [5, 25, 50, 75, 80, 95]) if len(counts) > 0 else [0] * 6

    return {
        "profile": profile["name"],
        "n_rows_sampled": int(min(n_rows, 5000)),
        "n_fractals_p5": float(pcts[0]),
        "n_fractals_p25": float(pcts[1]),
        "n_fractals_median": float(pcts[2]),
        "n_fractals_p75": float(pcts[3]),
        "n_fractals_p80": float(pcts[4]),
        "n_fractals_p95": float(pcts[5]),
        "pct_empty": float(np.mean(np.array(counts) == 0)) if len(counts) > 0 else 1.0,
        "pct_single": float(np.mean(np.array(counts) == 1)) if len(counts) > 0 else 0.0,
        "pct_two": float(np.mean(np.array(counts) == 2)) if len(counts) > 0 else 0.0,
        "pct_three_plus": float(np.mean(np.array(counts) >= 3)) if len(counts) > 0 else 0.0,
    }


def corridor_status(stats: dict) -> str:
    if stats["pct_empty"] > CORRIDOR_REJECTED_PCT_EMPTY or stats["n_fractals_median"] < CORRIDOR_REJECTED_MEDIAN:
        return "REJECTED"
    if stats["pct_empty"] > CORRIDOR_LOW_COVERAGE_PCT_EMPTY or stats["n_fractals_median"] < CORRIDOR_LOW_COVERAGE_MEDIAN:
        return "LOW_COVERAGE"
    return "OK"


# ===========================================================================
# Data loading
# ===========================================================================

def load_splits(target_col: str = TARGET_COLUMN):
    """Load XAUUSD labeled CSVs and split by year."""
    train_raw = pd.read_csv(TRAIN_FILE, sep=CSV_SEP)
    val_raw = pd.read_csv(VAL_FILE, sep=CSV_SEP)
    test_raw = pd.read_csv(TEST_FILE, sep=CSV_SEP)

    for df in [train_raw, val_raw, test_raw]:
        df["_year"] = pd.to_datetime(
            df["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year

    train_rows = []
    val_stop_rows = []
    holdout_rows = []

    for _, row in train_raw.iterrows():
        y = row["_year"]
        if pd.isna(y):
            continue
        y = int(y)
        if y <= TRAIN_MAX_YEAR:
            train_rows.append(row)
        elif y in VAL_STOP_YEARS:
            val_stop_rows.append(row)

    for _, row in val_raw.iterrows():
        y = row["_year"]
        if pd.isna(y):
            continue
        y = int(y)
        if y <= TRAIN_MAX_YEAR:
            train_rows.append(row)
        elif y in VAL_STOP_YEARS:
            val_stop_rows.append(row)

    for _, row in test_raw.iterrows():
        y = row["_year"]
        if pd.isna(y):
            continue
        y = int(y)
        if y >= HOLDOUT_MIN_YEAR:
            holdout_rows.append(row)
        elif y in VAL_STOP_YEARS:
            val_stop_rows.append(row)

    train_df = pd.DataFrame(train_rows).reset_index(drop=True)
    val_stop_df = pd.DataFrame(val_stop_rows).reset_index(drop=True)
    holdout_df = pd.DataFrame(holdout_rows).reset_index(drop=True)

    for name, df in [("train", train_df), ("val_stop", val_stop_df), ("holdout", holdout_df)]:
        mask = df[target_col].notna()
        before = len(df)
        df = df.loc[mask].reset_index(drop=True)
        if name == "train":
            train_df = df
        elif name == "val_stop":
            val_stop_df = df
        else:
            holdout_df = df
        print(f"  {name}: {before} → {len(df)} rows (non-null {target_col})")

    print(f"  Train years: {sorted(train_df['_year'].unique())}")
    print(f"  Val_stop years: {sorted(val_stop_df['_year'].unique())}")
    print(f"  Holdout years: {sorted(holdout_df['_year'].unique())}")

    return train_df, val_stop_df, holdout_df


# ===========================================================================
# Flat features for XGBoost baselines
# ===========================================================================

def build_flat_features(df: pd.DataFrame, profile: dict,
                        transform_variant: str = "current",
                        transform_params: dict | None = None) -> np.ndarray:
    """Build flat feature table for XGBoost from profile tokens+row_features."""
    tokens, row_feat, mask, _selection_meta = build_profile_features(
        df, profile, transform_variant=transform_variant, transform_params=transform_params)
    n_samples = len(df)
    flat = tokens.reshape(n_samples, -1)
    result = np.concatenate([flat, row_feat], axis=1)
    return result.astype(np.float32)


def build_xgb_features(df: pd.DataFrame, feature_type: str) -> np.ndarray:
    """Build XGBoost features: base_raw_plus_time, no_time, or time_only."""
    base_profile = find_profile("all100_base10_time")
    no_time_profile = find_profile("all100_base10_no_time")

    if feature_type == "base_raw_plus_time":
        return build_flat_features(df, base_profile)
    elif feature_type == "no_time":
        return build_flat_features(df, no_time_profile)
    elif feature_type == "time_only":
        # Only row-level time features (no fractal tokens)
        row_feat = build_row_features(df, base_profile)
        return row_feat.astype(np.float32)
    else:
        raise ValueError(f"Unknown feature_type: {feature_type}")


def build_xgb_features_for_profile(df: pd.DataFrame, profile_name: str,
                                   transform_variant: str = "current",
                                   transform_params: dict | None = None) -> np.ndarray:
    """Build flat XGBoost features for a named profile with a given transform variant.

    If transform_params is None, fits params on the provided df (caller must pass
    train_df for train-only fit). If transform_params is provided, uses them directly
    without re-fitting — this avoids leakage when params were fit on train only.
    """
    profile = find_profile(profile_name)
    if transform_params is None:
        parsed = parse_split_fractals(df)
        transform_params = fit_transform_params_for_profile(
            df, parsed, profile, transform_variant)
    return build_flat_features(
        df, profile, transform_variant=transform_variant, transform_params=transform_params)


def _stage5_0f_structure_profile() -> dict:
    """Profile with structural fractal fields + clock fields, without price and ATR."""
    return {
        "name": "stage5_0f_structure_only",
        "selection": "all100",
        "order": "freshness",
        "token_fields": NO_PRICE_TOKEN_FIELDS.copy(),
        "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 100,
        "token_dim": len(NO_PRICE_TOKEN_FIELDS),
        "row_dim": len(TIME_ONLY_ROW_FIELDS),
    }


def _stage5_0f_profile_for_key(profile_key: str) -> dict:
    if profile_key == "base_raw_plus_time":
        return find_profile("all100_base10_time")
    if profile_key == "structure_only":
        return _stage5_0f_structure_profile()
    if profile_key == "all100_relative_price_time":
        return find_profile("all100_relative_price_time")
    if profile_key == "time_only":
        return find_profile("time_only_clean")
    raise ValueError(f"Unknown Stage 5.0f profile_key: {profile_key}")


def fit_stage5_0f_transform_params(df: pd.DataFrame, profile_key: str,
                                   transform_variant: str = "asinh",
                                   parsed_cache: dict | None = None,
                                   cache_key: tuple | None = None) -> dict | None:
    """Fit Stage 5.0f transform params on train-core only."""
    if profile_key == "time_only":
        return None
    profile = _stage5_0f_profile_for_key(profile_key)
    if parsed_cache is not None and cache_key is not None:
        if cache_key not in parsed_cache:
            parsed_cache[cache_key] = parse_split_fractals(df)
        parsed = parsed_cache[cache_key]
    else:
        parsed = parse_split_fractals(df)
    return fit_transform_params_for_profile(df, parsed, profile, transform_variant)


def build_stage5_0f_features(df: pd.DataFrame, profile_key: str,
                             transform_variant: str = "asinh",
                             transform_params: dict | None = None) -> np.ndarray:
    """Build XGBoost feature matrix for a Stage 5.0f profile."""
    if profile_key == "time_only":
        profile = _stage5_0f_profile_for_key("time_only")
        return build_row_features(df, profile).astype(np.float32)

    profile = _stage5_0f_profile_for_key(profile_key)
    if transform_params is None:
        transform_params = fit_stage5_0f_transform_params(
            df, profile_key, transform_variant=transform_variant)
    return build_flat_features(
        df, profile, transform_variant=transform_variant, transform_params=transform_params)


def _stage5_1_profile_for_key(profile_key: str) -> dict:
    """Build Stage 5.1 feature profile for time-only, full, drop-one, or add-one."""
    if profile_key == "time_only":
        return {
            "name": "stage5_1_time_only",
            "selection": "all100",
            "order": "freshness",
            "token_fields": [],
            "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
            "uses_time": True,
            "seq_len": 0,
            "token_dim": 0,
            "row_dim": len(TIME_ONLY_ROW_FIELDS),
        }

    if profile_key == "structure_full":
        token_fields = STAGE5_1_FIELDS.copy()
    elif profile_key.startswith("drop_"):
        field = profile_key.removeprefix("drop_")
        if field not in STAGE5_1_FIELDS:
            raise ValueError(f"Unknown Stage 5.1 drop field: {field}")
        token_fields = [name for name in STAGE5_1_FIELDS if name != field]
    elif profile_key.startswith("add_"):
        field = profile_key.removeprefix("add_")
        if field not in STAGE5_1_FIELDS:
            raise ValueError(f"Unknown Stage 5.1 add field: {field}")
        token_fields = [field]
    else:
        raise ValueError(f"Unknown Stage 5.1 profile_key: {profile_key}")

    return {
        "name": f"stage5_1_{profile_key}",
        "selection": "all100",
        "order": "freshness",
        "token_fields": token_fields,
        "row_fields": TIME_ONLY_ROW_FIELDS.copy(),
        "uses_time": True,
        "seq_len": 100,
        "token_dim": len(token_fields),
        "row_dim": len(TIME_ONLY_ROW_FIELDS),
    }


def fit_stage5_1_transform_params(df: pd.DataFrame, profile_key: str,
                                  transform_variant: str = "asinh") -> dict:
    """Stage 5.1 has no price/ATR fields, so transform params are intentionally empty."""
    _ = df
    _ = transform_variant
    _stage5_1_profile_for_key(profile_key)
    return {}


def build_stage5_1_features(df: pd.DataFrame, profile_key: str,
                            transform_variant: str = "asinh",
                            transform_params: dict | None = None) -> np.ndarray:
    """Build XGBoost feature matrix for Stage 5.1 without leaking price/ATR fields."""
    profile = _stage5_1_profile_for_key(profile_key)
    if profile_key == "time_only":
        return build_row_features(
            df, profile, transform_variant=transform_variant,
            transform_params=transform_params).astype(np.float32)

    params = {} if transform_params is None else transform_params
    return build_flat_features(
        df, profile, transform_variant=transform_variant, transform_params=params)


# ===========================================================================
# Label sanity check (not full OHLC verification — see plan for manual step)
# ===========================================================================

def label_sanity_check(holdout_df: pd.DataFrame, target_col: str = TARGET_COLUMN) -> dict:
    """Sanity-check breach labels: random sample with basic stats."""
    n_sample = min(20, len(holdout_df))
    sample = holdout_df.sample(n=n_sample, random_state=42)
    verifications = []
    for idx, row in sample.iterrows():
        label = row[target_col]
        signal_val = row["signal"]
        atr_val = row["ATR"]
        try:
            f0 = str(row["fractal0"])
            price = float(f0.split(FRACTAL_SEP)[1]) if f0 != "nan" else 0.0
        except (ValueError, IndexError):
            price = 0.0
        verifications.append({
            "row": int(idx),
            "time": str(row.get("time", "")),
            "signal": int(signal_val),
            "price": float(price),
            "atr": float(atr_val),
            "label": int(label) if not pd.isna(label) else None,
        })

    pos_count = int(holdout_df[target_col].sum())
    total = len(holdout_df)

    return {
        "target": target_col,
        "total_rows": total,
        "positive_labels": pos_count,
        "positive_rate": float(pos_count / total) if total > 0 else 0.0,
        "sample_verifications": verifications,
        "note": "Random sample sanity-check only. Full OHLC label-parity verification is a manual step per plan.",
        "status": "SANITY_ONLY" if 0.30 < float(pos_count / max(total, 1)) < 0.50 else "CHECK",
    }


# ===========================================================================
# XGBoost baseline
# ===========================================================================

def train_xgb_baseline(X_train, y_train, X_val, y_val, seed=42):
    """Train XGBoost classifier with early stopping."""
    pos_weight = float((len(y_train) - y_train.sum()) / max(y_train.sum(), 1))

    dtrain = xgb.DMatrix(X_train, label=y_train.values)
    dval = xgb.DMatrix(X_val, label=y_val.values)

    params = {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "scale_pos_weight": pos_weight,
        "seed": seed,
        "n_jobs": 1,
        "verbosity": 0,
    }

    evals = [(dtrain, "train"), (dval, "val")]
    model = xgb.train(
        params, dtrain, num_boost_round=500,
        evals=evals, early_stopping_rounds=20,
        verbose_eval=False,
    )

    preds = model.predict(dval)
    val_auc = roc_auc_score(y_val, preds)

    return model, val_auc


# ===========================================================================
# Metrics
# ===========================================================================

def _safe(val):
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, float) and not np.isfinite(val):
        return None
    return val


def _write_json_atomic(path: Path, payload: dict) -> None:
    """Write JSON atomically to avoid partial reads during long-running updates."""
    path = Path(path)
    tmp_path = path.with_name(f"{path.name}.tmp")
    with open(tmp_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    os.replace(tmp_path, path)


def compute_metrics(y_true, y_pred_proba):
    n = len(y_true)
    if n == 0 or y_true.nunique() < 2:
        return {"auc": None, "pr_auc": None, "n": n, "lift_10": None, "lift_20": None, "lift_30": None}

    yt = y_true.values.astype(int)
    yp = y_pred_proba

    try:
        auc = float(roc_auc_score(yt, yp))
    except ValueError:
        auc = None
    try:
        pr_auc = float(average_precision_score(yt, yp))
    except ValueError:
        pr_auc = None

    sorted_idx = np.argsort(yp)  # ascending
    baseline_rate = float(np.mean(yt))

    lifts = {}
    for pct in [10, 20, 30]:
        k = max(1, int(n * pct / 100))
        bottom_rate = float(np.mean(yt[sorted_idx[:k]]))
        lifts[f"lift_{pct}"] = float(bottom_rate / max(baseline_rate, 0.001))

    return {"auc": auc, "pr_auc": pr_auc, "n": n, **lifts}


def compute_yearly_metrics(df, y_pred_proba, target_col: str = TARGET_COLUMN):
    years = sorted(df["_year"].unique())
    yearly = {}
    for yr in years:
        mask = df["_year"] == yr
        y_true = df.loc[mask, target_col]
        y_pred = y_pred_proba[mask.values]
        m = compute_metrics(y_true, pd.Series(y_pred))
        yearly[str(yr)] = {k: _safe(v) for k, v in m.items()}
    return yearly


def bootstrap_stage5_0f_metric_ci(y_true: pd.Series, y_pred: np.ndarray,
                                  metric_name: str, n_boot: int = STAGE5_0F_BOOTSTRAP_N,
                                  seed: int = 42) -> dict:
    """Bootstrap 95% CI for AUC or lift_30 by resampling test rows."""
    yt = pd.Series(y_true).reset_index(drop=True)
    yp = np.asarray(y_pred, dtype=float)
    n = len(yt)
    if n == 0 or yt.nunique() < 2:
        return {"metric": metric_name, "n_boot": int(n_boot), "low": None, "median": None, "high": None}

    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        sample_y = yt.iloc[idx].reset_index(drop=True)
        if sample_y.nunique() < 2:
            continue
        sample_p = yp[idx]
        metrics = compute_metrics(sample_y, pd.Series(sample_p))
        value = metrics.get(metric_name)
        if value is not None and np.isfinite(value):
            vals.append(float(value))

    if not vals:
        return {"metric": metric_name, "n_boot": int(n_boot), "low": None, "median": None, "high": None}

    arr = np.asarray(vals, dtype=float)
    return {
        "metric": metric_name,
        "n_boot": int(n_boot),
        "low": float(np.percentile(arr, 2.5)),
        "median": float(np.percentile(arr, 50.0)),
        "high": float(np.percentile(arr, 97.5)),
    }


# ===========================================================================
# Transformer training
# ===========================================================================

def set_seed(seed):
    torch.manual_seed(seed)
    np.random.seed(seed)


def train_transformer(tokens, row_feat, mask, y, tokens_val, row_feat_val, mask_val, y_val,
                      profile, seed, device, model_config: dict | None = None):
    """Train Transformer with early stopping on val_stop."""
    set_seed(seed)
    cfg = model_config or {
        "d_model": D_MODEL,
        "nhead": NHEAD,
        "num_layers": NUM_LAYERS,
        "dim_feedforward": DIM_FEEDFORWARD,
        "dropout": DROPOUT,
        "weight_decay": WEIGHT_DECAY,
        "learning_rate": LEARNING_RATE,
        "patience": EARLY_STOPPING_PATIENCE,
    }

    token_dim = tokens.shape[-1]
    row_dim = row_feat.shape[-1]
    seq_len = tokens.shape[1]

    model = FractalBreachTransformer(
        token_dim=token_dim,
        row_dim=row_dim,
        d_model=cfg["d_model"],
        nhead=cfg["nhead"],
        num_layers=cfg["num_layers"],
        dim_feedforward=cfg["dim_feedforward"],
        dropout=cfg["dropout"],
        max_seq_len=128,
    ).to(device)

    ds_train = TensorDataset(
        torch.from_numpy(tokens).float(),
        torch.from_numpy(row_feat).float(),
        torch.from_numpy(mask).bool(),
        torch.from_numpy(y.values.astype(np.float32)).float().unsqueeze(1),
    )
    ds_val = TensorDataset(
        torch.from_numpy(tokens_val).float(),
        torch.from_numpy(row_feat_val).float(),
        torch.from_numpy(mask_val).bool(),
        torch.from_numpy(y_val.values.astype(np.float32)).float().unsqueeze(1),
    )

    dl_train = DataLoader(ds_train, batch_size=min(BATCH_SIZE, len(ds_train)),
                          shuffle=True, drop_last=False)
    dl_val = DataLoader(ds_val, batch_size=min(BATCH_SIZE, len(ds_val)),
                        shuffle=False, drop_last=False)

    pos_count = float(y.sum())
    neg_count = float(len(y) - pos_count)
    pos_weight = torch.tensor([neg_count / max(pos_count, 1)], device=device)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"],
                                  weight_decay=cfg["weight_decay"])

    best_val_auc = 0.0
    best_state = None
    patience_left = cfg["patience"]
    train_losses = []
    val_aucs = []

    for epoch in range(MAX_EPOCHS):
        model.train()
        total_loss = 0.0
        for t, r, m, yb in dl_train:
            t, r, m, yb = t.to(device), r.to(device), m.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(t, r, m).reshape(yb.shape)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / max(len(dl_train), 1)
        train_losses.append(avg_loss)

        model.eval()
        all_probs = []
        all_ys = []
        with torch.no_grad():
            for t, r, m, yb in dl_val:
                t, r, m, yb = t.to(device), r.to(device), m.to(device), yb.to(device)
                logits = model(t, r, m).reshape(yb.shape)
                probs = torch.sigmoid(logits).cpu().numpy().ravel()
                all_probs.append(probs)
                all_ys.append(yb.cpu().numpy().ravel())

        val_probs = np.concatenate(all_probs)
        val_ys = np.concatenate(all_ys)
        if np.unique(val_ys).size < 2:
            val_auc = 0.5
        else:
            val_auc = float(roc_auc_score(val_ys, val_probs))
        val_aucs.append(val_auc)

        if val_auc > best_val_auc:
            best_val_auc = val_auc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_left = cfg["patience"]
        else:
            patience_left -= 1

        if patience_left <= 0:
            break

    if best_state is not None:
        model.load_state_dict(best_state)
    best_epoch = int(np.argmax(val_aucs) + 1) if val_aucs else 0
    last_val_auc = float(val_aucs[-1]) if val_aucs else 0.0
    best_val_auc = float(max(val_aucs)) if val_aucs else 0.0

    return model, {
        "best_val_auc": best_val_auc,
        "num_epochs": epoch + 1 - patience_left,
        "train_losses": [float(x) for x in train_losses],
        "val_aucs": [float(x) for x in val_aucs],
        "best_epoch": best_epoch,
        "last_val_auc": last_val_auc,
        "overfit_drop_after_best": float(best_val_auc - last_val_auc),
        "model_config": deepcopy(cfg),
    }


def evaluate_transformer(model, tokens, row_feat, mask, y, device):
    """Evaluate Transformer on a dataset."""
    model.eval()
    ds = TensorDataset(
        torch.from_numpy(tokens).float(),
        torch.from_numpy(row_feat).float(),
        torch.from_numpy(mask).bool(),
        torch.from_numpy(y.values.astype(np.float32)).float().unsqueeze(1),
    )
    dl = DataLoader(ds, batch_size=min(BATCH_SIZE, len(ds)), shuffle=False)
    all_probs = []
    with torch.no_grad():
        for t, r, m, _ in dl:
            t, r, m = t.to(device), r.to(device), m.to(device)
            logits = model(t, r, m).reshape(len(t), -1)
            probs = torch.sigmoid(logits).cpu().numpy().ravel()
            all_probs.append(probs)
    return np.concatenate(all_probs)


# ===========================================================================
# Main orchestrator
# ===========================================================================

def compute_xgb_baselines(train_df, val_stop_df, holdout_df, target_col: str = TARGET_COLUMN):
    """Compute all XGBoost baselines on same split."""
    y_train = train_df[target_col]
    y_val = val_stop_df[target_col]
    y_holdout = holdout_df[target_col]

    results = {}
    for ft in ["base_raw_plus_time", "no_time", "time_only"]:
        print(f"\n  Training XGBoost {ft}...")
        X_train = build_xgb_features(train_df, ft)
        X_val = build_xgb_features(val_stop_df, ft)
        X_holdout = build_xgb_features(holdout_df, ft)

        model, val_auc = train_xgb_baseline(X_train, y_train, X_val, y_val, seed=42)

        dhold = xgb.DMatrix(X_holdout)
        holdout_probs = model.predict(dhold)

        val_metrics = compute_metrics(y_val, pd.Series(model.predict(xgb.DMatrix(X_val))))
        holdout_metrics = compute_metrics(y_holdout, pd.Series(holdout_probs))
        yearly = compute_yearly_metrics(holdout_df, holdout_probs, target_col=target_col)

        results[ft] = {
            "val_auc": float(val_auc),
            "val": {k: _safe(v) for k, v in val_metrics.items()},
            "holdout": {k: _safe(v) for k, v in holdout_metrics.items()},
            "yearly": {k: {kk: _safe(vv) for kk, vv in v.items()} for k, v in yearly.items()},
        }
        print(f"    Val AUC: {val_auc:.4f}, Holdout AUC: {holdout_metrics.get('auc', 'N/A')}")

    return results


def compute_xgb_same_profile_baseline(train_df, val_stop_df, holdout_df,
                                      profile_name: str,
                                      transform_variant: str = "asinh",
                                      target_col: str = TARGET_COLUMN,
                                      seed: int = 42) -> dict:
    """Train XGBoost on the same profile features as the Transformer.

    This isolates 'features vs model': if XGBoost on the same flattened
    profile beats the Transformer, the issue is the model, not the features.

    Transform params are fit on train only and reused for val and holdout
    to avoid leakage from val/holdout into transform fitting.
    """
    print(f"\n  Training XGBoost same-profile: {profile_name} ({transform_variant})...")

    profile = find_profile(profile_name)
    parsed_train = parse_split_fractals(train_df)
    transform_params = fit_transform_params_for_profile(
        train_df, parsed_train, profile, transform_variant)

    X_train = build_xgb_features_for_profile(
        train_df, profile_name, transform_variant, transform_params=transform_params)
    X_val = build_xgb_features_for_profile(
        val_stop_df, profile_name, transform_variant, transform_params=transform_params)
    X_holdout = build_xgb_features_for_profile(
        holdout_df, profile_name, transform_variant, transform_params=transform_params)

    y_train = train_df[target_col]
    y_val = val_stop_df[target_col]
    y_holdout = holdout_df[target_col]

    model, val_auc = train_xgb_baseline(X_train, y_train, X_val, y_val, seed=seed)

    import xgboost as xgb
    val_probs = model.predict(xgb.DMatrix(X_val))
    holdout_probs = model.predict(xgb.DMatrix(X_holdout))

    val_metrics = compute_metrics(y_val, pd.Series(val_probs))
    holdout_metrics = compute_metrics(y_holdout, pd.Series(holdout_probs))
    yearly = compute_yearly_metrics(holdout_df, holdout_probs, target_col=target_col)

    print(f"    Val AUC: {val_auc:.4f}, Holdout AUC: {holdout_metrics.get('auc', 'N/A')}")

    return {
        "profile": profile_name,
        "transform_variant": transform_variant,
        "transform_params_fit_on": "train",
        "seed": seed,
        "val": {k: _safe(v) for k, v in val_metrics.items()},
        "holdout": {k: _safe(v) for k, v in holdout_metrics.items()},
        "yearly": {k: {kk: _safe(vv) for kk, vv in v.items()} for k, v in yearly.items()},
    }


def compute_logistic_same_profile_baseline(train_df, val_stop_df, holdout_df,
                                           profile_name: str,
                                           transform_variant: str = "current",
                                           target_col: str = TARGET_COLUMN,
                                           seed: int = 42) -> dict:
    """Train Logistic Regression on the same profile features as XGBoost.

    Linear baseline: if Logistic ≈ XGBoost, the signal is linear and
    Transformer is overkill. If XGBoost >> Logistic, the signal is in
    feature interactions.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    print(f"\n  Training Logistic same-profile: {profile_name} ({transform_variant})...")

    profile = find_profile(profile_name)
    parsed_train = parse_split_fractals(train_df)
    transform_params = fit_transform_params_for_profile(
        train_df, parsed_train, profile, transform_variant)

    X_train = build_xgb_features_for_profile(
        train_df, profile_name, transform_variant, transform_params=transform_params)
    X_val = build_xgb_features_for_profile(
        val_stop_df, profile_name, transform_variant, transform_params=transform_params)
    X_holdout = build_xgb_features_for_profile(
        holdout_df, profile_name, transform_variant, transform_params=transform_params)

    y_train = train_df[target_col]
    y_val = val_stop_df[target_col]
    y_holdout = holdout_df[target_col]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_holdout_s = scaler.transform(X_holdout)

    model = LogisticRegression(
        C=1.0, max_iter=1000, random_state=seed, solver="lbfgs",
        class_weight="balanced")
    model.fit(X_train_s, y_train)

    val_probs = model.predict_proba(X_val_s)[:, 1]
    holdout_probs = model.predict_proba(X_holdout_s)[:, 1]

    val_metrics = compute_metrics(y_val, pd.Series(val_probs))
    holdout_metrics = compute_metrics(y_holdout, pd.Series(holdout_probs))
    yearly = compute_yearly_metrics(holdout_df, holdout_probs, target_col=target_col)

    print(f"    Val AUC: {val_metrics.get('auc', 'N/A'):.4f}")

    return {
        "profile": profile_name,
        "model_type": "logistic_regression",
        "transform_variant": transform_variant,
        "transform_params_fit_on": "train",
        "seed": seed,
        "val": {k: _safe(v) for k, v in val_metrics.items()},
        "holdout": {k: _safe(v) for k, v in holdout_metrics.items()},
        "yearly": {k: {kk: _safe(vv) for kk, vv in v.items()} for k, v in yearly.items()},
    }


def _build_feature_group_masks(profile: dict) -> dict:
    """Build column masks for feature group ablation.

    Masks are built from profile["token_fields"] and profile["row_fields"]
    by name, not by positional assumption. Flattened layout:
    [token_flat (seq_len * token_dim), row_flat (row_dim)].

    Groups: price (first price-like token field), structure (remaining token
    fields), ATR (row field named "ATR"), time (row fields hour_sin/cos/dow_sin/cos).
    """
    seq_len = profile["seq_len"]
    token_dim = profile["token_dim"]
    row_fields = profile.get("row_fields", [])
    token_fields = profile.get("token_fields", [])
    total = seq_len * token_dim + len(row_fields)

    token_total = seq_len * token_dim
    masks = {"all": np.ones(total, dtype=bool)}

    price_token_names = {"price_coord_atr", "price_atr_scaled", "price_coord_unit", "price"}
    price_token_indices = [i for i, f in enumerate(token_fields) if f in price_token_names]
    structure_token_indices = [i for i in range(token_dim) if i not in price_token_indices]

    masks["price"] = np.zeros(total, dtype=bool)
    for ti in price_token_indices:
        masks["price"][ti::token_dim] = True
    masks["structure"] = np.zeros(total, dtype=bool)
    for ti in structure_token_indices:
        masks["structure"][ti::token_dim] = True

    masks["atr"] = np.zeros(total, dtype=bool)
    masks["time"] = np.zeros(total, dtype=bool)
    for ri, rf in enumerate(row_fields):
        if rf == "ATR":
            masks["atr"][token_total + ri] = True
        elif rf in ("hour_sin", "hour_cos", "dow_sin", "dow_cos"):
            masks["time"][token_total + ri] = True

    return masks


def compute_feature_group_ablation(train_df, val_stop_df, holdout_df,
                                   profile_name: str,
                                   transform_variant: str = "asinh",
                                   target_col: str = TARGET_COLUMN,
                                   seed: int = 42) -> dict:
    """Ablate feature groups and measure AUC drop.

    Groups: price (token), structure (token), ATR (row), time (row).
    For each group, remove its columns from flattened features and retrain XGBoost.
    Holdout metrics use real model predictions, not zeros.
    """
    import xgboost as xgb

    print(f"\n  Feature group ablation: {profile_name}...")

    profile = find_profile(profile_name)
    parsed_train = parse_split_fractals(train_df)
    transform_params = fit_transform_params_for_profile(
        train_df, parsed_train, profile, transform_variant)

    X_train = build_xgb_features_for_profile(
        train_df, profile_name, transform_variant, transform_params=transform_params)
    X_val = build_xgb_features_for_profile(
        val_stop_df, profile_name, transform_variant, transform_params=transform_params)
    X_holdout = build_xgb_features_for_profile(
        holdout_df, profile_name, transform_variant, transform_params=transform_params)

    y_train = train_df[target_col]
    y_val = val_stop_df[target_col]
    y_holdout = holdout_df[target_col]

    masks = _build_feature_group_masks(profile)
    groups = {
        "full": masks["all"],
        "no_price": ~masks["price"],
        "no_structure": ~masks["structure"],
        "no_atr": ~masks["atr"],
        "no_time": ~masks["time"],
    }

    results = {}
    for group_name, mask in groups.items():
        X_tr = X_train[:, mask]
        X_va = X_val[:, mask]
        X_ho = X_holdout[:, mask]

        model, val_auc = train_xgb_baseline(X_tr, y_train, X_va, y_val, seed=seed)

        val_probs = model.predict(xgb.DMatrix(X_va))
        holdout_probs = model.predict(xgb.DMatrix(X_ho))

        val_metrics = compute_metrics(y_val, pd.Series(val_probs))
        holdout_metrics = compute_metrics(y_holdout, pd.Series(holdout_probs))

        results[group_name] = {
            "n_features": int(mask.sum()),
            "val": {k: _safe(v) for k, v in val_metrics.items()},
            "holdout": {k: _safe(v) for k, v in holdout_metrics.items()},
        }
        print(f"    {group_name}: val AUC = {val_metrics.get('auc', 'N/A'):.4f} ({int(mask.sum())} features)")

    return results


def run_phase1(train_df, val_stop_df, holdout_df, seed, device, report):
    """Phase 1: all100_base10_time + all100_base10_no_time."""
    print(f"\n{'='*60}")
    print(f"Phase 1 — Baseline check (seed={seed})")
    print(f"{'='*60}")

    profiles = ["all100_base10_time", "all100_base10_no_time"]
    y_train = train_df[TARGET_COLUMN]
    y_val = val_stop_df[TARGET_COLUMN]
    y_holdout = holdout_df[TARGET_COLUMN]

    for pname in profiles:
        _train_and_eval_profile(train_df, val_stop_df, holdout_df, seed, device, report,
                                pname, y_train, y_val, y_holdout)

    return report


def _train_and_eval_profile(train_df, val_stop_df, holdout_df, seed, device, report,
                            pname, y_train, y_val, y_holdout, diagnostic_only=False,
                            transform_variant: str = "current",
                            parsed_splits: dict | None = None,
                            allow_dynamic_seq_len: bool = True,
                            profile_role: str = "legacy",
                            target_col: str = TARGET_COLUMN,
                            model_config: dict | None = None):
    """Shared train/eval loop for one profile. Returns elapsed_s or None if skipped."""
    profile = find_profile(pname)
    # Corridor validation
    if profile.get("selection") == "corridor":
        print(f"\n  --- Corridor validation: {pname} ---")
        stats_train = compute_corridor_stats(train_df, profile)
        stats_val = compute_corridor_stats(val_stop_df, profile)
        stats_holdout = compute_corridor_stats(holdout_df, profile)
        status = corridor_status(stats_train)

        report.setdefault("corridor_stats", {})[pname] = {
            "train": {k: _safe(v) for k, v in stats_train.items()},
            "val_stop": {k: _safe(v) for k, v in stats_val.items()},
            "holdout": {k: _safe(v) for k, v in stats_holdout.items()},
            "status": status,
        }
        print(f"    Status: {status}, median fractals: {stats_train['n_fractals_median']}")

        if status == "REJECTED":
            print(f"    SKIPPED: profile rejected by corridor validation")
            return None

        if allow_dynamic_seq_len:
            combined_stats = compute_corridor_stats(
                pd.concat([train_df, val_stop_df]), profile)
            combined_p80 = combined_stats.get("n_fractals_p80", profile["seq_len"])
            if combined_p80 < profile["seq_len"]:
                new_seq = max(int(combined_p80), 3)
                print(f"    Adjusting seq_len: {profile['seq_len']} → {new_seq} (P80={combined_p80:.1f})")
                profile = deepcopy(profile)
                profile["seq_len"] = new_seq

    tag = " [DIAGNOSTIC_ONLY]" if diagnostic_only else ""
    print(f"\n  Building profile: {pname}{tag}")
    t0 = time.time()

    if profile.get("full29", False):
        transform_params = {}
        tokens_train, rf_train, mask_train, _meta_train = build_profile_features(
            train_df, profile, transform_variant, transform_params)
        tokens_val, rf_val, mask_val, _meta_val = build_profile_features(
            val_stop_df, profile, transform_variant, transform_params)
        tokens_hold, rf_hold, mask_hold, _meta_hold = build_profile_features(
            holdout_df, profile, transform_variant, transform_params)
    else:
        parsed_splits = parsed_splits or {
            "train": parse_split_fractals(train_df),
            "val_stop": parse_split_fractals(val_stop_df),
            "holdout": parse_split_fractals(holdout_df),
        }
        transform_params = fit_transform_params_for_profile(
            train_df, parsed_splits["train"], profile, transform_variant)

        tokens_train, rf_train, mask_train, _meta_train = build_profile_features_from_parsed(
            train_df, parsed_splits["train"], profile, transform_variant, transform_params)
        tokens_val, rf_val, mask_val, _meta_val = build_profile_features_from_parsed(
            val_stop_df, parsed_splits["val_stop"], profile, transform_variant, transform_params)
        tokens_hold, rf_hold, mask_hold, _meta_hold = build_profile_features_from_parsed(
            holdout_df, parsed_splits["holdout"], profile, transform_variant, transform_params)

    print(f"    Train: {tokens_train.shape}, Val: {tokens_val.shape}, Holdout: {tokens_hold.shape}")

    # Normalize: fit StandardScaler on train valid positions only
    (tokens_train, rf_train, tokens_val, rf_val, tokens_hold, rf_hold), scaler_stats = \
        normalize_profile_features(
            tokens_train, rf_train, mask_train,
            tokens_val, rf_val, mask_val,
            tokens_hold, rf_hold, mask_hold,
        )

    # Normalized distribution audit (before training — mandatory)
    dist_audit = audit_normalized_distribution(
        tokens_train, mask_train,
        tokens_val, mask_val,
        tokens_hold, mask_hold,
        rf_train, rf_val, rf_hold,
        token_fields=profile.get("token_fields", None),
        row_fields=profile.get("row_fields", None),
    )
    print(f"    Dist audit: {dist_audit['status']} ({len(dist_audit['flags'])} flags)")
    if dist_audit["flags"]:
        for flag in dist_audit["flags"][:5]:
            print(f"      ⚠️  {flag}")
        if len(dist_audit["flags"]) > 5:
            print(f"      ... and {len(dist_audit['flags']) - 5} more flags")

    model, history = train_transformer(
        tokens_train, rf_train, mask_train, y_train,
        tokens_val, rf_val, mask_val, y_val,
        profile, seed, device,
        model_config=model_config,
    )

    val_probs = evaluate_transformer(model, tokens_val, rf_val, mask_val, y_val, device)
    holdout_probs = evaluate_transformer(model, tokens_hold, rf_hold, mask_hold, y_holdout, device)

    val_metrics = compute_metrics(y_val, pd.Series(val_probs))
    holdout_metrics = compute_metrics(y_holdout, pd.Series(holdout_probs))
    yearly = compute_yearly_metrics(holdout_df, holdout_probs, target_col=target_col)

    elapsed = time.time() - t0
    result = {
        "profile": pname,
        "seed": seed,
        "transform_variant": transform_variant,
        "transform_config": {
            "variant": transform_variant,
            "fit_params": transform_params,
            "fit_params_policy": "train only; val_stop/holdout are disclosure only",
        },
        "model_config": deepcopy(model_config) if model_config is not None else None,
        "profile_role": profile_role,
        "training_run": True,
        "history": {k: _safe(v) for k, v in history.items()},
        "val": {k: _safe(v) for k, v in val_metrics.items()},
        "holdout": {k: _safe(v) for k, v in holdout_metrics.items()},
        "yearly": {k: {kk: _safe(vv) for kk, vv in v.items()} for k, v in yearly.items()},
        "elapsed_s": float(elapsed),
        "scaler_stats": scaler_stats,
        "normalized_distribution_audit": dist_audit,
        "diagnostic_only": diagnostic_only or None,
    }
    report["transformer_results"].setdefault(pname, []).append(result)

    print(f"    Val AUC: {val_metrics.get('auc'):.4f}, Holdout AUC: {holdout_metrics.get('auc')}")
    print(f"    Epochs: {history.get('num_epochs')}, Time: {elapsed:.0f}s")
    return elapsed


def run_phase2(train_df, val_stop_df, holdout_df, seed, device, report):
    """Phase 2: newest20, nearest40, corridor_10atr + relative_price diagnostic."""
    print(f"\n{'='*60}")
    print(f"Phase 2 — Selection variations (seed={seed})")
    print(f"{'='*60}")

    profiles = ["newest20_base10_time", "nearest40_base10_time", "corridor_10atr_base10_time"]
    diag_profiles = [
        "all100_base10_relative_price_time",
        "nearest40_base10_relative_price_time",
        "corridor_10atr_base10_relative_price_time",
    ]
    y_train = train_df[TARGET_COLUMN]
    y_val = val_stop_df[TARGET_COLUMN]
    y_holdout = holdout_df[TARGET_COLUMN]

    for pname in profiles:
        _train_and_eval_profile(train_df, val_stop_df, holdout_df, seed, device, report,
                                pname, y_train, y_val, y_holdout)

    # Diagnostic: relative_price ablation
    if diag_profiles:
        print(f"\n{'='*60}")
        print(f"Phase 2 diagnostic — relative_price ablation (seed={seed})")
        print(f"{'='*60}")
        for pname in diag_profiles:
            _train_and_eval_profile(train_df, val_stop_df, holdout_df, seed, device, report,
                                    pname, y_train, y_val, y_holdout, diagnostic_only=True)

    return report


def run_phase3(train_df, val_stop_df, holdout_df, seed, device, report):
    """Phase 3: corridor ablation (5/10/15 ATR)."""
    print(f"\n{'='*60}")
    print(f"Phase 3 — Corridor ablation (seed={seed})")
    print(f"{'='*60}")

    profiles = ["corridor_5atr_base10_time", "corridor_15atr_base10_time"]
    y_train = train_df[TARGET_COLUMN]
    y_val = val_stop_df[TARGET_COLUMN]
    y_holdout = holdout_df[TARGET_COLUMN]

    for pname in profiles:
        _train_and_eval_profile(train_df, val_stop_df, holdout_df, seed, device, report,
                                pname, y_train, y_val, y_holdout)

    return report


def run_phase4(train_df, val_stop_df, holdout_df, seed, device, report):
    """Phase 4: optional extended features."""
    print(f"\n{'='*60}")
    print(f"Phase 4 — Extended features (seed={seed})")
    print(f"{'='*60}")

    profiles = ["all100_full29_time", "all100_base10_no_price_time"]
    y_train = train_df[TARGET_COLUMN]
    y_val = val_stop_df[TARGET_COLUMN]
    y_holdout = holdout_df[TARGET_COLUMN]

    for pname in profiles:
        _train_and_eval_profile(train_df, val_stop_df, holdout_df, seed, device, report,
                                pname, y_train, y_val, y_holdout)

    return report


def apply_holdout_gate(report):
    """Apply holdout gate to primary profile only. lift_X = breach_rate in bottom X% / baseline_rate: lower = better."""
    transformer_results = report.get("transformer_results", {})
    primary_name = "all100_base10_time"
    primary_results = transformer_results.get(primary_name, [])

    if not primary_results:
        report["holdout_gate"] = {"verdict": "NO_PRIMARY_RESULTS"}
        return report

    xgb_results = report.get("baselines", {}).get("base_raw_plus_time", {})
    time_results = report.get("baselines", {}).get("time_only", {})

    xgb_holdout_auc = xgb_results.get("holdout", {}).get("auc", 0.0) or 0.0
    xgb_holdout_lift30 = xgb_results.get("holdout", {}).get("lift_30", 1.0) or 1.0
    time_holdout_auc = time_results.get("holdout", {}).get("auc", 0.0) or 0.0

    checks = []
    for r in primary_results:
        h_auc = r.get("holdout", {}).get("auc")
        h_lift30 = r.get("holdout", {}).get("lift_30")
        yearly = r.get("yearly", {})

        if h_auc is None:
            checks.append({"seed": r["seed"], "verdict": "NO_VALID_AUC"})
            continue

        gate1 = h_auc >= max(xgb_holdout_auc + HOLDOUT_AUC_DELTA, time_holdout_auc + HOLDOUT_TIME_AUC_DELTA)
        # lift_30 = breach_rate in bottom 30% / baseline_rate. Lower = better (fewer breaches in safe zone).
        gate2 = (h_lift30 or 1.0) <= max((xgb_holdout_lift30 or 1.0) - HOLDOUT_LIFT_DELTA, 0.0)

        years_ok = sum(1 for yv in yearly.values()
                       if (yv.get("auc") or 0.0) >= YEARLY_AUC_MIN and (yv.get("n") or 0) >= 50)
        gate3 = years_ok >= MIN_VALID_YEARS

        verdict = "PASS" if (gate1 and gate2 and gate3) else "FAIL"

        checks.append({
            "seed": r["seed"],
            "holdout_auc": _safe(h_auc),
            "xgb_holdout_auc": _safe(xgb_holdout_auc),
            "gate1_auc_vs_xgb": _safe(h_auc - xgb_holdout_auc),
            "gate2_lift30_transformer": _safe(h_lift30),
            "gate2_lift30_xgb": _safe(xgb_holdout_lift30),
            "gate3_years_ok": years_ok,
            "verdict": verdict,
            "details": {
                "gate1_auc_threshold_met": gate1,
                "gate2_lift_threshold_met": gate2,
                "gate3_yearly_threshold_met": gate3,
            },
        })

    report["holdout_gate"] = checks

    return report


PREFLIGHT_PROFILE_NAMES = [
    "time_only_clean",
    "atr_only",
    "time_plus_atr",
    "all100_absolute_price_time",
    "all100_no_price_time",
    "all100_relative_price_no_time",
    "all100_relative_price_time",
    "corridor_5atr_relative_price_no_time",
    "corridor_10atr_relative_price_no_time",
    "corridor_5atr_relative_price_no_time_full",
    "corridor_10atr_relative_price_no_time_full",
    "corridor_5atr_relative_price_atr_full",
    "corridor_10atr_relative_price_atr_full",
    "corridor_15atr_relative_price_no_time",
    "corridor_10atr_relative_price_time",
    "nearest40_relative_price_no_time",
    "nearest40_relative_price_time",
]

RERUN_CANDIDATE_PROFILE_NAMES = [
    "all100_no_price_time",
    "all100_relative_price_no_time",
    "all100_relative_price_time",
    "all100_absolute_price_atr_scaled_time_raw",
    "all100_absolute_price_atr_scaled_time_asinh",
    "nearest40_relative_price_no_time",
    "nearest40_relative_price_time",
    "corridor_5atr_relative_price_atr_full",
    "corridor_10atr_relative_price_atr_full",
    "corridor_5atr_price_unit_atr_full",
    "corridor_10atr_price_unit_atr_full",
]

STAGE5_0B_CONFIRMATORY_PROFILE_NAMES = [
    "all100_relative_price_time",
    "nearest40_relative_price_time",
    "corridor_5atr_relative_price_atr_full",
    "corridor_10atr_relative_price_atr_full",
]

STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES = [
    "all100_relative_price_no_time",
    "nearest40_relative_price_no_time",
    "all100_absolute_price_atr_scaled_time_asinh",
    "corridor_5atr_price_unit_atr_full",
    "corridor_10atr_price_unit_atr_full",
]

STAGE5_0B_ASINH_PROFILE_NAMES = (
    STAGE5_0B_CONFIRMATORY_PROFILE_NAMES
    + STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES
)

TRANSFORM_VARIANTS = {
    "current": {
        "row_atr": "log1p",
        "price_coord_atr": "signed_log1p",
        "fit_params": False,
    },
    "asinh": {
        "row_atr": "asinh",
        "price_coord_atr": "asinh",
        "fit_params": False,
    },
    "piecewise_tail": {
        "row_atr": "piecewise_tail",
        "price_coord_atr": "piecewise_tail",
        "fit_params": True,
        "lower_q": 5,
        "upper_q": 95,
    },
}

STAGE5_0C_PROFILE_NAME = "all100_absolute_price_atr_scaled_time_asinh"
STAGE5_0C_TARGETS = [
    "sell_stop_broken_H6_off05_flag",
    "buy_stop_broken_H6_off05_flag",
]
STAGE5_0C_SEEDS = [42, 77, 123, 202, 777]
STAGE5_0C_GATES = {
    "g1_auc": {
        "median_above_xgb": True,
        "min_seeds_above_xgb_minus_tol": 4,
        "tolerance": 0.005,
    },
    "g2_lift30": {
        "median_below_xgb": True,
    },
    "g3_cross_target": {
        "both_targets_required": True,
    },
    "g5_seed_spread": {
        "max_range": 0.03,
    },
}
STAGE5_0C_HOLDOUT_CHECK = {
    "max_drop": 0.05,
    "enters_overall_pass": False,
}
STAGE5_0C_JSON_REPORT_PATH = REPORTS_DIR / "stage5_0c_cross_target_rerun.json"

STAGE5_0D_PROFILE_NAMES = STAGE5_0B_ASINH_PROFILE_NAMES
STAGE5_0D_SEEDS = [42, 77, 123]
STAGE5_0D_TARGETS = [
    "sell_stop_broken_H6_off05_flag",
    "buy_stop_broken_H6_off05_flag",
]
STAGE5_0D_SCREENER_THRESHOLD = 0.02
STAGE5_0D_JSON_REPORT_PATH = REPORTS_DIR / "stage5_0d_diagnostic_screening.json"
STAGE5_0E_TARGET = "sell_stop_broken_H6_off05_flag"
STAGE5_0E_PROFILE_NAMES = [
    "all100_relative_price_time",
]
STAGE5_0E_SEEDS = [42, 77, 123]
STAGE5_0E_MODEL_CONFIGS = [
    {
        "name": "current",
        "d_model": 64,
        "nhead": 4,
        "num_layers": 2,
        "dim_feedforward": 128,
        "dropout": 0.15,
        "weight_decay": 1e-4,
        "learning_rate": 1e-3,
        "patience": 8,
    },
    {
        "name": "small_regularized",
        "d_model": 32,
        "nhead": 2,
        "num_layers": 1,
        "dim_feedforward": 64,
        "dropout": 0.35,
        "weight_decay": 1e-3,
        "learning_rate": 7e-4,
        "patience": 3,
    },
]
STAGE5_0E_JSON_REPORT_PATH = REPORTS_DIR / "stage5_0e_small_transformer_check.json"


def run_feature_preflight(train_df, val_stop_df, holdout_df) -> dict:
    stats_rows = []
    summary_rows = []
    per_position_rows = []
    profile_reports = {}
    parsed_train = parse_split_fractals(train_df)
    parsed_val = parse_split_fractals(val_stop_df)
    parsed_holdout = parse_split_fractals(holdout_df)

    for profile_name in PREFLIGHT_PROFILE_NAMES:
        profile = deepcopy(find_profile(profile_name))
        contract = get_profile_contract(profile)
        tokens_train, rf_train, mask_train, meta_train = build_profile_features_from_parsed(train_df, parsed_train, profile)
        tokens_val, rf_val, mask_val, meta_val = build_profile_features_from_parsed(val_stop_df, parsed_val, profile)
        tokens_hold, rf_hold, mask_hold, meta_hold = build_profile_features_from_parsed(holdout_df, parsed_holdout, profile)

        normalized, scaler_stats = normalize_profile_features(
            tokens_train, rf_train, mask_train,
            tokens_val, rf_val, mask_val,
            tokens_hold, rf_hold, mask_hold,
        )
        tokens_train_n, rf_train_n, tokens_val_n, rf_val_n, tokens_hold_n, rf_hold_n = normalized

        dist_audit = audit_normalized_distribution(
            tokens_train_n, mask_train,
            tokens_val_n, mask_val,
            tokens_hold_n, mask_hold,
            rf_train_n, rf_val_n, rf_hold_n,
            token_fields=profile.get("token_fields"),
            row_fields=profile.get("row_fields"),
        )
        coverage_by_split = {
            "train": compute_profile_coverage(tokens_train_n, mask_train, profile, meta_train),
            "val_stop": compute_profile_coverage(tokens_val_n, mask_val, profile, meta_val),
            "holdout": compute_profile_coverage(tokens_hold_n, mask_hold, profile, meta_hold),
        }

        for split_name in ["train", "val_stop", "holdout"]:
            stats_rows.extend(flatten_audit_to_rows(
                profile_name,
                profile,
                split_name,
                dist_audit["by_split"][split_name],
                coverage_by_split[split_name],
            ))

        # A7 per-position token stats for sequence profiles (token order has meaning:
        # corridor/nearest/all100). row_only profiles (token_dim=0) return [].
        if profile.get("token_dim", 0) > 0:
            for split_name, tok_n, msk in [
                ("train", tokens_train_n, mask_train),
                ("val_stop", tokens_val_n, mask_val),
                ("holdout", tokens_hold_n, mask_hold),
            ]:
                pp_rows = compute_per_position_token_stats(
                    tok_n, msk, profile.get("token_fields") or [])
                for r in pp_rows:
                    r["profile"] = profile_name
                    r["split"] = split_name
                per_position_rows.extend(pp_rows)

        flags_text = ";".join(dist_audit["flags"])
        decision = "ALLOW"
        if dist_audit["status"] == "ERROR":
            decision = "BLOCK"
        elif dist_audit["status"] == "WARNING":
            decision = "REVIEW"

        summary_rows.append({
            "profile": profile_name,
            "status": dist_audit["status"],
            "decision": decision,
            "decision_basis_split": "train_val_stop_only",
            "token_order": contract["token_order"],
            "diagnostic_only": contract["diagnostic_only"],
            "scaler_type": "StandardScaler",
            "transform_type": "log1p_atr_or_price_coord_atr",
            "train_valid_tokens_p50": coverage_by_split["train"]["valid_tokens_p50"],
            "val_valid_tokens_p50": coverage_by_split["val_stop"]["valid_tokens_p50"],
            "holdout_valid_tokens_p50": coverage_by_split["holdout"]["valid_tokens_p50"],
            "train_pct_empty": coverage_by_split["train"]["pct_empty"],
            "val_pct_empty": coverage_by_split["val_stop"]["pct_empty"],
            "holdout_pct_empty": coverage_by_split["holdout"]["pct_empty"],
            "train_candidate_count_before_cap_p50": coverage_by_split["train"]["candidate_count_before_cap_p50"],
            "train_selected_count_after_cap_p50": coverage_by_split["train"]["selected_count_after_cap_p50"],
            "train_pct_truncation_true": coverage_by_split["train"]["pct_truncation_true"],
            "train_pct_candidate_count_ge_90": coverage_by_split["train"]["pct_candidate_count_ge_90"],
            "train_pct_selected_count_ge_90": coverage_by_split["train"]["pct_selected_count_ge_90"],
            "max_train_abs_gt10": max(
                [r.get("frac_abs_gt10", 0) or 0 for r in stats_rows if r["profile"] == profile_name and r["split"] == "train" and r["feature_group"] in {"token", "row"}] or [0]
            ),
            "max_holdout_abs_gt10": max(
                [r.get("frac_abs_gt10", 0) or 0 for r in stats_rows if r["profile"] == profile_name and r["split"] == "holdout" and r["feature_group"] in {"token", "row"}] or [0]
            ),
            "flags": flags_text,
        })

        profile_reports[profile_name] = {
            "profile_contract": contract,
            "normalization_config": {
                "method": "StandardScaler",
                "token_scaler_fit_on": "train valid positions only (mask=True)",
                "row_scaler_fit_on": "all train rows",
                "padding": "kept as zero, not transformed",
                "decision_policy": "holdout for disclosure only",
            },
            "scaler_stats": scaler_stats,
            "normalized_distribution_audit": dist_audit,
            "coverage": coverage_by_split,
        }

    stats_df = pd.DataFrame(stats_rows)
    summary_df = pd.DataFrame(summary_rows)
    stats_path = REPORTS_DIR / "stage5_0a_feature_stats_normalized.csv"
    summary_path = REPORTS_DIR / "stage5_0a_profile_summary.csv"
    json_path = REPORTS_DIR / "stage5_0a_feature_preflight.json"
    stats_df.to_csv(stats_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    # A7 per-position token stats artifact (sequence profiles only)
    per_position_path = REPORTS_DIR / "stage5_0a_feature_stats_per_position.csv"
    if per_position_rows:
        pp_df = pd.DataFrame(per_position_rows)
        col_order = ["profile", "split", "feature_group", "feature_name", "token_position",
                     "n_valid", "missing_pct", "zero_pct", "mean", "std", "min",
                     "p1", "p5", "p25", "p50", "p75", "p95", "p99", "max",
                     "frac_abs_gt3", "frac_abs_gt5", "frac_abs_gt10", "frac_abs_gt20",
                     "nan_count", "inf_count", "status", "flags"]
        pp_df = pp_df.reindex(columns=col_order)
        pp_df.to_csv(per_position_path, index=False)
    else:
        per_position_path = None

    report = {
        "status": "DIAGNOSTIC_ONLY",
        "stage": "5.0a_feature_preflight",
        "split": {
            "train": {"n_rows": len(train_df), "years": sorted(map(int, train_df["_year"].unique()))},
            "val_stop": {"n_rows": len(val_stop_df), "years": sorted(map(int, val_stop_df["_year"].unique()))},
            "holdout": {"n_rows": len(holdout_df), "years": sorted(map(int, holdout_df["_year"].unique()))},
        },
        "profiles": PREFLIGHT_PROFILE_NAMES,
        "profile_reports": profile_reports,
        "artifacts": {
            "json": str(json_path),
            "stats_csv": str(stats_path),
            "summary_csv": str(summary_path),
            "per_position_csv": str(per_position_path) if per_position_path else None,
        },
        "decision_policy": {
            "selection_basis": "train and val_stop only",
            "holdout_usage": "distribution shift disclosure only",
            "training_allowed": False,
        },
    }
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    return report


def run_transform_comparison(train_df, val_stop_df, holdout_df) -> dict:
    """Compare current/asinh/piecewise-tail transforms without model training."""
    stats_rows = []
    summary_rows = []
    per_position_rows = []
    profile_reports = {}
    parsed_train = parse_split_fractals(train_df)
    parsed_val = parse_split_fractals(val_stop_df)
    parsed_holdout = parse_split_fractals(holdout_df)

    for transform_variant, variant_cfg in TRANSFORM_VARIANTS.items():
        variant_reports = {}
        transform_type = (
            f"{variant_cfg['row_atr']}_atr__"
            f"{variant_cfg['price_coord_atr']}_price_coord_atr"
        )
        for profile_name in RERUN_CANDIDATE_PROFILE_NAMES:
            profile = deepcopy(find_profile(profile_name))
            contract = get_profile_contract(profile)
            transform_params = fit_transform_params_for_profile(
                train_df, parsed_train, profile, transform_variant)

            tokens_train, rf_train, mask_train, meta_train = build_profile_features_from_parsed(
                train_df, parsed_train, profile, transform_variant, transform_params)
            tokens_val, rf_val, mask_val, meta_val = build_profile_features_from_parsed(
                val_stop_df, parsed_val, profile, transform_variant, transform_params)
            tokens_hold, rf_hold, mask_hold, meta_hold = build_profile_features_from_parsed(
                holdout_df, parsed_holdout, profile, transform_variant, transform_params)

            normalized, scaler_stats = normalize_profile_features(
                tokens_train, rf_train, mask_train,
                tokens_val, rf_val, mask_val,
                tokens_hold, rf_hold, mask_hold,
            )
            tokens_train_n, rf_train_n, tokens_val_n, rf_val_n, tokens_hold_n, rf_hold_n = normalized

            dist_audit = audit_normalized_distribution(
                tokens_train_n, mask_train,
                tokens_val_n, mask_val,
                tokens_hold_n, mask_hold,
                rf_train_n, rf_val_n, rf_hold_n,
                token_fields=profile.get("token_fields"),
                row_fields=profile.get("row_fields"),
            )
            coverage_by_split = {
                "train": compute_profile_coverage(tokens_train_n, mask_train, profile, meta_train),
                "val_stop": compute_profile_coverage(tokens_val_n, mask_val, profile, meta_val),
                "holdout": compute_profile_coverage(tokens_hold_n, mask_hold, profile, meta_hold),
            }

            profile_stats_rows = []
            for split_name in ["train", "val_stop", "holdout"]:
                rows = flatten_audit_to_rows(
                    profile_name,
                    profile,
                    split_name,
                    dist_audit["by_split"][split_name],
                    coverage_by_split[split_name],
                )
                for r in rows:
                    r["transform_variant"] = transform_variant
                    r["transform_type"] = transform_type
                profile_stats_rows.extend(rows)
                stats_rows.extend(rows)

            if profile.get("token_dim", 0) > 0:
                for split_name, tok_n, msk in [
                    ("train", tokens_train_n, mask_train),
                    ("val_stop", tokens_val_n, mask_val),
                    ("holdout", tokens_hold_n, mask_hold),
                ]:
                    pp_rows = compute_per_position_token_stats(
                        tok_n, msk, profile.get("token_fields") or [])
                    for r in pp_rows:
                        r["transform_variant"] = transform_variant
                        r["transform_type"] = transform_type
                        r["profile"] = profile_name
                        r["split"] = split_name
                    per_position_rows.extend(pp_rows)

            flags_text = ";".join(dist_audit["flags"])
            decision = "ALLOW"
            if dist_audit["status"] == "ERROR":
                decision = "BLOCK"
            elif dist_audit["status"] == "WARNING":
                decision = "REVIEW"

            summary_rows.append({
                "transform_variant": transform_variant,
                "transform_type": transform_type,
                "profile": profile_name,
                "status": dist_audit["status"],
                "decision": decision,
                "decision_basis_split": "train_val_stop_only",
                "token_order": contract["token_order"],
                "diagnostic_only": contract["diagnostic_only"],
                "scaler_type": "StandardScaler",
                "train_valid_tokens_p50": coverage_by_split["train"]["valid_tokens_p50"],
                "val_valid_tokens_p50": coverage_by_split["val_stop"]["valid_tokens_p50"],
                "holdout_valid_tokens_p50": coverage_by_split["holdout"]["valid_tokens_p50"],
                "train_pct_truncation_true": coverage_by_split["train"]["pct_truncation_true"],
                "max_train_abs_gt10": max(
                    [r.get("frac_abs_gt10", 0) or 0 for r in profile_stats_rows
                     if r["split"] == "train" and r["feature_group"] in {"token", "row"}] or [0]
                ),
                "max_holdout_abs_gt10": max(
                    [r.get("frac_abs_gt10", 0) or 0 for r in profile_stats_rows
                     if r["split"] == "holdout" and r["feature_group"] in {"token", "row"}] or [0]
                ),
                "flags": flags_text,
            })

            variant_reports[profile_name] = {
                "profile_contract": contract,
                "transform_config": {
                    "variant": transform_variant,
                    "row_atr": variant_cfg["row_atr"],
                    "price_coord_atr": variant_cfg["price_coord_atr"],
                    "fit_params": transform_params,
                    "fit_params_policy": "train only; val_stop/holdout are disclosure only",
                },
                "normalization_config": {
                    "method": "StandardScaler",
                    "token_scaler_fit_on": "train valid positions only (mask=True)",
                    "row_scaler_fit_on": "all train rows",
                    "padding": "kept as zero, not transformed",
                    "decision_policy": "holdout for disclosure only",
                },
                "scaler_stats": scaler_stats,
                "normalized_distribution_audit": dist_audit,
                "coverage": coverage_by_split,
            }
        profile_reports[transform_variant] = variant_reports

    stats_df = pd.DataFrame(stats_rows)
    summary_df = pd.DataFrame(summary_rows)

    stats_path = REPORTS_DIR / "stage5_0a_transform_comparison_stats.csv"
    summary_path = REPORTS_DIR / "stage5_0a_transform_comparison_summary.csv"
    per_position_path = REPORTS_DIR / "stage5_0a_transform_comparison_per_position.csv"
    json_path = REPORTS_DIR / "stage5_0a_transform_comparison.json"

    preferred_cols = ["transform_variant", "transform_type", "profile", "split",
                      "feature_group", "feature_name", "token_position"]
    stats_cols = preferred_cols + [c for c in stats_df.columns if c not in preferred_cols]
    stats_df = stats_df.reindex(columns=stats_cols)
    stats_df.to_csv(stats_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    if per_position_rows:
        pp_df = pd.DataFrame(per_position_rows)
        pp_cols = preferred_cols + [c for c in pp_df.columns if c not in preferred_cols]
        pp_df = pp_df.reindex(columns=pp_cols)
        pp_df.to_csv(per_position_path, index=False)
    else:
        per_position_path = None

    report = {
        "status": "DIAGNOSTIC_ONLY",
        "stage": "5.0a_transform_comparison",
        "russian_name": "проверка распределения признаков",
        "training_allowed": False,
        "split": {
            "train": {"n_rows": len(train_df), "years": sorted(map(int, train_df["_year"].unique()))},
            "val_stop": {"n_rows": len(val_stop_df), "years": sorted(map(int, val_stop_df["_year"].unique()))},
            "holdout": {"n_rows": len(holdout_df), "years": sorted(map(int, holdout_df["_year"].unique()))},
        },
        "profiles": RERUN_CANDIDATE_PROFILE_NAMES,
        "transform_variants": TRANSFORM_VARIANTS,
        "profile_reports": profile_reports,
        "artifacts": {
            "json": str(json_path),
            "stats_csv": str(stats_path),
            "summary_csv": str(summary_path),
            "per_position_csv": str(per_position_path) if per_position_path else None,
        },
        "decision_policy": {
            "selection_basis": "train and val_stop only",
            "holdout_usage": "distribution shift disclosure only",
            "training_allowed": False,
        },
    }
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    return report


def stage5_0b_multiseed_decision(result: dict, xgb_results: dict, profile_role: str,
                                  use_gates: bool = True) -> dict:
    if profile_role != "confirmatory":
        return {"eligible": False, "reason": "diagnostic_control"}
    if not use_gates:
        return {"eligible": False, "reason": "selection_gates_disabled"}
    val = result.get("val", {})
    audit = result.get("normalized_distribution_audit", {})
    base = xgb_results.get("base_raw_plus_time", {}).get("val", {})
    time_only = xgb_results.get("time_only", {}).get("val", {})
    auc_gate = max((base.get("auc") or 0) + 0.01, (time_only.get("auc") or 0) + 0.03)
    lift_gate = min(base.get("lift_30") or float("inf"), time_only.get("lift_30") or float("inf"))
    eligible = (
        audit.get("status") != "ERROR"
        and (val.get("auc") or 0) >= auc_gate
        and (val.get("lift_30") or float("inf")) <= lift_gate
    )
    return {
        "eligible": bool(eligible),
        "auc_gate": float(auc_gate),
        "lift_30_gate": float(lift_gate),
        "reason": "passes_val_policy" if eligible else "fails_val_policy",
    }


def _median(values: list) -> float:
    import statistics
    return float(statistics.median(values))


def _stage5_0e_config_summary(config_runs: list[dict]) -> dict:
    if not config_runs:
        return {}
    val_aucs = [run["val"]["auc"] for run in config_runs]
    val_lifts = [run["val"]["lift_30"] for run in config_runs]
    overfit_drops = [
        run.get("history", {}).get("overfit_drop_after_best")
        for run in config_runs
        if run.get("history", {}).get("overfit_drop_after_best") is not None
    ]
    return {
        "n_runs": len(config_runs),
        "median_val_auc": _median(val_aucs),
        "median_val_lift_30": _median(val_lifts),
        "seed_spread_val_auc": (max(val_aucs) - min(val_aucs)) if len(val_aucs) > 1 else 0.0,
        "median_overfit_drop_after_best": _median(overfit_drops) if overfit_drops else None,
        "per_seed_pass_vs_xgb": sum(
            1 for run in config_runs
            if (run["val"]["auc"] >= run["xgb_same_profile"]["val"]["auc"])
            and (run["val"]["lift_30"] <= run["xgb_same_profile"]["val"]["lift_30"])
        ),
    }


def stage5_0e_overfit_decision(report: dict) -> dict:
    profile_runs = report.get("profiles", {})
    if not profile_runs:
        return {
            "status": "DIAGNOSTIC_ONLY",
            "overfit_hypothesis_supported": "no",
            "transformer_reopens_h6_off05": "no",
            "best_profile": None,
            "best_config": None,
            "reason": "no_profile_results",
            "next_step": "H6_off05 остаётся закрытым; новых действий по этой постановке нет.",
        }

    profile_name = next(iter(profile_runs))
    profile_data = profile_runs[profile_name]
    current_summary = profile_data["configs"].get("current", {}).get("summary", {})
    small_summary = profile_data["configs"].get("small_regularized", {}).get("summary", {})
    xgb_val = profile_data.get("xgb_same_profile", {}).get("val", {})

    overfit_supported = (
        current_summary
        and small_summary
        and small_summary.get("median_overfit_drop_after_best") is not None
        and current_summary.get("median_overfit_drop_after_best") is not None
        and small_summary["median_overfit_drop_after_best"]
            <= current_summary["median_overfit_drop_after_best"] - 0.01
        and small_summary["median_val_auc"] >= current_summary["median_val_auc"] - 0.005
        and small_summary["seed_spread_val_auc"] <= 0.02
    )

    reopens = (
        small_summary
        and small_summary["median_val_auc"] >= xgb_val.get("auc", 0.0)
        and small_summary["median_val_lift_30"] <= xgb_val.get("lift_30", float("inf"))
        and small_summary["per_seed_pass_vs_xgb"] >= 2
        and small_summary["seed_spread_val_auc"] <= 0.02
    )

    reason = (
        "small_regularized уменьшает признаки переобучения без заметной потери val_auc"
        if overfit_supported
        else "small_regularized не дал устойчивого уменьшения признаков переобучения"
    )
    next_step = (
        "Отдельно обсудить, достаточно ли результата для исключения из решения Stage 5.0d."
        if reopens
        else "H6_off05 остаётся закрытым; дальнейшие шаги только через новую цель или новые признаки."
    )
    best_config = None
    best_val_auc = float("-inf")
    for cfg_name, cfg_data in profile_data.get("configs", {}).items():
        summary = cfg_data.get("summary", {})
        if summary and summary["median_val_auc"] > best_val_auc:
            best_val_auc = summary["median_val_auc"]
            best_config = cfg_name

    return {
        "status": "DIAGNOSTIC_ONLY",
        "overfit_hypothesis_supported": "yes" if overfit_supported else "no",
        "transformer_reopens_h6_off05": "review_required" if reopens else "no",
        "best_profile": profile_name,
        "best_config": best_config,
        "reason": reason,
        "next_step": next_step,
    }


def stage5_0c_replication_decision(target_results: dict) -> dict:
    """Apply заранее зафиксированные пороги Stage 5.0c.

    All thresholds are frozen in STAGE5_0C_GATES before any run.
    Holdout check is separate (STAGE5_0C_HOLDOUT_CHECK) and does not
    enter overall_pass. Returns per-gate, per-target breakdown,
    per-target verdicts (sell_pass, buy_pass), and overall_pass.
    """
    gates = STAGE5_0C_GATES
    tol = gates["g1_auc"]["tolerance"]
    min_seeds = gates["g1_auc"]["min_seeds_above_xgb_minus_tol"]
    max_range = gates["g5_seed_spread"]["max_range"]
    max_drop = STAGE5_0C_HOLDOUT_CHECK["max_drop"]

    g1 = {"per_target": {}, "pass": True}
    g2 = {"per_target": {}, "pass": True}
    g5 = {"per_target": {}, "pass": True}
    holdout_check = {"per_target": {}, "status": "OK"}

    per_target_pass = {}

    for tname, tdata in target_results.items():
        seed_val_aucs = [s["val"]["auc"] for s in tdata["seed_metrics"]]
        seed_val_lifts = [s["val"]["lift_30"] for s in tdata["seed_metrics"]]
        seed_hold_aucs = [s["holdout"]["auc"] for s in tdata["seed_metrics"]]
        xgb_auc = tdata["xgb_same_profile"]["val"]["auc"]
        xgb_lift = tdata["xgb_same_profile"]["val"]["lift_30"]

        med_val_auc = _median(seed_val_aucs)
        med_val_lift = _median(seed_val_lifts)
        med_hold_auc = _median(seed_hold_aucs)
        seeds_above = sum(1 for a in seed_val_aucs if a > xgb_auc - tol)
        spread = max(seed_val_aucs) - min(seed_val_aucs)

        g1_pass = med_val_auc > xgb_auc and seeds_above >= min_seeds
        g2_pass = med_val_lift < xgb_lift
        g5_pass = spread < max_range
        holdout_ok = med_hold_auc >= med_val_auc - max_drop

        g1["per_target"][tname] = {
            "pass": g1_pass,
            "median_val_auc": med_val_auc,
            "xgb_val_auc": xgb_auc,
            "seeds_above_tol": seeds_above,
        }
        g2["per_target"][tname] = {
            "pass": g2_pass,
            "median_val_lift_30": med_val_lift,
            "xgb_val_lift_30": xgb_lift,
        }
        g5["per_target"][tname] = {
            "pass": g5_pass,
            "range": spread,
        }
        holdout_check["per_target"][tname] = {
            "status": "OK" if holdout_ok else "WARNING",
            "median_holdout_auc": med_hold_auc,
            "median_val_auc": med_val_auc,
            "drop": med_val_auc - med_hold_auc,
            "max_drop": max_drop,
        }
        if not holdout_ok:
            holdout_check["status"] = "WARNING"

        g1["pass"] = g1["pass"] and g1_pass
        g2["pass"] = g2["pass"] and g2_pass
        g5["pass"] = g5["pass"] and g5_pass

        per_target_pass[tname] = g1_pass and g2_pass and g5_pass

    both_required = gates["g3_cross_target"]["both_targets_required"]
    if both_required:
        cross_target_pass = all(per_target_pass.values())
    else:
        cross_target_pass = any(per_target_pass.values())

    g3_pass = cross_target_pass
    overall = g1["pass"] and g2["pass"] and g3_pass and g5["pass"]

    g1_out = dict(g1)
    g1_out.update(g1["per_target"])
    g2_out = dict(g2)
    g2_out.update(g2["per_target"])
    g5_out = dict(g5)
    g5_out.update(g5["per_target"])

    sell_pass = per_target_pass.get("sell", False)
    buy_pass = per_target_pass.get("buy", False)

    return {
        "overall_pass": bool(overall),
        "overall_pass_components": ["g1_auc", "g2_lift30", "g3_cross_target", "g5_seed_spread"],
        "sell_pass": bool(sell_pass),
        "buy_pass": bool(buy_pass),
        "cross_target_pass": bool(cross_target_pass),
        "g1_auc": g1_out,
        "g2_lift30": g2_out,
        "g3_cross_target": {"pass": bool(g3_pass), "both_targets_required": True},
        "g5_seed_spread": g5_out,
        "holdout_check": holdout_check,
        "gates_config": gates,
        "holdout_check_config": STAGE5_0C_HOLDOUT_CHECK,
    }


def run_stage5_0b_asinh_rerun(train_df, val_stop_df, holdout_df, seed, device,
                              ohlc_verification: dict, label_sanity: dict,
                              xgb_results: dict,
                              output_path: Path | str = STAGE5_0B_JSON_REPORT_PATH,
                              target_col: str = TARGET_COLUMN,
                              all_profiles_confirmatory: bool = False,
                              use_multiseed_gates: bool = True) -> dict:
    y_train = train_df[target_col]
    y_val = val_stop_df[target_col]
    y_holdout = holdout_df[target_col]
    parsed_splits = {
        "train": parse_split_fractals(train_df),
        "val_stop": parse_split_fractals(val_stop_df),
        "holdout": parse_split_fractals(holdout_df),
    }
    split_frames = {"train": train_df, "val_stop": val_stop_df, "holdout": holdout_df}
    confirmatory_profiles = (
        list(STAGE5_0B_ASINH_PROFILE_NAMES)
        if all_profiles_confirmatory
        else STAGE5_0B_CONFIRMATORY_PROFILE_NAMES
    )
    diagnostic_profiles = [] if all_profiles_confirmatory else STAGE5_0B_DIAGNOSTIC_PROFILE_NAMES
    report = {
        "status": "DIAGNOSTIC_ONLY",
        "stage": "5.0b_asinh_rerun",
        "target": target_col,
        "transform_variant": "asinh",
        "no_trading_winner_declared": True,
        "confirmatory_profiles": confirmatory_profiles,
        "diagnostic_control_profiles": diagnostic_profiles,
        "ohlc_verification": ohlc_verification,
        "label_sanity": label_sanity,
        "xgb_baselines": xgb_results,
        "target_contracts": {
            "trained": summarize_target_contract(split_frames, target_col),
            "sell": summarize_target_contract(split_frames, TARGET_COLUMN),
            "buy_candidates": {
                col: summarize_target_contract(split_frames, col)
                for col in find_buy_stop_target_columns(train_df)
            },
        },
        "decision_policy": {
            "profile_set": "frozen before training",
            "selection_basis": "val_stop only",
            "holdout_usage": "disclosure only",
            "multi_seed_rules": (
                {
                    "val_auc": ">= max(xgb_base_raw_plus_time + 0.01, xgb_time_only + 0.03)",
                    "val_lift_30": "<= min(xgb_base_raw_plus_time, xgb_time_only)",
                    "audit": "normalized_distribution_audit.status != ERROR",
                    "profile_role": "confirmatory only",
                }
                if use_multiseed_gates
                else {"status": "disabled; report ranks profiles but does not open multi-seed automatically"}
            ),
        },
        "transformer_results": {},
        "multi_seed_candidates": [],
    }

    for profile_name in STAGE5_0B_ASINH_PROFILE_NAMES:
        role = "confirmatory" if profile_name in confirmatory_profiles else "diagnostic_control"
        _train_and_eval_profile(
            train_df, val_stop_df, holdout_df, seed, device, report,
            profile_name, y_train, y_val, y_holdout,
            diagnostic_only=(role == "diagnostic_control"),
            transform_variant="asinh",
            parsed_splits=parsed_splits,
            allow_dynamic_seq_len=False,
            profile_role=role,
            target_col=target_col,
        )
        result = report["transformer_results"][profile_name][-1]
        decision = stage5_0b_multiseed_decision(result, xgb_results, role, use_gates=use_multiseed_gates)
        result["multi_seed_decision"] = decision
        if decision["eligible"]:
            report["multi_seed_candidates"].append(profile_name)

    output_path = Path(output_path)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    return report


def run_stage5_0c_cross_target_rerun(sell_splits: tuple, buy_splits: tuple,
                                     seeds: list, device, output_path=None) -> dict:
    """Stage 5.0c: повторная проверка гипотезы 5.0b на sell + buy.

    Framing: повторная проверка гипотезы 5.0b, не независимое открытие.
    Заранее зафиксированные пороги в STAGE5_0C_GATES; holdout — только
    раскрытие результата, не входит в overall_pass.
    """
    profile_name = STAGE5_0C_PROFILE_NAME
    report = {
        "status": "DIAGNOSTIC_ONLY",
        "stage": "5.0c_cross_target_rerun",
        "profile": profile_name,
        "transform_variant": "asinh",
        "seeds": list(seeds),
        "framing": "replication_test_of_5_0b_hypothesis",
        "no_trading_winner_declared": True,
        "holdout_used_for_decision": False,
        "pre_registered_gates": STAGE5_0C_GATES,
        "holdout_check_config": STAGE5_0C_HOLDOUT_CHECK,
        "decision_policy": {
            "selection_basis": "val_stop only",
            "holdout_usage": "только раскрытие результата, не входит в overall_pass",
            "profile_set": "single frozen profile, no grid search",
            "multi_seed_policy": "unconditional 5-seed, no single-seed gate",
        },
        "targets": {},
    }

    split_sets = {
        "sell": (sell_splits, STAGE5_0C_TARGETS[0]),
        "buy": (buy_splits, STAGE5_0C_TARGETS[1]),
    }

    for tname, (splits, target_col) in split_sets.items():
        train_df, val_df, hold_df = splits
        print(f"\n{'='*60}")
        print(f"Stage 5.0c — цель: {tname} ({target_col})")
        print(f"{'='*60}")

        ohlc = verify_breach_labels_against_ohlc(hold_df, target_col=target_col)
        sanity = label_sanity_check(hold_df, target_col=target_col)
        xgb_baselines = compute_xgb_baselines(train_df, val_df, hold_df, target_col=target_col)
        xgb_same = compute_xgb_same_profile_baseline(
            train_df, val_df, hold_df, profile_name,
            transform_variant="asinh", target_col=target_col, seed=seeds[0])

        parsed_splits = {
            "train": parse_split_fractals(train_df),
            "val_stop": parse_split_fractals(val_df),
            "holdout": parse_split_fractals(hold_df),
        }
        y_train = train_df[target_col]
        y_val = val_df[target_col]
        y_holdout = hold_df[target_col]

        seed_metrics = []
        transformer_report = {"transformer_results": {}}
        for seed in seeds:
            print(f"\n  --- seed={seed} ---")
            _train_and_eval_profile(
                train_df, val_df, hold_df, seed, device, transformer_report,
                profile_name, y_train, y_val, y_holdout,
                diagnostic_only=False,
                transform_variant="asinh",
                parsed_splits=parsed_splits,
                allow_dynamic_seq_len=False,
                profile_role="confirmatory",
                target_col=target_col,
            )
            result = transformer_report["transformer_results"][profile_name][-1]
            seed_metrics.append({
                "seed": seed,
                "val": result.get("val", {}),
                "holdout": result.get("holdout", {}),
                "normalized_distribution_audit": result.get("normalized_distribution_audit", {}),
            })

        report["targets"][tname] = {
            "target_col": target_col,
            "ohlc_verification": ohlc,
            "label_sanity": sanity,
            "xgb_baselines": xgb_baselines,
            "xgb_same_profile": xgb_same,
            "transformer_results": transformer_report["transformer_results"],
            "seed_metrics": seed_metrics,
        }

    target_for_decision = {
        tname: {
            "xgb_same_profile": tdata["xgb_same_profile"],
            "seed_metrics": tdata["seed_metrics"],
        }
        for tname, tdata in report["targets"].items()
    }
    report["replication_decision"] = stage5_0c_replication_decision(target_for_decision)

    if output_path is not None:
        output_path = Path(output_path)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
    return report


def run_stage5_0d_diagnostic_screening(sell_splits: tuple, buy_splits: tuple,
                                        seeds: list, device, output_path=None) -> dict:
    """Stage 5.0d: диагностический скрининг профилей (XGBoost + Logistic).

    Уровень: поисковый. Transformer не обучается.
    Если ни один профиль не превосходит base_raw_plus_time на +0.02 AUC —
    ветка Fractal Stop исследовательски исчерпана.
    """
    profile_names = STAGE5_0D_PROFILE_NAMES
    report = {
        "stage": "5.0d_diagnostic_screening",
        "level": "exploratory",
        "holdout_used_for_decision": False,
        "seeds": list(seeds),
        "profile_names": list(profile_names),
        "screener_threshold": STAGE5_0D_SCREENER_THRESHOLD,
        "decision_policy": {
            "selection_basis": "val_stop only",
            "holdout_usage": "disclosure only",
            "transformer_trained": False,
            "models": ["xgboost", "logistic_regression"],
        },
        "targets": {},
    }

    split_sets = {
        "sell": (sell_splits, STAGE5_0D_TARGETS[0]),
        "buy": (buy_splits, STAGE5_0D_TARGETS[1]),
    }

    for tname, (splits, target_col) in split_sets.items():
        train_df, val_df, hold_df = splits
        print(f"\n{'='*60}")
        print(f"Stage 5.0d — цель: {tname} ({target_col})")
        print(f"{'='*60}")

        xgb_baselines = compute_xgb_baselines(train_df, val_df, hold_df, target_col=target_col)
        base_auc = xgb_baselines["base_raw_plus_time"]["val"]["auc"]
        base_lift = xgb_baselines["base_raw_plus_time"]["val"].get("lift_30")

        profile_results = {}
        best_profile = None
        best_auc = -1.0

        for pname in profile_names:
            tv = "asinh"

            xgb_seed_results = []
            for seed in seeds:
                xgb_res = compute_xgb_same_profile_baseline(
                    train_df, val_df, hold_df, pname,
                    transform_variant=tv, target_col=target_col, seed=seed)
                xgb_seed_results.append(xgb_res)

            import statistics
            xgb_val_aucs = [r["val"]["auc"] for r in xgb_seed_results]
            xgb_val_lifts = [r["val"].get("lift_30") for r in xgb_seed_results]
            xgb_holdout_aucs = [r["holdout"].get("auc") for r in xgb_seed_results]
            xgb_median_auc = statistics.median(xgb_val_aucs)
            xgb_median_lift = statistics.median(xgb_val_lifts)
            xgb_spread = max(xgb_val_aucs) - min(xgb_val_aucs) if len(xgb_val_aucs) > 1 else 0.0

            logistic_res = compute_logistic_same_profile_baseline(
                train_df, val_df, hold_df, pname,
                transform_variant=tv, target_col=target_col, seed=seeds[0])

            profile_results[pname] = {
                "transform_variant": tv,
                "xgb_median_val_auc": xgb_median_auc,
                "xgb_seed_val_aucs": xgb_val_aucs,
                "xgb_seed_val_lifts_30": xgb_val_lifts,
                "xgb_median_val_lift_30": xgb_median_lift,
                "xgb_seed_spread": xgb_spread,
                "xgb_holdout_aucs": xgb_holdout_aucs,
                "logistic_val_auc": logistic_res["val"]["auc"],
                "logistic_val_lift_30": logistic_res["val"].get("lift_30"),
                "xgb_vs_base_delta": xgb_median_auc - base_auc,
                "xgb_vs_logistic_delta": xgb_median_auc - logistic_res["val"]["auc"],
                "xgb_lift_vs_base": xgb_median_lift - base_lift if base_lift is not None else None,
            }

            if xgb_median_auc > best_auc:
                best_auc = xgb_median_auc
                best_profile = pname

        ablation = compute_feature_group_ablation(
            train_df, val_df, hold_df, best_profile,
            transform_variant="asinh",
            target_col=target_col, seed=seeds[0])

        report["targets"][tname] = {
            "target_col": target_col,
            "base_raw_plus_time_auc": base_auc,
            "base_raw_plus_time_lift_30": base_lift,
            "xgb_baselines": xgb_baselines,
            "profiles": profile_results,
            "best_profile": best_profile,
            "best_profile_val_auc": best_auc,
            "ablation": {"profile": best_profile, "groups": ablation},
        }

    sell_profiles = report["targets"]["sell"]["profiles"]
    buy_profiles = report["targets"]["buy"]["profiles"]
    sell_base_auc = report["targets"]["sell"]["base_raw_plus_time_auc"]
    buy_base_auc = report["targets"]["buy"]["base_raw_plus_time_auc"]
    sell_base_lift = report["targets"]["sell"]["base_raw_plus_time_lift_30"]
    buy_base_lift = report["targets"]["buy"]["base_raw_plus_time_lift_30"]
    threshold = STAGE5_0D_SCREENER_THRESHOLD

    def _find_best(profiles, base_auc, base_lift):
        best_pname = None
        best_delta = -1.0
        for pname, p in profiles.items():
            if p["xgb_vs_base_delta"] > best_delta:
                best_delta = p["xgb_vs_base_delta"]
                best_pname = pname
        best_lift = profiles[best_pname]["xgb_median_val_lift_30"] if best_pname else None
        return best_pname, best_delta, best_lift

    sell_best_pname, sell_best_delta, sell_best_lift = _find_best(sell_profiles, sell_base_auc, sell_base_lift)
    buy_best_pname, buy_best_delta, buy_best_lift = _find_best(buy_profiles, buy_base_auc, buy_base_lift)

    if sell_best_delta >= buy_best_delta:
        overall_best_delta = sell_best_delta
        overall_best_target = "sell"
        overall_best_pname = sell_best_pname
        overall_best_lift = sell_best_lift
        overall_base_lift = sell_base_lift
    else:
        overall_best_delta = buy_best_delta
        overall_best_target = "buy"
        overall_best_pname = buy_best_pname
        overall_best_lift = buy_best_lift
        overall_base_lift = buy_base_lift

    auc_pass = overall_best_delta >= threshold
    lift_pass = (overall_best_lift is not None and overall_base_lift is not None
                 and overall_best_lift <= overall_base_lift)

    if auc_pass and lift_pass:
        screener_result = {
            "verdict": "profile_with_potential",
            "criteria": {
                "auc_threshold": threshold,
                "auc_delta": overall_best_delta,
                "auc_pass": True,
                "lift_pass": lift_pass,
                "lift_30": overall_best_lift,
                "base_lift_30": overall_base_lift,
            },
            "overall_best": {
                "target": overall_best_target,
                "profile": overall_best_pname,
                "delta": overall_best_delta,
                "lift_30": overall_best_lift,
            },
            "sell_best": {"profile": sell_best_pname, "delta": sell_best_delta, "lift_30": sell_best_lift},
            "buy_best": {"profile": buy_best_pname, "delta": buy_best_delta, "lift_30": buy_best_lift},
            "next_step": "Гипотеза для Stage 5.0e (Transformer multi-seed на лучшем профиле). Результат 5.0d не открывает Transformer-обучение автоматически — только формирует гипотезу для нового проверочного цикла с заранее зафиксированными порогами.",
        }
    else:
        screener_result = {
            "verdict": "h6_off05_target_exhausted",
            "criteria": {
                "auc_threshold": threshold,
                "auc_delta": overall_best_delta,
                "auc_pass": auc_pass,
                "lift_pass": lift_pass,
                "lift_30": overall_best_lift,
                "base_lift_30": overall_base_lift,
            },
            "overall_best": {
                "target": overall_best_target,
                "profile": overall_best_pname,
                "delta": overall_best_delta,
                "lift_30": overall_best_lift,
            },
            "sell_best": {"profile": sell_best_pname, "delta": sell_best_delta, "lift_30": sell_best_lift},
            "buy_best": {"profile": buy_best_pname, "delta": buy_best_delta, "lift_30": buy_best_lift},
            "next_step": "Постановка H6_off05 stop broken на текущих 9 профилях исчерпана. Fractal Stop как семейство целей не закрыт — остаются другие постановки (сторона, время до пробоя, выход). Результат 5.0d не открывает Transformer-обучение автоматически.",
        }

    report["screener_result"] = screener_result

    if output_path is not None:
        output_path = Path(output_path)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
    return report


def run_stage5_0e_small_transformer_check(sell_splits, seed, device,
                                          output_path=STAGE5_0E_JSON_REPORT_PATH) -> dict:
    train_df, val_df, hold_df = sell_splits
    report = {
        "status": "DIAGNOSTIC_ONLY",
        "stage": "5.0e_small_transformer_overfit_check",
        "level": "post_mortem_diagnostic",
        "target": STAGE5_0E_TARGET,
        "holdout_used_for_decision": False,
        "seeds": list(STAGE5_0E_SEEDS),
        "profile_names": list(STAGE5_0E_PROFILE_NAMES),
        "model_configs": deepcopy(STAGE5_0E_MODEL_CONFIGS),
        "decision_policy": {
            "selection_basis": "val_stop only",
            "holdout_usage": "disclosure only",
            "xgboost_role": "same-profile primary comparator",
            "reopen_policy": "no automatic reopen; only review_required",
        },
        "profiles": {},
    }
    y_train = train_df[STAGE5_0E_TARGET]
    y_val = val_df[STAGE5_0E_TARGET]
    y_holdout = hold_df[STAGE5_0E_TARGET]
    parsed_splits = {
        "train": parse_split_fractals(train_df),
        "val_stop": parse_split_fractals(val_df),
        "holdout": parse_split_fractals(hold_df),
    }

    ohlc = verify_breach_labels_against_ohlc(hold_df, target_col=STAGE5_0E_TARGET)
    sanity = label_sanity_check(hold_df, target_col=STAGE5_0E_TARGET)
    report["ohlc_verification"] = ohlc
    report["label_sanity"] = sanity

    for profile_name in STAGE5_0E_PROFILE_NAMES:
        xgb_same = compute_xgb_same_profile_baseline(
            train_df, val_df, hold_df, profile_name,
            transform_variant="asinh", target_col=STAGE5_0E_TARGET, seed=seed)
        profile_entry = {
            "xgb_same_profile": xgb_same,
            "configs": {},
        }
        for model_config in STAGE5_0E_MODEL_CONFIGS:
            cfg_name = model_config["name"]
            cfg_report = {"transformer_results": {}}
            runs = []
            for run_seed in STAGE5_0E_SEEDS:
                _train_and_eval_profile(
                    train_df, val_df, hold_df, run_seed, device, cfg_report,
                    profile_name, y_train, y_val, y_holdout,
                    diagnostic_only=True,
                    transform_variant="asinh",
                    parsed_splits=parsed_splits,
                    allow_dynamic_seq_len=False,
                    profile_role=f"stage5_0e::{cfg_name}",
                    target_col=STAGE5_0E_TARGET,
                    model_config=model_config,
                )
                run_result = deepcopy(cfg_report["transformer_results"][profile_name][-1])
                run_result["model_config"] = deepcopy(model_config)
                run_result["xgb_same_profile"] = {
                    "val": xgb_same["val"],
                    "holdout": xgb_same["holdout"],
                }
                runs.append(run_result)
            profile_entry["configs"][cfg_name] = {
                "model_config": deepcopy(model_config),
                "runs": runs,
                "summary": _stage5_0e_config_summary(runs),
            }
        report["profiles"][profile_name] = profile_entry

    report["decision"] = stage5_0e_overfit_decision(report)
    output_path = Path(output_path)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    return report


def _stage5_0f_year_list(df: pd.DataFrame) -> list[int]:
    if "_year" in df.columns:
        return sorted(int(y) for y in df["_year"].dropna().unique().tolist())
    years = pd.to_datetime(df["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    return sorted(int(y) for y in years.dropna().unique().tolist())


def _stage5_0f_with_year(df: pd.DataFrame) -> pd.DataFrame:
    if "_year" in df.columns:
        return df.copy()
    out = df.copy()
    out["_year"] = pd.to_datetime(out["time"], format="%Y.%m.%d %H:%M", errors="coerce").dt.year
    return out


def _stage5_0f_split_manifest_part(df: pd.DataFrame, target_col: str) -> dict:
    years = _stage5_0f_year_list(df)
    non_null = df[target_col].dropna() if target_col in df.columns else pd.Series(dtype=float)
    return {
        "years": years,
        "n_rows": int(len(df)),
        "positive_rate": float((non_null == 1).mean()) if len(non_null) else None,
    }


def stage5_0f_split_manifest(train_core: pd.DataFrame, val_stop: pd.DataFrame,
                             test: pd.DataFrame, strategy: str, test_year: int,
                             target_col: str) -> dict:
    return {
        "strategy": strategy,
        "test_year": int(test_year),
        "target": target_col,
        "train_core": _stage5_0f_split_manifest_part(train_core, target_col),
        "val_stop": _stage5_0f_split_manifest_part(val_stop, target_col),
        "test": _stage5_0f_split_manifest_part(test, target_col),
    }


def build_stage5_0f_window(df: pd.DataFrame, strategy: str, test_year: int,
                           target_col: str = STAGE5_0F_TARGETS[0],
                           rolling_window_years: int = STAGE5_0F_ROLLING_WINDOW_YEARS) -> dict:
    """Build train-core / val-stop / test split for one Stage 5.0f window."""
    data = _stage5_0f_with_year(df)
    test_year = int(test_year)

    if strategy == "rolling":
        val_year = test_year - 1
        train_start = test_year - rolling_window_years
        train_end = test_year - 2
        train_core = data[(data["_year"] >= train_start) & (data["_year"] <= train_end)].copy()
        val_stop = data[data["_year"] == val_year].copy()
    elif strategy == "anchored":
        val_year = test_year - 1
        train_core = data[data["_year"] <= test_year - 2].copy()
        val_stop = data[data["_year"] == val_year].copy()
    elif strategy == "fixed":
        train_core = data[data["_year"] <= 2019].copy()
        val_stop = data[data["_year"] == 2020].copy()
    else:
        raise ValueError(f"Unknown Stage 5.0f strategy: {strategy}")

    test = data[data["_year"] == test_year].copy()
    manifest = stage5_0f_split_manifest(
        train_core, val_stop, test, strategy=strategy, test_year=test_year, target_col=target_col)
    return {
        "train_core": train_core,
        "val_stop": val_stop,
        "test": test,
        "manifest": manifest,
    }


def build_stage5_0f_windows(df: pd.DataFrame, target_col: str) -> list[dict]:
    windows = []
    for test_year in [2021, 2022, 2023, 2024, 2025, 2026]:
        windows.append(build_stage5_0f_window(
            df, "rolling", test_year, target_col=target_col))
        windows.append(build_stage5_0f_window(
            df, "fixed", test_year, target_col=target_col))
    for test_year in [2019, 2020, 2021, 2022, 2023, 2024, 2025]:
        windows.append(build_stage5_0f_window(
            df, "anchored", test_year, target_col=target_col))
    return windows


def build_stage5_1_split(df: pd.DataFrame, target_col: str) -> dict:
    """Build fixed Stage 5.1 train/val/diagnostic split."""
    data = _stage5_0f_with_year(df)
    train_core = data[data["_year"] <= 2020].copy()
    val_stop = data[data["_year"].isin(STAGE5_1_VAL_YEARS)].copy()
    diagnostic_holdout = data[data["_year"].isin(STAGE5_1_HOLDOUT_YEARS)].copy()
    low_n_disclosure = data[data["_year"] == STAGE5_1_LOW_N_YEAR].copy()

    manifest = {
        "target": target_col,
        "train_core": _stage5_0f_split_manifest_part(train_core, target_col),
        "val_stop": _stage5_0f_split_manifest_part(val_stop, target_col),
        "diagnostic_holdout": _stage5_0f_split_manifest_part(diagnostic_holdout, target_col),
        "low_n_disclosure": _stage5_0f_split_manifest_part(low_n_disclosure, target_col),
        "holdout_disclosure": "2023-2025 are diagnostic disclosure only, already used in Stage 5.0f.",
    }
    return {
        "train_core": train_core,
        "val_stop": val_stop,
        "diagnostic_holdout": diagnostic_holdout,
        "low_n_disclosure": low_n_disclosure,
        "manifest": manifest,
    }


def evaluate_stage5_0f_window_seed(window: dict, profile_key: str, target_col: str,
                                   seed: int, transform_variant: str = "asinh",
                                   parsed_cache: dict | None = None) -> dict:
    """Train one XGBoost model for one Stage 5.0f window/profile/target/seed."""
    train_core = window["train_core"]
    val_stop = window["val_stop"]
    test = window["test"]

    cache_key = (
        target_col,
        window["manifest"]["strategy"],
        int(window["manifest"]["test_year"]),
        "train_core",
    )
    transform_params = fit_stage5_0f_transform_params(
        train_core, profile_key, transform_variant=transform_variant,
        parsed_cache=parsed_cache, cache_key=cache_key)
    X_train = build_stage5_0f_features(
        train_core, profile_key, transform_variant=transform_variant, transform_params=transform_params)
    X_val = build_stage5_0f_features(
        val_stop, profile_key, transform_variant=transform_variant, transform_params=transform_params)
    X_test = build_stage5_0f_features(
        test, profile_key, transform_variant=transform_variant, transform_params=transform_params)

    y_train = train_core[target_col]
    y_val = val_stop[target_col]
    y_test = test[target_col]

    model, val_auc = train_xgb_baseline(X_train, y_train, X_val, y_val, seed=seed)
    train_probs = model.predict(xgb.DMatrix(X_train))
    val_probs = model.predict(xgb.DMatrix(X_val))
    test_probs = model.predict(xgb.DMatrix(X_test))

    train_metrics = compute_metrics(y_train, pd.Series(train_probs))
    val_metrics = compute_metrics(y_val, pd.Series(val_probs))
    test_metrics = compute_metrics(y_test, pd.Series(test_probs))

    return {
        "strategy": window["manifest"]["strategy"],
        "test_year": int(window["manifest"]["test_year"]),
        "profile": profile_key,
        "target": target_col,
        "seed": int(seed),
        "transform_variant": transform_variant,
        "train_core": {k: _safe(v) for k, v in train_metrics.items()},
        "val_stop": {k: _safe(v) for k, v in val_metrics.items()},
        "test": {
            **{k: _safe(v) for k, v in test_metrics.items()},
            "auc_ci": bootstrap_stage5_0f_metric_ci(
                y_test, test_probs, "auc", n_boot=STAGE5_0F_BOOTSTRAP_N, seed=seed),
            "lift_30_ci": bootstrap_stage5_0f_metric_ci(
                y_test, test_probs, "lift_30", n_boot=STAGE5_0F_BOOTSTRAP_N, seed=seed),
        },
        "split_manifest": window["manifest"],
        "val_auc_from_training": _safe(val_auc),
    }


def _stage5_1_metrics_with_ci(y_true: pd.Series, probs: np.ndarray, seed: int) -> dict:
    metrics = compute_metrics(y_true, pd.Series(probs))
    return {
        **{k: _safe(v) for k, v in metrics.items()},
        "auc_ci": bootstrap_stage5_0f_metric_ci(
            y_true, probs, "auc", n_boot=STAGE5_1_BOOTSTRAP_N, seed=seed),
        "lift_30_ci": bootstrap_stage5_0f_metric_ci(
            y_true, probs, "lift_30", n_boot=STAGE5_1_BOOTSTRAP_N, seed=seed),
    }


def evaluate_stage5_1_profile_seed(split: dict, profile_key: str, target_col: str,
                                   seed: int, transform_variant: str = "asinh") -> dict:
    """Train one Stage 5.1 XGBoost model for one profile/target/seed."""
    train_core = split["train_core"]
    val_stop = split["val_stop"]
    diagnostic_holdout = split["diagnostic_holdout"]
    low_n_disclosure = split["low_n_disclosure"]
    transform_params = fit_stage5_1_transform_params(
        train_core, profile_key, transform_variant=transform_variant)

    X_train = build_stage5_1_features(
        train_core, profile_key, transform_variant=transform_variant, transform_params=transform_params)
    X_val = build_stage5_1_features(
        val_stop, profile_key, transform_variant=transform_variant, transform_params=transform_params)
    X_holdout = build_stage5_1_features(
        diagnostic_holdout, profile_key, transform_variant=transform_variant, transform_params=transform_params)
    X_low_n = build_stage5_1_features(
        low_n_disclosure, profile_key, transform_variant=transform_variant, transform_params=transform_params)

    y_train = train_core[target_col]
    y_val = val_stop[target_col]
    y_holdout = diagnostic_holdout[target_col]
    y_low_n = low_n_disclosure[target_col]

    model, val_auc = train_xgb_baseline(X_train, y_train, X_val, y_val, seed=seed)
    train_probs = model.predict(xgb.DMatrix(X_train))
    val_probs = model.predict(xgb.DMatrix(X_val))
    holdout_probs = model.predict(xgb.DMatrix(X_holdout))
    low_n_probs = model.predict(xgb.DMatrix(X_low_n)) if len(low_n_disclosure) else np.asarray([])

    return {
        "profile": profile_key,
        "target": target_col,
        "seed": int(seed),
        "transform_variant": transform_variant,
        "transform_params": transform_params,
        "transform_params_fit_on": "train_core",
        "train_core": {k: _safe(v) for k, v in compute_metrics(y_train, pd.Series(train_probs)).items()},
        "val_stop": _stage5_1_metrics_with_ci(y_val, val_probs, seed),
        "diagnostic_holdout": _stage5_1_metrics_with_ci(y_holdout, holdout_probs, seed),
        "low_n_disclosure": _stage5_1_metrics_with_ci(y_low_n, low_n_probs, seed),
        "yearly_val": compute_yearly_metrics(val_stop, val_probs, target_col=target_col),
        "yearly_diagnostic_holdout": compute_yearly_metrics(
            diagnostic_holdout, holdout_probs, target_col=target_col),
        "split_manifest": split["manifest"],
        "val_auc_from_training": _safe(val_auc),
        "predictions": {
            "val_stop": [float(v) for v in val_probs],
            "diagnostic_holdout": [float(v) for v in holdout_probs],
            "low_n_disclosure": [float(v) for v in low_n_probs],
        },
        "labels": {
            "val_stop": [int(v) for v in y_val.tolist()],
            "diagnostic_holdout": [int(v) for v in y_holdout.tolist()],
            "low_n_disclosure": [int(v) for v in y_low_n.tolist()],
        },
    }


def _median_or_none(values: list) -> float | None:
    clean = [float(v) for v in values if v is not None and np.isfinite(v)]
    if not clean:
        return None
    return float(np.median(clean))


def _min_or_none(values: list) -> float | None:
    clean = [float(v) for v in values if v is not None and np.isfinite(v)]
    return float(np.min(clean)) if clean else None


def _max_or_none(values: list) -> float | None:
    clean = [float(v) for v in values if v is not None and np.isfinite(v)]
    return float(np.max(clean)) if clean else None


def bootstrap_stage5_1_delta_ci(y_true, pred_a, pred_b,
                                n_boot: int = STAGE5_1_BOOTSTRAP_N,
                                seed: int = 42) -> dict:
    """Paired bootstrap CI for AUC(profile_a) - AUC(profile_b)."""
    yt = pd.Series(y_true).reset_index(drop=True)
    pa = np.asarray(pred_a, dtype=float)
    pb = np.asarray(pred_b, dtype=float)
    n = len(yt)
    if n == 0 or yt.nunique() < 2:
        return {"metric": "auc_delta", "n_boot": int(n_boot), "low": None, "median": None, "high": None}

    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        sample_y = yt.iloc[idx].reset_index(drop=True)
        if sample_y.nunique() < 2:
            continue
        try:
            auc_a = roc_auc_score(sample_y, pa[idx])
            auc_b = roc_auc_score(sample_y, pb[idx])
        except ValueError:
            continue
        vals.append(float(auc_a - auc_b))

    if not vals:
        return {"metric": "auc_delta", "n_boot": int(n_boot), "low": None, "median": None, "high": None}

    arr = np.asarray(vals, dtype=float)
    return {
        "metric": "auc_delta",
        "n_boot": int(n_boot),
        "low": float(np.percentile(arr, 2.5)),
        "median": float(np.percentile(arr, 50.0)),
        "high": float(np.percentile(arr, 97.5)),
    }


def _stage5_1_period_summary(runs: list[dict], period_key: str) -> dict:
    aucs = [r[period_key].get("auc") for r in runs]
    lifts = [r[period_key].get("lift_30") for r in runs]
    auc_lows = [r[period_key].get("auc_ci", {}).get("low") for r in runs]
    auc_highs = [r[period_key].get("auc_ci", {}).get("high") for r in runs]
    return {
        "n": runs[0][period_key].get("n") if runs else 0,
        "auc_median": _median_or_none(aucs),
        "auc_seed_min": _min_or_none(aucs),
        "auc_seed_max": _max_or_none(aucs),
        "lift_30_median": _median_or_none(lifts),
        "lift_30_seed_min": _min_or_none(lifts),
        "lift_30_seed_max": _max_or_none(lifts),
        "auc_ci_low": _median_or_none(auc_lows),
        "auc_ci_high": _median_or_none(auc_highs),
    }


def _stage5_1_yearly_summary(runs: list[dict], yearly_key: str) -> dict:
    years = sorted({
        year
        for run in runs
        for year in run.get(yearly_key, {}).keys()
    })
    out = {}
    for year in years:
        aucs = [run.get(yearly_key, {}).get(year, {}).get("auc") for run in runs]
        lifts = [run.get(yearly_key, {}).get(year, {}).get("lift_30") for run in runs]
        out[year] = {
            "auc_median": _median_or_none(aucs),
            "auc_seed_min": _min_or_none(aucs),
            "auc_seed_max": _max_or_none(aucs),
            "lift_30_median": _median_or_none(lifts),
        }
    return out


def summarize_stage5_0f_seed_runs(runs: list[dict]) -> dict:
    """Summarize seed-level Stage 5.0f runs by median."""
    auc_lows = [r["test"].get("auc_ci", {}).get("low") for r in runs]
    auc_highs = [r["test"].get("auc_ci", {}).get("high") for r in runs]
    lift_lows = [r["test"].get("lift_30_ci", {}).get("low") for r in runs]
    lift_highs = [r["test"].get("lift_30_ci", {}).get("high") for r in runs]
    return {
        "n_seed_runs": int(len(runs)),
        "train_core": {
            "auc_median": _median_or_none([r["train_core"].get("auc") for r in runs]),
        },
        "val_stop": {
            "auc_median": _median_or_none([r["val_stop"].get("auc") for r in runs]),
            "lift_30_median": _median_or_none([r["val_stop"].get("lift_30") for r in runs]),
        },
        "test": {
            "n": runs[0]["test"].get("n") if runs else 0,
            "auc_median": _median_or_none([r["test"].get("auc") for r in runs]),
            "lift_30_median": _median_or_none([r["test"].get("lift_30") for r in runs]),
            "auc_ci_low": _median_or_none(auc_lows),
            "auc_ci_high": _median_or_none(auc_highs),
            "lift_30_ci_low": _median_or_none(lift_lows),
            "lift_30_ci_high": _median_or_none(lift_highs),
        },
        "split_manifest": runs[0].get("split_manifest") if runs else None,
    }


def summarize_stage5_1_seed_runs(runs: list[dict]) -> dict:
    """Summarize Stage 5.1 seed-level runs by median and seed spread."""
    return {
        "n_seed_runs": int(len(runs)),
        "train_core": {
            "auc_median": _median_or_none([r["train_core"].get("auc") for r in runs]),
        },
        "val_stop": _stage5_1_period_summary(runs, "val_stop"),
        "diagnostic_holdout": _stage5_1_period_summary(runs, "diagnostic_holdout"),
        "low_n_disclosure": _stage5_1_period_summary(runs, "low_n_disclosure"),
        "yearly_val": _stage5_1_yearly_summary(runs, "yearly_val"),
        "yearly_diagnostic_holdout": _stage5_1_yearly_summary(runs, "yearly_diagnostic_holdout"),
        "split_manifest": runs[0].get("split_manifest") if runs else None,
    }


def _stage5_1_seed_auc_by_profile(raw_runs: list[dict], profile: str,
                                  period_key: str) -> dict[int, float | None]:
    return {
        int(run["seed"]): run[period_key].get("auc")
        for run in raw_runs
        if run["profile"] == profile
    }


def _stage5_1_run_by_profile_seed(raw_runs: list[dict], profile: str) -> dict[int, dict]:
    return {
        int(run["seed"]): run
        for run in raw_runs
        if run["profile"] == profile
    }


def _stage5_1_delta_summary(raw_runs: list[dict], profile: str,
                            baseline_profile: str, period_key: str) -> dict:
    profile_by_seed = _stage5_1_seed_auc_by_profile(raw_runs, profile, period_key)
    baseline_by_seed = _stage5_1_seed_auc_by_profile(raw_runs, baseline_profile, period_key)
    profile_runs = _stage5_1_run_by_profile_seed(raw_runs, profile)
    baseline_runs = _stage5_1_run_by_profile_seed(raw_runs, baseline_profile)
    deltas = []
    ci_lows = []
    ci_highs = []
    signs = []
    for seed, auc in profile_by_seed.items():
        base_auc = baseline_by_seed.get(seed)
        if auc is None or base_auc is None:
            continue
        delta = float(auc - base_auc)
        deltas.append(delta)
        signs.append(1 if delta > 0 else -1 if delta < 0 else 0)
        profile_run = profile_runs.get(seed)
        baseline_run = baseline_runs.get(seed)
        if profile_run and baseline_run:
            ci = bootstrap_stage5_1_delta_ci(
                profile_run["labels"][period_key],
                profile_run["predictions"][period_key],
                baseline_run["predictions"][period_key],
                n_boot=STAGE5_1_BOOTSTRAP_N,
                seed=seed,
            )
            ci_lows.append(ci.get("low"))
            ci_highs.append(ci.get("high"))
    return {
        "baseline_profile": baseline_profile,
        "period": period_key,
        "delta_median": _median_or_none(deltas),
        "delta_seed_min": _min_or_none(deltas),
        "delta_seed_max": _max_or_none(deltas),
        "delta_ci_low": _median_or_none(ci_lows),
        "delta_ci_high": _median_or_none(ci_highs),
        "delta_ci_method": "median_of_per_seed_paired_bootstrap_bounds",
        "positive_seed_count": int(sum(1 for s in signs if s > 0)),
        "negative_seed_count": int(sum(1 for s in signs if s < 0)),
        "zero_seed_count": int(sum(1 for s in signs if s == 0)),
    }


def summarize_stage5_1_target(raw_runs: list[dict], target_col: str) -> dict:
    """Summarize one Stage 5.1 target across profiles and add drop/add deltas."""
    target_runs = [r for r in raw_runs if r["target"] == target_col]
    summary = {}
    for profile in STAGE5_1_PROFILE_KEYS:
        runs = [r for r in target_runs if r["profile"] == profile]
        summary[profile] = summarize_stage5_1_seed_runs(runs)

    for field in STAGE5_1_FIELDS:
        drop_profile = f"drop_{field}"
        add_profile = f"add_{field}"
        if drop_profile in summary:
            summary[drop_profile]["delta_vs_structure_full"] = {
                "val_stop": _stage5_1_delta_summary(target_runs, drop_profile, "structure_full", "val_stop"),
                "diagnostic_holdout": _stage5_1_delta_summary(
                    target_runs, drop_profile, "structure_full", "diagnostic_holdout"),
            }
        if add_profile in summary:
            summary[add_profile]["delta_vs_time_only"] = {
                "val_stop": _stage5_1_delta_summary(target_runs, add_profile, "time_only", "val_stop"),
                "diagnostic_holdout": _stage5_1_delta_summary(
                    target_runs, add_profile, "time_only", "diagnostic_holdout"),
            }
    return summary


def _stage5_0f_get_summary(report: dict, target: str, profile: str,
                           strategy: str, year: int) -> dict | None:
    return (
        report.get("summary", {})
        .get(target, {})
        .get(profile, {})
        .get(strategy, {})
        .get(str(year))
    )


def _stage5_0f_auc(summary: dict | None) -> float | None:
    if not summary:
        return None
    return summary.get("test", {}).get("auc_median")


def _stage5_0f_ci_low(summary: dict | None) -> float | None:
    if not summary:
        return None
    return summary.get("test", {}).get("auc_ci_low")


def _stage5_0f_ci_high(summary: dict | None) -> float | None:
    if not summary:
        return None
    return summary.get("test", {}).get("auc_ci_high")


def _stage5_0f_rolling_fixed_deltas(report: dict, target: str, profile: str) -> list[float]:
    deltas = []
    for year in STAGE5_0F_DECISION_YEARS:
        fixed = _stage5_0f_auc(_stage5_0f_get_summary(report, target, profile, "fixed", year))
        rolling = _stage5_0f_auc(_stage5_0f_get_summary(report, target, profile, "rolling", year))
        if fixed is not None and rolling is not None:
            deltas.append(float(rolling - fixed))
    return deltas


def _stage5_0f_anchored_spearman(report: dict, target: str, profile: str) -> dict:
    from scipy.stats import spearmanr

    years = []
    aucs = []
    for year in STAGE5_0F_DECISION_YEARS:
        summary = _stage5_0f_get_summary(report, target, profile, "anchored", year)
        auc = _stage5_0f_auc(summary)
        if auc is not None:
            years.append(year)
            aucs.append(float(auc))
    if len(years) < 3:
        return {"rho": None, "pvalue": None, "pass": False}
    res = spearmanr(years, aucs)
    rho = float(res.statistic) if np.isfinite(res.statistic) else None
    pvalue = float(res.pvalue) if np.isfinite(res.pvalue) else None
    return {
        "rho": rho,
        "pvalue": pvalue,
        "pass": bool(rho is not None and pvalue is not None and rho > 0 and pvalue < 0.1),
    }


def _stage5_0f_time_only_not_worse(report: dict, target: str) -> bool:
    time_deltas = _stage5_0f_rolling_fixed_deltas(report, target, "time_only")
    fractal_profiles = ["base_raw_plus_time", "structure_only", "all100_relative_price_time"]
    fractal_deltas = []
    for profile in fractal_profiles:
        fractal_deltas.extend(_stage5_0f_rolling_fixed_deltas(report, target, profile))
    if not time_deltas or not fractal_deltas:
        return False
    return float(np.median(time_deltas)) <= float(np.median(fractal_deltas))


def _stage5_0f_all_profiles_low_auc(report: dict, target: str) -> bool:
    for profile in STAGE5_0F_PROFILE_KEYS:
        for strategy in ["fixed", "rolling"]:
            for year in STAGE5_0F_DECISION_YEARS:
                auc = _stage5_0f_auc(_stage5_0f_get_summary(report, target, profile, strategy, year))
                if auc is None or not (0.55 <= auc <= 0.68):
                    return False
    return True


def _stage5_0f_structure_close_to_base(report: dict, target: str, tolerance: float = 0.02) -> bool:
    diffs = []
    for strategy in ["fixed", "rolling"]:
        for year in STAGE5_0F_DECISION_YEARS:
            base = _stage5_0f_auc(_stage5_0f_get_summary(report, target, "base_raw_plus_time", strategy, year))
            structure = _stage5_0f_auc(_stage5_0f_get_summary(report, target, "structure_only", strategy, year))
            if base is not None and structure is not None:
                diffs.append(abs(float(structure - base)))
    return bool(diffs and max(diffs) <= tolerance)


def _stage5_0f_structure_base_deltas(report: dict, target: str) -> dict:
    deltas = {}
    for strategy in ["fixed", "rolling"]:
        deltas[strategy] = {}
        for year in STAGE5_0F_DECISION_YEARS:
            base = _stage5_0f_auc(_stage5_0f_get_summary(report, target, "base_raw_plus_time", strategy, year))
            structure = _stage5_0f_auc(_stage5_0f_get_summary(report, target, "structure_only", strategy, year))
            deltas[strategy][str(year)] = (
                float(structure - base) if base is not None and structure is not None else None
            )
    return deltas


def _stage5_0f_target_verdict(report: dict, target: str) -> dict:
    decisive_improvements = 0
    comparable_years = 0
    all_overlap = True

    for year in STAGE5_0F_DECISION_YEARS:
        fixed = _stage5_0f_get_summary(report, target, "base_raw_plus_time", "fixed", year)
        rolling = _stage5_0f_get_summary(report, target, "base_raw_plus_time", "rolling", year)
        if not fixed or not rolling:
            continue
        f_high = _stage5_0f_ci_high(fixed)
        r_low = _stage5_0f_ci_low(rolling)
        f_auc = _stage5_0f_auc(fixed)
        r_auc = _stage5_0f_auc(rolling)
        if f_auc is not None and r_auc is not None:
            comparable_years += 1
        if f_high is not None and r_low is not None and r_low > f_high:
            decisive_improvements += 1
            all_overlap = False

    anchored = _stage5_0f_anchored_spearman(report, target, "base_raw_plus_time")
    time_only_not_worse = _stage5_0f_time_only_not_worse(report, target)
    all_profiles_low_auc = _stage5_0f_all_profiles_low_auc(report, target)
    structure_close_to_base = _stage5_0f_structure_close_to_base(report, target)

    if decisive_improvements >= 1 and anchored["pass"] and time_only_not_worse:
        verdict = "temporal_decay"
    elif (
        comparable_years == len(STAGE5_0F_DECISION_YEARS)
        and all_overlap
        and all_profiles_low_auc
        and structure_close_to_base
    ):
        verdict = "weak_signal"
    else:
        verdict = "inconclusive"

    return {
        "verdict": verdict,
        "comparable_years": int(comparable_years),
        "rolling_ci_above_fixed_years": int(decisive_improvements),
        "anchored_spearman": anchored,
        "time_only_not_worse_than_fractals": bool(time_only_not_worse),
        "all_profiles_low_auc": bool(all_profiles_low_auc),
        "structure_close_to_base": bool(structure_close_to_base),
        "structure_minus_base_auc": _stage5_0f_structure_base_deltas(report, target),
        "decision_years": list(STAGE5_0F_DECISION_YEARS),
        "low_n_disclosure_year": STAGE5_0F_LOW_N_YEAR,
    }


def stage5_0f_stationarity_decision(report: dict) -> dict:
    target_verdicts = {
        target: _stage5_0f_target_verdict(report, target)
        for target in STAGE5_0F_TARGETS
    }
    unique = {v["verdict"] for v in target_verdicts.values()}
    if len(unique) == 1:
        overall = next(iter(unique))
    else:
        overall = "inconclusive"
    return {
        "status": "DIAGNOSTIC_ONLY",
        "overall_verdict": overall,
        "target_verdicts": target_verdicts,
        "holdout_burned": "2023-2025 used for diagnostic management decision; future confirmatory work needs 2026+ or explicit disclosure.",
    }


def _stage5_1_yearly_drop_signs(target_summary: dict, field: str) -> list[int]:
    return _stage5_1_yearly_drop_signs_for_key(
        target_summary, field, "yearly_diagnostic_holdout", ["2023", "2024", "2025"])


def _stage5_1_yearly_val_drop_signs(target_summary: dict, field: str) -> list[int]:
    return _stage5_1_yearly_drop_signs_for_key(
        target_summary, field, "yearly_val", ["2021", "2022"])


def _stage5_1_yearly_drop_signs_for_key(target_summary: dict, field: str,
                                        yearly_key: str, years: list[str]) -> list[int]:
    drop = target_summary.get(f"drop_{field}", {})
    full = target_summary.get("structure_full", {})
    signs = []
    for year in years:
        drop_auc = drop.get(yearly_key, {}).get(year, {}).get("auc_median")
        full_auc = full.get(yearly_key, {}).get(year, {}).get("auc_median")
        if drop_auc is None or full_auc is None:
            continue
        delta = float(drop_auc - full_auc)
        signs.append(1 if delta > 0 else -1 if delta < 0 else 0)
    return signs


def _stage5_1_field_target_verdict(target_summary: dict, field: str) -> dict:
    drop = target_summary.get(f"drop_{field}", {})
    add = target_summary.get(f"add_{field}", {})
    drop_val = drop.get("delta_vs_structure_full", {}).get("val_stop", {})
    add_val = add.get("delta_vs_time_only", {}).get("val_stop", {}).get("delta_median")
    add_holdout = add.get("delta_vs_time_only", {}).get("diagnostic_holdout", {}).get("delta_median")
    drop_delta = drop_val.get("delta_median")
    drop_ci_low = drop_val.get("delta_ci_low")
    drop_ci_high = drop_val.get("delta_ci_high")
    yearly_signs = _stage5_1_yearly_drop_signs(target_summary, field)
    yearly_val_signs = _stage5_1_yearly_val_drop_signs(target_summary, field)
    yearly_negative = sum(1 for s in yearly_signs if s < 0)
    yearly_positive = sum(1 for s in yearly_signs if s > 0)
    negative_seed_count = int(drop_val.get("negative_seed_count") or 0)
    positive_seed_count = int(drop_val.get("positive_seed_count") or 0)
    useful_ci_or_seed_confirmed = (
        (drop_ci_high is not None and drop_ci_high < 0)
        or negative_seed_count == 3
    )
    noise_ci_or_seed_confirmed = (
        (drop_ci_low is not None and drop_ci_low > 0)
        or positive_seed_count == 3
    )

    useful = (
        drop_delta is not None
        and drop_delta < 0
        and yearly_negative >= 2
        and negative_seed_count >= 2
        and useful_ci_or_seed_confirmed
        and (
            (add_val is not None and add_val > 0)
            or (add_holdout is not None and add_holdout > 0)
        )
    )
    noise = (
        drop_delta is not None
        and drop_delta > 0
        and yearly_positive >= 2
        and positive_seed_count >= 2
        and noise_ci_or_seed_confirmed
        and add_val is not None
        and add_val <= 0
    )

    if useful:
        verdict = "likely_useful"
    elif noise:
        verdict = "likely_noise"
    else:
        verdict = "mixed_or_unclear"

    return {
        "verdict": verdict,
        "drop_val_delta_median": drop_delta,
        "drop_val_delta_ci_low": drop_ci_low,
        "drop_val_delta_ci_high": drop_ci_high,
        "drop_val_negative_seed_count": negative_seed_count,
        "drop_val_positive_seed_count": positive_seed_count,
        "yearly_val_drop_signs_2021_2022": yearly_val_signs,
        "yearly_drop_signs_2023_2025": yearly_signs,
        "add_val_delta_median": add_val,
        "add_holdout_delta_median": add_holdout,
    }


def stage5_1_field_verdicts(report: dict) -> dict:
    """Classify Stage 5.1 fields as diagnostic likely useful/noise/unclear."""
    verdicts = {}
    for field in STAGE5_1_FIELDS:
        per_target = {}
        target_verdicts = []
        for target in STAGE5_1_TARGETS:
            target_summary = report.get("summary", {}).get(target, {})
            target_result = _stage5_1_field_target_verdict(target_summary, field)
            per_target[target] = target_result
            target_verdicts.append(target_result["verdict"])

        if "likely_useful" in target_verdicts and "likely_noise" in target_verdicts:
            overall = "mixed_or_unclear"
        elif "likely_useful" in target_verdicts:
            overall = "likely_useful"
        elif "likely_noise" in target_verdicts:
            overall = "likely_noise"
        else:
            overall = "mixed_or_unclear"

        verdicts[field] = {
            "overall_verdict": overall,
            "targets": per_target,
            "diagnostic_only": True,
        }
    return verdicts


def run_stage5_0f_signal_stationarity(target_splits: dict,
                                      output_path=STAGE5_0F_JSON_REPORT_PATH) -> dict:
    """Run Stage 5.0f XGBoost signal stationarity diagnostics."""
    started_at = time.time()
    total_runs = (
        len(STAGE5_0F_TARGETS)
        * len(STAGE5_0F_PROFILE_KEYS)
        * (6 + 6 + 7)
        * len(STAGE5_0F_SEEDS)
    )
    report = {
        "stage": "5.0f_signal_stationarity",
        "status": "RUNNING",
        "level": "exploratory",
        "holdout_used_for_diagnostic_decision": True,
        "holdout_burned_after_stage": "2023-2025",
        "targets": list(STAGE5_0F_TARGETS),
        "profiles": list(STAGE5_0F_PROFILE_KEYS),
        "seeds": list(STAGE5_0F_SEEDS),
        "strategies": ["rolling", "fixed", "anchored"],
        "raw_runs": [],
        "summary": {},
        "low_n_disclosure": {"year": STAGE5_0F_LOW_N_YEAR},
        "progress": {
            "started_at_unix": started_at,
            "done_runs": 0,
            "total_runs": int(total_runs),
            "last_completed": None,
        },
    }
    parsed_cache = {}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(output_path, report)

    for target_col in STAGE5_0F_TARGETS:
        train_df, val_df, hold_df = target_splits[target_col]
        combined = pd.concat([train_df, val_df, hold_df], ignore_index=True)
        combined = _stage5_0f_with_year(combined)
        report["summary"].setdefault(target_col, {})

        windows = build_stage5_0f_windows(combined, target_col)
        grouped_runs = {}
        for profile_key in STAGE5_0F_PROFILE_KEYS:
            report["summary"][target_col].setdefault(profile_key, {})
            for window in windows:
                strategy = window["manifest"]["strategy"]
                test_year = int(window["manifest"]["test_year"])
                seed_runs = []
                for seed in STAGE5_0F_SEEDS:
                    run = evaluate_stage5_0f_window_seed(
                        window, profile_key=profile_key, target_col=target_col,
                        seed=seed, parsed_cache=parsed_cache)
                    run["elapsed_sec"] = round(time.time() - started_at, 1)
                    seed_runs.append(run)
                    report["raw_runs"].append(run)
                    report["progress"]["done_runs"] += 1
                    report["progress"]["last_completed"] = {
                        "target": target_col,
                        "profile": profile_key,
                        "strategy": strategy,
                        "test_year": test_year,
                        "seed": int(seed),
                        "val_auc": _safe(run["val_stop"].get("auc")),
                        "test_auc": _safe(run["test"].get("auc")),
                        "test_lift_30": _safe(run["test"].get("lift_30")),
                        "elapsed_sec": run["elapsed_sec"],
                    }
                    done_runs = report["progress"]["done_runs"]
                    total = report["progress"]["total_runs"]
                    last = report["progress"]["last_completed"]
                    print(
                        f"[{done_runs}/{total}] "
                        f"{target_col} | {profile_key} | {strategy} | {test_year} | "
                        f"seed={seed} | val_auc={last['val_auc']} | "
                        f"test_auc={last['test_auc']} | lift_30={last['test_lift_30']}"
                    )
                    _write_json_atomic(output_path, report)
                grouped_runs[(profile_key, strategy, test_year)] = seed_runs

        for (profile_key, strategy, test_year), seed_runs in grouped_runs.items():
            report["summary"][target_col].setdefault(profile_key, {}).setdefault(strategy, {})
            report["summary"][target_col][profile_key][strategy][str(test_year)] = (
                summarize_stage5_0f_seed_runs(seed_runs)
            )
            _write_json_atomic(output_path, report)

    report["status"] = "DIAGNOSTIC_ONLY"
    report["decision"] = stage5_0f_stationarity_decision(report)
    report["progress"]["finished_at_unix"] = time.time()
    report["progress"]["elapsed_sec"] = round(report["progress"]["finished_at_unix"] - started_at, 1)
    _write_json_atomic(output_path, report)
    return report


def _stage5_1_public_run(run: dict) -> dict:
    """Return JSON-safe run metadata without arrays used only for local delta CI."""
    return {
        key: value
        for key, value in run.items()
        if key not in {"predictions", "labels"}
    }


def run_stage5_1_structural_field_ablation(target_splits: dict,
                                           output_path=STAGE5_1_JSON_REPORT_PATH) -> dict:
    """Run Stage 5.1 structural fractal field ablation diagnostics."""
    started_at = time.time()
    total_runs = len(STAGE5_1_TARGETS) * len(STAGE5_1_PROFILE_KEYS) * len(STAGE5_1_SEEDS)
    report = {
        "stage": "5.1_structural_field_ablation",
        "status": "RUNNING",
        "level": "exploratory",
        "verdict_scope": "DIAGNOSTIC_ONLY",
        "targets": list(STAGE5_1_TARGETS),
        "fields": list(STAGE5_1_FIELDS),
        "profiles": list(STAGE5_1_PROFILE_KEYS),
        "seeds": list(STAGE5_1_SEEDS),
        "raw_runs": [],
        "summary": {},
        "field_verdicts": {},
        "multiple_testing_context": {
            "diagnostic_only": True,
            "correction_applied": None,
            "note": "No Bonferroni/FDR correction; likely_* labels are preliminary diagnostic categories.",
        },
        "holdout_disclosure": {
            "val_stop": "2021-2022 pooled primary diagnostic validation plus yearly disclosure.",
            "diagnostic_holdout": "2023-2025 already used in Stage 5.0f; disclosure only.",
            "low_n_disclosure": "2026 optional low-N disclosure, not used for verdict.",
        },
        "transform_config": {
            "transform_variant": "asinh",
            "transform_params_fit_on": "train_core",
            "stage5_1_transform_params": {},
            "reason": "Stage 5.1 excludes price/ATR fields; only structural tokens and clock row fields remain.",
        },
        "sanity_checks": {
            "time_only_row_fields": TIME_ONLY_ROW_FIELDS.copy(),
            "excluded_fields": ["price", "price_coord_atr", "price_atr_scaled", "ATR"],
            "expected_model_count": int(total_runs),
            "stage5_0d_no_price_reference": {
                "source": "docs/reports/2026-06-23-stage5_0d-diagnostic-screening.md",
                "sell_val_auc": 0.6693,
                "sell_holdout_auc": 0.6592,
                "comparison_note": "Compare to Stage 5.1 structure_full; not a PASS/FAIL gate.",
            },
            "stage5_1_structure_full_actual": {},
        },
        "progress": {
            "started_at_unix": started_at,
            "done_runs": 0,
            "total_runs": int(total_runs),
            "last_completed": None,
        },
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(output_path, report)

    for target_col in STAGE5_1_TARGETS:
        train_df, val_df, hold_df = target_splits[target_col]
        combined = pd.concat([train_df, val_df, hold_df], ignore_index=True)
        split = build_stage5_1_split(combined, target_col)
        report["summary"].setdefault(target_col, {})

        target_runs = []
        for profile_key in STAGE5_1_PROFILE_KEYS:
            for seed in STAGE5_1_SEEDS:
                run = evaluate_stage5_1_profile_seed(
                    split, profile_key=profile_key, target_col=target_col, seed=seed)
                run["elapsed_sec"] = round(time.time() - started_at, 1)
                target_runs.append(run)
                report["raw_runs"].append(_stage5_1_public_run(run))
                report["progress"]["done_runs"] += 1
                report["progress"]["last_completed"] = {
                    "target": target_col,
                    "profile": profile_key,
                    "seed": int(seed),
                    "val_auc": _safe(run["val_stop"].get("auc")),
                    "holdout_auc": _safe(run["diagnostic_holdout"].get("auc")),
                    "elapsed_sec": run["elapsed_sec"],
                }
                done_runs = report["progress"]["done_runs"]
                total = report["progress"]["total_runs"]
                last = report["progress"]["last_completed"]
                print(
                    f"[{done_runs}/{total}] {target_col} | {profile_key} | "
                    f"seed={seed} | val_auc={last['val_auc']} | "
                    f"holdout_auc={last['holdout_auc']}"
                )
                _write_json_atomic(output_path, report)

        report["summary"][target_col] = summarize_stage5_1_target(target_runs, target_col)
        structure_summary = report["summary"][target_col].get("structure_full", {})
        report["sanity_checks"]["stage5_1_structure_full_actual"][target_col] = {
            "val_auc_median": structure_summary.get("val_stop", {}).get("auc_median"),
            "diagnostic_holdout_auc_median": structure_summary.get("diagnostic_holdout", {}).get("auc_median"),
        }
        _write_json_atomic(output_path, report)

    report["field_verdicts"] = stage5_1_field_verdicts(report)
    report["status"] = "DIAGNOSTIC_ONLY"
    report["progress"]["finished_at_unix"] = time.time()
    report["progress"]["elapsed_sec"] = round(report["progress"]["finished_at_unix"] - started_at, 1)
    _write_json_atomic(output_path, report)
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the benchmark CLI."""
    parser = argparse.ArgumentParser(description="Stage 5.0 Transformer Breach Holdout")
    parser.add_argument("--feature-preflight-only", action="store_true",
                        help="Run Stage 5.0a feature preflight only; no model training")
    parser.add_argument("--transform-comparison-only", action="store_true",
                        help="Run Stage 5.0a transform comparison only; no model training")
    parser.add_argument("--stage5-0b-asinh-rerun", action="store_true",
                        help="Run Stage 5.0b frozen asinh Transformer rerun")
    parser.add_argument("--stage5-0c-cross-target-rerun", action="store_true",
                        help="Stage 5.0c: повторная проверка гипотезы на двух целях")
    parser.add_argument("--stage5-0d-diagnostic-screening", action="store_true",
                        help="Stage 5.0d: диагностический скрининг профилей (XGBoost + Logistic, без Transformer)")
    parser.add_argument("--stage5-0e-small-transformer-check", action="store_true",
                        help="Stage 5.0e: проверка меньшего Transformer против переобучения")
    parser.add_argument("--stage5-0f-signal-stationarity", action="store_true",
                        help="Stage 5.0f: диагностика стационарности H6_off05 breach-сигнала")
    parser.add_argument("--stage5-1-structural-field-ablation", action="store_true",
                        help="Stage 5.1: абляция структурных фрактальных полей H6_off05")
    parser.add_argument("--target", type=str, default=TARGET_COLUMN,
                        help="Target column for Stage 5 training")
    parser.add_argument("--all-profiles-confirmatory", action="store_true",
                        help="Treat all Stage 5.0b profiles as primary candidates")
    parser.add_argument("--no-multiseed-gates", action="store_true",
                        help="Disable automatic multi-seed threshold rules")
    parser.add_argument("--single-seed", action="store_true",
                        help="Use single seed [42] instead of [42, 77, 123]")
    parser.add_argument("--phase", type=str, default=None,
                        help="Run specific phase only (1, 2, 3, 4)")
    parser.add_argument("--skip-phase1", action="store_true",
                        help="Skip Phase 1 (for restart after Phase 1 completion)")
    parser.add_argument("--output", type=str, default=str(JSON_REPORT_PATH),
                        help="Output JSON path")
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    seeds = [42] if args.single_seed else SEEDS
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Seeds: {seeds}")

    # Load data
    print("\n" + "=" * 60)
    print("Loading data...")
    print("=" * 60)
    train_df, val_stop_df, holdout_df = load_splits(target_col=args.target)

    if args.feature_preflight_only:
        report = run_feature_preflight(train_df, val_stop_df, holdout_df)
        print(f"\n{'='*60}")
        print("Stage 5.0a feature preflight completed")
        print(json.dumps(report["artifacts"], indent=2))
        print(f"{'='*60}")
        return

    if args.transform_comparison_only:
        report = run_transform_comparison(train_df, val_stop_df, holdout_df)
        print(f"\n{'='*60}")
        print("Stage 5.0a transform comparison completed")
        print(json.dumps(report["artifacts"], indent=2))
        print(f"{'='*60}")
        return

    # OHLC label verification (mandatory before training)
    print("\n" + "=" * 60)
    print("OHLC label verification...")
    print("=" * 60)
    ohlc_verification = verify_breach_labels_against_ohlc(holdout_df, target_col=args.target)
    print(f"  Matches: {ohlc_verification['n_matches']}/{ohlc_verification['n_checked']}, "
          f"mismatches: {ohlc_verification['n_mismatches']}, status: {ohlc_verification['status']}")

    # Label sanity check
    sanity = label_sanity_check(holdout_df, target_col=args.target)
    print(f"\n  Label sanity check: {sanity['status']}, pos_rate={sanity['positive_rate']:.4f}")

    # XGBoost baselines
    print("\n" + "=" * 60)
    print("Computing XGBoost baselines...")
    print("=" * 60)
    xgb_results = compute_xgb_baselines(train_df, val_stop_df, holdout_df, target_col=args.target)

    if args.stage5_0b_asinh_rerun:
        output_path = STAGE5_0B_JSON_REPORT_PATH
        if args.target != TARGET_COLUMN:
            output_path = REPORTS_DIR / f"stage5_0b_asinh_rerun_{args.target}.json"
        report = run_stage5_0b_asinh_rerun(
            train_df, val_stop_df, holdout_df, seeds[0], device,
            ohlc_verification=ohlc_verification,
            label_sanity=sanity,
            xgb_results=xgb_results,
            output_path=output_path,
            target_col=args.target,
            all_profiles_confirmatory=args.all_profiles_confirmatory,
            use_multiseed_gates=not args.no_multiseed_gates,
        )
        print("\n" + "=" * 60)
        print("Stage 5.0b asinh rerun completed")
        print(json.dumps({"json": str(output_path)}, indent=2))
        print("=" * 60)
        return

    if args.stage5_0c_cross_target_rerun:
        print("\n" + "=" * 60)
        print("Загрузка buy splits для Stage 5.0c...")
        print("=" * 60)
        buy_train, buy_val, buy_hold = load_splits(target_col="buy_stop_broken_H6_off05_flag")
        report = run_stage5_0c_cross_target_rerun(
            sell_splits=(train_df, val_stop_df, holdout_df),
            buy_splits=(buy_train, buy_val, buy_hold),
            seeds=STAGE5_0C_SEEDS,
            device=device,
            output_path=STAGE5_0C_JSON_REPORT_PATH,
        )
        print("\n" + "=" * 60)
        print("Stage 5.0c: повторная проверка на двух целях завершена")
        print(json.dumps({"json": str(STAGE5_0C_JSON_REPORT_PATH)}, indent=2))
        print("=" * 60)
        return

    if args.stage5_0d_diagnostic_screening:
        print("\n" + "=" * 60)
        print("Загрузка buy splits для Stage 5.0d...")
        print("=" * 60)
        buy_train, buy_val, buy_hold = load_splits(target_col="buy_stop_broken_H6_off05_flag")
        report = run_stage5_0d_diagnostic_screening(
            sell_splits=(train_df, val_stop_df, holdout_df),
            buy_splits=(buy_train, buy_val, buy_hold),
            seeds=STAGE5_0D_SEEDS,
            device=device,
            output_path=STAGE5_0D_JSON_REPORT_PATH,
        )
        print("\n" + "=" * 60)
        print("Stage 5.0d: диагностический скрининг завершён")
        print(json.dumps({"json": str(STAGE5_0D_JSON_REPORT_PATH)}, indent=2))
        print("=" * 60)
        return

    if args.stage5_0e_small_transformer_check:
        report = run_stage5_0e_small_transformer_check(
            (train_df, val_stop_df, holdout_df),
            seed=args.seed if hasattr(args, "seed") else 42,
            device=device,
            output_path=STAGE5_0E_JSON_REPORT_PATH,
        )
        print("\n" + "=" * 60)
        print("Stage 5.0e: посмертная проверка переобучения завершена")
        print(json.dumps(report["decision"], indent=2))
        print(json.dumps({"json": str(STAGE5_0E_JSON_REPORT_PATH)}, indent=2))
        print("=" * 60)
        return

    if args.stage5_0f_signal_stationarity:
        print("\n" + "=" * 60)
        print("Загрузка buy splits для Stage 5.0f...")
        print("=" * 60)
        buy_train, buy_val, buy_hold = load_splits(target_col="buy_stop_broken_H6_off05_flag")
        report = run_stage5_0f_signal_stationarity(
            target_splits={
                "sell_stop_broken_H6_off05_flag": (train_df, val_stop_df, holdout_df),
                "buy_stop_broken_H6_off05_flag": (buy_train, buy_val, buy_hold),
            },
            output_path=STAGE5_0F_JSON_REPORT_PATH,
        )
        print("\n" + "=" * 60)
        print("Stage 5.0f: диагностика стационарности завершена")
        print(json.dumps(report["decision"], indent=2))
        print(json.dumps({"json": str(STAGE5_0F_JSON_REPORT_PATH)}, indent=2))
        print("=" * 60)
        return

    if args.stage5_1_structural_field_ablation:
        print("\n" + "=" * 60)
        print("Загрузка buy splits для Stage 5.1...")
        print("=" * 60)
        buy_train, buy_val, buy_hold = load_splits(target_col="buy_stop_broken_H6_off05_flag")
        report = run_stage5_1_structural_field_ablation(
            target_splits={
                "sell_stop_broken_H6_off05_flag": (train_df, val_stop_df, holdout_df),
                "buy_stop_broken_H6_off05_flag": (buy_train, buy_val, buy_hold),
            },
            output_path=STAGE5_1_JSON_REPORT_PATH,
        )
        print("\n" + "=" * 60)
        print("Stage 5.1: абляция структурных фрактальных полей завершена")
        print(json.dumps({
            "json": str(STAGE5_1_JSON_REPORT_PATH),
            "field_verdicts": report.get("field_verdicts", {}),
        }, indent=2))
        print("=" * 60)
        return

    # Init report
    report = {
        "status": "DIAGNOSTIC_RERUN_NORMALIZED",
        "previous_run_status": "DIAGNOSTIC_FAIL_WITH_PREPROCESSING_BUG",
        "diagnostic_preprocessing_bug": {
            "description": (
                "Первоначальный прогон Stage 5.0 использовал сырые признаки без StandardScaler. "
                "Цена золота (сотни/тысячи) доминировала над остальными признаками (0..1) в attention-механизме Transformer. "
                "Исправлено: раздельный StandardScaler для token-признаков (fit на валидных позициях train) и row-признаков. "
                "Padding остаётся нулём. Добавлены relative_price диагностические профили."
            ),
            "fix_applied": True,
            "original_run": "2026-06-17 (no normalization)",
            "rerun": "2026-06-17 (with normalization)",
        },
        "normalization_config": {
            "method": "StandardScaler",
            "token_scaler_fit_on": "train valid positions only (mask=True)",
            "row_scaler_fit_on": "all train rows",
            "padding": "kept as zero, not transformed",
            "apply_to": "train, val_stop, holdout",
            "relative_price_profiles": "diagnostic ablation: price_i → (price_i - f0_price) / ATR, executed in Phase 2 as DIAGNOSTIC_ONLY",
            "phase2_diag_profiles": [
                "all100_base10_relative_price_time",
                "nearest40_base10_relative_price_time",
                "corridor_10atr_base10_relative_price_time",
            ],
        },
        "config": {
            "primary_profile": "all100_base10_time",
            "target": TARGET_COLUMN,
            "seeds": seeds,
            "d_model": D_MODEL,
            "nhead": NHEAD,
            "dim_feedforward": DIM_FEEDFORWARD,
            "max_epochs": MAX_EPOCHS,
            "early_stopping_patience": EARLY_STOPPING_PATIENCE,
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "device": str(device),
            "split": {
                "train_max_year": TRAIN_MAX_YEAR,
                "val_stop_years": sorted(VAL_STOP_YEARS),
                "holdout_min_year": HOLDOUT_MIN_YEAR,
            },
        },
        "primary_profile": {
            "name": "all100_base10_time",
            "gate_applies_here": True,
            "target": TARGET_COLUMN,
        },
        "split": {
            "train": {"n_rows": len(train_df), "years": sorted(map(int, train_df["_year"].unique()))},
            "val_stop": {"n_rows": len(val_stop_df), "years": sorted(map(int, val_stop_df["_year"].unique()))},
            "holdout": {"n_rows": len(holdout_df), "years": sorted(map(int, holdout_df["_year"].unique()))},
        },
        "label_sanity_check": sanity,
        "ohlc_label_verification": ohlc_verification,
        "legacy_holdout_disclosure": (
            "2023-2026 was used as diagnostic holdout in Stage 4.6/walk-forward. "
            "It is not a clean future test for manual tuning."
        ),
        "legacy_xgb_reference": {
            "note": "Stage 4.2 result (train <=2016, val 2019-2022). Not for gate comparison — split differs.",
            "stage": "Stage 4.2",
            "train_max_year": 2016,
            "auc": 0.6674,
            "pf": 1.015,
        },
        "baselines": xgb_results,
        "transformer_results": {},
        "corridor_stats": {},
        "diagnostic_profile_ranking": {"status": "DIAGNOSTIC_ONLY"},
        "interpretation_guards": {
            "holdout_is_diagnostic_not_clean_test": True,
            "primary_profile_only_for_gate": True,
            "other_profiles_ranking_is_diagnostic_only": True,
            "no_trading_winner_declared": True,
            "walk_forward_not_run_transformer_fail": True,
        },
    }

    # Phase 1
    if not args.skip_phase1 and (args.phase is None or args.phase == "1"):
        seed = seeds[0]
        run_phase1(train_df, val_stop_df, holdout_df, seed, device, report)

        # Phase 1 stop condition
        primary_results = report["transformer_results"].get("all100_base10_time", [])
        if primary_results:
            t_auc = primary_results[0].get("val", {}).get("auc")
            xgb_auc = xgb_results.get("base_raw_plus_time", {}).get("val_auc", 0.0)
            if t_auc is not None and xgb_auc is not None:
                gap = float(t_auc) - float(xgb_auc)
                report["phase1_stop_check"] = {
                    "transformer_val_auc": float(t_auc),
                    "xgb_val_auc": float(xgb_auc),
                    "gap": gap,
                    "threshold": PHASE1_STOP_GAP,
                }
                if gap < -PHASE1_STOP_GAP:
                    print(f"\n  PHASE 1 HALTED: Transformer val AUC {t_auc:.4f} trails XGBoost {xgb_auc:.4f} by {gap:.4f} (threshold {PHASE1_STOP_GAP})")
                    report["status"] = "halted_phase1"
                    report["halt_reason"] = f"Transformer val AUC trails XGBoost by {gap:.4f} > {PHASE1_STOP_GAP}"
                else:
                    report["status"] = "phase1_complete"
            else:
                report["status"] = "phase1_complete"
        else:
            report["status"] = "phase1_complete"
    else:
        report["status"] = "phase1_skipped"

    # Phase 2 (conditional: only if Phase 1 not halted)
    if args.phase is None or args.phase == "2":
        if report.get("status") in ("phase1_complete", "phase1_skipped", "halted_phase1"):
            if report.get("status") != "halted_phase1":
                seed = seeds[0]
                run_phase2(train_df, val_stop_df, holdout_df, seed, device, report)
                report["status"] = "phase2_complete"

    # Phase 3 (conditional: only if corridor_10atr promising)
    if args.phase is None or args.phase == "3":
        if report.get("status") in ("phase2_complete",):
            corridor_results = report["transformer_results"].get("corridor_10atr_base10_time", [])
            if corridor_results and corridor_results[0].get("val", {}).get("auc", 0) > 0.65:
                seed = seeds[0]
                run_phase3(train_df, val_stop_df, holdout_df, seed, device, report)
            report["status"] = "phase3_complete"

    # Phase 4 (conditional: only if clear benefit)
    if args.phase is None or args.phase == "4":
        if report.get("status") in ("phase2_complete", "phase3_complete"):
            primary_results = report["transformer_results"].get("all100_base10_time", [])
            if primary_results:
                t_auc = primary_results[0].get("val", {}).get("auc")
                xgb_auc = xgb_results.get("base_raw_plus_time", {}).get("val_auc", 0.0)
                if t_auc is not None and xgb_auc is not None and float(t_auc) > float(xgb_auc):
                    seed = seeds[0]
                    run_phase4(train_df, val_stop_df, holdout_df, seed, device, report)
            report["status"] = "completed"

    # Gate verdict
    apply_holdout_gate(report)

    # Final status: set from gate verdict
    gate_v = report.get("holdout_gate", [])
    if gate_v and isinstance(gate_v, list) and len(gate_v) > 0:
        verdict = gate_v[0].get("verdict", "UNKNOWN")
        report["execution_completed"] = True
        report["verdict"] = f"MODEL_{verdict}"
        if verdict == "PASS":
            report["status"] = "DIAGNOSTIC_RERUN_PASS"
        else:
            report["status"] = "DIAGNOSTIC_RERUN_FAIL"
    else:
        report["execution_completed"] = True
        report["verdict"] = "MODEL_NO_RESULTS"

    # Save JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"Report saved: {output_path}")
    print(f"Holdout gate: {json.dumps(report.get('holdout_gate', 'N/A'), indent=2)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
