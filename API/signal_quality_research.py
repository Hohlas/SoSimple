# =============================================================================
# Файл: API/signal_quality_research.py
# Назначение: Signal Quality Filter Research (Variant 4):
#              исследование multi-horizon prediction features как фильтров
#              качества ML-сигналов
# Язык: Python 3.10+
# Создан: 2026-04-03
# Зависимости:
#   Входные данные:
#     - MT/MQL4/Files/ml_signals.csv
#     - DATA/XAUUSD_H1_OHLC.csv
#   Выходные данные:
#     - stdout (таблицы)
# Использование:
#   python -m API.signal_quality_research
#   python -m API.signal_quality_research --test-only
# =============================================================================

"""
Signal Quality Filter Research (Variant 4).

Исследует, могут ли комбинации multi-horizon predictions модели (up_3..dn_48)
дать более точный фильтр качества сигнала, чем текущий ratio_12.

Pipeline:
  Step 0: Feature Variance Check — убиваем features с near-zero дисперсией
  Step 1: Discovery / Holdout Split — 60/40 по дате
  Step 2: Univariate Response Maps — quantile bins → PF, N, net_ATR
  Step 3: Shallow Tree Discovery — depth-2 tree для поиска лучших splits
  Step 4: Pairwise Combinations — top splits × top univariate winners
  Step 5: Score Construction & Holdout Validation

Filter Feature Families:
  1. ratio_h = pred_fav_h / pred_adv_h          (h ∈ {3,6,12,24,48})
  2. spread_h = pred_fav_h - pred_adv_h          (h ∈ {3,6,12,24,48})
  3. short_vs_long: ratio/spread divergence       (3v12, 6v24, 12v48)

Response Variables (post-signal, not filters):
  fav_k_atr, adv_k_atr (k ∈ {1,3,6}), net_12_atr
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import signal_research as sr

PROJECT_ROOT = Path(__file__).resolve().parent.parent

HORIZONS = [3, 6, 12, 24, 48]
PRED_COLS = sr.PRED_COLS
PULLBACK_WINDOWS = [1, 3, 6]
BASE_HORIZON = 12
DISCOVERY_CUTOFF = '2024-12-31'
MIN_DISCOVERY_N = 1000
MIN_HOLDOUT_N = 400
MIN_N_FINAL = 56

EPS = 1e-6

RATIO_FEATURES = [f'ratio_{h}' for h in HORIZONS]
SPREAD_FEATURES = [f'spread_{h}' for h in HORIZONS]
SVL_FEATURES = [
    'ratio_3_vs_12', 'spread_3_vs_12', 'fav_3_vs_12',
    'ratio_6_vs_24', 'spread_6_vs_24',
    'ratio_12_vs_48', 'spread_12_vs_48',
]
ALL_FILTER_FEATURES = RATIO_FEATURES + SPREAD_FEATURES + SVL_FEATURES


def compute_filter_features(sig_df: pd.DataFrame,
                            ohlc: pd.DataFrame) -> pd.DataFrame:
    """Compute excursions via signal_research, then add filter features
    and response variables."""
    exc = sr.compute_excursions(sig_df, ohlc)

    # pred_fav/pred_adv for ALL 5 horizons (signal_research only does 3,6,12)
    for h in HORIZONS:
        fav_col = f'pred_fav_{h}'
        adv_col = f'pred_adv_{h}'
        if fav_col not in exc.columns:
            exc[fav_col] = np.where(
                exc['signal'] == 1, exc[f'up_{h}'], exc[f'dn_{h}'])
            exc[adv_col] = np.where(
                exc['signal'] == 1, exc[f'dn_{h}'], exc[f'up_{h}'])

    # Family 1: ratio_h
    for h in HORIZONS:
        exc[f'ratio_{h}'] = exc[f'pred_fav_{h}'] / (exc[f'pred_adv_{h}'] + EPS)

    # Family 2: spread_h
    for h in HORIZONS:
        exc[f'spread_{h}'] = exc[f'pred_fav_{h}'] - exc[f'pred_adv_{h}']

    # Family 3: short_vs_long
    exc['ratio_3_vs_12'] = exc['ratio_3'] / (exc['ratio_12'] + EPS)
    exc['spread_3_vs_12'] = exc['spread_3'] / (exc['spread_12'] + EPS)
    exc['fav_3_vs_12'] = exc['pred_fav_3'] / (exc['pred_fav_12'] + EPS)
    exc['ratio_6_vs_24'] = exc['ratio_6'] / (exc['ratio_24'] + EPS)
    exc['spread_6_vs_24'] = exc['spread_6'] / (exc['spread_24'] + EPS)
    exc['ratio_12_vs_48'] = exc['ratio_12'] / (exc['ratio_48'] + EPS)
    exc['spread_12_vs_48'] = exc['spread_12'] / (exc['spread_48'] + EPS)

    # Response variables (not filters)
    atr = exc['entry_atr14']
    for k in PULLBACK_WINDOWS:
        exc[f'fav_{k}_atr'] = exc[f'fav_{k}'] / (atr + EPS)
        exc[f'adv_{k}_atr'] = exc[f'adv_{k}'] / (atr + EPS)
    exc['net_12_atr'] = exc[f'net_{BASE_HORIZON}'] / (atr + EPS)

    return exc


# ── Step 0: Feature Variance Check ──────────────────────────────────────────

def variance_check(exc: pd.DataFrame,
                   features: list[str],
                   n_bins: int = 10) -> tuple[list, list, pd.DataFrame]:
    """Check feature variance, kill near-constant features.

    Returns (alive_features, dead_features, report_df).
    """
    rows = []
    alive, dead = [], []
    for f in features:
        s = exc[f].dropna()
        if len(s) < 20:
            dead.append(f)
            rows.append({'feature': f, 'mean': np.nan, 'std': np.nan,
                         'Q10': np.nan, 'Q50': np.nan, 'Q90': np.nan,
                         'max_bin_pct': 100.0, 'alive': False,
                         'kill_reason': 'too few values'})
            continue

        mean, std = s.mean(), s.std()
        q10, q50, q90 = s.quantile([0.1, 0.5, 0.9])
        iqr = s.quantile(0.75) - s.quantile(0.25)

        try:
            binned = pd.qcut(s, n_bins, duplicates='drop')
            max_bin_pct = binned.value_counts(normalize=True).max() * 100
        except ValueError:
            max_bin_pct = 100.0

        is_ratio = f.startswith('ratio') or f.startswith('fav_')
        if max_bin_pct > 90.0:
            dead.append(f)
            reason = '>90% in one bin'
        elif is_ratio and abs(mean) > EPS and std < 0.01 * abs(mean):
            dead.append(f)
            reason = 'std < 1% of |mean|'
        elif not is_ratio and iqr > 0 and std < 0.01 * iqr:
            dead.append(f)
            reason = 'std < 1% of IQR'
        else:
            alive.append(f)
            reason = ''

        rows.append({'feature': f, 'mean': mean, 'std': std,
                     'Q10': q10, 'Q50': q50, 'Q90': q90,
                     'max_bin_pct': max_bin_pct, 'alive': reason == '',
                     'kill_reason': reason})

    return alive, dead, pd.DataFrame(rows)


# ── Step 1: Discovery / Holdout Split ───────────────────────────────────────

def discovery_holdout_split(exc: pd.DataFrame
                            ) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Split by DISCOVERY_CUTOFF date.

    Raises ValueError if either split is too small.
    """
    cutoff = pd.Timestamp(DISCOVERY_CUTOFF)
    disc = exc[exc['time'] <= cutoff].copy()
    hold = exc[exc['time'] > cutoff].copy()

    if len(disc) < MIN_DISCOVERY_N or len(hold) < MIN_HOLDOUT_N:
        raise ValueError(
            f'Split too few: discovery={len(disc)}, holdout={len(hold)}. '
            f'Need discovery>={MIN_DISCOVERY_N}, holdout>={MIN_HOLDOUT_N}')

    buy_d = (disc['signal'] == 1).sum()
    buy_h = (hold['signal'] == 1).sum()
    info = {
        'N_discovery': len(disc),
        'N_holdout': len(hold),
        'discovery_range': f"{disc['time'].min()} — {disc['time'].max()}",
        'holdout_range': f"{hold['time'].min()} — {hold['time'].max()}",
        'discovery_BUY_pct': round(buy_d / len(disc) * 100, 1),
        'holdout_BUY_pct': round(buy_h / len(hold) * 100, 1),
    }
    return disc, hold, info


