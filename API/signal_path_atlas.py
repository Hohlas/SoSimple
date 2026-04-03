import argparse
import re
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier, export_text

try:
    from . import signal_research as sr
except ImportError:
    import signal_research as sr

DISCOVERY_END = pd.Timestamp('2024-12-31 23:59:59')
PATH_HORIZONS = list(range(1, 13))
ADVERSE_LEVELS = [1.0, 2.0, 3.0]
RATIO_BIN_EDGES = [0.0, 2.0, 3.0, 4.0, 5.0, np.inf]
RATIO_BIN_LABELS = ['<2', '2-3', '3-4', '4-5', '5+']
NUMERIC_FEATURES = [
    'ratio_3', 'ratio_6', 'ratio_12', 'ratio_24', 'ratio_48',
    'spread_3', 'spread_6', 'spread_12', 'spread_24', 'spread_48',
    'ratio_3_vs_12', 'spread_3_vs_12', 'fav_3_vs_12',
    'ratio_6_vs_24', 'spread_6_vs_24', 'ratio_12_vs_48', 'spread_12_vs_48',
]
FIXED_COHORT_COLS = ['signal_label', 'ratio_bin_12', 'atr_bucket']
KEY_REPLICATION_METRICS = [
    ('signed_ret_12_q50', 1.0),
    ('fav_hit_3atr_12h', 1.0),
    ('adv_hit_1atr_3h', -1.0),
    ('adverse_first_1atr', -1.0),
]


