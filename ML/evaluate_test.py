import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ML.data_loader import create_test_loader, UPDN_REGRESSION_TARGET, TEST_FILE, CSV_SEP, FRACTAL_SEP, UPDN_TARGETS
from ML.models import get_model
from ML.utils import set_seed, get_device

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINTS_DIR = PROJECT_ROOT / 'ML' / 'checkpoints'
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'


def load_test_metadata(task: str = 'regression') -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Загрузка signal, predict/updn и direction из TEST CSV."""
    print("  📄 Загрузка метаданных из TEST CSV...")
    df = pd.read_csv(TEST_FILE, sep=CSV_SEP, low_memory=False)

    signal = df['signal'].values.astype(int)
    
    if task == 'regression_updn':
        predict_val = df[UPDN_TARGETS].values.astype(np.float64)
    else:
        predict_val = np.abs(df['predict'].values.astype(np.float64))

    # Извлекаем direction из fractal0
    direction = df['fractal0'].astype(str).apply(
        lambda x: int(float(x.split(FRACTAL_SEP)[2]))
    ).values

    print(f"    Загружено {len(signal)} строк")
    return signal, predict_val, direction


def run_evaluation(
    model_name: str | None = None,
    checkpoint_path: str | None = None,
    task: str = 'regression',
    horizon: int = 12,
    theta: float = 2.665,
    seed: int = 42,
    optuna_json: str | None = None,
):
    set_seed(seed)
    device = get_device()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Определяем чекпоинт ──────────────────────────────────────────────────
    if checkpoint_path:
        ckpt_path = Path(checkpoint_path)
    elif model_name:
        suffix = '_updn' if task == 'regression_updn' else '_regression'
        ckpt_path = CHECKPOINTS_DIR / f'{model_name}{suffix}_best.pt'
    else:
        suffix = '_updn' if task == 'regression_updn' else '_regression'
        ckpt_path = CHECKPOINTS_DIR / f'best_model{suffix}.pt'

    if not ckpt_path.exists():
        raise FileNotFoundError(f"Чекпоинт не найден: {ckpt_path}")

    print(f"\n{'═' * 60}")
    print(f"  OUT-OF-SAMPLE TEST EVALUATION")
    print(f"{'═' * 60}")
    print(f"  Чекпоинт: {ckpt_path.name}")
    print(f"  Задача: {task}, Горизонт: {horizon}H")
    print(f"  Торговый порог θ: {theta}")

    # ── Загрузка чекпоинта ───────────────────────────────────────────────────
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    ckpt_model_name = ckpt.get('model_name', model_name or 'bilstm')
    num_classes = ckpt.get('num_classes', 1)

    model_kwargs = ckpt.get('model_kwargs', {})
    
    if optuna_json:
        with open(optuna_json, 'r', encoding='utf-8') as f:
            optuna_data = json.load(f)
        best_params = optuna_data.get('best_params', {})
        for k in ['hidden_size', 'num_layers', 'dropout', 'input_features']:
            if k in best_params:
                model_kwargs[k] = best_params[k]
        print(f"  📥 Загружены параметры архитектуры из {optuna_json}")

    model = get_model(ckpt_model_name, num_classes=num_classes, **model_kwargs)
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    model.eval()
    print(f"  ✅ Модель загружена")

    # ── Загрузка данных ──────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    target_col = UPDN_REGRESSION_TARGET if task == 'regression_updn' else 'predict'
    test_loader = create_test_loader(
        batch_size=256,
        target=target_col,
        seq_len=model_kwargs.get('seq_len', 20) if optuna_json else 20,
    )

    signal_true, predict_val_true, direction = load_test_metadata(task)

    # ── Инференс ─────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("🧠 Inference на Test...")
    all_preds = []
    
    with torch.no_grad():
        for X_batch, _y_batch, mask_batch in test_loader:
            X_batch = X_batch.to(device)
            mask_batch = mask_batch.to(device)
            preds = model(X_batch, mask=mask_batch).cpu().numpy()
            if preds.ndim > 1 and preds.shape[-1] == 1:
                preds = preds.squeeze(-1)
            all_preds.append(preds)

    y_pred = np.concatenate(all_preds)

    # ── Анализ и Торговое Правило ───────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("📈 Симуляция торгового правила...")

    if task == 'regression_updn':
        idx_map = {12: 0, 24: 2, 48: 4}
        if horizon not in idx_map:
            raise ValueError(f"Unknown horizon {horizon}")
        idx = idx_map[horizon]
        
        pred_up = y_pred[:, idx]
        pred_dn = y_pred[:, idx + 1]
        true_up = predict_val_true[:, idx]
        true_dn = predict_val_true[:, idx + 1]
        
        ratio_up = pred_up / (pred_dn + 1e-6)
        ratio_dn = pred_dn / (pred_up + 1e-6)
        
        signal = np.zeros(len(y_pred), dtype=int)
        signal[ratio_up > theta] = 1
        signal[ratio_dn > theta] = -1
        
        trades = np.count_nonzero(signal)
        profit_trades = 0
        loss_trades = 0
        gross_profit = 0.0
        gross_loss = 0.0
        
        buy_mask = (signal == 1)
        gross_profit += true_up[buy_mask].sum()
        gross_loss += true_dn[buy_mask].sum()
        profit_trades += (true_up[buy_mask] > true_dn[buy_mask]).sum()
        loss_trades += (true_up[buy_mask] <= true_dn[buy_mask]).sum()
        
        sell_mask = (signal == -1)
        gross_profit += true_dn[sell_mask].sum()
        gross_loss += true_up[sell_mask].sum()
        profit_trades += (true_dn[sell_mask] > true_up[sell_mask]).sum()
        loss_trades += (true_dn[sell_mask] <= true_up[sell_mask]).sum()
        
        pf = gross_profit / gross_loss if gross_loss > 0 else np.inf
        precision = profit_trades / trades if trades > 0 else 0.0
        recall = trades / len(y_pred)
        
        print("\n🏆 Out-of-Sample Performance:")
        print(f"  Выбранный порог θ: {theta}")
        print(f"  Сделок сгенерировано: {trades} из {len(y_pred)} ({recall*100:.1f}%)")
        print(f"  Прибыльных сделок (TP): {profit_trades}")
        print(f"  Убыточных сделок (FP): {loss_trades}")
        print(f"  Win Rate (Precision): {precision*100:.2f}%")
        print(f"  Gross Profit: {gross_profit:.2f}")
        print(f"  Gross Loss: {gross_loss:.2f}")
        print(f"  PROFIT FACTOR: {pf:.4f}")
        
    else:
        print("Эта симуляция предназначена только для multi-target regression_updn.")
        return

    # Генерация отчета
    report_path = REPORTS_DIR / f'evaluate_test_H{horizon}.md'
    lines = [
        f"# Test Set Evaluation Report",
        f"",
        f"**Дата генерации**: (auto)",
        f"**Модель**: {ckpt_model_name} ({task})",
        f"**Набор**: Test Set ({len(y_pred)} строк)",
        f"",
        f"## 1. Торговые метрики (θ={theta}, Горизонт={horizon}H)",
        f"| Параметр | Значение |",
        f"|----------|----------|",
        f"| **Profit Factor** | **{pf:.4f}** |",
        f"| Precision | {precision*100:.2f}% |",
        f"| Trades count | {trades} |",
        f"| TP (положительных) | {profit_trades} |",
        f"| FP (отрицательных) | {loss_trades} |",
        f"| Gross profit | {gross_profit:.2f} |",
        f"| Gross loss | {gross_loss:.2f} |",
    ]
    report_path.write_text("\n".join(lines), 'utf-8')
    print(f"\n✅ Отчет сохранён в: {report_path.name}")
    print(f"{'═' * 60}\n")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='transformer')
    parser.add_argument('--checkpoint', type=str, default=None)
    parser.add_argument('--task', type=str, default='regression_updn')
    parser.add_argument('--horizon', type=int, default=12)
    parser.add_argument('--theta', type=float, required=True, help='Торговый порог (ratio pred_up/pred_dn)')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--optuna_json', type=str, default=None)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    run_evaluation(
        model_name=args.model,
        checkpoint_path=args.checkpoint,
        task=args.task,
        horizon=args.horizon,
        theta=args.theta,
        seed=args.seed,
        optuna_json=args.optuna_json,
    )