# ── Step 2: Univariate Response Maps ────────────────────────────────────────

def _profit_factor(net: pd.Series) -> float:
    wins = net[net > 0].sum()
    losses = net[net < 0].abs().sum()
    if losses == 0:
        return np.inf if wins > 0 else np.nan
    if wins == 0:
        return 0.0
    return wins / losses


def univariate_response_map(disc: pd.DataFrame,
                            feature: str,
                            n_bins: int = 5) -> pd.DataFrame:
    """Quantile-bin a feature, compute PF and response metrics per bin."""
    s = disc[feature].dropna()
    valid = disc.loc[s.index].copy()
    valid['_bin'] = pd.qcut(s, n_bins, duplicates='drop')

    baseline_pf = _profit_factor(valid['net_12'])
    years = ((valid['time'].max() - valid['time'].min()).days + 1) / 365.25

    rows = []
    for label, grp in valid.groupby('_bin', observed=True):
        net = grp['net_12']
        pf = _profit_factor(net)
        atr_col = grp['entry_atr14'] + EPS
        rows.append({
            'bin': str(label),
            'N': len(grp),
            'trades_per_year': round(len(grp) / max(years, 0.1), 1),
            'PF': round(pf, 2) if np.isfinite(pf) else pf,
            'net_ATR': round((net / atr_col).mean(), 3),
            'fav_ATR': round((grp['fav_6'] / atr_col).mean(), 3),
            'adv_ATR': round((grp['adv_6'] / atr_col).mean(), 3),
            'uplift': round(pf - baseline_pf, 2) if (
                np.isfinite(pf) and np.isfinite(baseline_pf)) else np.nan,
        })
    return pd.DataFrame(rows).sort_values(
        'PF', ascending=False).reset_index(drop=True)