def annotate_sample_split(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out['sample'] = np.where(out['time'] <= DISCOVERY_END, 'discovery', 'holdout')
    return out


def _fit_atr_edges(frame: pd.DataFrame) -> np.ndarray:
    atr_values = pd.to_numeric(frame['entry_atr14'], errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
    if atr_values.empty:
        return np.array([], dtype=float)
    return np.unique(np.quantile(atr_values.to_numpy(dtype=float), [0.0, 0.25, 0.5, 0.75, 1.0]))


def _assign_atr_buckets(frame: pd.DataFrame, atr_edges: np.ndarray) -> pd.Series:
    out = pd.Series(pd.NA, index=frame.index, dtype='object')
    atr_values = pd.to_numeric(frame['entry_atr14'], errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
    if atr_values.empty:
        return out
    if len(atr_edges) < 2:
        out.loc[atr_values.index] = 'Q1'
        return out
    atr_labels = ['Q1', 'Q2', 'Q3', 'Q4'][:len(atr_edges) - 1]
    out.loc[atr_values.index] = pd.cut(
        atr_values,
        bins=atr_edges,
        labels=atr_labels,
        include_lowest=True,
    ).astype('object')
    return out


def build_conditioning_frame(frame: pd.DataFrame, atr_edges: np.ndarray | None = None) -> tuple[pd.DataFrame, dict]:
    out = frame.copy()
    eps = 1e-6

    for h in (3, 6, 12, 24, 48):
        fav_col = f'pred_fav_{h}'
        adv_col = f'pred_adv_{h}'
        fav_fill = pd.Series(np.where(out['signal'] == 1, out[f'up_{h}'], out[f'dn_{h}']), index=out.index)
        adv_fill = pd.Series(np.where(out['signal'] == 1, out[f'dn_{h}'], out[f'up_{h}']), index=out.index)
        if fav_col not in out.columns:
            out[fav_col] = fav_fill
        else:
            out[fav_col] = out[fav_col].fillna(fav_fill)
        if adv_col not in out.columns:
            out[adv_col] = adv_fill
        else:
            out[adv_col] = out[adv_col].fillna(adv_fill)
        out[f'ratio_{h}'] = out[fav_col] / out[adv_col].clip(lower=eps)
        out[f'spread_{h}'] = out[fav_col] - out[adv_col]

    out['ratio_3_vs_12'] = out['ratio_3'] / out['ratio_12'].clip(lower=eps)
    out['spread_3_vs_12'] = out['spread_3'] / out['spread_12'].replace(0, np.nan)
    out['fav_3_vs_12'] = out['pred_fav_3'] / out['pred_fav_12'].clip(lower=eps)
    out['ratio_6_vs_24'] = out['ratio_6'] / out['ratio_24'].clip(lower=eps)
    out['spread_6_vs_24'] = out['spread_6'] / out['spread_24'].replace(0, np.nan)
    out['ratio_12_vs_48'] = out['ratio_12'] / out['ratio_48'].clip(lower=eps)
    out['spread_12_vs_48'] = out['spread_12'] / out['spread_48'].replace(0, np.nan)

    out['signal_label'] = np.where(out['signal'] == 1, 'BUY', 'SELL')
    out['ratio_bin_12'] = pd.cut(
        out['ratio_12'],
        bins=RATIO_BIN_EDGES,
        labels=RATIO_BIN_LABELS,
        right=False,
    )
    resolved_atr_edges = _fit_atr_edges(out) if atr_edges is None else np.asarray(atr_edges, dtype=float)
    out['atr_bucket'] = _assign_atr_buckets(out, resolved_atr_edges)
    return out, {'atr_edges': resolved_atr_edges}


def screen_numeric_features(frame: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    live = []

    for feature in features:
        series = pd.to_numeric(frame[feature], errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
        q10 = series.quantile(0.10)
        q50 = series.quantile(0.50)
        q90 = series.quantile(0.90)
        iqr = series.quantile(0.75) - series.quantile(0.25)
        n_unique = int(series.nunique())
        is_live = not (q90 == q10 or iqr == 0 or n_unique < 20)
        rows.append({
            'feature': feature,
            'mean': series.mean(),
            'std': series.std(ddof=0),
            'q10': q10,
            'q50': q50,
            'q90': q90,
            'iqr': iqr,
            'n_unique': n_unique,
            'is_live': is_live,
        })
        if is_live:
            live.append(feature)

    return pd.DataFrame(rows), live


def build_global_atlas(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    def raw_horizons(prefix: str) -> set[int]:
        pattern = re.compile(rf'^{re.escape(prefix)}_(\d+)$')
        return {
            int(match.group(1))
            for col in frame.columns
            if (match := pattern.match(col)) is not None
        }

    signed_ret_horizons = raw_horizons('signed_ret')
    fav_horizons = raw_horizons('fav')
    adv_horizons = raw_horizons('adv')
    path_horizons = sorted(signed_ret_horizons & fav_horizons & adv_horizons)
    first_passage_adv_horizons = sorted(adv_horizons)
    first_passage_fav_horizons = sorted(fav_horizons)
    ordering_pattern = re.compile(
        r'^(adverse_first|favorable_first|dip_then_rally|rally_then_dip)_(\d+(?:\.\d+)?)atr$'
    )
    ordering_levels = sorted({
        float(match.group(2))
        for col in frame.columns
        if (match := ordering_pattern.match(col)) is not None
    })

    path_rows = []
    for h in path_horizons:
        signed = frame[f'signed_ret_{h}']
        fav = frame[f'fav_{h}']
        adv = frame[f'adv_{h}']
        path_rows.append({
            'horizon': h,
            'signed_ret_q10': signed.quantile(0.10),
            'signed_ret_q50': signed.quantile(0.50),
            'signed_ret_q90': signed.quantile(0.90),
            'fav_q10': fav.quantile(0.10),
            'fav_q50': fav.quantile(0.50),
            'fav_q90': fav.quantile(0.90),
            'adv_q10': adv.quantile(0.10),
            'adv_q50': adv.quantile(0.50),
            'adv_q90': adv.quantile(0.90),
        })

    first_passage_rows = []
    for h in first_passage_adv_horizons:
        adv_col = f'adv_{h}'
        if adv_col in frame.columns:
            series = pd.to_numeric(frame[adv_col], errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
            for level in ADVERSE_LEVELS:
                first_passage_rows.append({
                    'side': 'adverse',
                    'level_atr': level,
                    'horizon': h,
                    'hit_pct': np.nan if series.empty else 100.0 * (series >= level).mean(),
                })
    for h in first_passage_fav_horizons:
        fav_col = f'fav_{h}'
        if fav_col in frame.columns:
            series = pd.to_numeric(frame[fav_col], errors='coerce').replace([np.inf, -np.inf], np.nan).dropna()
            for level in ADVERSE_LEVELS:
                first_passage_rows.append({
                    'side': 'favorable',
                    'level_atr': level,
                    'horizon': h,
                    'hit_pct': np.nan if series.empty else 100.0 * (series >= level).mean(),
                })

    ordering_rows = []
    for level in ordering_levels:
        level_label = f'{int(level)}atr' if float(level).is_integer() else f'{level}atr'
        alt_label = f'{level}atr'
        adverse_col = next(
            (f'adverse_first_{label}' for label in (level_label, alt_label) if f'adverse_first_{label}' in frame.columns),
            None,
        )
        favorable_col = next(
            (f'favorable_first_{label}' for label in (level_label, alt_label) if f'favorable_first_{label}' in frame.columns),
            None,
        )
        dip_col = next(
            (f'dip_then_rally_{label}' for label in (level_label, alt_label) if f'dip_then_rally_{label}' in frame.columns),
            None,
        )
        rally_col = next(
            (f'rally_then_dip_{label}' for label in (level_label, alt_label) if f'rally_then_dip_{label}' in frame.columns),
            None,
        )
        if adverse_col is None and favorable_col is None and dip_col is None and rally_col is None:
            continue

        ordering_rows.append({
            'level_atr': level,
            'adverse_first_pct': np.nan if adverse_col is None else 100.0 * pd.to_numeric(frame[adverse_col], errors='coerce').mean(),
            'favorable_first_pct': np.nan if favorable_col is None else 100.0 * pd.to_numeric(frame[favorable_col], errors='coerce').mean(),
            'dip_then_rally_pct': np.nan if dip_col is None else 100.0 * pd.to_numeric(frame[dip_col], errors='coerce').mean(),
            'rally_then_dip_pct': np.nan if rally_col is None else 100.0 * pd.to_numeric(frame[rally_col], errors='coerce').mean(),
        })

    return {
        'path_quantiles': pd.DataFrame(path_rows),
        'first_passage': pd.DataFrame(first_passage_rows),
        'ordering': pd.DataFrame(ordering_rows),
    }


def summarize_slice_groups(frame: pd.DataFrame, group_col: str) -> pd.DataFrame:
    metric_mask = frame.reindex(columns=['signed_ret_12', 'fav_12', 'adv_12']).notna().all(axis=1)
    work = frame.loc[metric_mask].copy()
    gb = work.groupby(group_col, dropna=False)
    summary = gb.agg(
        N=('signed_ret_12', 'size'),
        signed_ret_12_q50=('signed_ret_12', 'median'),
        fav_12_q50=('fav_12', 'median'),
        adv_12_q50=('adv_12', 'median'),
    )
    first_passage_sources = {
        'adverse_first_1atr_pct': ('adverse_first_1atr', 'adverse_first_1.0atr'),
        'favorable_first_1atr_pct': ('favorable_first_1atr', 'favorable_first_1.0atr'),
        'dip_then_rally_1atr_pct': ('dip_then_rally_1atr', 'dip_then_rally_1.0atr'),
        'rally_then_dip_1atr_pct': ('rally_then_dip_1atr', 'rally_then_dip_1.0atr'),
    }
    for out_col, candidates in first_passage_sources.items():
        source_col = next((col for col in candidates if col in frame.columns), None)
        summary[out_col] = np.nan if source_col is None else 100.0 * gb[source_col].mean()
    return summary.reset_index()


def build_numeric_slices(frame: pd.DataFrame, feature: str, min_rows: int = 80, min_frac: float = 0.05) -> pd.DataFrame:
    raw_metric_pattern = re.compile(r'^(signed_ret|fav|adv)_(\d+)$')
    metric_cols = [
        col for col in frame.columns
        if raw_metric_pattern.match(col) is not None
    ]
    metric_cols += [
        col for col in [
            'adverse_first_1atr', 'adverse_first_1.0atr',
            'favorable_first_1atr', 'favorable_first_1.0atr',
            'dip_then_rally_1atr', 'dip_then_rally_1.0atr',
            'rally_then_dip_1atr', 'rally_then_dip_1.0atr',
        ]
        if col in frame.columns
    ]
    selected_cols = list(dict.fromkeys([feature] + metric_cols))
    work = frame[selected_cols].dropna(subset=[feature]).copy()
    support_mask = work.reindex(columns=['signed_ret_12', 'fav_12', 'adv_12']).notna().all(axis=1)
    work = work.loc[support_mask].copy()
    if work.empty:
        return pd.DataFrame(columns=['feature', 'bin_id', 'N', 'signed_ret_12_q50', 'fav_12_q50', 'adv_12_q50',
                                     'adverse_first_1atr_pct', 'favorable_first_1atr_pct',
                                     'dip_then_rally_1atr_pct', 'rally_then_dip_1atr_pct',
                                     'lower_edge', 'upper_edge', 'interval_left', 'interval_right', 'interval_closed'])

    bin_count = min(4, max(1, int(work[feature].nunique())))
    try:
        interval_bins = pd.qcut(work[feature], q=bin_count, duplicates='drop')
        work['_interval'] = pd.Series(interval_bins, index=work.index)
        work['bin_id'] = work['_interval'].cat.codes
    except ValueError:
        work['_interval'] = pd.Series(
            [pd.Interval(work[feature].min(), work[feature].max(), closed='both')] * len(work),
            index=work.index,
        )
        work['bin_id'] = 0
    work['bin_id'] = pd.Series(work['bin_id'], index=work.index).fillna(0).astype(int)

    target_floor = max(min_rows, int(np.ceil(min_frac * len(work))))
    while True:
        counts = work['bin_id'].value_counts().sort_index()
        if len(counts) <= 1:
            break
        if counts.min() >= target_floor and len(counts) <= 4:
            break

        smallest = counts.idxmin()
        smallest_pos = counts.index.get_loc(smallest)
        if smallest_pos == 0:
            target = counts.index[1]
        elif smallest_pos == len(counts) - 1:
            target = counts.index[-2]
        else:
            left = counts.iloc[smallest_pos - 1]
            right = counts.iloc[smallest_pos + 1]
            target = counts.index[smallest_pos - 1] if left <= right else counts.index[smallest_pos + 1]
        work.loc[work['bin_id'] == smallest, 'bin_id'] = target
        remap = {old: new for new, old in enumerate(sorted(work['bin_id'].unique()))}
        work['bin_id'] = work['bin_id'].map(remap).astype(int)

    summary = summarize_slice_groups(work, 'bin_id')
    edges = work.groupby('bin_id')[feature].agg(lower_edge='min', upper_edge='max').reset_index()
    interval_rows = []
    for bin_id, group in work.groupby('bin_id'):
        intervals = sorted(group['_interval'].tolist(), key=lambda interval: (interval.left, interval.right))
        left_interval = intervals[0]
        right_interval = intervals[-1]
        if left_interval.closed in ('both', 'left') and right_interval.closed in ('both', 'right'):
            closed = 'both'
        elif left_interval.closed in ('both', 'left'):
            closed = 'left'
        elif right_interval.closed in ('both', 'right'):
            closed = 'right'
        else:
            closed = 'neither'
        interval_rows.append({
            'bin_id': bin_id,
            'interval_left': left_interval.left,
            'interval_right': right_interval.right,
            'interval_closed': closed,
        })
    intervals = pd.DataFrame(interval_rows)
    summary.insert(0, 'feature', feature)
    return summary.merge(edges, on='bin_id', how='left').merge(intervals, on='bin_id', how='left')


def build_categorical_slices(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    parts = []
    for col in cols:
        grouped = summarize_slice_groups(frame, col)
        grouped.insert(0, 'group_col', col)
        parts.append(grouped)
    if not parts:
        return pd.DataFrame(columns=['group_col'])
    return pd.concat(parts, ignore_index=True)


def build_path_tensor(signals: pd.DataFrame, ohlc: pd.DataFrame) -> pd.DataFrame:
    ohlc = ohlc.sort_values('time').reset_index(drop=True)
    time_to_idx = {ts: idx for idx, ts in enumerate(ohlc['time'])}
    highs = ohlc['high'].to_numpy()
    lows = ohlc['low'].to_numpy()
    closes = ohlc['close'].to_numpy()
    rows = []
    missing_times = []

    for row in signals.itertuples(index=False):
        idx = time_to_idx.get(row.time)
        if idx is None:
            missing_times.append(row.time)
            continue

        rec = {
            'time': row.time,
            'signal': row.signal,
            'entry_close': row.entry_close,
            'entry_atr14': row.entry_atr14,
        }
        tail_censored = idx + PATH_HORIZONS[-1] >= len(ohlc)
        for h in PATH_HORIZONS:
            end = idx + h
            if end >= len(ohlc):
                rec[f'signed_ret_{h}'] = np.nan
                rec[f'fav_{h}'] = np.nan
                rec[f'adv_{h}'] = np.nan
                continue

            window_high = highs[idx + 1:end + 1]
            window_low = lows[idx + 1:end + 1]
            exit_close = closes[end]
            rec[f'signed_ret_{h}'] = (exit_close - row.entry_close) * row.signal / row.entry_atr14
            if row.signal == 1:
                rec[f'fav_{h}'] = (window_high.max() - row.entry_close) / row.entry_atr14
                rec[f'adv_{h}'] = (row.entry_close - window_low.min()) / row.entry_atr14
            else:
                rec[f'fav_{h}'] = (row.entry_close - window_low.min()) / row.entry_atr14
                rec[f'adv_{h}'] = (window_high.max() - row.entry_close) / row.entry_atr14

        for level in ADVERSE_LEVELS:
            level_label = str(level)
            adverse_hits = [h for h in PATH_HORIZONS if pd.notna(rec[f'adv_{h}']) and rec[f'adv_{h}'] >= level]
            favorable_hits = [h for h in PATH_HORIZONS if pd.notna(rec[f'fav_{h}']) and rec[f'fav_{h}'] >= level]
            adverse_idx = adverse_hits[0] if adverse_hits else np.nan
            favorable_idx = favorable_hits[0] if favorable_hits else np.nan
            rec[f'adverse_first_{level_label}atr'] = float(
                pd.notna(adverse_idx) and (pd.isna(favorable_idx) or adverse_idx < favorable_idx)
            )
            rec[f'favorable_first_{level_label}atr'] = float(
                pd.notna(favorable_idx) and (pd.isna(adverse_idx) or favorable_idx < adverse_idx)
            )
            rec[f'dip_then_rally_{level_label}atr'] = float(
                pd.notna(adverse_idx) and pd.notna(favorable_idx) and adverse_idx < favorable_idx
            )
            rec[f'rally_then_dip_{level_label}atr'] = float(
                pd.notna(adverse_idx) and pd.notna(favorable_idx) and favorable_idx < adverse_idx
            )
        if tail_censored:
            for level in ADVERSE_LEVELS:
                level_label = str(level)
                rec[f'adverse_first_{level_label}atr'] = np.nan
                rec[f'favorable_first_{level_label}atr'] = np.nan
                rec[f'dip_then_rally_{level_label}atr'] = np.nan
                rec[f'rally_then_dip_{level_label}atr'] = np.nan
        rows.append(rec)

    if missing_times:
        missing_str = ', '.join(str(ts) for ts in missing_times)
        raise ValueError(f'Signal timestamps missing from OHLC: {missing_str}')

    return pd.DataFrame(rows)


ARCHETYPE_NAMES = {
    'best_early_and_final': 'immediate_continuation',
    'worst_early_but_positive_final': 'deep_dip_then_recovery',
    'worst_final': 'failure_or_adverse_continuation',
    'remainder': 'flat_or_noisy_drift',
}


class MergedClusterPredictor:
    def __init__(self, base_model, label_map: dict[int, int]):
        self.base_model = base_model
        self.label_map = dict(label_map)

    def predict(self, X):
        if not isinstance(X, pd.DataFrame) and hasattr(self.base_model, 'feature_names_in_'):
            X = pd.DataFrame(X, columns=self.base_model.feature_names_in_)
        raw_labels = self.base_model.predict(X)
        return np.asarray([self.label_map[int(label)] for label in raw_labels], dtype=int)


def fit_path_archetypes(frame: pd.DataFrame, min_frac: float = 0.10) -> tuple[pd.DataFrame, dict]:
    if frame.empty:
        raise ValueError('fit_path_archetypes requires at least one row')
    signed_ret_cols = sorted([col for col in frame.columns if col.startswith('signed_ret_')])
    adv_cols = sorted([col for col in frame.columns if col.startswith('adv_')])
    if not signed_ret_cols:
        raise ValueError('fit_path_archetypes requires at least one signed_ret_ column')
    if not adv_cols:
        raise ValueError('fit_path_archetypes requires at least one adv_ column')
    feature_cols = sorted([
        col for col in frame.columns
        if col.startswith('signed_ret_') or col.startswith('fav_') or col.startswith('adv_')
    ])
    X = frame[feature_cols].fillna(0.0)
    distinct_rows = len(X.drop_duplicates())
    n_clusters = max(1, min(4, distinct_rows))
    model = KMeans(n_clusters=n_clusters, n_init=20, random_state=0)
    labels = model.fit_predict(X)
    out = frame.copy()
    out['cluster_id'] = labels
    cluster_sizes = out['cluster_id'].value_counts().to_dict()
    cluster_centers = {
        int(cluster_id): model.cluster_centers_[cluster_id].copy()
        for cluster_id in range(len(model.cluster_centers_))
    }
    label_map = {int(cluster_id): int(cluster_id) for cluster_id in cluster_sizes}
    total = len(out)
    while len(cluster_sizes) > 1:
        shares = {cluster_id: size / total for cluster_id, size in cluster_sizes.items()}
        small = min(shares, key=shares.get)
        if shares[small] >= min_frac:
            break

        small_center = cluster_centers.get(small)
        if small_center is None:
            break

        candidates = [cluster_id for cluster_id in cluster_sizes if cluster_id != small and cluster_id in cluster_centers]
        if not candidates:
            break

        distances = {
            cluster_id: float(np.sum((cluster_centers[cluster_id] - small_center) ** 2))
            for cluster_id in candidates
        }
        nearest = min(distances, key=distances.get)
        nearest_size = cluster_sizes[nearest]
        small_size = cluster_sizes[small]
        cluster_centers[nearest] = (
            cluster_centers[nearest] * nearest_size + small_center * small_size
        ) / (nearest_size + small_size)
        out.loc[out['cluster_id'] == small, 'cluster_id'] = nearest
        for raw_label, final_label in list(label_map.items()):
            if final_label == small:
                label_map[raw_label] = nearest
        cluster_sizes[nearest] = nearest_size + small_size
        del cluster_sizes[small]
        del cluster_centers[small]

    early_col = 'signed_ret_1' if 'signed_ret_1' in out.columns else signed_ret_cols[0]
    final_col = 'signed_ret_12' if 'signed_ret_12' in out.columns else signed_ret_cols[-1]
    dip_col = 'adv_3' if 'adv_3' in out.columns else adv_cols[-1]
    cluster_stats = out.groupby('cluster_id').agg(
        early_q50=(early_col, 'median'),
        final_q50=(final_col, 'median'),
        dip_q50=(dip_col, 'median'),
    )
    best_early = cluster_stats['early_q50'].idxmax()
    worst_final = cluster_stats['final_q50'].idxmin()
    recovery_candidates = cluster_stats[cluster_stats['final_q50'] > 0]
    deepest_dip = None if recovery_candidates.empty else recovery_candidates['dip_q50'].idxmax()
    role_targets = {
        ARCHETYPE_NAMES['best_early_and_final']: best_early,
        ARCHETYPE_NAMES['worst_final']: worst_final,
    }
    if deepest_dip is not None:
        role_targets[ARCHETYPE_NAMES['worst_early_but_positive_final']] = deepest_dip
    collisions = Counter(role_targets.values())
    name_map = {
        cluster_id: name
        for name, cluster_id in role_targets.items()
        if collisions[cluster_id] == 1
    }
    for cluster_id in cluster_stats.index:
        name_map.setdefault(cluster_id, ARCHETYPE_NAMES['remainder'])
    out['archetype'] = out['cluster_id'].map(name_map)
    predictor = MergedClusterPredictor(model, label_map)
    return out, {
        'feature_cols': feature_cols,
        'cluster_stats': cluster_stats.reset_index(),
        'model': predictor,
        'name_map': name_map,
    }


def fit_explanation_tree(frame: pd.DataFrame, feature_cols: list[str]) -> tuple[DecisionTreeClassifier, str]:
    if frame.empty:
        raise ValueError('fit_explanation_tree requires at least one row')
    if not feature_cols:
        raise ValueError('fit_explanation_tree requires a non-empty feature_cols list')
    missing = [col for col in feature_cols if col not in frame.columns]
    if missing:
        missing_cols = ', '.join(missing)
        raise ValueError(f'fit_explanation_tree missing feature columns: {missing_cols}')
    if 'archetype' not in frame.columns:
        raise ValueError('fit_explanation_tree requires an archetype column')
    min_leaf = max(80, int(np.ceil(0.05 * len(frame))))
    model = DecisionTreeClassifier(max_depth=2, min_samples_leaf=min_leaf, random_state=0)
    model.fit(frame[feature_cols].fillna(0.0), frame['archetype'])
    return model, export_text(model, feature_names=feature_cols)


def classify_replication_verdict(row: dict) -> str:
    if row['N_holdout'] < 30:
        return 'Exploratory'

    same_sign = 0
    retained = 0
    for metric, direction in KEY_REPLICATION_METRICS:
        discovery_key = f'delta_{metric}_discovery'
        holdout_key = f'delta_{metric}_holdout'
        discovery_value = row[discovery_key]
        holdout_value = row[holdout_key]
        if pd.isna(discovery_value) or pd.isna(holdout_value):
            continue
        discovery_value *= direction
        holdout_value *= direction
        if discovery_value == 0:
            continue
        if np.sign(discovery_value) == np.sign(holdout_value) or holdout_value == 0:
            same_sign += 1
        if abs(holdout_value) >= 0.5 * abs(discovery_value):
            retained += 1

    if same_sign >= 3 and retained >= 2:
        return 'Replicated'
    if same_sign >= 3:
        return 'Directionally consistent'
    return 'Failed'


def build_split_summary(discovery: pd.DataFrame, holdout: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([
        {
            'sample': 'discovery',
            'N': len(discovery),
            'start': discovery['time'].min(),
            'end': discovery['time'].max(),
            'buy_N': int((discovery['signal'] == 1).sum()),
            'sell_N': int((discovery['signal'] == -1).sum()),
        },
        {
            'sample': 'holdout',
            'N': len(holdout),
            'start': holdout['time'].min(),
            'end': holdout['time'].max(),
            'buy_N': int((holdout['signal'] == 1).sum()),
            'sell_N': int((holdout['signal'] == -1).sum()),
        },
    ])


def summarize_archetypes(frame: pd.DataFrame) -> pd.DataFrame:
    adverse_first_col = _resolve_first_passage_col(frame, 'adverse_first_1atr', 'adverse_first_1.0atr')
    grouped = frame.groupby('archetype', dropna=False)
    rows = []
    for archetype, group in grouped:
        rows.append({
            'archetype': archetype,
            'N': len(group),
            'signed_ret_12_q50': group['signed_ret_12'].median(),
            'fav_12_q50': group['fav_12'].median(),
            'adv_12_q50': group['adv_12'].median(),
            'adverse_first_1atr_pct': np.nan if adverse_first_col is None else 100.0 * group[adverse_first_col].mean(),
        })
    return pd.DataFrame(rows)


def _resolve_first_passage_col(frame: pd.DataFrame, *candidates: str) -> str | None:
    return next((col for col in candidates if col in frame.columns), None)


def _artifact_metrics(frame: pd.DataFrame) -> dict:
    adverse_first_col = _resolve_first_passage_col(frame, 'adverse_first_1atr', 'adverse_first_1.0atr')
    return {
        'N': len(frame),
        'signed_ret_12_q50': frame['signed_ret_12'].median(),
        'fav_hit_3atr_12h': 100.0 * (frame['fav_12'] >= 3.0).mean(),
        'adv_hit_1atr_3h': 100.0 * (frame['adv_3'] >= 1.0).mean(),
        'adverse_first_1atr': np.nan if adverse_first_col is None else 100.0 * frame[adverse_first_col].mean(),
    }


def _subset_for_value(frame: pd.DataFrame, col: str, value) -> pd.DataFrame:
    if pd.isna(value):
        return frame[frame[col].isna()]
    return frame[frame[col] == value]


def _build_interval_mask(series: pd.Series, left: float, right: float, closed: str) -> pd.Series:
    lower = series >= left if closed in ('both', 'left') else series > left
    upper = series <= right if closed in ('both', 'right') else series < right
    return series.notna() & lower & upper


def _slice_membership_mask(frame: pd.DataFrame, slice_row) -> pd.Series:
    series = pd.to_numeric(frame[slice_row.feature], errors='coerce')
    if hasattr(slice_row, 'interval_left') and hasattr(slice_row, 'interval_right') and hasattr(slice_row, 'interval_closed'):
        return _build_interval_mask(series, slice_row.interval_left, slice_row.interval_right, slice_row.interval_closed)
    return series.between(slice_row.lower_edge, slice_row.upper_edge, inclusive='both')


def build_holdout_verdicts(
    discovery: pd.DataFrame,
    holdout: pd.DataFrame,
    numeric_slices: pd.DataFrame,
    archetype_artifacts: dict,
) -> pd.DataFrame:
    discovery_base = _artifact_metrics(discovery)
    holdout_base = _artifact_metrics(holdout)
    rows = []

    for slice_row in numeric_slices.itertuples(index=False):
        discovery_mask = _slice_membership_mask(discovery, slice_row)
        holdout_mask = _slice_membership_mask(holdout, slice_row)
        discovery_metrics = _artifact_metrics(discovery[discovery_mask])
        holdout_metrics = _artifact_metrics(holdout[holdout_mask])
        row = {
            'artifact_id': f'{slice_row.feature}:bin_{slice_row.bin_id}',
            'N_holdout': holdout_metrics['N'],
        }
        for metric, _direction in KEY_REPLICATION_METRICS:
            row[f'delta_{metric}_discovery'] = discovery_metrics[metric] - discovery_base[metric]
            row[f'delta_{metric}_holdout'] = holdout_metrics[metric] - holdout_base[metric]
        row['verdict'] = classify_replication_verdict(row)
        rows.append(row)

    for col in FIXED_COHORT_COLS:
        if col not in discovery.columns or col not in holdout.columns:
            continue
        for value, discovery_group in discovery.groupby(col, dropna=False):
            holdout_group = _subset_for_value(holdout, col, value)
            discovery_metrics = _artifact_metrics(discovery_group)
            holdout_metrics = _artifact_metrics(holdout_group)
            row = {
                'artifact_id': f'{col}={value}',
                'N_holdout': holdout_metrics['N'],
            }
            for metric, _direction in KEY_REPLICATION_METRICS:
                row[f'delta_{metric}_discovery'] = discovery_metrics[metric] - discovery_base[metric]
                row[f'delta_{metric}_holdout'] = holdout_metrics[metric] - holdout_base[metric]
            row['verdict'] = classify_replication_verdict(row)
            rows.append(row)

    holdout_named = holdout.copy()
    if not holdout_named.empty:
        X_holdout = holdout_named[archetype_artifacts['feature_cols']].fillna(0.0)
        holdout_clusters = archetype_artifacts['model'].predict(X_holdout)
        holdout_named['archetype'] = pd.Series(holdout_clusters, index=holdout_named.index).map(archetype_artifacts['name_map'])
    else:
        holdout_named['archetype'] = pd.Series(dtype='object')
    for archetype, discovery_group in discovery.groupby('archetype', dropna=False):
        group = _subset_for_value(holdout_named, 'archetype', archetype)
        discovery_metrics = _artifact_metrics(discovery_group)
        holdout_metrics = _artifact_metrics(group)
        row = {
            'artifact_id': f'archetype:{archetype}',
            'N_holdout': holdout_metrics['N'],
        }
        for metric, _direction in KEY_REPLICATION_METRICS:
            row[f'delta_{metric}_discovery'] = discovery_metrics[metric] - discovery_base[metric]
            row[f'delta_{metric}_holdout'] = holdout_metrics[metric] - holdout_base[metric]
        row['verdict'] = classify_replication_verdict(row)
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=['artifact_id', 'N_holdout', 'verdict'])
    return pd.DataFrame(rows).sort_values(['verdict', 'artifact_id']).reset_index(drop=True)


def build_execution_implications(holdout_verdicts: pd.DataFrame) -> pd.DataFrame:
    replicated = holdout_verdicts[holdout_verdicts['verdict'] == 'Replicated']
    recommendation = 'neither'
    if (
        not replicated.empty
        and replicated['artifact_id'].str.contains('archetype:deep_dip_then_recovery', regex=False).any()
    ):
        recommendation = 'pullback'
    if (
        not replicated.empty
        and replicated['artifact_id'].str.contains('archetype:immediate_continuation', regex=False).any()
    ):
        recommendation = 'market' if recommendation == 'neither' else 'market and pullback both justified'
    return pd.DataFrame([{'recommendation': recommendation}])


def export_tables(tables: dict[str, pd.DataFrame], export_dir: Path) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(export_dir / f'{name}.csv', index=False)


def load_atlas_inputs(test_only: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged, ohlc = sr.load_data(test_only=test_only)
    base = merged[merged['signal'] != 0].copy()
    base['entry_close'] = base['close']
    base['entry_atr14'] = base['atr14']
    return base.reset_index(drop=True), ohlc


def print_report_sections(tables: dict[str, pd.DataFrame]) -> None:
    print('Signal Path Atlas — Discovery/Holdout Split')
    print(tables['split_summary'].to_string(index=False))
    print('\nFeature Variance Screen')
    print(tables['feature_screen'].to_string(index=False))
    print('\nGlobal Path Quantiles')
    print(tables['path_quantiles'].to_string(index=False))
    print('\nFirst Passage Atlas')
    print(tables['first_passage'].to_string(index=False))
    print('\nOrdering Atlas')
    print(tables['ordering'].to_string(index=False))
    print('\nArchetype Summary')
    print(tables['archetype_summary'].to_string(index=False))
    print('\nHoldout Replication Verdicts')
    print(tables['holdout_verdicts'].to_string(index=False))
    print('\nExecution Implications')
    print(tables['execution_implications'].to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description='Signal Path Atlas')
    parser.add_argument('--test-only', action='store_true')
    parser.add_argument('--export-dir', type=Path, default=None)
    args = parser.parse_args()

    signals, ohlc = load_atlas_inputs(test_only=args.test_only)
    split = annotate_sample_split(signals)
    tensor = build_path_tensor(split, ohlc)
    merged = tensor.merge(split, on=['time', 'signal', 'entry_close', 'entry_atr14'])
    discovery_raw = merged[merged['sample'] == 'discovery'].reset_index(drop=True)
    holdout_raw = merged[merged['sample'] == 'holdout'].reset_index(drop=True)
    discovery, conditioning_artifacts = build_conditioning_frame(discovery_raw)
    holdout, _holdout_artifacts = build_conditioning_frame(
        holdout_raw,
        atr_edges=conditioning_artifacts['atr_edges'],
    )

    feature_screen, live_numeric = screen_numeric_features(discovery, NUMERIC_FEATURES)
    global_atlas = build_global_atlas(discovery)
    if live_numeric:
        numeric_slices = pd.concat(
            [build_numeric_slices(discovery, feature) for feature in live_numeric],
            ignore_index=True,
        )
    else:
        numeric_slices = pd.DataFrame(columns=[
            'feature', 'bin_id', 'N', 'signed_ret_12_q50', 'fav_12_q50', 'adv_12_q50',
            'adverse_first_1atr_pct', 'favorable_first_1atr_pct',
            'dip_then_rally_1atr_pct', 'rally_then_dip_1atr_pct',
            'lower_edge', 'upper_edge',
        ])
    categorical_slices = build_categorical_slices(discovery, FIXED_COHORT_COLS)
    archetyped, archetype_artifacts = fit_path_archetypes(discovery)
    if live_numeric:
        _tree_model, _tree_text = fit_explanation_tree(archetyped, live_numeric)
    else:
        _tree_model, _tree_text = None, ''
    holdout_verdicts = build_holdout_verdicts(archetyped, holdout, numeric_slices, archetype_artifacts)
    tables = {
        'split_summary': build_split_summary(archetyped, holdout),
        'feature_screen': feature_screen,
        'path_quantiles': global_atlas['path_quantiles'],
        'first_passage': global_atlas['first_passage'],
        'ordering': global_atlas['ordering'],
        'numeric_slices': numeric_slices,
        'categorical_slices': categorical_slices,
        'archetype_summary': summarize_archetypes(archetyped),
        'holdout_verdicts': holdout_verdicts,
        'execution_implications': build_execution_implications(holdout_verdicts),
    }
    print_report_sections(tables)
    if args.export_dir is not None:
        export_tables(tables, args.export_dir)


if __name__ == '__main__':
    main()
