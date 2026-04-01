# =============================================================================
# Файл: API/generate_signals.py
# Назначение: Генерация CSV с предрассчитанными ML-сигналами для MT4 Strategy Tester
# Язык: Python 3.11+
# Создан: 2026-03-20
# Зависимости:
#   Входные данные:
#     - ML/checkpoints/transformer_updn_best.pt
#     - ML/reports/optuna_best_params_transformer_regression_updn.json
#     - DATA/Nero_{train,validation,test}_labeled.csv
#   Выходные данные:
#     - MT/MQL4/Files/ml_signals.csv
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
# =============================================================================

"""
Генерация CSV с ML-сигналами для MT4.

Загружает обученную модель, прогоняет все три датасета (train, validation, test),
применяет порог θ и пишет результат в MQL4/Files/ml_signals.csv.
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
)
from ML.models import get_model
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
) -> pd.DataFrame:
    """
    Convert 12 TB logits to best signal per row.

    For each row: sigmoid → filter P>theta → pick max EV.
    EV = P * TP - (1-P) * SL. Conflict BUY+SELL: max EV wins.
    """
    proba = 1.0 / (1.0 + np.exp(-y_pred_logits))  # sigmoid
    n = len(proba)

    signals = np.zeros(n, dtype=int)
    sl_atrs = np.zeros(n, dtype=float)
    tp_atrs = np.zeros(n, dtype=float)
    probs = np.zeros(n, dtype=float)
    evs = np.zeros(n, dtype=float)

    for row_idx in range(n):
        best_ev = -np.inf
        best_signal = 0
        best_sl = 0.0
        best_tp = 0.0
        best_prob = 0.0

        for i, name in enumerate(TB_TARGET_NAMES):
            p = proba[row_idx, i]
            if p <= theta:
                continue

            parts = name.split('_')
            direction = 1 if parts[0] == 'buy' else -1
            sl = int(parts[1][2:])
            tp = int(parts[2][2:])

            ev = p * tp - (1 - p) * sl

            if ev > best_ev:
                best_ev = ev
                best_signal = direction
                best_sl = float(sl)
                best_tp = float(tp)
                best_prob = p

        signals[row_idx] = best_signal
        sl_atrs[row_idx] = best_sl
        tp_atrs[row_idx] = best_tp
        probs[row_idx] = round(best_prob, 4)
        evs[row_idx] = round(best_ev, 4) if best_ev > -np.inf else 0.0

    return pd.DataFrame({
        'signal': signals,
        'sl_atr': sl_atrs,
        'tp_atr': tp_atrs,
        'prob': probs,
        'ev': evs,
    })


def generate_tb_signals(
    model_name: str = DEFAULT_MODEL,
    theta: float = 0.6,
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
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Чекпоинт не найден: {ckpt_path}")

    print(f"  📥 Чекпоинт: {ckpt_path.name}")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)

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

    all_results = []

    # Train + Validation
    print(f"\n{'─' * 60}")
    print(f"  🔮 Обработка train + validation...")
    train_loader, val_loader, _ = create_data_loaders(
        batch_size=256, target=TB_TARGET,
        use_scaler=False, seq_len=seq_len,
    )

    for split_name, loader, csv_path in [
        ('train', train_loader, TRAIN_FILE),
        ('validation', val_loader, VAL_FILE),
    ]:
        df_meta = pd.read_csv(csv_path, sep=CSV_SEP, usecols=['time'], low_memory=False)
        times = df_meta['time'].values

        y_pred = run_inference(model, loader, device)
        print(f"    {split_name}: {len(y_pred)} предсказаний")
        assert len(y_pred) == len(times)

        df_signals = tb_preds_to_signals(y_pred, theta)
        df_signals.insert(0, 'time', times)

        buy_count = (df_signals['signal'] == 1).sum()
        sell_count = (df_signals['signal'] == -1).sum()
        print(f"    {split_name}: BUY={buy_count}, SELL={sell_count}, FLAT={len(df_signals)-buy_count-sell_count}")
        all_results.append(df_signals)

    # Test
    print(f"\n{'─' * 60}")
    print(f"  🔮 Обработка test...")
    test_loader = create_test_loader(batch_size=256, target=TB_TARGET, seq_len=seq_len)
    df_meta = pd.read_csv(TEST_FILE, sep=CSV_SEP, usecols=['time'], low_memory=False)
    times = df_meta['time'].values

    y_pred = run_inference(model, test_loader, device)
    print(f"    test: {len(y_pred)} предсказаний")
    assert len(y_pred) == len(times)

    df_signals = tb_preds_to_signals(y_pred, theta)
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
):
    """Полный pipeline: загрузка модели → инференс → запись CSV."""

    set_seed(seed)
    device = get_device()
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

    # ── Загрузка чекпоинта ───────────────────────────────────────────────────
    suffix = '_updn' if task == 'regression_updn' else '_regression'
    ckpt_path = CHECKPOINTS_DIR / f'{model_name}{suffix}_best.pt'

    if not ckpt_path.exists():
        raise FileNotFoundError(f"Чекпоинт не найден: {ckpt_path}")

    print(f"  📥 Чекпоинт: {ckpt_path.name}")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)

    ckpt_model_name = ckpt.get('model_name', model_name)
    num_classes = ckpt.get('num_classes', 1)
    model_kwargs = ckpt.get('model_kwargs', {})

    # Загрузка параметров Optuna
    if optuna_json and Path(optuna_json).exists():
        with open(optuna_json, 'r', encoding='utf-8') as f:
            optuna_data = json.load(f)
        best_params = optuna_data.get('best_params', {})
        for k in ['hidden_size', 'num_layers', 'dropout', 'input_features']:
            if k in best_params:
                model_kwargs[k] = best_params[k]
        print(f"  📥 Optuna параметры из {Path(optuna_json).name}")

    seq_len = model_kwargs.get('seq_len', 20)

    model = get_model(ckpt_model_name, num_classes=num_classes, **model_kwargs)
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    model.eval()
    print(f"  ✅ Модель {ckpt_model_name} загружена (seq_len={seq_len})")
    print(f"  📈 Горизонт: {horizon}H, Порог (θ): {theta}")

    # ── Обработка каждого датасета ───────────────────────────────────────────
    target_col = UPDN_REGRESSION_TARGET if task == 'regression_updn' else 'predict'

    all_results = []

    # ── Train + Validation (один вызов create_data_loaders) ──────────────
    print(f"\n{'─' * 60}")
    print(f"  🔮 Обработка train + validation...")
    train_loader, val_loader, _scaler = create_data_loaders(
        batch_size=256, target=target_col,
        use_scaler=False, seq_len=seq_len,
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
    test_loader = create_test_loader(batch_size=256, target=target_col, seq_len=seq_len)
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
        choices=['bilstm', 'cnn1d', 'transformer', 'hybrid'],
        help=f"Модель (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        '--task', type=str, default=DEFAULT_TASK,
        choices=['regression', 'regression_updn', 'triple_barrier'],
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
        '--optuna_json', type=str, default=DEFAULT_OPTUNA_JSON,
        help="Путь к JSON с Optuna параметрами"
    )
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument(
        '--conformal', action='store_true', default=False,
        help="Использовать Conformal Prediction фильтр (требует предварительной калибровки: python -m ML.conformal)"
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.task == 'triple_barrier':
        generate_tb_signals(
            model_name=args.model,
            theta=args.theta,
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
        )
