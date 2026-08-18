# =============================================================================
# Файл: statistics/pair_spread/run_pair_spread.py
# Назначение: оркестратор двух ступеней kill-теста pair-spread; JSON-артефакты
# Обновлён: 2026-08-18
# Зависимости:
#   Входные данные:
#     - MT/MQL4/Files/M5/*_OHLC.csv, MT/MQL4/Files/H1/*_OHLC.csv (Task 2)
#     - MT/MQL4/Files/pair_spread_costs_snapshot.csv (Task 2)
#   Выходные данные:
#     - DATA/pair_spread/screening.json, DATA/pair_spread/backtest.json,
#       DATA/pair_spread/backtest_stress2x.json (при --stress-costs 2.0)
#   Внутренние зависимости: pair_data, screening, backtest (тот же каталог)
# Использование:
#   ./.venv/bin/python statistics/pair_spread/run_pair_spread.py [--stage 1|2|all]
#   [--stress-costs 2.0]
# Примечания: все пороги заморожены спекой 2026-08-17; изменения после запуска
#   только документированным решением.
# =============================================================================
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pair_data import (CANDIDATES, TEST_START, TRAIN_END, build_log_spreads,
                       load_ohlc_csv)
from screening import (ScreeningThresholds, engle_granger_pvalue, fit_beta,
                       half_life_bars, screening_metrics, verdict_pass)
from backtest import profit_factor, run_backtest, stationary_bootstrap_ci

ROOT = Path(__file__).resolve().parents[2]
M5_DIR = ROOT / 'MT' / 'MQL4' / 'Files' / 'M5'
H1_DIR = ROOT / 'MT' / 'MQL4' / 'Files' / 'H1'
COSTS_CSV = ROOT / 'MT' / 'MQL4' / 'Files' / 'pair_spread_costs_snapshot.csv'
OUT_DIR = ROOT / 'DATA' / 'pair_spread'

THRESHOLDS = ScreeningThresholds()  # заморожено спекой


def build_costs(snapshot_csv_path: Path) -> dict:
    df = pd.read_csv(snapshot_csv_path, sep=';')
    out = {}
    for _, row in df.iterrows():
        out[row['symbol']] = {
            'spread_price': float(row['spread_price']),
            'point': float(row['point']),
            'swap_long': float(row['swap_long']),
            'swap_short': float(row['swap_short']),
        }
    return out


def round_trip_cost_c(spread_a_price: float, spread_b_price: float,
                      price_a: float, price_b: float, beta: float) -> float:
    return 2.0 * (spread_a_price / price_a + abs(beta) * spread_b_price / price_b)


def stress_cost_c(cost_c: float, factor: float) -> float:
    """Стресс-множитель издержек (методология 12: обязательный стресс 2x)."""
    return cost_c * factor


def pair_verdict(m: dict) -> str:
    # Приоритет (аудит Q-1): слом коинтеграции на test убивает независимо от
    # PF и числа сделок (мощность EG-теста определяется барами, не сделками).
    # Гейт N ограничивает только SURVIVED (методология 06).
    if m['eg_p_test'] > 0.10:
        return 'KILLED'
    if m['n_trades'] < 100 or m['n_per_side_min'] < 30:
        return 'DIAGNOSTIC_ONLY'
    if m['pf'] >= 1.3 and m['bs_p05'] > 1.0:
        return 'SURVIVED'
    return 'KILLED'


def _load_legs(tf_dir: Path) -> dict[str, pd.DataFrame]:
    symbols = sorted({s for c in CANDIDATES.values() for s in c['legs']})
    return {s: load_ohlc_csv(tf_dir / f'{s}_OHLC.csv') for s in symbols}


def _stage1_for_tf(legs: dict[str, pd.DataFrame], costs: dict, tf: str) -> dict:
    results = {}
    for name, spec in CANDIDATES.items():
        sym_a, sym_b = spec['legs']
        df_a, df_b = legs[sym_a], legs[sym_b]
        a_close, b_close = df_a['close'].align(df_b['close'], join='inner')
        train_mask = a_close.index <= TRAIN_END
        a_log = np.log(a_close.to_numpy(dtype=float))
        b_log = np.log(b_close.to_numpy(dtype=float))
        beta = fit_beta(a_log[train_mask.to_numpy()], b_log[train_mask.to_numpy()])
        s = build_log_spreads(a_close, b_close, beta)
        s_train = s[s.index <= TRAIN_END]
        z_train = (s_train - s_train.mean()) / s_train.std(ddof=1)
        # нормировка издержек — последние цены TRAIN, не test (аудит В-5)
        a_train_close = a_close[train_mask.to_numpy()]
        b_train_close = b_close[train_mask.to_numpy()]
        cost_c = round_trip_cost_c(costs[sym_a]['spread_price'], costs[sym_b]['spread_price'],
                                   float(a_train_close.iloc[-1]),
                                   float(b_train_close.iloc[-1]), beta)
        metrics = screening_metrics(s_train, z_train, cost_c, THRESHOLDS)
        metrics.update({
            'beta': beta,
            'coint_p': engle_granger_pvalue(a_log[train_mask.to_numpy()],
                                            b_log[train_mask.to_numpy()]),
            'half_life_bars': half_life_bars(s_train),
            'mu_train': float(s_train.mean()),
            'sigma_train': float(s_train.std(ddof=1)),
        })
        passed, reasons = verdict_pass(metrics, THRESHOLDS)
        metrics['pass'] = passed
        metrics['kill_reasons'] = reasons
        results[name] = metrics
    return {'tf': tf, 'thresholds': vars(THRESHOLDS), 'candidates': results}


