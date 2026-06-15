# Тесты для ML/baseline/diagnose_stage4_3.py
# Stage 4.3: DIAGNOSTIC_ONLY helpers

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ML.baseline.diagnose_stage4_3 import (
    compute_trade_metrics,
    compute_yearly_metrics,
    loss_attribution,
    actual_rr,
    resolve_tp_val,
    block_bootstrap_pf,
    block_bootstrap_mean_pnl,
    profit_concentration,
    summarize_trade_category,
)


class TestComputeTradeMetrics:
    def test_compute_trade_metrics_basic_pf_and_years(self):
        trades = [
            {"pnl_val": 1.0, "year": 2019, "exit": "TP"},
            {"pnl_val": -0.5, "year": 2019, "exit": "SL"},
            {"pnl_val": 0.2, "year": 2020, "exit": "TIMEOUT"},
            {"pnl_val": -0.3, "year": 2020, "exit": "SL"},
        ]
        out = compute_trade_metrics(trades)
        assert out["n_trades"] == 4
        assert out["pf"] == pytest.approx(1.5)
        assert "yearly" in out
        assert "2019" in out["yearly"]
        assert out["yearly"]["2019"]["pf"] == pytest.approx(2.0)
        assert out["yearly"]["2019"]["n"] == 2

    def test_compute_trade_metrics_empty(self):
        out = compute_trade_metrics([])
        assert out["n_trades"] == 0
        assert out["pf"] == 0.0

    def test_compute_trade_metrics_gross_profit_loss(self):
        trades = [
            {"pnl_val": 0.8, "year": 2020, "exit": "TP"},
            {"pnl_val": -0.4, "year": 2020, "exit": "SL"},
        ]
        out = compute_trade_metrics(trades)
        assert out["gross_profit"] == pytest.approx(0.8)
        assert out["gross_loss"] == pytest.approx(0.4)

    def test_compute_yearly_metrics(self):
        trades = [
            {"pnl_val": 1.0, "year": 2019, "exit": "TP"},
            {"pnl_val": -0.5, "year": 2019, "exit": "SL"},
            {"pnl_val": 0.2, "year": 2020, "exit": "TIMEOUT"},
        ]
        yearly = compute_yearly_metrics(trades)
        assert "2019" in yearly
        assert yearly["2019"]["n"] == 2
        assert yearly["2019"]["pf"] == pytest.approx(2.0)
        assert "2020" in yearly
        assert yearly["2020"]["pf"] == pytest.approx(float('inf'))


class TestLossAttribution:
    def test_loss_attribution_separates_exit_types_and_ambiguous_sl(self):
        trades = [
            {"pnl_val": 0.4, "exit": "TP", "ambiguous": 0},
            {"pnl_val": -1.0, "exit": "SL", "ambiguous": 0},
            {"pnl_val": -1.0, "exit": "SL", "ambiguous": 1},
            {"pnl_val": -0.2, "exit": "TIMEOUT", "ambiguous": 0},
        ]
        out = loss_attribution(trades)
        assert out["SL"]["n"] == 2
        assert out["SL"]["ambiguous_sl"] == 1
        assert out["SL"]["breach_fn_non_ambiguous"] == 1
        assert out["TIMEOUT"]["total_pnl"] == pytest.approx(-0.2)

    def test_loss_attribution_tp_gross_profit(self):
        trades = [
            {"pnl_val": 0.5, "exit": "TP", "ambiguous": 0},
            {"pnl_val": -0.3, "exit": "SL", "ambiguous": 0},
        ]
        out = loss_attribution(trades)
        assert out["TP"]["n"] == 1
        assert out["TP"]["gross_profit"] == pytest.approx(0.5)
        assert out["SL"]["n"] == 1
        assert out["SL"]["gross_loss"] == pytest.approx(0.3)

    def test_loss_attribution_pct_of_total(self):
        trades = [
            {"pnl_val": 0.8, "exit": "TP", "ambiguous": 0},
            {"pnl_val": -0.3, "exit": "SL", "ambiguous": 0},
            {"pnl_val": -0.2, "exit": "TIMEOUT", "ambiguous": 0},
        ]
        out = loss_attribution(trades)
        total_gross_loss = 0.3 + 0.2
        assert out["SL"]["pct_of_total_gross_loss"] == pytest.approx(0.3 / total_gross_loss)
        assert out["SL"]["pct_of_total_gross_profit"] == pytest.approx(0.0)


