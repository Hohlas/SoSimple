import pandas as pd


def summarize_candidate(
    frame: pd.DataFrame,
    score_col: str,
    threshold: float,
    true_pnl_col: str,
) -> dict[str, float]:
    live = frame.loc[frame[score_col] >= threshold].copy()
    pnl = live[true_pnl_col].to_numpy(dtype=float)
    gross_profit = float(pnl[pnl > 0].sum())
    gross_loss = float(-pnl[pnl < 0].sum())
    pf = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
    return {
        "candidate": score_col,
        "threshold": float(threshold),
        "trades": int(len(live)),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "pf": float(pf),
        "ulcer_index_atr": float(abs(pnl.cumsum()).mean()) if len(pnl) else 0.0,
    }


def pick_validation_winner(table: pd.DataFrame, min_pf: float = 1.0) -> pd.Series | None:
    eligible = table.loc[table["pf"] >= min_pf].copy()
    if eligible.empty:
        return None
    ranked = eligible.sort_values(["pf", "ulcer_index_atr", "trades"], ascending=[False, True, False])
    return ranked.iloc[0]
