# Tests for Stage 4.6 clean candidate-cycle protocol

import pytest
import numpy as np
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ML.baseline.benchmark_stage4_6_clean_cycle import (
    CandidateRule,
    select_rule,
    evaluate_rule,
)


class TestSelectRule:
    def test_selects_best_bs_p05(self):
        candidates = [
            CandidateRule('a', pf=1.5, bs_p05=1.2, n_trades=50, neg_years=0),
            CandidateRule('b', pf=2.0, bs_p05=0.9, n_trades=60, neg_years=0),
        ]
        result = select_rule(candidates, gates={'min_trades_per_year': 30})
        assert result.name == 'a'

    def test_tie_breaks_by_pf(self):
        candidates = [
            CandidateRule('a', pf=1.5, bs_p05=1.2, n_trades=50, neg_years=0),
            CandidateRule('c', pf=2.0, bs_p05=1.2, n_trades=50, neg_years=0),
        ]
        result = select_rule(candidates, gates={'min_trades_per_year': 30})
        assert result.name == 'c'

    def test_rejects_below_min_trades(self):
        candidates = [
            CandidateRule('a', pf=2.0, bs_p05=1.5, n_trades=20, neg_years=0),
            CandidateRule('b', pf=1.0, bs_p05=0.8, n_trades=60, neg_years=0),
        ]
        result = select_rule(candidates, gates={'min_trades_per_year': 30})
        assert result.name == 'b'

    def test_rejects_null_bs_p05(self):
        candidates = [
            CandidateRule('a', pf=2.0, bs_p05=None, n_trades=50, neg_years=0),
            CandidateRule('b', pf=1.0, bs_p05=0.8, n_trades=60, neg_years=0),
        ]
        result = select_rule(candidates, gates={'min_trades_per_year': 30})
        assert result.name == 'b'

    def test_no_candidate_passes_returns_none(self):
        candidates = [
            CandidateRule('a', pf=2.0, bs_p05=1.5, n_trades=20, neg_years=0),
            CandidateRule('b', pf=2.0, bs_p05=None, n_trades=20, neg_years=0),
        ]
        result = select_rule(candidates, gates={'min_trades_per_year': 30})
        assert result is None

    def test_rejects_high_concentration(self):
        candidates = [
            CandidateRule('a', pf=2.0, bs_p05=1.5, n_trades=50, neg_years=0,
                          gross_profit_concentration=0.8),
            CandidateRule('b', pf=1.0, bs_p05=0.9, n_trades=60, neg_years=0,
                          gross_profit_concentration=0.4),
        ]
        result = select_rule(candidates, gates={
            'min_trades_per_year': 30,
            'max_concentration': 0.6,
        })
        assert result.name == 'b'


class TestEvaluateRule:
    def test_evaluate_returns_metrics(self):
        trades = [
            {'pnl_val': 0.5, 'year': 2021, 'exit': 'TP'},
            {'pnl_val': -0.3, 'year': 2021, 'exit': 'SL'},
            {'pnl_val': 0.8, 'year': 2022, 'exit': 'TP'},
            {'pnl_val': -0.2, 'year': 2022, 'exit': 'SL'},
        ]
        result = evaluate_rule(trades)
        assert result.pf > 1.0
        assert result.n_trades == 4
        assert result.neg_years == 0

    def test_evaluate_empty_trades(self):
        result = evaluate_rule([])
        assert result.pf == 0.0
        assert result.n_trades == 0
        assert result.bs_p05 is None
