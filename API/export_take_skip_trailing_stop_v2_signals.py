# =============================================================================
# Файл: export_take_skip_trailing_stop_v2_signals.py
# Назначение: Применение frozen take/skip v2 rule к prediction CSV и экспорт time;signal для MT4
# Обновлён: 2026-05-12
# Входные данные:
#   - prediction CSV с колонками time, signal, pred_take_* (откуда: evaluate/export или frozen reconstruction)
#   - rule JSON из ML/reports/take_skip_trailing_stop_v2_*_selected_rule.json
#   - optional base CSV с полным рядом time/signal (откуда: DATA/Nero_*_labeled.csv)
# Выходные данные:
#   - CSV time;signal (куда: output_path, optional MT/tester/files и MT/MQL4/Files)
# Использование:
#   python -m API.export_take_skip_trailing_stop_v2_signals --predictions ... --rule-path ... --output ...
# Примечания:
#   - rule поддерживает только selector = prob_ge_threshold или top_k_probability
#   - top_k применяется только к активным строкам signal != 0
# =============================================================================

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path

import pandas as pd


MT4_TESTER_SIGNALS = Path('MT/tester/files/ml_signals.csv')
MT4_RUNTIME_SIGNALS = Path('MT/MQL4/Files/ml_signals.csv')
SUPPORTED_SELECTORS = {'prob_ge_threshold', 'top_k_probability'}
SUPPORTED_DIAGNOSTIC_DIRECTION_SOURCES = {'predict', 'fractal0_direction'}


def write_csv_atomic(frame: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + '.tmp')
    frame.to_csv(temp, sep=';', index=False)
    os.replace(temp, target)