# ── Step 3: Shallow Tree Discovery ──────────────────────────────────────────

def shallow_tree_discovery(disc: pd.DataFrame,
                           features: list[str],
                           max_depth: int = 2) -> dict:
    """Fit depth-2 tree, extract splits and leaf stats."""
    from sklearn.tree import DecisionTreeClassifier, export_text

    valid = disc.dropna(subset=features + ['net_12']).copy()
    X = valid[features].values
    y = (valid['net_12'] > 0).astype(int).values

    tree = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    tree.fit(X, y)

    tree_text = export_text(tree, feature_names=features, decimals=3)
    importances = pd.Series(tree.feature_importances_,
                            index=features, name='importance')

    leaf_ids = tree.apply(X)
    valid['_leaf'] = leaf_ids
    leaf_rows = []
    for lid, grp in valid.groupby('_leaf'):
        net = grp['net_12']
        pf = _profit_factor(net)
        atr_col = grp['entry_atr14'] + EPS if 'entry_atr14' in grp.columns else None
        leaf_rows.append({
            'leaf': lid,
            'N': len(grp),
            'win_rate': round((net > 0).mean() * 100, 1),
            'PF': round(pf, 2) if np.isfinite(pf) else pf,
            'net_ATR_mean': round((net / atr_col).mean(), 3) if atr_col is not None else round(net.mean(), 3),
        })

    return {
        'tree_text': tree_text,
        'importances': importances.sort_values(ascending=False),
        'leaves': pd.DataFrame(leaf_rows),
        'tree': tree,
    }


# ── Step 4: Pairwise Combinations ───────────────────────────────────────────

