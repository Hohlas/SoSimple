# =============================================================================
# Файл: ML/conformal/calibrate.py
# Назначение: Conformal Prediction — калибровка интервалов неопределённости
#              поверх обученной модели (post-processing, без переобучения)
# Язык: Python 3.10+
# Создан: 2026-03-20
# Зависимости:
#   Входные данные:
#     - ML/checkpoints/transformer_updn_best.pt
#     - ML/reports/optuna_best_params_transformer_regression_updn.json
#     - DATA/Nero_validation_labeled.csv
#   Выходные данные:
#     - ML/conformal/conformal_quantiles.json
#     - ML/conformal/conformal_calibration.md
# Внешние зависимости:
#   - torch>=2.0, numpy>=1.24, pandas>=2.0
# Использование:
#   python -m ML.conformal.calibrate
#   python -m ML.conformal.calibrate --alpha 0.10 --model transformer
# Примечания:
#   - Split Conformal Prediction на validation set
#   - Nonconformity score = |y_true - y_pred| (per target)
#   - Квантиль уровня (1-α)(1+1/n) — finite-sample correction
#   - Результат: 6 чисел (по одному на каждый из Up/Dn таргетов)
# =============================================================================

"""
Conformal Prediction: калибровка доверительных интервалов.

Прогоняет обученную модель через validation set, вычисляет
nonconformity scores (|y_true - y_pred|) и находит квантили
для построения prediction intervals с гарантированным покрытием.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ML.data_loader import (
    create_data_loaders, CSV_SEP, VAL_FILE,
    UPDN_REGRESSION_TARGET, UPDN_TARGETS,
)
from ML.models import get_model
from ML.utils import set_seed, get_device


# ─── Пути ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFORMAL_DIR = Path(__file__).resolve().parent
CHECKPOINTS_DIR = PROJECT_ROOT / 'ML' / 'checkpoints'
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'

DEFAULT_MODEL = 'transformer'
DEFAULT_ALPHA = 0.10
DEFAULT_OPTUNA_JSON = str(REPORTS_DIR / 'optuna_best_params_transformer_regression_updn.json')

QUANTILES_FILE = CONFORMAL_DIR / 'conformal_quantiles.json'


# ═══════════════════════════════════════════════════════════════════════════════
# ИНФЕРЕНС
# ═══════════════════════════════════════════════════════════════════════════════

@torch.no_grad()
def run_inference(
    model: torch.nn.Module,
    loader: torch.utils.data.DataLoader,
    device: torch.device,
) -> np.ndarray:
    """Прогон модели, возвращает y_pred shape (N, 6)."""
    model.eval()
    all_preds = []
    for X_batch, _y, mask_batch in loader:
        X_batch = X_batch.to(device)
        mask_batch = mask_batch.to(device)
        preds = model(X_batch, mask=mask_batch).cpu().numpy()
        if preds.ndim > 1 and preds.shape[-1] == 1:
            preds = preds.squeeze(-1)
        all_preds.append(preds)
    return np.concatenate(all_preds)


# ═══════════════════════════════════════════════════════════════════════════════
# КАЛИБРОВКА
# ═══════════════════════════════════════════════════════════════════════════════

def calibrate(
    model_name: str = DEFAULT_MODEL,
    alpha: float = DEFAULT_ALPHA,
    optuna_json: str | None = DEFAULT_OPTUNA_JSON,
    seed: int = 42,
) -> dict:
    """
    Полный pipeline калибровки Conformal Prediction.

    1. Загружает чекпоинт модели
    2. Inference на validation set
    3. Вычисляет nonconformity scores = |y_true - y_pred|
    4. Берёт квантиль уровня (1-α)(1+1/n) на каждый таргет
    5. Сохраняет квантили в JSON

    Аргументы:
        model_name: Имя модели ('transformer', 'bilstm', ...)
        alpha: Уровень ошибки покрытия (0.10 = 90% coverage)
        optuna_json: Путь к JSON с параметрами Optuna
        seed: Random seed

    Возвращает:
        Словарь с квантилями и метаданными калибровки
    """
    set_seed(seed)
    device = get_device()

    print(f"\n{'═' * 60}")
    print(f"  CONFORMAL PREDICTION CALIBRATION")
    print(f"{'═' * 60}")
    print(f"  Alpha: {alpha} (coverage target: {(1 - alpha) * 100:.0f}%)")

    # ── Загрузка чекпоинта ───────────────────────────────────────────────────
    ckpt_path = CHECKPOINTS_DIR / f'{model_name}_updn_best.pt'
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Чекпоинт не найден: {ckpt_path}")

    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    ckpt_model_name = ckpt.get('model_name', model_name)
    num_classes = ckpt.get('num_classes', 1)
    model_kwargs = ckpt.get('model_kwargs', {})

    if optuna_json and Path(optuna_json).exists():
        with open(optuna_json, 'r', encoding='utf-8') as f:
            best_params = json.load(f).get('best_params', {})
        for k in ['hidden_size', 'num_layers', 'dropout', 'input_features']:
            if k in best_params:
                model_kwargs[k] = best_params[k]
        print(f"  Optuna параметры из {Path(optuna_json).name}")

    seq_len = model_kwargs.get('seq_len', 20)

    model = get_model(ckpt_model_name, num_classes=num_classes, **model_kwargs)
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    print(f"  Модель: {ckpt_model_name} (seq_len={seq_len})")

    # ── Загрузка validation данных ───────────────────────────────────────────
    _train_loader, val_loader, _ = create_data_loaders(
        batch_size=256, target=UPDN_REGRESSION_TARGET,
        use_scaler=False, seq_len=seq_len,
    )

    # ── Inference ────────────────────────────────────────────────────────────
    print(f"\n  Inference на validation set...")
    y_pred = run_inference(model, val_loader, device)
    n_cal = len(y_pred)
    print(f"  Предсказания: {n_cal} samples, shape {y_pred.shape}")

    # ── True targets из CSV ──────────────────────────────────────────────────
    df_val = pd.read_csv(VAL_FILE, sep=CSV_SEP, usecols=UPDN_TARGETS, low_memory=False)
    y_true = df_val[UPDN_TARGETS].values.astype(np.float32)
    assert len(y_true) == n_cal, f"y_true ({len(y_true)}) != y_pred ({n_cal})"

    # ── Nonconformity scores ─────────────────────────────────────────────────
    scores = np.abs(y_true - y_pred)  # shape (N, 6)

    # ── Квантиль с finite-sample correction ──────────────────────────────────
    level = min((1 - alpha) * (1 + 1 / n_cal), 1.0)
    quantiles = {}

    print(f"\n  {'Таргет':<8} {'Квантиль':>10} {'Mean |err|':>12} {'Median':>10}")
    print(f"  {'─' * 44}")
    for i, name in enumerate(UPDN_TARGETS):
        q = float(np.quantile(scores[:, i], level))
        quantiles[name] = q
        print(f"  {name:<8} {q:>10.4f} {scores[:, i].mean():>12.4f} {np.median(scores[:, i]):>10.4f}")

    # ── Проверка покрытия ────────────────────────────────────────────────────
    print(f"\n  Эмпирическое покрытие (ожидается >= {(1 - alpha) * 100:.0f}%):")
    for i, name in enumerate(UPDN_TARGETS):
        covered = (scores[:, i] <= quantiles[name]).mean()
        print(f"    {name}: {covered * 100:.1f}%")

    # ── Сохранение ───────────────────────────────────────────────────────────
    output = {
        'alpha': alpha,
        'coverage_target': 1 - alpha,
        'n_calibration': n_cal,
        'model': ckpt_model_name,
        'checkpoint': ckpt_path.name,
        'quantiles': quantiles,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    with open(QUANTILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  Сохранено: {QUANTILES_FILE}")

    # ── Отчёт ────────────────────────────────────────────────────────────────
    _generate_report(output, scores)

    print(f"{'═' * 60}\n")
    return output


def _generate_report(cal_data: dict, scores: np.ndarray):
    """Генерация markdown-отчёта калибровки."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    alpha = cal_data['alpha']
    quantiles = cal_data['quantiles']
    n_cal = cal_data['n_calibration']

    lines = [
        "# Conformal Prediction — Calibration Report",
        "",
        f"**Дата**: {cal_data['timestamp']}",
        f"**Модель**: {cal_data['model']}",
        f"**Чекпоинт**: {cal_data['checkpoint']}",
        f"**Alpha**: {alpha} (покрытие: {(1 - alpha) * 100:.0f}%)",
        f"**Калибровочный набор**: validation ({n_cal} samples)",
        "",
        "## Квантили (пороги неконформности)",
        "",
        "| Таргет | q (полуширина интервала) | Mean |y−ŷ| | Median |y−ŷ| |",
        "|--------|-------------------------|-------------|---------------|",
    ]
    for i, name in enumerate(UPDN_TARGETS):
        q = quantiles[name]
        lines.append(
            f"| {name} | {q:.4f} | {scores[:, i].mean():.4f} | {np.median(scores[:, i]):.4f} |"
        )

    lines += [
        "",
        "## Эмпирическое покрытие",
        "",
        "| Таргет | Покрытие |",
        "|--------|----------|",
    ]
    for i, name in enumerate(UPDN_TARGETS):
        cov = (scores[:, i] <= quantiles[name]).mean()
        lines.append(f"| {name} | {cov * 100:.1f}% |")

    lines += [
        "",
        "## Использование в торговле",
        "",
        "Для каждого предсказания строится интервал:",
        "```",
        "pred_up ± q_up  →  [pred_up − q_up, pred_up + q_up]",
        "pred_dn ± q_dn  →  [pred_dn − q_dn, pred_dn + q_dn]",
        "```",
        "",
        "**Фильтр минимальной величины:**",
        "```",
        "if ratio_up > θ AND pred_up > q_up → BUY",
        "if ratio_dn > θ AND pred_dn > q_dn → SELL",
        "else → FLAT",
        "```",
        "",
        "Смысл: отсекаются сигналы, где ratio > θ только потому что",
        "обе стороны (pred_up, pred_dn) близки к нулю — модель предсказывает",
        "малое движение в обе стороны, а ratio случайно велик.",
        "Сигнал сохраняется только если доминирующее предсказание",
        "превышает типичную ошибку модели (q).",
    ]

    report_path = CONFORMAL_DIR / 'conformal_calibration.md'
    report_path.write_text("\n".join(lines), encoding='utf-8')
    print(f"  Отчёт: {report_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Conformal Prediction: калибровка на validation set.'
    )
    parser.add_argument(
        '--model', type=str, default=DEFAULT_MODEL,
        choices=['bilstm', 'cnn1d', 'transformer', 'hybrid'],
        help=f"Модель (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        '--alpha', type=float, default=DEFAULT_ALPHA,
        help=f"Уровень ошибки покрытия (default: {DEFAULT_ALPHA}, т.е. 90%% coverage)"
    )
    parser.add_argument(
        '--optuna_json', type=str, default=DEFAULT_OPTUNA_JSON,
        help="Путь к JSON с Optuna параметрами"
    )
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    calibrate(
        model_name=args.model,
        alpha=args.alpha,
        optuna_json=args.optuna_json,
        seed=args.seed,
    )
