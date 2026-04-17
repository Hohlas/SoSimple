# =============================================================================
# Файл: API/generate_signals.py
# Назначение: Генерация CSV с предрассчитанными ML-сигналами для MT4 Strategy Tester
#            и research-only export для entry_path_v1
# Язык: Python 3.11+
# Создан: 2026-03-20
# Зависимости:
#   Входные данные:
#     - ML/checkpoints/transformer_updn_best.pt
#     - ML/reports/optuna_best_params_transformer_regression_updn.json
#     - DATA/Nero_{train,validation,test}_labeled.csv
#   Выходные данные:
#     - MT/MQL4/Files/ml_signals.csv
#     - ML/reports/<prefix>_{validation,test}_predictions.csv
# Внешние зависимости:
#   - torch>=2.0, numpy>=1.24, pandas>=2.0
# Использование:
#   python -m API.generate_signals
#   python -m API.generate_signals --horizon 24 --theta 3.0
#   python -m API.generate_signals --conformal
# Примечания:
#   - time в CSV совпадает с Time[bar] в MT4 (формат "YYYY.MM.DD HH:MM")
#   - signal: 1 (BUY), -1 (SELL), 0 (FLAT)
#   - Файл сортируется по time для бинарного поиска в MQL4
#   - Для Triple Barrier probabilities сначала калибруются на validation-only
# =============================================================================