def _stage2(legs_m5: dict[str, pd.DataFrame], screening_out: dict, costs: dict,
            cost_factor: float = 1.0) -> dict:
    results = {}
    for name, m in screening_out['candidates'].items():
        if not m['pass']:
            continue
        sym_a, sym_b = CANDIDATES[name]['legs']
        df_a, df_b = legs_m5[sym_a], legs_m5[sym_b]
        a_o, b_o = df_a['open'].align(df_b['open'], join='inner')
        a_c, b_c = df_a['close'].align(df_b['close'], join='inner')
        beta, mu, sigma = m['beta'], m['mu_train'], m['sigma_train']
        s_sig = build_log_spreads(a_c, b_c, beta)
        s_exec = build_log_spreads(a_o, b_o, beta)
        idx = s_sig.index.intersection(s_exec.index)
        s_sig, s_exec = s_sig.loc[idx], s_exec.loc[idx]
        test_mask = idx >= TEST_START
        z_test = ((s_sig - mu) / sigma).to_numpy()[test_mask.to_numpy()]
        s_test = s_exec.to_numpy()[test_mask.to_numpy()]
        times = idx.to_numpy()[test_mask.to_numpy()]
        cost_c = stress_cost_c(m['cost_c'], cost_factor)
        swap_cost_long = swap_cost_short = 0.0
        if name == 'XAUXAG':
            # своп комбинированной позиции зависит от стороны (аудит В-6, спека раздел 7).
            # MT5 swap_long/swap_short — знаковый доход за ночь; стоимость = -доход.
            # side=+1: long ноги A / short ноги B; side=-1: наоборот.
            swap_cost_long = -(costs[sym_a]['swap_long'] + costs[sym_b]['swap_short'])
            swap_cost_short = -(costs[sym_a]['swap_short'] + costs[sym_b]['swap_long'])
        result = run_backtest(z_test, s_test, times, cost_c,
                              swap_cost_long=swap_cost_long,
                              swap_cost_short=swap_cost_short)
        trades = result.trades
        pnls = [t.pnl_net for t in trades]
        sides = [t.side for t in trades]
        n_long = sum(1 for x in sides if x > 0)
        n_short = len(sides) - n_long
        # длина блока bootstrap — медианная длительность эпизодов TRAIN,
        # заморожена в screening.json (спека раздел 6, аудит В-1)
        expected_block = float(m['median_episode_duration_bars']) or 1.0
        results[name] = {
            'n_trades': len(trades),
            'n_per_side_min': min(n_long, n_short),
            'dropped_open_at_end': result.dropped_open_at_end,
            'pf': profit_factor(pnls),
            'pf_gross': profit_factor([t.pnl_gross for t in trades]),
            'bs_p05': stationary_bootstrap_ci(pnls, expected_block, n_resamples=10000, seed=0),
            'expected_block_bars': expected_block,
            'cost_factor': cost_factor,
            'eg_p_test': engle_granger_pvalue(
                np.log(a_c.loc[idx[test_mask.to_numpy()]].to_numpy(dtype=float)),
                np.log(b_c.loc[idx[test_mask.to_numpy()]].to_numpy(dtype=float))),
            'exit_reasons': {r: sum(1 for t in trades if t.exit_reason == r)
                             for r in ('revert', 'stop', 'timeout')},
            'pnl_by_reason': {r: float(sum(t.pnl_net for t in trades if t.exit_reason == r))
                              for r in ('revert', 'stop', 'timeout')},
            'swap_cost_long': swap_cost_long,
            'swap_cost_short': swap_cost_short,
        }
        results[name]['verdict'] = pair_verdict(results[name])
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['1', '2', 'all'], default='all')
    ap.add_argument('--stress-costs', type=float, default=1.0,
                    help='множитель round-trip издержек (методология 12: стресс 2x); '
                         'пишет отдельный артефакт backtest_stress<F>x.json')
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    costs = build_costs(COSTS_CSV)
    screening_path = OUT_DIR / 'screening.json'

    if args.stage in ('1', 'all'):
        legs_m5 = _load_legs(M5_DIR)
        # H1 — независимая агрегация брокера (экспорт MT5, Task 2),
        # не ресемплинг M5 (аудит В-2, спека раздел 3.3)
        legs_h1 = _load_legs(H1_DIR)
        out_m5 = _stage1_for_tf(legs_m5, costs, 'M5')
        out_h1 = _stage1_for_tf(legs_h1, costs, 'H1')
        payload = {'M5': out_m5, 'H1': out_h1}
        screening_path.write_text(json.dumps(payload, indent=2, default=_json_default))
        print(f'Stage 1 -> {screening_path}')
        for tf in ('M5', 'H1'):
            for name, m in payload[tf]['candidates'].items():
                status = 'PASS' if m['pass'] else 'KILL(' + '; '.join(m['kill_reasons']) + ')'
                print(f"  [{tf}] {name}: {status}")
        if args.stage == '1':
            return 0

    screening_out = json.loads(screening_path.read_text())['M5']
    legs_m5 = _load_legs(M5_DIR)
    stage2 = _stage2(legs_m5, screening_out, costs, cost_factor=args.stress_costs)
    if args.stress_costs == 1.0:
        backtest_path = OUT_DIR / 'backtest.json'
    else:
        backtest_path = OUT_DIR / f'backtest_stress{args.stress_costs:g}x.json'
    backtest_path.write_text(json.dumps(stage2, indent=2, default=_json_default))
    print(f'Stage 2 (cost x{args.stress_costs:g}) -> {backtest_path}')
    for name, r in stage2.items():
        print(f"  {name}: {r['verdict']} PF={r['pf']:.2f} BS_p05={r['bs_p05']:.2f} N={r['n_trades']}")
    return 0


def _json_default(obj):
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    raise TypeError(f'Object of type {type(obj).__name__} is not JSON serializable')


if __name__ == '__main__':
    sys.exit(main())