def _apply_rule(exc, feature, op, threshold):
    if op == '>':
        return exc[feature] > threshold
    if op == '<':
        return exc[feature] < threshold
    if op == '>=':
        return exc[feature] >= threshold
    if op == '<=':
        return exc[feature] <= threshold
    return pd.Series(False, index=exc.index)


def negative_control_check(exc: pd.DataFrame,
                           filter_mask: pd.Series) -> dict:
    """Apply filter_mask to negative control cohorts, return their PF."""
    result = {}
    r34_mask = exc['ratio_bin'] == '3-4'
    r34_filtered = exc[r34_mask & filter_mask]
    result['ratio_3_4_PF'] = (
        _profit_factor(r34_filtered['net_12'])
        if len(r34_filtered) > 0 else np.nan)
    result['ratio_3_4_N'] = len(r34_filtered)

    nq4_mask = exc['atr_bucket'] != 'Q4'
    nq4_filtered = exc[nq4_mask & filter_mask]
    result['non_Q4_PF'] = (
        _profit_factor(nq4_filtered['net_12'])
        if len(nq4_filtered) > 0 else np.nan)
    result['non_Q4_N'] = len(nq4_filtered)

    return result


def pairwise_combinations(disc: pd.DataFrame,
                          candidates: list[tuple],
                          max_pairs: int = 20) -> pd.DataFrame:
    """Test pairwise AND-combinations of candidate rules."""
    from itertools import combinations

    baseline_pf = _profit_factor(disc['net_12'])
    has_controls = 'ratio_bin' in disc.columns

    rows = []

    # Single rules
    for f, op, thr in candidates:
        mask = _apply_rule(disc, f, op, thr)
        subset = disc[mask]
        if len(subset) < 10:
            continue
        pf = _profit_factor(subset['net_12'])
        ctrl = negative_control_check(disc, mask) if has_controls else {}
        atr_col = subset['entry_atr14'] + EPS
        rows.append({
            'rule': f'{f} {op} {thr:.3f}',
            'N': len(subset),
            'PF': round(pf, 2) if np.isfinite(pf) else pf,
            'net_ATR': round((subset['net_12'] / atr_col).mean(), 3),
            'uplift': round(pf - baseline_pf, 2) if (
                np.isfinite(pf) and np.isfinite(baseline_pf)) else np.nan,
            **ctrl,
        })

    # Pairwise
    pairs = list(combinations(range(len(candidates)), 2))
    if len(pairs) > max_pairs:
        pairs = pairs[:max_pairs]

    for i, j in pairs:
        f1, op1, thr1 = candidates[i]
        f2, op2, thr2 = candidates[j]
        mask = _apply_rule(disc, f1, op1, thr1) & _apply_rule(disc, f2, op2, thr2)
        subset = disc[mask]
        if len(subset) < 10:
            continue
        pf = _profit_factor(subset['net_12'])
        ctrl = negative_control_check(disc, mask) if has_controls else {}
        atr_col = subset['entry_atr14'] + EPS
        rows.append({
            'rule': f'{f1} {op1} {thr1:.3f} AND {f2} {op2} {thr2:.3f}',
            'N': len(subset),
            'PF': round(pf, 2) if np.isfinite(pf) else pf,
            'net_ATR': round((subset['net_12'] / atr_col).mean(), 3),
            'uplift': round(pf - baseline_pf, 2) if (
                np.isfinite(pf) and np.isfinite(baseline_pf)) else np.nan,
            **ctrl,
        })

    return pd.DataFrame(rows).sort_values(
        'PF', ascending=False).reset_index(drop=True)


# ── Step 5: Score Construction & Holdout Validation ─────────────────────────

def build_score(df: pd.DataFrame,
                features: list[str],
                weights: dict | None = None) -> pd.DataFrame:
    """Rank-based normalization + additive score."""
    result = df.copy()
    if weights is None:
        weights = {f: 1.0 / len(features) for f in features}

    score = pd.Series(0.0, index=df.index)
    for f in features:
        ranked = df[f].rank(pct=True)
        score += weights[f] * ranked

    smin, smax = score.min(), score.max()
    if smax > smin:
        score = (score - smin) / (smax - smin)
    result['score'] = score
    return result


