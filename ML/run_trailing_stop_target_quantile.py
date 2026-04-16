from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

from API.generate_signals import generate_signals
from ML.benchmark_trailing_stop_target_quantile import _jsonable, run_benchmark
from ML.data_loader import task_checkpoint_suffix
from ML.evaluate_test import run_evaluation
from ML.train import CHECKPOINTS_DIR, REPORTS_DIR, train_model
from ML.trailing_stop_target_quantile_task import TRAILING_STOP_TARGET_QUANTILE_TARGET


RUN_SLUG = 'transformer_seq20_x3_quantile'
TARGET_COLUMN = 'trail_48_pnl_atr_x3'


def _copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _same_run_config(
    saved_payload: dict[str, object],
    *,
    epochs: int,
    patience: int,
    batch_size: int,
    seed: int,
    min_pf: float,
) -> bool:
    saved_config = saved_payload.get('config', {})
    if not isinstance(saved_config, dict):
        return False
    return saved_config == {
        'seq_len': 20,
        'target_column': TARGET_COLUMN,
        'epochs': epochs,
        'patience': patience,
        'batch_size': batch_size,
        'seed': seed,
        'min_pf': min_pf,
    }


def run_single_config(
    *,
    output_dir: Path,
    epochs: int,
    patience: int,
    batch_size: int,
    seed: int,
    min_pf: float,
    skip_existing: bool,
) -> dict[str, object]:
    run_dir = output_dir / RUN_SLUG
    run_dir.mkdir(parents=True, exist_ok=True)

    summary_path = run_dir / 'summary.json'
    if skip_existing and summary_path.exists():
        saved_payload = json.loads(summary_path.read_text(encoding='utf-8'))
        if _same_run_config(
            saved_payload,
            epochs=epochs,
            patience=patience,
            batch_size=batch_size,
            seed=seed,
            min_pf=min_pf,
        ):
            return saved_payload

    started_at = time.time()
    train_result = train_model(
        model_name='transformer',
        task=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        epochs=epochs,
        batch_size=batch_size,
        lr=1e-3,
        weight_decay=1e-4,
        patience=patience,
        seed=seed,
        use_scaler=False,
        use_weighted_sampler=False,
        seq_len=20,
        clear_cache=False,
        silent=False,
        model_kwargs={},
    )

    suffix = task_checkpoint_suffix(TRAILING_STOP_TARGET_QUANTILE_TARGET)
    checkpoint_path = CHECKPOINTS_DIR / f'transformer{suffix}_best.pt'
    run_checkpoint_path = run_dir / 'checkpoint.pt'
    _copy_if_exists(checkpoint_path, run_checkpoint_path)

    run_evaluation(
        model_name='transformer',
        checkpoint_path=str(run_checkpoint_path),
        task=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        seed=seed,
        seq_len_override=20,
    )
    _copy_if_exists(
        REPORTS_DIR / 'evaluate_test_trailing_stop_target_quantile_v1.md',
        run_dir / 'evaluate_test_trailing_stop_target_quantile_v1.md',
    )
    _copy_if_exists(
        REPORTS_DIR / 'trailing_stop_target_quantile_test_predictions.csv',
        run_dir / 'trailing_stop_target_quantile_test_predictions.csv',
    )

    export_prefix = run_dir / 'trailing_stop_target_quantile'
    generate_signals(
        model_name='transformer',
        task=TRAILING_STOP_TARGET_QUANTILE_TARGET,
        seed=seed,
        research_out_prefix=str(export_prefix),
        seq_len_override=20,
    )

    benchmark = run_benchmark(
        validation_csv=run_dir / 'trailing_stop_target_quantile_validation_predictions.csv',
        test_csv=run_dir / 'trailing_stop_target_quantile_test_predictions.csv',
        output_dir=run_dir / 'benchmark',
        min_pf=min_pf,
    )

    payload = {
        'config': {
            'seq_len': 20,
            'target_column': TARGET_COLUMN,
            'epochs': epochs,
            'patience': patience,
            'batch_size': batch_size,
            'seed': seed,
            'min_pf': min_pf,
        },
        'train_result': _jsonable(train_result),
        'checkpoint_path': str(run_checkpoint_path),
        'exports': {
            'validation_csv': str(run_dir / 'trailing_stop_target_quantile_validation_predictions.csv'),
            'test_csv': str(run_dir / 'trailing_stop_target_quantile_test_predictions.csv'),
        },
        'benchmark': _jsonable(benchmark),
        'runtime_sec': time.time() - started_at,
    }
    summary_path.write_text(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run bounded trailing-stop target quantile benchmark.')
    parser.add_argument('--output-dir', default='ML/reports/trailing_stop_target_quantile')
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--patience', type=int, default=2)
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--min-pf', type=float, default=1.0)
    parser.add_argument('--skip-existing', action='store_true')
    return parser.parse_args()


def main() -> dict[str, object]:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_single_config(
        output_dir=output_dir,
        epochs=args.epochs,
        patience=args.patience,
        batch_size=args.batch_size,
        seed=args.seed,
        min_pf=args.min_pf,
        skip_existing=args.skip_existing,
    )
    (output_dir / 'manifest.json').write_text(json.dumps(_jsonable({'runs': [result]}), ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(_jsonable(result), ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    main()
