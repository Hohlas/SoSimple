import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ML.data_loader import (
    ARCHETYPE_TARGET,
    BINARY_CLASSIFICATION_TARGETS,
    CSV_SEP,
    FRACTAL_SEP,
    TEST_FILE,
    TB_TARGET,
    TB_TARGET_NAMES,
    TRADE_OUTCOME_TARGET,
    TRADE_PNL_TARGET,
    UPDN_REGRESSION_TARGET,
    UPDN_TARGETS,
    create_test_loader,
    task_checkpoint_suffix,
    task_target_column,
)
from ML.entry_path_task import (
    ENTRY_PATH_MODEL_NAMES,
    ENTRY_PATH_TARGET,
    ENTRY_PATH_V1_FEATURE_COLUMNS,
    build_entry_path_model,
    build_entry_path_export_frame,
    build_entry_path_report_markdown,
)
from ML.entry_path_v1_quantile_task import (
    ENTRY_PATH_V1_QUANTILE_TARGET,
    build_entry_path_v1_quantile_export_frame,
    build_entry_path_v1_quantile_model,
    build_entry_path_v1_quantile_report_markdown,
    count_crossed_quantile_rows,
)
from ML.trailing_stop_target_quantile_task import (
    TRAILING_STOP_TARGET_QUANTILE_BASE_COLUMN,
    TRAILING_STOP_TARGET_QUANTILE_TARGET,
    build_trailing_stop_quantile_export_frame,
    compute_trailing_stop_quantile_metrics,
)
from ML.trailing_stop_target_task import (
    TRAILING_STOP_TARGET,
    TRAILING_STOP_TARGET_COLUMNS,
    build_trailing_stop_export_frame,
)
from ML.models import get_model
from ML.models.trailing_stop_target_quantile_transformer import TrailingStopTargetQuantileTransformer
from ML.tb_probability_calibration import (
    apply_tb_probability_calibration,
    load_tb_probability_calibrator,
)
from ML.tb_signal_logic import evaluate_tb_signal_rule, tb_proba_to_signals
from ML.utils import (
    compute_binary_classification_metrics,
    compute_regression_metrics,
    compute_single_binary_classification_metrics,
    get_device,
    set_seed,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINTS_DIR = PROJECT_ROOT / 'ML' / 'checkpoints'
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'
TB_CALIBRATOR_PATH = REPORTS_DIR / 'tb_probability_calibrator.joblib'
TB_RULE_PATH = REPORTS_DIR / 'tb_selected_rule.json'
FROZEN_OUTCOME_TARGET_PATH = REPORTS_DIR / 'frozen_outcome_target.json'


def build_trailing_stop_target_quantile_model(model_kwargs: dict | None = None) -> TrailingStopTargetQuantileTransformer:
    return TrailingStopTargetQuantileTransformer(**(model_kwargs or {}))


def _order_trailing_stop_quantiles(
    pred_q10: np.ndarray,
    pred_q50: np.ndarray,
    pred_q90: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ordered = np.sort(
        np.stack(
            [
                np.asarray(pred_q10, dtype=np.float64).reshape(-1),
                np.asarray(pred_q50, dtype=np.float64).reshape(-1),
                np.asarray(pred_q90, dtype=np.float64).reshape(-1),
            ],
            axis=1,
        ),
        axis=1,
    )
    return ordered[:, 0], ordered[:, 1], ordered[:, 2]


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


def load_outcome_test_frame() -> pd.DataFrame:
    cols = ['time', 'signal', 'trade_pnl_h12_atr', 'trade_outcome_h12', 'archetype_target']
    frame = pd.read_csv(TEST_FILE, sep=CSV_SEP, usecols=cols, low_memory=False)
    frame['time'] = pd.to_datetime(frame['time'], format='%Y.%m.%d %H:%M', errors='coerce')
    return frame


def load_frozen_outcome_target() -> dict | None:
    if not FROZEN_OUTCOME_TARGET_PATH.exists():
        return None
    return json.loads(FROZEN_OUTCOME_TARGET_PATH.read_text(encoding='utf-8'))


def run_evaluation(
    model_name: str | None = None,
    checkpoint_path: str | None = None,
    task: str = 'regression',
    horizon: int = 12,
    theta: float = 2.665,
    min_ev: float = 0.0,
    score_threshold: float | None = None,
    seed: int = 42,
    optuna_json: str | None = None,
    seq_len_override: int | None = None,
):
    set_seed(seed)
    device = get_device()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Определяем чекпоинт ──────────────────────────────────────────────────
    if checkpoint_path:
        ckpt_path = Path(checkpoint_path)
    elif model_name:
        suffix = task_checkpoint_suffix(task)
        ckpt_path = CHECKPOINTS_DIR / f'{model_name}{suffix}_best.pt'
    else:
        suffix = task_checkpoint_suffix(task)
        ckpt_path = CHECKPOINTS_DIR / f'best_model{suffix}.pt'

    if not ckpt_path.exists():
        raise FileNotFoundError(f"Чекпоинт не найден: {ckpt_path}")

    print(f"\n{'═' * 60}")
    print(f"  OUT-OF-SAMPLE TEST EVALUATION")
    print(f"{'═' * 60}")
    print(f"  Чекпоинт: {ckpt_path.name}")
    print(f"  Задача: {task}, Горизонт: {horizon}H")
    print(f"  Торговый порог θ: {theta}")
    if task == 'triple_barrier':
        print(f"  Min EV: {min_ev}")

    # ── Загрузка чекпоинта ───────────────────────────────────────────────────
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    ckpt_model_name = ckpt.get('model_name', model_name or 'bilstm')
    num_classes = ckpt.get('num_classes', 1)
    seq_len = int(seq_len_override if seq_len_override is not None else ckpt.get('seq_len', 20))
    model_kwargs = ckpt.get('model_kwargs', {})
    
    if optuna_json:
        with open(optuna_json, 'r', encoding='utf-8') as f:
            optuna_data = json.load(f)
        best_params = optuna_data.get('best_params', {})
        for k in ['hidden_size', 'num_layers', 'dropout', 'input_features']:
            if k in best_params:
                model_kwargs[k] = best_params[k]
        print(f"  📥 Загружены параметры архитектуры из {optuna_json}")

    if task == ENTRY_PATH_TARGET:
        model_kwargs.setdefault('engineered_feature_dim', len(ENTRY_PATH_V1_FEATURE_COLUMNS))
        entry_model_name = ckpt_model_name if ckpt_model_name in ENTRY_PATH_MODEL_NAMES else 'transformer'
        model = build_entry_path_model(entry_model_name, model_kwargs)
    elif task == ENTRY_PATH_V1_QUANTILE_TARGET:
        model = build_entry_path_v1_quantile_model(model_kwargs)
    elif task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
        model = build_trailing_stop_target_quantile_model(model_kwargs)
    else:
        model = get_model(ckpt_model_name, num_classes=num_classes, **model_kwargs)
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    model.eval()
    print(f"  ✅ Модель загружена")

    # ── Загрузка данных ──────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    target_col = ENTRY_PATH_V1_QUANTILE_TARGET if task == ENTRY_PATH_V1_QUANTILE_TARGET else task_target_column(task)
    test_loader = create_test_loader(
        batch_size=256,
        target=target_col,
        seq_len=seq_len,
        num_workers=0,
    )

    if task in (ENTRY_PATH_TARGET, ENTRY_PATH_V1_QUANTILE_TARGET):
        df_test_full = pd.read_csv(TEST_FILE, sep=CSV_SEP, low_memory=False)
        df_test = df_test_full[['time', 'signal']].copy()
        entry_path_gt_available = has_entry_path_ground_truth(df_test_full)
    elif task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
        df_test_full = pd.read_csv(TEST_FILE, sep=CSV_SEP, low_memory=False)
    elif task == TRAILING_STOP_TARGET:
        df_test_full = pd.read_csv(TEST_FILE, sep=CSV_SEP, low_memory=False)
    else:
        signal_true, predict_val_true, direction = load_test_metadata(task)

    frozen_outcome = None
    if task in [TRADE_OUTCOME_TARGET, TRADE_PNL_TARGET, ARCHETYPE_TARGET]:
        frozen_outcome = load_frozen_outcome_target()
        if (
            score_threshold is None and
            frozen_outcome is not None and
            frozen_outcome.get('winner', {}).get('task') == task
        ):
            score_threshold = float(frozen_outcome['winner']['score_threshold'])

    # ── Инференс ─────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("🧠 Inference на Test...")
    if task == ENTRY_PATH_TARGET:
        all_ret = []
        all_path_reg = []
        all_path_cls = []
        all_true_reg = []
        all_true_cls = []

        with torch.no_grad():
            for X_batch, engineered_batch, y_reg_batch, y_cls_batch, mask_batch, _signal_batch in test_loader:
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

        pred_ret = np.concatenate(all_ret)
        pred_path_reg = np.concatenate(all_path_reg)
        pred_path_cls = np.concatenate(all_path_cls)
        true_reg = np.concatenate(all_true_reg)
        true_cls = np.concatenate(all_true_cls)

        export_kwargs = {
            'times': df_test['time'].values,
            'signals': df_test['signal'].values.astype(int),
            'pred_ret': pred_ret,
            'pred_path_reg': pred_path_reg,
            'pred_path_cls': pred_path_cls,
        }
        if entry_path_gt_available:
            export_kwargs['true_reg'] = true_reg
            export_kwargs['true_cls'] = true_cls
        export = build_entry_path_export_frame(**export_kwargs)
        export_path = REPORTS_DIR / 'entry_path_test_predictions.csv'
        export.to_csv(export_path, sep=';', index=False)
        row_count = int(len(export))
        report_path = REPORTS_DIR / 'evaluate_test_entry_path_v1.md'
        report_path.write_text(
            build_entry_path_report_markdown(
                frame=export,
                model_name=ckpt_model_name,
                artifact_name=export_path.name,
                split_label='Test',
                checkpoint_epoch=ckpt.get('epoch'),
                checkpoint_metric_name=ckpt.get('metric_name'),
                checkpoint_metric_value=ckpt.get('best_metric'),
            ),
            encoding='utf-8',
        )

        print(f"  ✅ CSV сохранён: {export_path.name}")
        print(f"  ✅ Отчет сохранён: {report_path.name}")
        print(f"  row_count={row_count}")
        if ckpt.get('epoch') is not None and ckpt.get('best_metric') is not None:
            print(f"  checkpoint_epoch={ckpt.get('epoch')}")
            print(f"  best_val_{ckpt.get('metric_name', 'metric')}={ckpt.get('best_metric'):.4f}")
        if entry_path_gt_available:
            report_text = report_path.read_text(encoding='utf-8')
            summary_lines = [
                line for line in report_text.splitlines()
                if line.startswith('- ret_pearson_r:')
                or line.startswith('- path_reg_pearson_r:')
                or line.startswith('- path_cls_f1_macro:')
            ]
            for line in summary_lines:
                print(f"  {line[2:]}")
        else:
            print("  ⚠ Test ground truth для entry_path_v1 отсутствует; report written with N/A metrics.")
        print(f"{'═' * 60}\n")
        return

    if task == ENTRY_PATH_V1_QUANTILE_TARGET:
        all_ret = []
        all_path_reg = []
        all_path_cls = []
        all_q10 = []
        all_q90 = []
        all_true_reg = []
        all_true_cls = []

        with torch.no_grad():
            for X_batch, y_reg_batch, y_cls_batch, mask_batch, _signal_batch in test_loader:
                outputs = model(X_batch.to(device), mask=mask_batch.to(device))
                all_ret.append(outputs['ret'].cpu().numpy())
                all_path_reg.append(outputs['path_reg'].cpu().numpy())
                all_path_cls.append(torch.softmax(outputs['path_cls'], dim=1).cpu().numpy())
                all_q10.append(outputs['ret_q10'].cpu().numpy())
                all_q90.append(outputs['ret_q90'].cpu().numpy())
                all_true_reg.append(y_reg_batch.numpy())
                all_true_cls.append(y_cls_batch.numpy())

        pred_ret = np.concatenate(all_ret)
        pred_path_reg = np.concatenate(all_path_reg)
        pred_path_cls = np.concatenate(all_path_cls)
        pred_q10 = np.concatenate(all_q10)
        pred_q90 = np.concatenate(all_q90)
        true_reg = np.concatenate(all_true_reg)
        true_cls = np.concatenate(all_true_cls)

        export_kwargs = {
            'times': df_test['time'].values,
            'signals': df_test['signal'].values.astype(int),
            'pred_ret': pred_ret,
            'pred_path_reg': pred_path_reg,
            'pred_path_cls': pred_path_cls,
            'pred_q10': pred_q10,
            'pred_q90': pred_q90,
        }
        if entry_path_gt_available:
            export_kwargs['true_reg'] = true_reg
            export_kwargs['true_cls'] = true_cls
        export = build_entry_path_v1_quantile_export_frame(**export_kwargs)
        export_path = REPORTS_DIR / 'entry_path_v1_quantile_test_predictions.csv'
        export.to_csv(export_path, sep=';', index=False)
        crossed_quantile_rows = count_crossed_quantile_rows(export)
        row_count = int(len(export))
        report_path = REPORTS_DIR / 'evaluate_test_entry_path_v1_quantile.md'
        report_path.write_text(
            build_entry_path_v1_quantile_report_markdown(
                frame=export,
                model_name=ckpt_model_name,
                artifact_name=export_path.name,
                split_label='Test',
                checkpoint_epoch=ckpt.get('epoch'),
                checkpoint_metric_name=ckpt.get('metric_name'),
                checkpoint_metric_value=ckpt.get('best_metric'),
                crossed_quantile_rows=crossed_quantile_rows,
            ),
            encoding='utf-8',
        )

        print(f"  ✅ CSV сохранён: {export_path.name}")
        print(f"  ✅ Отчет сохранён: {report_path.name}")
        print(f"  row_count={row_count}")
        if ckpt.get('epoch') is not None and ckpt.get('best_metric') is not None:
            print(f"  checkpoint_epoch={ckpt.get('epoch')}")
            print(f"  best_val_{ckpt.get('metric_name', 'metric')}={ckpt.get('best_metric'):.4f}")
        if crossed_quantile_rows > 0:
            print(f"  ⚠ crossed_quantile_rows={crossed_quantile_rows}")
        if entry_path_gt_available:
            report_text = report_path.read_text(encoding='utf-8')
            summary_lines = [
                line for line in report_text.splitlines()
                if line.startswith('- ret_pearson_r:')
                or line.startswith('- interval_coverage:')
                or line.startswith('- median_interval_width:')
                or line.startswith('- val_score:')
                or line.startswith('- crossed_quantile_rows:')
            ]
            for line in summary_lines:
                print(f"  {line[2:]}")
        else:
            print("  ⚠ Test ground truth для entry_path_v1_quantile отсутствует; report written with N/A metrics.")
        print(f"{'═' * 60}\n")
        return

    if task == TRAILING_STOP_TARGET_QUANTILE_TARGET:
        all_q10 = []
        all_q50 = []
        all_q90 = []
        all_true = []

        with torch.no_grad():
            for X_batch, y_batch, mask_batch in test_loader:
                outputs = model(X_batch.to(device), mask=mask_batch.to(device))
                all_q10.append(outputs['q10'].cpu().numpy())
                all_q50.append(outputs['q50'].cpu().numpy())
                all_q90.append(outputs['q90'].cpu().numpy())
                all_true.append(y_batch.numpy())

        pred_q10 = np.concatenate(all_q10)
        pred_q50 = np.concatenate(all_q50)
        pred_q90 = np.concatenate(all_q90)
        true_target = np.concatenate(all_true).reshape(-1)
        ordered_q10, ordered_q50, ordered_q90 = _order_trailing_stop_quantiles(
            pred_q10,
            pred_q50,
            pred_q90,
        )
        metrics = compute_trailing_stop_quantile_metrics(
            true_target=true_target,
            pred_q10=ordered_q10,
            pred_q50=ordered_q50,
            pred_q90=ordered_q90,
        )
        metrics['val_score'] = metrics['q50_pearson_r']

        export = build_trailing_stop_quantile_export_frame(
            times=df_test_full['time'].values,
            signals=df_test_full['signal'].values.astype(int),
            pred_q10=pred_q10,
            pred_q50=pred_q50,
            pred_q90=pred_q90,
            true=true_target,
        )
        export_path = REPORTS_DIR / 'trailing_stop_target_quantile_test_predictions.csv'
        export.to_csv(export_path, sep=';', index=False)
        report_path = REPORTS_DIR / 'evaluate_test_trailing_stop_target_quantile_v1.md'
        report_lines = [
            '# Trailing Stop Target Quantile Test Set Evaluation',
            '',
            f'**Модель**: {ckpt_model_name}',
            f'**Набор**: Test ({len(export)} строк)',
            '',
            '## Summary',
            '',
            f"- row_count: **{len(export)}**",
            f"- val_score: **{metrics['val_score']:.4f}**",
            f"- q50_pearson_r: **{metrics['q50_pearson_r']:.4f}**",
            f"- q50_mae: **{metrics['q50_mae']:.4f}**",
            f"- interval_coverage: **{metrics['interval_coverage']:.4f}**",
            f"- median_interval_width: **{metrics['median_interval_width']:.4f}**",
            '',
            '## Artifacts',
            '',
            f'- Predictions CSV: `{export_path.name}`',
        ]
        report_path.write_text('\n'.join(report_lines), encoding='utf-8')

        print(f"  ✅ CSV сохранён: {export_path.name}")
        print(f"  ✅ Отчет сохранён: {report_path.name}")
        print(f"  row_count={len(export)}")
        print(f"  val_score={metrics['val_score']:.4f}")
        print(f"  q50_pearson_r={metrics['q50_pearson_r']:.4f}")
        print(f"{'═' * 60}\n")
        return

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

    if task == TRAILING_STOP_TARGET:
        true_targets = df_test_full[TRAILING_STOP_TARGET_COLUMNS].values.astype(np.float32)
        per_target_metrics = {
            name: compute_regression_metrics(true_targets[:, idx], y_pred[:, idx])
            for idx, name in enumerate(TRAILING_STOP_TARGET_COLUMNS)
        }
        metrics = {
            'mae': float(np.mean([item['mae'] for item in per_target_metrics.values()])),
            'rmse': float(np.mean([item['rmse'] for item in per_target_metrics.values()])),
            'r2': float(np.mean([item['r2'] for item in per_target_metrics.values()])),
            'pearson_r': float(np.mean([item['pearson_r'] for item in per_target_metrics.values()])),
            'per_target': per_target_metrics,
        }
        export = build_trailing_stop_export_frame(
            times=df_test_full['time'].values,
            signals=df_test_full['signal'].values.astype(int),
            pred=y_pred,
            true=true_targets,
        )
        export_path = REPORTS_DIR / 'trailing_stop_target_test_predictions.csv'
        export.to_csv(export_path, sep=';', index=False)
        report_path = REPORTS_DIR / 'evaluate_test_trailing_stop_target_v1.md'
        report_lines = [
            '# Trailing Stop Target Test Set Evaluation',
            '',
            f'**Модель**: {ckpt_model_name}',
            f'**Набор**: Test ({len(export)} строк)',
            '',
            '## Summary',
            '',
            f"- row_count: **{len(export)}**",
            f"- mae: **{metrics['mae']:.4f}**",
            f"- rmse: **{metrics['rmse']:.4f}**",
            f"- r2: **{metrics['r2']:.4f}**",
            f"- pearson_r: **{metrics['pearson_r']:.4f}**",
            '',
            '## Artifacts',
            '',
            f'- Predictions CSV: `{export_path.name}`',
        ]
        report_path.write_text('\n'.join(report_lines), encoding='utf-8')

        print(f"  ✅ CSV сохранён: {export_path.name}")
        print(f"  ✅ Отчет сохранён: {report_path.name}")
        print(f"  row_count={len(export)}")
        print(f"  mae={metrics['mae']:.4f}")
        print(f"  rmse={metrics['rmse']:.4f}")
        print(f"  r2={metrics['r2']:.4f}")
        print(f"  pearson_r={metrics['pearson_r']:.4f}")
        print(f"{'═' * 60}\n")
        return

    # ── Triple Barrier Evaluation ─────────────────────────────────────────────
    if task == 'triple_barrier':
        print(f"\n{'─' * 60}")
        print("📊 Triple Barrier OOS Evaluation...")
        if not TB_CALIBRATOR_PATH.exists():
            raise FileNotFoundError(f"Калибратор вероятностей не найден: {TB_CALIBRATOR_PATH}")

        y_proba = 1.0 / (1.0 + np.exp(-y_pred))
        calibrator_bundle = load_tb_probability_calibrator(TB_CALIBRATOR_PATH)
        y_proba = apply_tb_probability_calibration(y_proba, calibrator_bundle)

        df_test = pd.read_csv(TEST_FILE, sep=CSV_SEP, low_memory=False)
        y_true_raw = df_test[TB_TARGET_NAMES].values.astype(np.float32)
        y_true_binary = np.where(y_true_raw == 1.0, 1.0, 0.0)

        metrics = compute_binary_classification_metrics(y_true_binary, y_proba, TB_TARGET_NAMES)

        selected_theta = theta
        selected_min_ev = min_ev
        selected_rule = None
        if TB_RULE_PATH.exists() and theta == 2.665 and min_ev == 0.0:
            selected_rule = json.loads(TB_RULE_PATH.read_text(encoding='utf-8'))
            selected_theta = float(selected_rule['theta'])
            selected_min_ev = float(selected_rule.get('min_ev', 0.0))

        df_signals = tb_proba_to_signals(
            y_proba,
            theta=selected_theta,
            min_ev=selected_min_ev,
            target_names=TB_TARGET_NAMES,
        )
        signal_summary = evaluate_tb_signal_rule(df_signals, y_true_raw)

        print(f"\n🏆 Out-of-Sample Triple Barrier Results:")
        print(f"  Mean AUC: {metrics['mean_auc']:.4f}")
        print(f"  Signal rule: θ={selected_theta:.3f}, min_ev={selected_min_ev:.2f}")
        print(f"  Trades={signal_summary['trades']}, Wins={signal_summary['wins']}, "
              f"Losses={signal_summary['losses']}, Timeouts={signal_summary['timeouts']}, "
              f"PF={signal_summary['pf']:.2f}")
        print(f"\n  Per-target results:")
        print(f"  {'Target':<20} {'AUC':>8} {'Prec':>8} {'Recall':>8} {'Pos%':>8}")
        print(f"  {'─'*52}")
        for name, tm in metrics['per_target'].items():
            print(f"  {name:<20} {tm['auc']:>8.4f} {tm['precision']:>8.4f} "
                  f"{tm['recall']:>8.4f} {tm['pos_rate']:>8.1%}")

        # Generate report
        report_path = REPORTS_DIR / 'evaluate_test_tb.md'
        lines = [
            f"# Triple Barrier Test Set Evaluation",
            f"",
            f"**Модель**: {ckpt_model_name}",
            f"**Набор**: Test ({len(y_pred)} строк)",
            f"**Mean AUC**: {metrics['mean_auc']:.4f}",
            f"**Калибратор**: `{TB_CALIBRATOR_PATH.name}`",
            f"",
            f"## Frozen Signal Rule",
            f"",
            f"- θ: **{selected_theta:.3f}**",
            f"- min_ev: **{selected_min_ev:.2f}**",
            f"- Trades: {signal_summary['trades']}",
            f"- Wins / Losses / Timeouts: {signal_summary['wins']} / {signal_summary['losses']} / {signal_summary['timeouts']}",
            f"- Win Rate: {signal_summary['win_rate']:.1%}",
            f"- Profit Factor: **{signal_summary['pf']:.2f}**",
            f"- Dominant target: `{signal_summary['dominant_target']}` ({signal_summary['dominant_target_count']} trades)",
            f"",
            f"## Per-target AUC",
            f"| Target | AUC | Precision | Recall | Pos Rate |",
            f"|--------|-----|-----------|--------|----------|",
        ]
        for name, tm in metrics['per_target'].items():
            lines.append(f"| {name} | {tm['auc']:.4f} | {tm['precision']:.4f} | "
                        f"{tm['recall']:.4f} | {tm['pos_rate']:.1%} |")

        if selected_rule:
            lines.extend([
                f"",
                f"## Rule Source",
                f"",
                f"Loaded from `{TB_RULE_PATH.name}`",
            ])
        report_path.write_text("\n".join(lines), 'utf-8')

        print(f"\n✅ Отчет сохранён: {report_path.name}")
        print(f"{'═' * 60}\n")
        return

    # ── Анализ и Торговое Правило ───────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("📈 Симуляция торгового правила...")

    if task in [TRADE_OUTCOME_TARGET, TRADE_PNL_TARGET, ARCHETYPE_TARGET]:
        outcome_frame = load_outcome_test_frame()
        signal_mask = outcome_frame['signal'].values.astype(int) != 0
        realized_pnl = outcome_frame['trade_pnl_h12_atr'].values.astype(np.float64)

        if task in BINARY_CLASSIFICATION_TARGETS:
            score = torch.softmax(torch.from_numpy(y_pred), dim=1).numpy()[:, 1]
            if score_threshold is None:
                score_threshold = 0.5
            truth_col = 'trade_outcome_h12' if task == TRADE_OUTCOME_TARGET else 'archetype_target'
            base_metrics = compute_single_binary_classification_metrics(
                outcome_frame[truth_col].values.astype(int),
                score,
                threshold=score_threshold,
            )
            main_metric_name = 'AUC'
            main_metric_value = base_metrics['auc']
        else:
            score = y_pred.astype(np.float64)
            if score_threshold is None:
                score_threshold = 0.0
            base_metrics = compute_regression_metrics(realized_pnl, score)
            main_metric_name = 'Pearson r'
            main_metric_value = base_metrics['pearson_r']

        trade_mask = signal_mask & (score >= score_threshold)
        selected = outcome_frame.loc[trade_mask].copy()
        selected_pnl = selected['trade_pnl_h12_atr'].values.astype(np.float64)

        trades = int(len(selected))
        wins = int((selected_pnl > 0).sum())
        losses = int((selected_pnl <= 0).sum())
        gross_profit = float(selected_pnl[selected_pnl > 0].sum())
        gross_loss = float(-selected_pnl[selected_pnl < 0].sum())
        pf = gross_profit / gross_loss if gross_loss > 0 else (np.inf if gross_profit > 0 else 0.0)
        win_rate = wins / trades if trades > 0 else 0.0
        coverage = trades / int(signal_mask.sum()) if signal_mask.sum() > 0 else 0.0
        mean_pnl = float(selected_pnl.mean()) if trades > 0 else 0.0

        yearly_lines = []
        if trades > 0:
            selected['year'] = selected['time'].dt.year
            for year, group in selected.groupby('year', dropna=True):
                pnl = group['trade_pnl_h12_atr'].values.astype(np.float64)
                gp = float(pnl[pnl > 0].sum())
                gl = float(-pnl[pnl < 0].sum())
                year_pf = gp / gl if gl > 0 else (np.inf if gp > 0 else 0.0)
                yearly_lines.append(f"- {int(year)}: trades={len(group)}, pf={year_pf:.4f}, mean_pnl={pnl.mean():.4f}")

        print("\n🏆 Outcome-Aligned Test Performance:")
        print(f"  {main_metric_name}: {main_metric_value:.4f}")
        print(f"  Score threshold: {score_threshold:.4f}")
        print(f"  Trades: {trades} из {int(signal_mask.sum())} signal rows ({coverage*100:.1f}%)")
        print(f"  Wins / Losses: {wins} / {losses}")
        print(f"  Win Rate: {win_rate*100:.2f}%")
        print(f"  Mean PnL (ATR): {mean_pnl:.4f}")
        print(f"  Profit Factor: {pf:.4f}")

        report_path = REPORTS_DIR / f'evaluate_test_{task}.md'
        lines = [
            f"# Outcome-Aligned Test Evaluation",
            f"",
            f"**Модель**: {ckpt_model_name}",
            f"**Задача**: {task}",
            f"**Набор**: Test ({len(score)} строк)",
            f"**{main_metric_name}**: {main_metric_value:.4f}",
            f"**Score threshold**: {score_threshold:.4f}",
            f"",
            f"## Trading Summary",
            f"",
            f"- Trades: {trades}",
            f"- Signal rows considered: {int(signal_mask.sum())}",
            f"- Coverage: {coverage:.1%}",
            f"- Wins / Losses: {wins} / {losses}",
            f"- Win Rate: {win_rate:.1%}",
            f"- Mean PnL (ATR): {mean_pnl:.4f}",
            f"- Profit Factor: {pf:.4f}",
        ]
        if task in BINARY_CLASSIFICATION_TARGETS:
            lines.extend([
                f"",
                f"## Classification Metrics",
                f"",
                f"- Precision: {base_metrics['precision']:.4f}",
                f"- Recall: {base_metrics['recall']:.4f}",
                f"- F1: {base_metrics['f1']:.4f}",
            ])
        else:
            lines.extend([
                f"",
                f"## Regression Metrics",
                f"",
                f"- MAE: {base_metrics['mae']:.4f}",
                f"- RMSE: {base_metrics['rmse']:.4f}",
                f"- R2: {base_metrics['r2']:.4f}",
                f"- Pearson r: {base_metrics['pearson_r']:.4f}",
            ])
        if yearly_lines:
            lines.extend([
                f"",
                f"## Yearly Stability",
                f"",
                *yearly_lines,
            ])
        if frozen_outcome and frozen_outcome.get('winner', {}).get('task') == task:
            lines.extend([
                f"",
                f"## Frozen Validation Winner",
                f"",
                f"Loaded from `{FROZEN_OUTCOME_TARGET_PATH.name}`",
            ])
        report_path.write_text("\n".join(lines), 'utf-8')

        print(f"\n✅ Отчет сохранён в: {report_path.name}")
        print(f"{'═' * 60}\n")
        return

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
    parser.add_argument('--task', type=str, default='regression_updn',
                        choices=[
                            'regression',
                            'regression_updn',
                            'triple_barrier',
                            ENTRY_PATH_TARGET,
                            ENTRY_PATH_V1_QUANTILE_TARGET,
                            TRADE_OUTCOME_TARGET,
                            TRADE_PNL_TARGET,
                            ARCHETYPE_TARGET,
                            TRAILING_STOP_TARGET,
                            TRAILING_STOP_TARGET_QUANTILE_TARGET,
                        ])
    parser.add_argument('--horizon', type=int, default=12)
    parser.add_argument('--theta', type=float, default=2.665, help='Торговый порог (ratio pred_up/pred_dn)')
    parser.add_argument('--min-ev', type=float, default=0.0, help='Минимальный EV для TB signal rule')
    parser.add_argument('--score-threshold', type=float, default=None,
                        help='Порог score для outcome-aligned задач. Если не задан, берётся из frozen_outcome_target.json.')
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
        min_ev=args.min_ev,
        score_threshold=args.score_threshold,
        seed=args.seed,
        optuna_json=args.optuna_json,
    )