def holdout_validation(hold: pd.DataFrame,
                       top_pct: float = 0.25) -> dict:
    """One-shot holdout test on top-scoring signals."""
    threshold = hold['score'].quantile(1.0 - top_pct)
    top = hold[hold['score'] >= threshold]
    baseline_pf = _profit_factor(hold['net_12'])
    top_pf = _profit_factor(top['net_12'])
    confirmed = (np.isfinite(top_pf) and np.isfinite(baseline_pf)
                 and top_pf > baseline_pf)

    ctrl = (negative_control_check(hold, hold['score'] >= threshold)
            if 'ratio_bin' in hold.columns else {})

    return {
        'top_pct': top_pct,
        'N_holdout': len(top),
        'PF_holdout': round(top_pf, 2) if np.isfinite(top_pf) else top_pf,
        'PF_baseline': round(baseline_pf, 2) if np.isfinite(baseline_pf) else baseline_pf,
        'confirmed': confirmed,
        **ctrl,
    }


# ── Report output ───────────────────────────────────────────────────────────

def print_separator(title: str):
    print(f'\n{"=" * 70}')
    print(f'  {title}')
    print(f'{"=" * 70}\n')


def print_variance_report(exc, features):
    print_separator('Step 0: Feature Variance Check')
    alive, dead, report = variance_check(exc, features)
    print(report.to_string(index=False))
    print(f'\nAlive: {len(alive)} | Dead: {len(dead)}')
    if dead:
        print(f'Killed: {", ".join(dead)}')
    return alive, dead


def print_split_info(info):
    print_separator('Step 1: Discovery / Holdout Split')
    for k, v in info.items():
        print(f'  {k}: {v}')


def print_univariate_maps(disc, alive_features, n_bins=5):
    print_separator('Step 2: Univariate Response Maps')
    maps = {}
    for f in alive_features:
        print(f'\n--- {f} ---')
        m = univariate_response_map(disc, f, n_bins=n_bins)
        print(m.to_string(index=False))
        maps[f] = m
    return maps


def print_tree_discovery(disc, alive_features):
    print_separator('Step 3: Shallow Tree Discovery')
    result = shallow_tree_discovery(disc, alive_features)
    print('Tree structure:')
    print(result['tree_text'])
    print('\nFeature importances:')
    print(result['importances'].to_string())
    print('\nLeaf statistics:')
    print(result['leaves'].to_string(index=False))
    return result


def _is_trivial_rule(disc, feature, op, threshold, max_pass_pct=90.0):
    """Return True if rule passes >max_pass_pct of the data (trivial)."""
    mask = _apply_rule(disc, feature, op, threshold)
    pct = mask.sum() / len(disc) * 100
    return pct > max_pass_pct


def extract_candidates_from_maps_and_tree(maps, tree_result, disc,
                                           alive_features):
    """Pick top univariate thresholds + tree split points as candidates.
    Filters out trivial rules that pass >90% of data."""
    candidates = []
    seen = set()
    baseline_pf = _profit_factor(disc['net_12'])

    for f, m in maps.items():
        for _, row in m.iterrows():
            if row['N'] < 30:
                continue
            pf = row['PF']
            if not np.isfinite(pf) or pf <= baseline_pf + 0.1:
                continue
            bin_str = row['bin']
            try:
                right = float(bin_str.split(',')[0].strip('(['))
                key = (f, '>', round(right, 3))
                if key not in seen and not _is_trivial_rule(disc, f, '>', round(right, 3)):
                    candidates.append(key)
                    seen.add(key)
            except (ValueError, IndexError):
                continue

    tree = tree_result['tree']
    feature_idx = tree.tree_.feature
    threshold = tree.tree_.threshold
    for node_id in range(tree.tree_.node_count):
        if feature_idx[node_id] >= 0:
            fname = alive_features[feature_idx[node_id]]
            thr = round(threshold[node_id], 3)
            for op in ('>', '<='):
                key = (fname, op, thr)
                if key not in seen and not _is_trivial_rule(disc, fname, op, thr):
                    candidates.append(key)
                    seen.add(key)

    return candidates