"""
Генерация CSV с ML-сигналами для MT4 и research-only export для entry_path_v1.

Загружает обученную модель, прогоняет все три датасета (train, validation, test),
применяет порог θ и пишет результат в MQL4/Files/ml_signals.csv.
Для entry_path_v1 вместо MT4 CSV формирует validation/test prediction exports.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ML.data_loader import (
    create_data_loaders, create_test_loader,
    CSV_SEP, TRAIN_FILE, VAL_FILE, TEST_FILE,
    UPDN_REGRESSION_TARGET, UPDN_TARGETS,
    TB_TARGET, TB_TARGET_NAMES,
    TRAILING_STOP_TARGET,
    TRAILING_STOP_TARGET_COLUMNS,
    task_checkpoint_suffix,
)
from ML.entry_path_task import (
    ENTRY_PATH_MODEL_NAMES,
    ENTRY_PATH_TARGET,
    ENTRY_PATH_V1_FEATURE_COLUMNS,
    build_entry_path_export_frame,
    build_entry_path_model,
)
from ML.take_skip_trailing_stop_task import (
    TAKE_SKIP_TRAILING_STOP_TARGET,
    TAKE_SKIP_TRUE_PNL_COLUMNS,
    build_take_skip_export_frame,
)
from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    build_trailing_stop_quantile_export_frame,
)
from ML.trailing_stop_target_task import build_trailing_stop_export_frame
from ML.trailing_stop_target_task import validate_trailing_stop_prediction_shape
from ML.models import get_model
from ML.models.trailing_stop_target_quantile_transformer import TrailingStopTargetQuantileTransformer
from ML.tb_probability_calibration import (
    apply_tb_probability_calibration,
    load_tb_probability_calibrator,
)
from ML.tb_signal_logic import tb_proba_to_signals
from ML.utils import set_seed, get_device


# ─── Пути ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINTS_DIR = PROJECT_ROOT / 'ML' / 'checkpoints'
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'
OUTPUT_DIR = PROJECT_ROOT / 'MT' / 'MQL4' / 'Files'

# Дефолтные параметры (transformer_updn, Profit Factor 4.5 на Test)
DEFAULT_MODEL = 'transformer'
DEFAULT_TASK = 'regression_updn'
DEFAULT_HORIZON = 12
DEFAULT_THETA = 2.665
DEFAULT_OPTUNA_JSON = str(REPORTS_DIR / 'optuna_best_params_transformer_regression_updn.json')
RESEARCH_EXPORT_TASKS = {
    ENTRY_PATH_TARGET,
    TRAILING_STOP_TARGET,
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    TAKE_SKIP_TRAILING_STOP_TARGET,
}


def build_trailing_stop_target_quantile_model(model_kwargs: dict | None = None) -> TrailingStopTargetQuantileTransformer:
    return TrailingStopTargetQuantileTransformer(**(model_kwargs or {}))


def resolve_optuna_json(task: str, optuna_json: str | None) -> str | None:
    if task in {TRAILING_STOP_TARGET, TRAILING_STOP_TARGET_QUANTILE_TARGET, TAKE_SKIP_TRAILING_STOP_TARGET}:
        if not optuna_json:
            return None
        if Path(optuna_json) == Path(DEFAULT_OPTUNA_JSON):
            return None
        return optuna_json if Path(optuna_json).exists() else None
    if optuna_json is None:
        return DEFAULT_OPTUNA_JSON
    return optuna_json if Path(optuna_json).exists() else None


def has_entry_path_ground_truth(df: pd.DataFrame) -> bool:
    required = {
        'ret_6_dir_atr',
        'ret_12_dir_atr',
        'ret_24_dir_atr',
        'fav_6_atr',
        'adv_6_atr',
        'fav_12_atr',
        'adv_12_atr',
        'fav_24_atr',
        'adv_24_atr',
        'path_6_class',
    }
    return required.issubset(df.columns)


# ═══════════════════════════════════════════════════════════════════════════════
# ИНФЕРЕНС
# ═══════════════════════════════════════════════════════════════════════════════

@torch.no_grad()
def run_inference(
    model: torch.nn.Module,
    loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> np.ndarray:
    """Прогон модели через DataLoader, сбор предсказаний."""
    model.eval()
    all_preds = []

    for X_batch, _y_batch, mask_batch in loader:
        X_batch = X_batch.to(device)
        mask_batch = mask_batch.to(device)
        preds = model(X_batch, mask=mask_batch).cpu().numpy()
        if preds.ndim > 1 and preds.shape[-1] == 1:
            preds = preds.squeeze(-1)
        all_preds.append(preds)

    return np.concatenate(all_preds)


def preds_to_signals(
    y_pred: np.ndarray,
    horizon: int,
    theta: float,
    conformal_quantiles: dict | None = None,
) -> np.ndarray:
    """
    Конвертация предсказаний updn в торговые сигналы.

    Returns:
        signals: np.ndarray of {-1, 0, 1}
    """
    idx_map = {3: 0, 6: 2, 12: 4, 24: 6, 48: 8}
    idx = idx_map[horizon]

    pred_up = y_pred[:, idx]
    pred_dn = y_pred[:, idx + 1]

    ratio_up = pred_up / (pred_dn + 1e-6)
    ratio_dn = pred_dn / (pred_up + 1e-6)

    signals = np.zeros(len(y_pred), dtype=int)
    signals[ratio_up > theta] = 1    # BUY
    signals[ratio_dn > theta] = -1   # SELL

    if conformal_quantiles:
        q_up = conformal_quantiles[UPDN_TARGETS[idx]]
        q_dn = conformal_quantiles[UPDN_TARGETS[idx + 1]]
        signals[(signals == 1) & (pred_up < q_up)] = 0
        signals[(signals == -1) & (pred_dn < q_dn)] = 0

    return signals


# ═══════════════════════════════════════════════════════════════════════════════
# TRIPLE BARRIER
# ═══════════════════════════════════════════════════════════════════════════════

def tb_preds_to_signals(
    y_pred_logits: np.ndarray,
    theta: float,
    min_ev: float = 0.0,
) -> pd.DataFrame:
    """
    Convert 12 TB logits to best signal per row.

    For each row: sigmoid → filter P>theta → pick max EV.
    EV = P * TP - (1-P) * SL. Conflict BUY+SELL: max EV wins.
    """
    proba = 1.0 / (1.0 + np.exp(-y_pred_logits))
    df = tb_proba_to_signals(proba, theta=theta, min_ev=min_ev, target_names=TB_TARGET_NAMES)
    return df[['signal', 'sl_atr', 'tp_atr', 'prob', 'ev']]


def generate_tb_signals(
    model_name: str = DEFAULT_MODEL,
    theta: float = 0.6,
    min_ev: float = 0.0,
    optuna_json: str | None = None,
    seed: int = 42,
):
    """Generate ml_signals_tb.csv for Triple Barrier task."""
    set_seed(seed)
    device = get_device()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'═' * 60}")
    print(f"  GENERATE TRIPLE BARRIER SIGNALS FOR MT4")
    print(f"{'═' * 60}")

    ckpt_path = CHECKPOINTS_DIR / f'{model_name}_tb_best.pt'
    calibrator_path = REPORTS_DIR / 'tb_probability_calibrator.joblib'
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Чекпоинт не найден: {ckpt_path}")
    if not calibrator_path.exists():
        raise FileNotFoundError(
            f"Калибратор вероятностей не найден: {calibrator_path}\n"
            f"Сначала заново обучите TB-модель: python -m ML.train --task triple_barrier"
        )

    print(f"  📥 Чекпоинт: {ckpt_path.name}")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    calibrator_bundle = load_tb_probability_calibrator(calibrator_path)

    ckpt_model_name = ckpt.get('model_name', model_name)
    num_classes = ckpt.get('num_classes', len(TB_TARGET_NAMES))
    model_kwargs = ckpt.get('model_kwargs', {})

    if optuna_json and Path(optuna_json).exists():
        with open(optuna_json, 'r', encoding='utf-8') as f:
            optuna_data = json.load(f)
        best_params = optuna_data.get('best_params', {})
        for k in ['hidden_size', 'num_layers', 'dropout', 'input_features']:
            if k in best_params:
                model_kwargs[k] = best_params[k]

    seq_len = model_kwargs.get('seq_len', 20)

    model = get_model(ckpt_model_name, num_classes=num_classes, **model_kwargs)
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    model.eval()
    print(f"  ✅ Модель {ckpt_model_name} загружена (seq_len={seq_len})")
    print(f"  📈 Порог (θ): {theta}")
    print(f"  🚫 Min EV: {min_ev}")
    print(f"  🛡️  Калибратор: {calibrator_path.name}")

    all_results = []

    # Train + Validation
    print(f"\n{'─' * 60}")
    print(f"  🔮 Обработка train + validation...")
    train_loader, val_loader, _ = create_data_loaders(
        batch_size=256, target=TB_TARGET,
        use_scaler=False, seq_len=seq_len,
        num_workers=0,
    )

    for split_name, loader, csv_path in [
        ('train', train_loader, TRAIN_FILE),
        ('validation', val_loader, VAL_FILE),
    ]:
        df_meta = pd.read_csv(csv_path, sep=CSV_SEP, usecols=['time'], low_memory=False)
        times = df_meta['time'].values

        y_pred_logits = run_inference(model, loader, device)
        print(f"    {split_name}: {len(y_pred_logits)} предсказаний")
        assert len(y_pred_logits) == len(times)

        y_pred_proba = 1.0 / (1.0 + np.exp(-y_pred_logits))
        y_pred_proba = apply_tb_probability_calibration(y_pred_proba, calibrator_bundle)

        df_signals = tb_proba_to_signals(
            y_pred_proba,
            theta=theta,
            min_ev=min_ev,
            target_names=TB_TARGET_NAMES,
        )[['signal', 'sl_atr', 'tp_atr', 'prob', 'ev']]
        df_signals.insert(0, 'time', times)

        buy_count = (df_signals['signal'] == 1).sum()
        sell_count = (df_signals['signal'] == -1).sum()
        print(f"    {split_name}: BUY={buy_count}, SELL={sell_count}, FLAT={len(df_signals)-buy_count-sell_count}")
        all_results.append(df_signals)

    # Test
    print(f"\n{'─' * 60}")
    print(f"  🔮 Обработка test...")
    test_loader = create_test_loader(batch_size=256, target=TB_TARGET, seq_len=seq_len, num_workers=0)
    df_meta = pd.read_csv(TEST_FILE, sep=CSV_SEP, usecols=['time'], low_memory=False)
    times = df_meta['time'].values

    y_pred_logits = run_inference(model, test_loader, device)
    print(f"    test: {len(y_pred_logits)} предсказаний")
    assert len(y_pred_logits) == len(times)

    y_pred_proba = 1.0 / (1.0 + np.exp(-y_pred_logits))
    y_pred_proba = apply_tb_probability_calibration(y_pred_proba, calibrator_bundle)

    df_signals = tb_proba_to_signals(
        y_pred_proba,
        theta=theta,
        min_ev=min_ev,
        target_names=TB_TARGET_NAMES,
    )[['signal', 'sl_atr', 'tp_atr', 'prob', 'ev']]
    df_signals.insert(0, 'time', times)

    buy_count = (df_signals['signal'] == 1).sum()
    sell_count = (df_signals['signal'] == -1).sum()
    print(f"    test: BUY={buy_count}, SELL={sell_count}, FLAT={len(df_signals)-buy_count-sell_count}")
    all_results.append(df_signals)

    # Combine and write
    df_all = pd.concat(all_results, ignore_index=True)
    df_all.sort_values('time', inplace=True)
    df_all.drop_duplicates(subset='time', keep='last', inplace=True)

    output_path = OUTPUT_DIR / 'ml_signals_tb.csv'
    df_all.to_csv(output_path, sep=';', index=False)

    print(f"\n{'═' * 60}")
    print(f"  ✅ Записано {len(df_all)} строк в {output_path}")
    print(f"  📅 Диапазон: {df_all['time'].iloc[0]} — {df_all['time'].iloc[-1]}")

    total_buy = (df_all['signal'] == 1).sum()
    total_sell = (df_all['signal'] == -1).sum()
    total_flat = (df_all['signal'] == 0).sum()
    print(f"  📊 Итого: BUY={total_buy}, SELL={total_sell}, FLAT={total_flat}")
    print(f"{'═' * 60}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def generate_signals(
    model_name: str = DEFAULT_MODEL,
    task: str = DEFAULT_TASK,
    horizon: int = DEFAULT_HORIZON,
    theta: float = DEFAULT_THETA,
    optuna_json: str | None = DEFAULT_OPTUNA_JSON,
    seed: int = 42,
    conformal: bool = False,
    research_out_prefix: str = '',
    seq_len_override: int | None = None,
):
    """Полный pipeline: загрузка модели → инференс → запись CSV."""

    set_seed(seed)
    device = get_device()
    if task != ENTRY_PATH_TARGET:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Conformal Prediction (опционально) ────────────────────────────────────
    conformal_quantiles = None
    if conformal:
        cp_path = PROJECT_ROOT / 'ML' / 'conformal' / 'conformal_quantiles.json'
        if not cp_path.exists():
            raise FileNotFoundError(
                f"Conformal quantiles не найдены: {cp_path}\n"
                f"Сначала запустите калибровку: python -m ML.conformal"
            )
        with open(cp_path, 'r', encoding='utf-8') as f:
            cp_data = json.load(f)
        conformal_quantiles = cp_data['quantiles']

    print(f"\n{'═' * 60}")
    print(f"  GENERATE ML SIGNALS FOR MT4")
    if conformal:
        print(f"  🛡️  Conformal Prediction: ON (alpha={cp_data['alpha']})")
    print(f"{'═' * 60}")

    effective_optuna_json = resolve_optuna_json(task, optuna_json)

    # ── Загрузка чекпоинта ───────────────────────────────────────────────────
    suffix = task_checkpoint_suffix(task)
    ckpt_path = CHECKPOINTS_DIR / f'{model_name}{suffix}_best.pt'

    if not ckpt_path.exists():
        raise FileNotFoundError(f"Чекпоинт не найден: {ckpt_path}")

    print(f"  📥 Чекпоинт: {ckpt_path.name}")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)

    ckpt_model_name = ckpt.get('model_name', model_name)
    num_classes = ckpt.get('num_classes', 1)
    seq_len = int(seq_len_override if seq_len_override is not None else ckpt.get('seq_len', 20))
    model_kwargs = ckpt.get('model_kwargs', {})

    # Загрузка параметров Optuna
    if task != ENTRY_PATH_TARGET and effective_optuna_json:
        with open(effective_optuna_json, 'r', encoding='utf-8') as f:
            optuna_data = json.load(f)
        best_params = optuna_data.get('best_params', {})
        for k in ['hidden_size', 'num_layers', 'dropout', 'input_features']:
            if k in best_params:
                model_kwargs[k] = best_params[k]
        print(f"  📥 Optuna параметры из {Path(effective_optuna_json).name}")

    if task == ENTRY_PATH_TARGET:
        model_kwargs.setdefault('engineered_feature_dim', len(ENTRY_PATH_V1_FEATURE_COLUMNS))
        entry_model_name = ckpt_model_name if ckpt_model_name in ENTRY_PATH_MODEL_NAMES else 'transformer'
        model = build_entry_path_model(entry_model_name, model_kwargs)
    elif task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
        model = build_trailing_stop_target_quantile_model(model_kwargs)
    else:
        model = get_model(ckpt_model_name, num_classes=num_classes, **model_kwargs)
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    model.eval()
    print(f"  ✅ Модель {ckpt_model_name} загружена (seq_len={seq_len})")
    print(f"  📈 Горизонт: {horizon}H, Порог (θ): {theta}")

    if task == ENTRY_PATH_TARGET:
        if not research_out_prefix:
            raise ValueError('Для entry_path_v1 нужен --research-out-prefix; MT4 CSV пока не выпускается')

        prefix_path = Path(research_out_prefix)
        prefix_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"  🔬 Research export prefix: {prefix_path}")
        _train_loader, val_loader, _scaler = create_data_loaders(
            batch_size=256,
            target=ENTRY_PATH_TARGET,
            use_scaler=False,
            seq_len=seq_len,
            num_workers=0,
        )
        test_loader = create_test_loader(
            batch_size=256,
            target=ENTRY_PATH_TARGET,
            seq_len=seq_len,
            num_workers=0,
        )

        for split_name, loader, csv_path in [
            ('validation', val_loader, VAL_FILE),
            ('test', test_loader, TEST_FILE),
        ]:
            df_full = pd.read_csv(csv_path, sep=CSV_SEP, low_memory=False)
            df_meta = df_full[['time', 'signal']].copy()
            include_truth = has_entry_path_ground_truth(df_full)
            all_ret = []
            all_path_reg = []
            all_path_cls = []
            all_true_reg = []
            all_true_cls = []

            with torch.no_grad():
                for X_batch, engineered_batch, y_reg_batch, y_cls_batch, mask_batch, _signal_batch in loader:
                    outputs = model(
                        X_batch.to(device),
                        engineered_batch.to(device),
                        mask=mask_batch.to(device),
                    )
                    all_ret.append(outputs['ret'].cpu().numpy())
                    all_path_reg.append(outputs['path_reg'].cpu().numpy())
                    all_path_cls.append(torch.softmax(outputs['path_cls'], dim=1).cpu().numpy())
                    all_true_reg.append(y_reg_batch.numpy())
                    all_true_cls.append(y_cls_batch.numpy())

            export_kwargs = {
                'times': df_meta['time'].values,
                'signals': df_meta['signal'].values.astype(int),
                'pred_ret': np.concatenate(all_ret),
                'pred_path_reg': np.concatenate(all_path_reg),
                'pred_path_cls': np.concatenate(all_path_cls),
            }
            if include_truth:
                export_kwargs['true_reg'] = np.concatenate(all_true_reg)
                export_kwargs['true_cls'] = np.concatenate(all_true_cls)

            export = build_entry_path_export_frame(**export_kwargs)
            output_path = prefix_path.parent / f'{prefix_path.name}_{split_name}_predictions.csv'
            export.to_csv(output_path, sep=';', index=False)
            print(f"  ✅ {split_name}: {len(export)} строк -> {output_path}")
            if not include_truth:
                print(f"  ⚠ {split_name}: true entry_path_v1 columns not found; export written without true_* columns.")

        print(f"{'═' * 60}\n")
        return

    if task == TAKE_SKIP_TRAILING_STOP_TARGET:
        if not research_out_prefix:
            raise ValueError('Для take_skip_trailing_stop_v1 нужен --research-out-prefix')

        prefix_path = Path(research_out_prefix)
        prefix_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"  🔬 Research export prefix: {prefix_path}")
        _train_loader, val_loader, _scaler = create_data_loaders(
            batch_size=256,
            target=TAKE_SKIP_TRAILING_STOP_TARGET,
            use_scaler=False,
            seq_len=seq_len,
            num_workers=0,
        )
        test_loader = create_test_loader(
            batch_size=256,
            target=TAKE_SKIP_TRAILING_STOP_TARGET,
            seq_len=seq_len,
            num_workers=0,
        )

        for split_name, loader, csv_path in [
            ('validation', val_loader, VAL_FILE),
            ('test', test_loader, TEST_FILE),
        ]:
            df_full = pd.read_csv(csv_path, sep=CSV_SEP, low_memory=False)
            true_pnl = df_full[TAKE_SKIP_TRUE_PNL_COLUMNS].values.astype(np.float32)
            all_prob = []
            all_true = []

            with torch.no_grad():
                for X_batch, y_batch, mask_batch in loader:
                    logits = model(X_batch.to(device), mask=mask_batch.to(device))
                    all_prob.append(torch.sigmoid(logits).cpu().numpy())
                    all_true.append(y_batch.numpy())

            pred_prob = np.concatenate(all_prob)
            true_label = np.concatenate(all_true).astype(np.float32)
            export = build_take_skip_export_frame(
                times=df_full['time'].values,
                signals=df_full['signal'].values.astype(int),
                pred_prob=pred_prob,
                true_label=true_label,
                true_pnl=true_pnl,
            )
            output_path = prefix_path.parent / f'{prefix_path.name}_{split_name}_predictions.csv'
            export.to_csv(output_path, sep=';', index=False)
            print(f"  ✅ {split_name}: {len(export)} строк -> {output_path}")

        print(f"{'═' * 60}\n")
        return

    if task == TRAILING_STOP_TARGET:
        if not research_out_prefix:
            raise ValueError('Для trailing_stop_target_v1 нужен --research-out-prefix')

        prefix_path = Path(research_out_prefix)
        prefix_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"  🔬 Research export prefix: {prefix_path}")
        _train_loader, val_loader, _scaler = create_data_loaders(
            batch_size=256,
            target=TRAILING_STOP_TARGET,
            use_scaler=False,
            seq_len=seq_len,
            num_workers=0,
        )
        test_loader = create_test_loader(
            batch_size=256,
            target=TRAILING_STOP_TARGET,
            seq_len=seq_len,
            num_workers=0,
        )

        for split_name, loader, csv_path in [
            ('validation', val_loader, VAL_FILE),
            ('test', test_loader, TEST_FILE),
        ]:
            df_full = pd.read_csv(csv_path, sep=CSV_SEP, low_memory=False)
            y_true = df_full[TRAILING_STOP_TARGET_COLUMNS].values.astype(np.float32)
            all_preds = []

            with torch.no_grad():
                for X_batch, y_batch, mask_batch in loader:
                    preds = model(X_batch.to(device), mask=mask_batch.to(device)).cpu().numpy()
                    all_preds.append(preds)

            pred = np.concatenate(all_preds)
            validate_trailing_stop_prediction_shape(pred, context='predictions')
            export = build_trailing_stop_export_frame(
                times=df_full['time'].values,
                signals=df_full['signal'].values.astype(int),
                pred=pred,
                true=y_true,
            )
            output_path = prefix_path.parent / f'{prefix_path.name}_{split_name}_predictions.csv'
            export.to_csv(output_path, sep=';', index=False)
            print(f"  ✅ {split_name}: {len(export)} строк -> {output_path}")

        print(f"{'═' * 60}\n")
        return

    if task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
        if not research_out_prefix:
            raise ValueError('Для trailing_stop_target_quantile_v1 нужен --research-out-prefix')

        prefix_path = Path(research_out_prefix)
        prefix_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"  🔬 Research export prefix: {prefix_path}")
        _train_loader, val_loader, _scaler = create_data_loaders(
            batch_size=256,
            target=TRAILING_STOP_TARGET_QUANTILE_TARGET,
            use_scaler=False,
            seq_len=seq_len,
            num_workers=0,
        )
        test_loader = create_test_loader(
            batch_size=256,
            target=TRAILING_STOP_TARGET_QUANTILE_TARGET,
            seq_len=seq_len,
            num_workers=0,
        )

        for split_name, loader, csv_path in [
            ('validation', val_loader, VAL_FILE),
            ('test', test_loader, TEST_FILE),
        ]:
            df_full = pd.read_csv(csv_path, sep=CSV_SEP, low_memory=False)
            all_q10 = []
            all_q50 = []
            all_q90 = []

            with torch.no_grad():
                for X_batch, _y_batch, mask_batch in loader:
                    outputs = model(X_batch.to(device), mask=mask_batch.to(device))
                    all_q10.append(outputs['q10'].cpu().numpy())
                    all_q50.append(outputs['q50'].cpu().numpy())
                    all_q90.append(outputs['q90'].cpu().numpy())

            export = build_trailing_stop_quantile_export_frame(
                times=df_full['time'].values,
                signals=df_full['signal'].values.astype(int),
                pred_q10=np.concatenate(all_q10),
                pred_q50=np.concatenate(all_q50),
                pred_q90=np.concatenate(all_q90),
                true=df_full['trail_48_pnl_atr_x3'].values.astype(np.float32).reshape(-1, 1),
            )
            output_path = prefix_path.parent / f'{prefix_path.name}_{split_name}_predictions.csv'
            export.to_csv(output_path, sep=';', index=False)
            print(f"  ✅ {split_name}: {len(export)} строк -> {output_path}")

        print(f"{'═' * 60}\n")
        return

    # ── Обработка каждого датасета ───────────────────────────────────────────
    target_col = TRAILING_STOP_TARGET if task == TRAILING_STOP_TARGET else (
        UPDN_REGRESSION_TARGET if task == 'regression_updn' else 'predict'
    )

    all_results = []

    # ── Train + Validation (один вызов create_data_loaders) ──────────────
    print(f"\n{'─' * 60}")
    print(f"  🔮 Обработка train + validation...")
    train_loader, val_loader, _scaler = create_data_loaders(
        batch_size=256, target=target_col,
        use_scaler=False, seq_len=seq_len,
        num_workers=0,
    )

    for split_name, loader, csv_path in [
        ('train', train_loader, TRAIN_FILE),
        ('validation', val_loader, VAL_FILE),
    ]:
        df_meta = pd.read_csv(csv_path, sep=CSV_SEP, usecols=['time'], low_memory=False)
        times = df_meta['time'].values

        y_pred = run_inference(model, loader, device)
        print(f"    {split_name}: {len(y_pred)} предсказаний")

        assert len(y_pred) == len(times), (
            f"Размер предсказаний ({len(y_pred)}) ≠ размер times ({len(times)}) для {split_name}"
        )

        signals = preds_to_signals(y_pred, horizon, theta, conformal_quantiles)
        buy_count = (signals == 1).sum()
        sell_count = (signals == -1).sum()
        print(f"    {split_name}: BUY={buy_count}, SELL={sell_count}, FLAT={len(signals)-buy_count-sell_count}")

        df = pd.DataFrame({'time': times, 'signal': signals})
        for i, name in enumerate(UPDN_TARGETS):
            df[name] = np.round(y_pred[:, i], 4)
        all_results.append(df)

    # ── Test ─────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"  🔮 Обработка test...")
    test_loader = create_test_loader(batch_size=256, target=target_col, seq_len=seq_len, num_workers=0)
    df_meta = pd.read_csv(TEST_FILE, sep=CSV_SEP, usecols=['time'], low_memory=False)
    times = df_meta['time'].values

    y_pred = run_inference(model, test_loader, device)
    print(f"    test: {len(y_pred)} предсказаний")
    assert len(y_pred) == len(times)

    signals = preds_to_signals(y_pred, horizon, theta, conformal_quantiles)
    buy_count = (signals == 1).sum()
    sell_count = (signals == -1).sum()
    print(f"    test: BUY={buy_count}, SELL={sell_count}, FLAT={len(signals)-buy_count-sell_count}")

    df = pd.DataFrame({'time': times, 'signal': signals})
    for i, name in enumerate(UPDN_TARGETS):
        df[name] = np.round(y_pred[:, i], 4)
    all_results.append(df)

    # ── Объединение и запись CSV ──────────────────────────────────────────────
    df_all = pd.concat(all_results, ignore_index=True)
    df_all.sort_values('time', inplace=True)
    df_all.drop_duplicates(subset='time', keep='last', inplace=True)

    output_path = OUTPUT_DIR / 'ml_signals.csv'
    df_all.to_csv(output_path, sep=';', index=False)

    print(f"\n{'═' * 60}")
    print(f"  ✅ Записано {len(df_all)} строк в {output_path}")
    print(f"  📅 Диапазон: {df_all['time'].iloc[0]} — {df_all['time'].iloc[-1]}")

    total_buy = (df_all['signal'] == 1).sum()
    total_sell = (df_all['signal'] == -1).sum()
    total_flat = (df_all['signal'] == 0).sum()
    print(f"  📊 Итого: BUY={total_buy}, SELL={total_sell}, FLAT={total_flat}")
    print(f"{'═' * 60}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Генерация CSV с ML-сигналами для MT4 Strategy Tester.'
    )
    parser.add_argument(
        '--model', type=str, default=DEFAULT_MODEL,
        choices=['bilstm', 'cnn1d', 'transformer', 'hybrid', 'entry_path_dual_stream'],
        help=f"Модель (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        '--task', type=str, default=DEFAULT_TASK,
        choices=[
            'regression',
            'regression_updn',
            'triple_barrier',
            ENTRY_PATH_TARGET,
            TRAILING_STOP_TARGET,
            TRAILING_STOP_TARGET_QUANTILE_TARGET,
            TAKE_SKIP_TRAILING_STOP_TARGET,
        ],
        help=f"Тип таргета (default: {DEFAULT_TASK})"
    )
    parser.add_argument(
        '--horizon', type=int, default=DEFAULT_HORIZON,
        choices=[3, 6, 12, 24, 48],
        help=f"Горизонт для updn (default: {DEFAULT_HORIZON})"
    )
    parser.add_argument(
        '--theta', type=float, default=DEFAULT_THETA,
        help=f"Порог θ (default: {DEFAULT_THETA})"
    )
    parser.add_argument(
        '--min-ev', type=float, default=0.0,
        help="Минимальный expected value для TB-сигнала (default: 0.0)"
    )
    parser.add_argument(
        '--optuna_json', type=str, default=DEFAULT_OPTUNA_JSON,
        help="Путь к JSON с Optuna параметрами"
    )
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument(
        '--conformal', action='store_true', default=False,
        help="Использовать Conformal Prediction фильтр (требует предварительной калибровки: python -m ML.conformal)"
    )
    parser.add_argument(
        '--research-out-prefix', type=str, default='',
        help='Prefix for entry_path_v1 research CSVs; example ML/reports/entry_path_v1'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.task == 'triple_barrier':
        generate_tb_signals(
            model_name=args.model,
            theta=args.theta,
            min_ev=args.min_ev,
            seed=args.seed,
        )
    else:
        generate_signals(
            model_name=args.model,
            task=args.task,
            horizon=args.horizon,
            theta=args.theta,
            optuna_json=args.optuna_json,
            seed=args.seed,
            conformal=args.conformal,
            research_out_prefix=args.research_out_prefix,
        )