class TestActualRR:
    def test_actual_rr_uses_tp_val_over_stop_val(self):
        trade = {"tp_val": 0.4, "stop_val": 1.0}
        assert actual_rr(trade) == pytest.approx(0.4)

    def test_actual_rr_zero_stop(self):
        trade = {"tp_val": 0.4, "stop_val": 0.0}
        assert actual_rr(trade) == 0.0


class TestResolveTpVal:
    def test_fixed_atr(self):
        assert resolve_tp_val("fixed_atr", 0.5, pred_fav=2.0, stop_val=1.2) == pytest.approx(0.5)

    def test_fixed_r(self):
        assert resolve_tp_val("fixed_r", 0.5, pred_fav=2.0, stop_val=1.2) == pytest.approx(0.6)

    def test_fav_fraction(self):
        assert resolve_tp_val("fav_fraction", 0.4, pred_fav=2.0, stop_val=1.2) == pytest.approx(0.8)


class TestBlockBootstrap:
    def test_block_bootstrap_returns_quantiles(self):
        rng = np.random.RandomState(42)
        trades = []
        for i in range(200):
            pnl = rng.choice([0.3, -0.2, 0.1, -0.15, 0.5])
            trades.append({"pnl_val": pnl, "year": 2020})
        result = block_bootstrap_pf(trades, block_size=15, n_iter=100, seed=42)
        assert "pf_median" in result
        assert "pf_p05" in result
        assert "pf_p95" in result
        assert result["pf_p05"] <= result["pf_median"] <= result["pf_p95"]

    def test_block_bootstrap_too_few_trades(self):
        trades = [{"pnl_val": 0.1, "year": 2020}]
        result = block_bootstrap_pf(trades, block_size=15, n_iter=100, seed=42)
        assert result["pf_median"] is None

    def test_block_bootstrap_mean_pnl_returns_quantiles(self):
        trades = [{"pnl_val": 0.1 if i % 2 == 0 else -0.05, "year": 2020}
                  for i in range(120)]
        result = block_bootstrap_mean_pnl(
            trades, block_size=10, n_iter=100, seed=42)
        assert "mean_pnl_median" in result
        assert "mean_pnl_p05" in result
        assert "mean_pnl_p95" in result
        assert result["mean_pnl_p05"] <= result["mean_pnl_median"] <= result["mean_pnl_p95"]


class TestTradeCategorySummary:
    def test_summarize_trade_category_includes_pnl_yearly_exits_and_bootstrap(self):
        trades = []
        for i in range(120):
            trades.append({
                "pnl_val": 0.2 if i % 3 else -0.1,
                "year": 2019 + (i % 2),
                "exit": "TP" if i % 3 else "SL",
            })
        out = summarize_trade_category(
            trades, n_candidates=150, n_eligible=300,
            baseline_total_pnl=5.0, block_size=10, n_bootstrap=100)
        assert out["n_candidates"] == 150
        assert out["pct_of_eligible"] == pytest.approx(50.0)
        assert out["n_trades"] == 120
        assert "total_pnl" in out
        assert "mean_pnl" in out
        assert "yearly_pf" in out
        assert "bootstrap_mean_pnl" in out
        assert "tp_n" in out
        assert "sl_n" in out
        assert "delta_vs_baseline_total_pnl" in out


class TestProfitConcentration:
    def test_concentration_no_warning(self):
        yearly = {
            "2019": {"gross_profit": 0.5},
            "2020": {"gross_profit": 0.3},
            "2021": {"gross_profit": 0.2},
            "2022": {"gross_profit": 0.1},
        }
        result = profit_concentration(yearly)
        assert result["max_year_profit_share"] < 0.6
        assert result["profit_concentration_warning"] is False

    def test_concentration_warning_dominant_year(self):
        yearly = {
            "2019": {"gross_profit": 0.1},
            "2020": {"gross_profit": 0.8},
            "2021": {"gross_profit": 0.05},
            "2022": {"gross_profit": 0.05},
        }
        result = profit_concentration(yearly)
        assert result["max_year_profit_share"] > 0.6
        assert result["profit_concentration_warning"] is True
