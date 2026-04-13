import pandas as pd

from ML.benchmark_quantile_forward_validation import (
    compute_forward_metrics,
    decide_operational_verdict,
)


def test_compute_forward_metrics_counts_pf_and_trades():
    frame = pd.DataFrame(
        {
            "true_ret_24_dir_atr": [2.0, -1.0, 3.0],
        }
    )

    result = compute_forward_metrics(frame)

    assert result["n_trades"] == 3
    assert result["gross_profit"] == 5.0
    assert result["gross_loss"] == 1.0
    assert result["pf"] == 5.0


def test_decide_operational_verdict_prefers_pf_drawdown_signal():
    result = decide_operational_verdict(
        historical_pf=8.18,
        forward_pf=3.5,
        n_trades=18,
        negative_slices=1,
    )

    assert result["verdict"] == "watch"