# ── Year stability ──────────────────────────────────────────────────────────

def year_stability(exc: pd.DataFrame,
                   filter_mask: pd.Series,
                   rule_label: str) -> pd.DataFrame:
    """PF per year for a given filter rule."""
    subset = exc[filter_mask].copy()
    if subset.empty:
        return pd.DataFrame()
    subset['year'] = subset['time'].dt.year
    rows = []
    for yr, grp in subset.groupby('year'):
        net = grp['net_12']
        pf = _profit_factor(net)
        rows.append({
            'rule': rule_label,
            'year': yr,
            'N': len(grp),
            'PF': round(pf, 2) if np.isfinite(pf) else pf,
            'net_ATR': round((net / (grp['entry_atr14'] + EPS)).mean(), 3),
        })
    return pd.DataFrame(rows)


def print_pairwise_results(disc, candidates):
    print_separator('Step 4: Pairwise Combinations')
    print(f'Candidates: {len(candidates)}')
    for c in candidates:
        print(f'  {c[0]} {c[1]} {c[2]}')
    result = pairwise_combinations(disc, candidates)
    print(f'\nResults ({len(result)} rules):')
    if not result.empty:
        print(result.to_string(index=False))
    return result


def print_holdout_results(hold, top_pcts, label=''):
    if label:
        print(f'\n  Score source: {label}')
    results = []
    for pct in top_pcts:
        r = holdout_validation(hold, top_pct=pct)
        results.append(r)
        status = 'CONFIRMED' if r['confirmed'] else 'NOT CONFIRMED'
        print(f"  top {pct*100:.0f}%: N={r['N_holdout']}, "
              f"PF={r['PF_holdout']}, baseline={r['PF_baseline']} "
              f"-> {status}")
    return results


def _top_univariate_features(maps, baseline_pf, top_n=5):
    """Pick features with highest best-bin uplift."""
    scores = []
    for f, m in maps.items():
        best_pf = m['PF'].replace([np.inf, -np.inf], np.nan).max()
        if np.isfinite(best_pf):
            scores.append((f, best_pf - baseline_pf))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [f for f, _ in scores[:top_n]]


def print_year_stability(exc, top_rules):
    print_separator('Step 6: Year Stability')
    for rule_label, mask in top_rules:
        ys = year_stability(exc, mask, rule_label)
        if not ys.empty:
            print(f'\n--- {rule_label} ---')
            print(ys.to_string(index=False))


def print_direct_holdout(disc, hold, top_rules):
    print_separator('Step 7: Direct Holdout — Individual Rules')
    baseline_disc = _profit_factor(disc['net_12'])
    baseline_hold = _profit_factor(hold['net_12'])
    print(f'  Baseline PF: discovery={baseline_disc:.2f}, holdout={baseline_hold:.2f}\n')

    rows = []
    for rule_label, disc_mask in top_rules:
        # Apply same rule to holdout
        disc_sub = disc[disc_mask]
        # Parse rule to apply on holdout
        hold_mask = pd.Series(True, index=hold.index)
        parts = rule_label.split(' AND ')
        for part in parts:
            tokens = part.strip().split()
            if len(tokens) == 3:
                f, op, thr = tokens[0], tokens[1], float(tokens[2])
                hold_mask = hold_mask & _apply_rule(hold, f, op, thr)

        hold_sub = hold[hold_mask]
        pf_d = _profit_factor(disc_sub['net_12'])
        pf_h = _profit_factor(hold_sub['net_12']) if len(hold_sub) > 0 else np.nan

        confirmed = (np.isfinite(pf_h) and pf_h > baseline_hold)
        rows.append({
            'rule': rule_label,
            'N_disc': len(disc_sub),
            'PF_disc': round(pf_d, 2) if np.isfinite(pf_d) else pf_d,
            'N_hold': len(hold_sub),
            'PF_hold': round(pf_h, 2) if np.isfinite(pf_h) else pf_h,
            'confirmed': 'YES' if confirmed else 'NO',
        })

    result = pd.DataFrame(rows)
    if not result.empty:
        print(result.to_string(index=False))
    return result


