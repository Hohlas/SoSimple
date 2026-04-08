import numpy as np
import pandas as pd

from ML.data_loader import TB_TARGET_NAMES


def parse_tb_target_name(name: str) -> tuple[int, int, int]:
    parts = name.split('_')
    direction = 1 if parts[0] == 'buy' else -1
    sl = int(parts[1][2:])
    tp = int(parts[2][2:])
    return direction, sl, tp


def expected_value_from_probability(p, sl, tp):
    p_arr = np.asarray(p, dtype=np.float64)
    return p_arr * float(tp) - (1.0 - p_arr) * float(sl)


def tb_proba_to_signals(
    y_pred_proba: np.ndarray,
    theta: float,
    min_ev: float = 0.0,
    target_names: list[str] | None = None,
) -> pd.DataFrame:
    target_names = list(TB_TARGET_NAMES if target_names is None else target_names)
    proba = np.asarray(y_pred_proba, dtype=np.float64)
    if proba.ndim != 2:
        raise ValueError(f"Expected 2D probability array, got shape {proba.shape}")

    n_rows = proba.shape[0]
    signals = np.zeros(n_rows, dtype=int)
    sl_atrs = np.zeros(n_rows, dtype=float)
    tp_atrs = np.zeros(n_rows, dtype=float)
    probs = np.zeros(n_rows, dtype=float)
    evs = np.zeros(n_rows, dtype=float)
    target_indices = np.full(n_rows, -1, dtype=int)
    target_labels = np.array([''] * n_rows, dtype=object)

    for row_idx in range(n_rows):
        best_idx = -1
        best_signal = 0
        best_sl = 0.0
        best_tp = 0.0
        best_prob = 0.0
        best_ev = -np.inf
        tie_between_directions = False

        for i, name in enumerate(target_names):
            p = float(proba[row_idx, i])
            if p <= theta:
                continue

            direction, sl, tp = parse_tb_target_name(name)
            ev = float(expected_value_from_probability(p, sl=sl, tp=tp))

            if ev > best_ev + 1e-12:
                best_idx = i
                best_signal = direction
                best_sl = float(sl)
                best_tp = float(tp)
                best_prob = p
                best_ev = ev
                tie_between_directions = False
                continue

            if abs(ev - best_ev) <= 1e-12 and best_signal != 0 and direction != best_signal:
                tie_between_directions = True

        if best_idx < 0 or tie_between_directions or best_ev < min_ev:
            continue

        signals[row_idx] = best_signal
        sl_atrs[row_idx] = best_sl
        tp_atrs[row_idx] = best_tp
        probs[row_idx] = round(best_prob, 4)
        evs[row_idx] = round(best_ev, 4)
        target_indices[row_idx] = best_idx
        target_labels[row_idx] = target_names[best_idx]

    return pd.DataFrame({
        'signal': signals,
        'sl_atr': sl_atrs,
        'tp_atr': tp_atrs,
        'prob': probs,
        'ev': evs,
        'target_index': target_indices,
        'target_name': target_labels,
    })


def evaluate_tb_signal_rule(
    df_signals: pd.DataFrame,
    y_true_raw: np.ndarray,
) -> dict:
    trade_mask = df_signals['signal'].to_numpy(dtype=int) != 0
    if not trade_mask.any():
        return {
            'trades': 0,
            'wins': 0,
            'losses': 0,
            'timeouts': 0,
            'win_rate': 0.0,
            'profit': 0.0,
            'loss': 0.0,
            'pf': 0.0,
            'avg_ev': 0.0,
            'dominant_target': '',
            'dominant_target_count': 0,
        }

    row_indices = np.flatnonzero(trade_mask)
    target_indices = df_signals.loc[trade_mask, 'target_index'].to_numpy(dtype=int)
    outcomes = y_true_raw[row_indices, target_indices]

    tp_atrs = df_signals.loc[trade_mask, 'tp_atr'].to_numpy(dtype=float)
    sl_atrs = df_signals.loc[trade_mask, 'sl_atr'].to_numpy(dtype=float)
    evs = df_signals.loc[trade_mask, 'ev'].to_numpy(dtype=float)

    win_mask = outcomes == 1.0
    timeout_mask = outcomes == 0.5
    loss_mask = ~win_mask

    wins = int(win_mask.sum())
    timeouts = int(timeout_mask.sum())
    losses = int(loss_mask.sum())
    trades = int(len(outcomes))

    profit = float(tp_atrs[win_mask].sum())
    loss = float(sl_atrs[loss_mask].sum())
    pf = profit / loss if loss > 0 else float('inf')
    win_rate = wins / trades if trades > 0 else 0.0

    target_counts = df_signals.loc[trade_mask, 'target_name'].value_counts()
    dominant_target = str(target_counts.index[0]) if not target_counts.empty else ''
    dominant_target_count = int(target_counts.iloc[0]) if not target_counts.empty else 0

    return {
        'trades': trades,
        'wins': wins,
        'losses': losses,
        'timeouts': timeouts,
        'win_rate': win_rate,
        'profit': profit,
        'loss': loss,
        'pf': pf,
        'avg_ev': float(evs.mean()) if len(evs) else 0.0,
        'dominant_target': dominant_target,
        'dominant_target_count': dominant_target_count,
    }
