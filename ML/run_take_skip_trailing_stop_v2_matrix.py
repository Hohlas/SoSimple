from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

from API.generate_signals import generate_signals
from ML.benchmark_take_skip_trailing_stop_v2 import run_benchmark
from ML.data_loader import task_checkpoint_suffix
from ML.evaluate_test import run_evaluation
from ML.take_skip_trailing_stop_v2_task import TAKE_SKIP_TRAILING_STOP_V2_COLUMNS, TAKE_SKIP_TRAILING_STOP_V2_TARGET
from ML.train import CHECKPOINTS_DIR, REPORTS_DIR, train_model


DEFAULT_SEQ_LENS = (20, 50, 100)


def config_slug(seq_len: int) -> str:
    return f'transformer_seq{seq_len}'


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, 'tolist'):
        return value.tolist()
    if hasattr(value, 'item'):
        return value.item()
    return value


def _copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _copy_required(source: Path, destination: Path, label: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    if not source.exists():
        raise FileNotFoundError(f'required {label} missing: {source}')
    shutil.copy2(source, destination)


def run_single_config(
    *,
    seq_len: int,
    output_dir: Path,
    epochs: int,
    patience: int,
    batch_size: int,
    seed: int,
    min_pf: float,
    min_trades_per_year: float,
) -> dict[str, object]:
    slug = config_slug(seq_len)
    run_dir = output_dir / slug
    run_dir.mkdir(parents=True, exist_ok=True)

    started_at = time.time()
    train_result = train_model(
        model_name='transformer',
        task=TAKE_SKIP_TRAILING_STOP_V2_TARGET,
        epochs=epochs,
        batch_size=batch_size,
        lr=1e-3,
        weight_decay=1e-4,
        patience=patience,
        seed=seed,
        use_scaler=False,
        use_weighted_sampler=False,
        seq_len=seq_len,
        clear_cache=False,
        silent=False,
        model_kwargs={},
    )

    suffix = task_checkpoint_suffix(TAKE_SKIP_TRAILING_STOP_V2_TARGET)
    checkpoint_path = CHECKPOINTS_DIR / f'transformer{suffix}_best.pt'
    run_checkpoint_path = run_dir / 'checkpoint.pt'
    _copy_required(checkpoint_path, run_checkpoint_path, 'checkpoint')

    run_evaluation(
        model_name='transformer',
        checkpoint_path=str(run_checkpoint_path),
        task=TAKE_SKIP_TRAILING_STOP_V2_TARGET,
        seed=seed,
        seq_len_override=seq_len,
    )
    _copy_if_exists(REPORTS_DIR / 'evaluate_test_take_skip_trailing_stop_v2.md', run_dir / 'evaluate_test_take_skip_trailing_stop_v2.md')
    _copy_if_exists(REPORTS_DIR / 'take_skip_trailing_stop_v2_test_predictions.csv', run_dir / 'take_skip_trailing_stop_v2_test_predictions.csv')

    export_prefix = run_dir / 'take_skip_trailing_stop_v2'
    generate_signals(
        model_name='transformer',
        task=TAKE_SKIP_TRAILING_STOP_V2_TARGET,
        seed=seed,
        research_out_prefix=str(export_prefix),
        seq_len_override=seq_len,
    )

    benchmark = run_benchmark(
        validation_csv=run_dir / 'take_skip_trailing_stop_v2_validation_predictions.csv',
        test_csv=run_dir / 'take_skip_trailing_stop_v2_test_predictions.csv',
        output_dir=run_dir / 'benchmark',
        min_pf=min_pf,
        min_trades_per_year=min_trades_per_year,
    )

    payload = {
        'config': {
            'seq_len': seq_len,
            'epochs': epochs,
            'patience': patience,
            'batch_size': batch_size,
            'seed': seed,
            'min_pf': min_pf,
            'min_trades_per_year': min_trades_per_year,
            'target_columns': list(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS),
        },
        'train_result': _jsonable(train_result),
        'checkpoint_path': str(run_checkpoint_path),
        'exports': {
            'validation_csv': str(run_dir / 'take_skip_trailing_stop_v2_validation_predictions.csv'),
            'test_csv': str(run_dir / 'take_skip_trailing_stop_v2_test_predictions.csv'),
        },
        'benchmark': _jsonable(benchmark),
        'runtime_sec': time.time() - started_at,
    }
    (run_dir / 'summary.json').write_text(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run bounded take-skip trailing-stop v2 matrix.')
    parser.add_argument('--output-dir', default='ML/reports/take_skip_trailing_stop_v2_matrix')
    parser.add_argument('--seq-lens', nargs='*', type=int, default=list(DEFAULT_SEQ_LENS))
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--patience', type=int, default=2)
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--min-pf', type=float, default=1.0)
    parser.add_argument('--min-trades-per-year', type=float, default=6.0)
    return parser.parse_args()


def main() -> dict[str, object]:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    runs = [
        run_single_config(
            seq_len=seq_len,
            output_dir=output_dir,
            epochs=args.epochs,
            patience=args.patience,
            batch_size=args.batch_size,
            seed=args.seed,
            min_pf=args.min_pf,
            min_trades_per_year=args.min_trades_per_year,
        )
        for seq_len in args.seq_lens
    ]

    payload = {'seq_lens': list(args.seq_lens), 'runs': _jsonable(runs)}
    (output_dir / 'manifest.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


if __name__ == '__main__':
    main()