# ── Step 8: Cross-analysis with Variant 3 pullback entry ────────────────────

CROSS_SCENARIOS = [
    {'scenario': 'market'},
    {'scenario': 'pullback', 'anchor': 'entry_close', 'offset_atr': 1.0},
    {'scenario': 'pullback', 'anchor': 'entry_close', 'offset_atr': 2.0},
    {'scenario': 'pullback', 'anchor': 'entry_close', 'offset_atr': 3.0},
]

CROSS_RULES = [
    ('ALL (no filter)', None),
    ('fav_3_vs_12 <= 0.653', [('fav_3_vs_12', '<=', 0.653)]),
    ('ratio_6 > 4.41 AND fav_3_vs_12 <= 0.653',
     [('ratio_6', '>', 4.41), ('fav_3_vs_12', '<=', 0.653)]),
    ('ratio_3_vs_12 > 4.751', [('ratio_3_vs_12', '>', 4.751)]),
]


def _apply_filter_rules(df, rules):
    """Apply a list of (feature, op, threshold) rules as AND mask."""
    if rules is None:
        return pd.Series(True, index=df.index)
    mask = pd.Series(True, index=df.index)
    for f, op, thr in rules:
        mask = mask & _apply_rule(df, f, op, thr)
    return mask


def cross_filter_x_pullback(exc_subset: pd.DataFrame,
                             ohlc: pd.DataFrame,
                             label: str) -> pd.DataFrame:
    """Run pullback scenarios on a filtered subset, return summary."""
    if exc_subset.empty:
        return pd.DataFrame()

    outcomes = sr.build_variant3_scenario_outcomes(
        exc_subset, ohlc, scenario_specs=CROSS_SCENARIOS)
    if outcomes.empty:
        return pd.DataFrame()

    summary = sr.summarize_variant3_scenarios(outcomes, ['scenario', 'params'])
    summary.insert(0, 'filter', label)
    return summary


def print_cross_analysis(exc, ohlc, split_label=''):
    """Run cross filter × pullback for all rules on a given exc subset."""
    parts = []
    for label, rules in CROSS_RULES:
        mask = _apply_filter_rules(exc, rules)
        subset = exc[mask]
        summary = cross_filter_x_pullback(subset, ohlc, label)
        if not summary.empty:
            parts.append(summary)

    if not parts:
        print('  No results.')
        return pd.DataFrame()

    combined = pd.concat(parts, ignore_index=True)
    display_cols = ['filter', 'scenario', 'params', 'N_signals',
                    'N_filled', 'fill_pct', 'PF', 'AvgPnL',
                    'TP_FIRST_pct', 'SL_FIRST_pct', 'NEITHER_pct']
    available = [c for c in display_cols if c in combined.columns]
    print(combined[available].to_string(index=False))
    return combined