def append_newer_signal_rows_atomic(frame: pd.DataFrame, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.stat().st_size == 0:
        write_csv_atomic(frame, target)
        return

    existing = pd.read_csv(target, sep=';')
    if {'time', 'signal'}.difference(existing.columns):
        raise ValueError(f'existing signal CSV must contain time and signal columns: {target}')
    if existing.empty:
        merged = frame
    else:
        last_time = str(existing['time'].astype(str).iloc[-1])
        new_rows = frame.loc[frame['time'].astype(str) > last_time].copy()
        if new_rows.empty:
            return
        merged = pd.concat([existing, new_rows], ignore_index=True)
    write_csv_atomic(merged, target)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_prediction_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(Path(path), sep=';')
    if {'time', 'signal'}.difference(frame.columns):
        raise ValueError('prediction CSV must contain time and signal columns')
    return frame.drop_duplicates(subset=['time', 'signal'], keep='last').reset_index(drop=True)


def load_rule_payload_from_file(rule_path: str | Path) -> dict:
    raw = json.loads(Path(rule_path).read_text(encoding='utf-8'))
    winner = raw.get('winner', {})
    selector = str(winner.get('selector', ''))
    score_target = str(winner.get('score_target', ''))
    threshold = float(winner.get('threshold', -1.0))
    exit_multiplier = int(winner.get('exit_atr_multiplier', 0))

    if selector not in SUPPORTED_SELECTORS:
        supported = ', '.join(sorted(SUPPORTED_SELECTORS))
        raise ValueError(f'unsupported selector: {selector}. Supported: {supported}')
    if not score_target:
        raise ValueError('rule winner must contain score_target')
    if selector == 'prob_ge_threshold' and not 0.0 <= threshold <= 1.0:
        raise ValueError('prob_ge_threshold rule must use threshold in [0, 1]')
    if selector == 'top_k_probability' and not 0.0 < threshold <= 1.0:
        raise ValueError('top_k_probability rule must use threshold in (0, 1]')
    if exit_multiplier <= 0:
        raise ValueError('rule winner must contain positive exit_atr_multiplier')

    return {
        'mode': str(raw.get('mode', '')),
        'winner': {
            'score_target': score_target,
            'selector': selector,
            'threshold': threshold,
            'exit_atr_multiplier': exit_multiplier,
        },
        'frozen_validation': raw.get('frozen_validation', {}),
        'frozen_test': raw.get('frozen_test', {}),
    }


def apply_rule(frame: pd.DataFrame, rule_payload: dict) -> pd.Series:
    winner = rule_payload['winner']
    score_col = f"pred_{winner['score_target']}"
    selector = winner['selector']
    threshold = float(winner['threshold'])

    if score_col not in frame.columns:
        raise ValueError(f'missing score column: {score_col}')

    scores = pd.to_numeric(frame[score_col], errors='coerce').fillna(float('-inf'))
    active = frame['signal'].astype(int) != 0
    selected = pd.Series(False, index=frame.index)

    if selector == 'prob_ge_threshold':
        return active & (scores >= threshold)

    active_idx = frame.index[active]
    if len(active_idx) == 0:
        return selected

    k_count = max(1, int(math.ceil(len(active_idx) * threshold)))
    top_idx = scores.loc[active_idx].nlargest(k_count).index
    selected.loc[top_idx] = True
    return selected


def diagnostic_signal_from_fractal0(fractal0: pd.Series) -> pd.Series:
    direction = fractal0.astype(str).str.split(':', n=3).str[2]
    direction = pd.to_numeric(direction, errors='coerce').fillna(0).astype(int)

    diagnostic_signal = pd.Series(0, index=fractal0.index, dtype='int64')
    diagnostic_signal.loc[direction == -1] = 1
    diagnostic_signal.loc[direction == 1] = -1
    return diagnostic_signal


def build_diagnostic_all_rows_export(
    *,
    frame: pd.DataFrame,
    base: pd.DataFrame,
    rule_payload: dict,
    target_signals_per_year: int,
    direction_source: str = 'predict',
) -> pd.DataFrame:
    winner = rule_payload['winner']
    score_col = f"pred_{winner['score_target']}"
    if score_col not in frame.columns:
        raise ValueError(f'missing score column: {score_col}')
    if direction_source not in SUPPORTED_DIAGNOSTIC_DIRECTION_SOURCES:
        supported = ', '.join(sorted(SUPPORTED_DIAGNOSTIC_DIRECTION_SOURCES))
        raise ValueError(f'unsupported diagnostic_direction_source: {direction_source}. Supported: {supported}')
    if direction_source == 'predict' and 'predict' not in base.columns:
        raise ValueError('diagnostic_all_rows with predict direction requires base_csv with predict column')
    if direction_source == 'fractal0_direction' and 'fractal0' not in base.columns:
        raise ValueError('diagnostic_all_rows with fractal0_direction requires base_csv with fractal0 column')
    if target_signals_per_year <= 0:
        raise ValueError('diagnostic_target_signals_per_year must be positive')

    base = base.drop_duplicates(subset=['time'], keep='last').reset_index(drop=True)
    direction_cols = ['time', 'predict'] if direction_source == 'predict' else ['time', 'fractal0']
    merged = frame[['time', score_col]].merge(base[direction_cols], on='time', how='left', validate='many_to_one')
    merged['score'] = pd.to_numeric(merged[score_col], errors='coerce').fillna(float('-inf'))
    if direction_source == 'predict':
        predict = pd.to_numeric(merged['predict'], errors='coerce').fillna(0.0)
        merged['diagnostic_signal'] = 0
        merged.loc[predict > 0, 'diagnostic_signal'] = 1
        merged.loc[predict < 0, 'diagnostic_signal'] = -1
    else:
        # Offline diagnostic used sign(predict), and predict = -back * direction.
        # Online raw Nero.csv has no future-derived predict, so use the equivalent
        # reversal sign from current fractal0 direction.
        merged['diagnostic_signal'] = diagnostic_signal_from_fractal0(merged['fractal0'])
    merged['year'] = pd.to_datetime(merged['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year

    selected = pd.Series(False, index=merged.index)
    candidates = merged.loc[(merged['diagnostic_signal'] != 0) & merged['year'].notna()].copy()
    for _, group in candidates.groupby('year', sort=False):
        top_idx = group.nlargest(int(target_signals_per_year), 'score').index
        selected.loc[top_idx] = True

    export = frame[['time']].copy()
    export['signal'] = 0
    export.loc[selected, 'signal'] = merged.loc[selected, 'diagnostic_signal'].astype(int)
    return export.drop_duplicates(subset=['time'], keep='last').reset_index(drop=True)


def export_signals(
    *,
    predictions_path: str | Path,
    rule_path: str | Path,
    output_path: str | Path,
    base_csv: str | Path | None = None,
    copy_to_mt4: bool = False,
    metadata_output: str | Path | None = None,
    label: str = 'take_skip_trailing_stop_v2',
    diagnostic_all_rows: bool = False,
    diagnostic_target_signals_per_year: int | None = None,
    diagnostic_direction_source: str = 'predict',
    append_to_mt4: bool = False,
) -> Path:
    if append_to_mt4 and not copy_to_mt4:
        raise ValueError('append_to_mt4 requires copy_to_mt4')

    frame = load_prediction_frame(predictions_path)
    rule_payload = load_rule_payload_from_file(rule_path)
    if diagnostic_all_rows:
        if base_csv is None:
            raise ValueError('diagnostic_all_rows requires base_csv')
        if diagnostic_target_signals_per_year is None:
            raise ValueError('diagnostic_all_rows requires diagnostic_target_signals_per_year')
        direction_usecols = ['time', 'predict'] if diagnostic_direction_source == 'predict' else ['time', 'fractal0']
        base = pd.read_csv(Path(base_csv), sep=';', usecols=direction_usecols)
        export = build_diagnostic_all_rows_export(
            frame=frame,
            base=base,
            rule_payload=rule_payload,
            target_signals_per_year=int(diagnostic_target_signals_per_year),
            direction_source=diagnostic_direction_source,
        )
    else:
        selected_mask = apply_rule(frame, rule_payload)

        selected = frame[['time', 'signal']].copy()
        selected.loc[~selected_mask, 'signal'] = 0

        if base_csv is None:
            export = selected
        else:
            base = pd.read_csv(Path(base_csv), sep=';', usecols=['time', 'signal'])
            original_signal = pd.to_numeric(base['signal'], errors='coerce').fillna(0).astype(int)
            chosen_pairs = set(
                zip(
                    selected.loc[selected['signal'] != 0, 'time'].astype(str),
                    selected.loc[selected['signal'] != 0, 'signal'].astype(int),
                )
            )
            export = base[['time', 'signal']].copy()
            export['signal'] = [
                sig if (str(time), int(sig)) in chosen_pairs else 0
                for time, sig in zip(base['time'], original_signal)
            ]

    output = Path(output_path)
    write_csv_atomic(export, output)

    if metadata_output is not None:
        metadata = build_export_metadata(
            label=label,
            predictions_path=predictions_path,
            rule_path=rule_path,
            output_path=output,
            export=export,
        )
        metadata_path = Path(metadata_output)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')

    if copy_to_mt4:
        writer = append_newer_signal_rows_atomic if append_to_mt4 else write_csv_atomic
        writer(export, MT4_TESTER_SIGNALS)
        writer(export, MT4_RUNTIME_SIGNALS)

    return output


def build_export_metadata(
    *,
    label: str,
    predictions_path: str | Path,
    rule_path: str | Path,
    output_path: str | Path,
    export: pd.DataFrame,
) -> dict:
    signals = pd.to_numeric(export['signal'], errors='coerce').fillna(0).astype(int)
    nonzero = export.loc[signals != 0].copy()
    nonzero_signals = signals.loc[signals != 0]
    time_counts = Counter(nonzero['time'].astype(str))
    by_time = nonzero.assign(signal=nonzero_signals.values).groupby('time')['signal'].nunique() if not nonzero.empty else pd.Series(dtype=int)
    return {
        'label': label,
        'predictions_path': str(predictions_path),
        'rule_path': str(rule_path),
        'output_path': str(output_path),
        'predictions_sha256': sha256_file(predictions_path),
        'rule_sha256': sha256_file(rule_path),
        'output_sha256': sha256_file(output_path),
        'rows_total': int(len(export)),
        'nonzero_rows': int(len(nonzero)),
        'buy_rows': int((nonzero_signals > 0).sum()),
        'sell_rows': int((nonzero_signals < 0).sum()),
        'duplicate_time_rows': int(sum(count - 1 for count in time_counts.values() if count > 1)),
        'same_time_opposite_signal_groups': int((by_time > 1).sum()) if not by_time.empty else 0,
    }


def parse_args():
    parser = argparse.ArgumentParser(description='Apply frozen take/skip v2 rule to prediction CSV and export time;signal.')
    parser.add_argument('--predictions', required=True, help='Prediction CSV with pred_take_* columns.')
    parser.add_argument('--rule-path', required=True, help='Path to take_skip_trailing_stop_v2_*_selected_rule.json')
    parser.add_argument('--output', required=True, help='Output CSV path for time;signal')
    parser.add_argument('--base-csv', default=None, help='Optional full time/signal CSV to expand sparse predictions into full series.')
    parser.add_argument('--copy-to-mt4', action='store_true', help='Also copy exported CSV to tester/runtime ml_signals.csv paths.')
    parser.add_argument('--append-to-mt4', action='store_true', help='When copying to MT4, preserve existing rows and append only rows newer than the current file tail.')
    parser.add_argument('--metadata-output', default=None, help='Optional JSON metadata output with hashes and signal counts.')
    parser.add_argument('--label', default='take_skip_trailing_stop_v2', help='Label stored in metadata output.')
    parser.add_argument('--diagnostic-all-rows', action='store_true', help='Build diagnostic signals from all rows using base_csv predict sign as direction.')
    parser.add_argument('--diagnostic-target-signals-per-year', type=int, default=None, help='Top-N diagnostic signals per calendar year.')
    parser.add_argument(
        '--diagnostic-direction-source',
        choices=sorted(SUPPORTED_DIAGNOSTIC_DIRECTION_SOURCES),
        default='predict',
        help='Direction source for diagnostic_all_rows: predict for labeled offline data, fractal0_direction for raw online Nero.csv.',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    path = export_signals(
        predictions_path=args.predictions,
        rule_path=args.rule_path,
        output_path=args.output,
        base_csv=args.base_csv,
        copy_to_mt4=args.copy_to_mt4,
        metadata_output=args.metadata_output,
        label=args.label,
        diagnostic_all_rows=args.diagnostic_all_rows,
        diagnostic_target_signals_per_year=args.diagnostic_target_signals_per_year,
        diagnostic_direction_source=args.diagnostic_direction_source,
        append_to_mt4=args.append_to_mt4,
    )
    print(path)
    return path


if __name__ == '__main__':
    main()