def print_cross_analysis_full(disc, hold, ohlc):
    print_separator('Step 8: Quality Filters × Pullback Entry (Discovery)')
    disc_result = print_cross_analysis(disc, ohlc, 'discovery')

    print_separator('Step 9: Quality Filters × Pullback Entry (Holdout)')
    hold_result = print_cross_analysis(hold, ohlc, 'holdout')

    # Summary comparison
    if not disc_result.empty and not hold_result.empty:
        print_separator('Step 10: Cross-Analysis Summary — Discovery vs Holdout')
        for label, rules in CROSS_RULES:
            d_rows = disc_result[disc_result['filter'] == label]
            h_rows = hold_result[hold_result['filter'] == label]
            if d_rows.empty or h_rows.empty:
                continue
            print(f'\n--- {label} ---')
            for _, d_row in d_rows.iterrows():
                scenario = d_row.get('scenario', '')
                params = d_row.get('params', '')
                h_match = h_rows[(h_rows['scenario'] == scenario)
                                 & (h_rows['params'] == params)]
                if h_match.empty:
                    continue
                h_row = h_match.iloc[0]
                d_pf = d_row['PF']
                h_pf = h_row['PF']
                d_n = d_row['N_filled']
                h_n = h_row['N_filled']
                d_pf_s = f'{d_pf:.2f}' if np.isfinite(d_pf) else str(d_pf)
                h_pf_s = f'{h_pf:.2f}' if np.isfinite(h_pf) else str(h_pf)
                status = 'OK' if (np.isfinite(h_pf) and h_pf > 1.0) else '--'
                print(f'  {scenario:12s} {str(params):30s} '
                      f'disc: PF={d_pf_s:>6s} N={int(d_n):>4d}  |  '
                      f'hold: PF={h_pf_s:>6s} N={int(h_n):>4d}  [{status}]')


# ── main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Signal Quality Filter Research (Variant 4)')
    parser.add_argument('--test-only', action='store_true',
                        help='Use only OOS test-period signals')
    args = parser.parse_args()

    sig_df, ohlc = sr.load_data(test_only=args.test_only)
    real = sig_df[sig_df['signal'].isin([1, -1])].copy()
    print(f'Loaded {len(real)} real BUY/SELL signals')

    exc = compute_filter_features(real, ohlc)
    print(f'Computed features for {len(exc)} signals')

    # Step 0
    alive, dead = print_variance_report(exc, ALL_FILTER_FEATURES)
    if not alive:
        print('ERROR: No features survived variance check. Aborting.')
        return

    # Step 1
    disc, hold, info = discovery_holdout_split(exc)
    print_split_info(info)

    # Step 2
    maps = print_univariate_maps(disc, alive)

    # Step 3
    tree_result = print_tree_discovery(disc, alive)

    # Step 4
    candidates = extract_candidates_from_maps_and_tree(
        maps, tree_result, disc, alive)
    if candidates:
        pw_result = print_pairwise_results(disc, candidates)
    else:
        print('\nNo candidates passed filters. Skipping pairwise.')
        pw_result = pd.DataFrame()

    # Step 5: Score from top univariate features (not tree importances)
    print_separator('Step 5: Score-Based Holdout Validation')
    baseline_pf = _profit_factor(disc['net_12'])
    top_uni = _top_univariate_features(maps, baseline_pf, top_n=5)
    print(f'  Top univariate features for score: {top_uni}')

    if len(top_uni) >= 2:
        # Try multiple score variants
        for n_feat in (3, 5):
            feats = top_uni[:n_feat]
            if len(feats) < 2:
                continue
            scored_disc = build_score(disc, feats)
            scored_hold = build_score(hold, feats)
            label = f'top-{n_feat} univariate ({", ".join(feats)})'
            print_holdout_results(scored_hold, [0.10, 0.15, 0.20, 0.25],
                                 label=label)

    # Step 6: Year stability for top pairwise candidates
    top_rules = []
    if not pw_result.empty:
        viable = pw_result[(pw_result['N'] >= MIN_N_FINAL)
                           & (pw_result['PF'] > 1.0)].head(10)
        for _, row in viable.iterrows():
            rule_str = row['rule']
            mask = pd.Series(True, index=disc.index)
            parts = rule_str.split(' AND ')
            for part in parts:
                tokens = part.strip().split()
                if len(tokens) == 3:
                    f, op, thr = tokens[0], tokens[1], float(tokens[2])
                    mask = mask & _apply_rule(disc, f, op, thr)
            top_rules.append((rule_str, mask))

    if top_rules:
        print_year_stability(disc, top_rules)
        print_direct_holdout(disc, hold, top_rules)

    # Step 8-10: Cross quality filters × pullback entry
    print_cross_analysis_full(disc, hold, ohlc)


if __name__ == '__main__':
    main()
