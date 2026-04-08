import json
from pathlib import Path

import pandas as pd
import ML.benchmark_outcome_targets as bot


def test_pick_winner_prefers_higher_pf_with_trade_floor():
    frame = pd.DataFrame([
        {'task': 'a', 'pf': 1.4, 'trades': 120, 'stability_ratio': 1.0},
        {'task': 'b', 'pf': 1.8, 'trades': 24, 'stability_ratio': 1.0},
        {'task': 'c', 'pf': 1.6, 'trades': 100, 'stability_ratio': 0.75},
    ])

    out = bot.pick_winner(frame, min_trades=80)

    assert out['task'] == 'c'


def test_pick_winner_filters_out_unstable_candidates():
    frame = pd.DataFrame([
        {'task': 'a', 'pf': 1.9, 'trades': 140, 'stability_ratio': 0.5},
        {'task': 'b', 'pf': 1.6, 'trades': 110, 'stability_ratio': 0.75},
    ])

    out = bot.pick_winner(frame, min_trades=80, min_stability_ratio=0.75)

    assert out['task'] == 'b'


def test_benchmark_skips_family_without_viable_slice_and_freezes_remaining_winner(tmp_path, monkeypatch):
    monkeypatch.setattr(bot, 'REPORTS_DIR', tmp_path)
    monkeypatch.setattr(bot, 'TASKS', ['task_a', 'task_b'])
    monkeypatch.setattr(bot, 'task_target_column', lambda task: task)
    monkeypatch.setattr(bot, 'set_seed', lambda seed: None)
    monkeypatch.setattr(bot, 'get_device', lambda: 'cpu')
    monkeypatch.setattr(bot, 'load_validation_frame', lambda: pd.DataFrame({'signal': [1, -1]}))
    monkeypatch.setattr(bot, 'create_data_loaders', lambda **kwargs: (None, kwargs['target'], None))
    monkeypatch.setattr(bot, 'load_model_for_task', lambda model_name, task, device: (object(), {}, Path(f'/tmp/{task}.pt')))
    monkeypatch.setattr(bot, 'run_validation_scores', lambda model, val_loader, task, device: [0.1, 0.2])

    def fake_slices(_frame, _score, task, top_pcts, min_year_trades):
        if task == 'task_a':
            return pd.DataFrame([
                {'task': 'task_a', 'top_pct': 0.10, 'score_threshold': 0.9, 'trades': 40, 'pf': 2.0,
                 'stability_ratio': 0.0, 'eligible_years': 1, 'stable_years': 0, 'worst_year_pf': 0.8,
                 'mean_pnl_atr': 0.4, 'yearly_detail_json': '{}'}
            ])
        return pd.DataFrame([
            {'task': 'task_b', 'top_pct': 0.20, 'score_threshold': 0.7, 'trades': 120, 'pf': 1.5,
             'stability_ratio': 1.0, 'eligible_years': 3, 'stable_years': 3, 'worst_year_pf': 1.1,
             'mean_pnl_atr': 0.2, 'yearly_detail_json': '{}'}
        ])

    monkeypatch.setattr(bot, 'evaluate_score_slices', fake_slices)

    result = bot.benchmark_outcome_targets(model_name='transformer', min_trades=80, min_stability_ratio=0.75)

    assert result['winner']['task'] == 'task_b'

    frozen = json.loads((tmp_path / 'frozen_outcome_target.json').read_text(encoding='utf-8'))
    rejected = {row['task']: row for row in frozen['rejected']}

    assert rejected['task_a']['passed_filters'] is False
    assert rejected['task_a']['rejection_reason'] == 'no_slice_passed_filters'


def test_benchmark_returns_no_winner_when_all_families_fail_filters(tmp_path, monkeypatch):
    monkeypatch.setattr(bot, 'REPORTS_DIR', tmp_path)
    monkeypatch.setattr(bot, 'TASKS', ['task_a', 'task_b'])
    monkeypatch.setattr(bot, 'task_target_column', lambda task: task)
    monkeypatch.setattr(bot, 'set_seed', lambda seed: None)
    monkeypatch.setattr(bot, 'get_device', lambda: 'cpu')
    monkeypatch.setattr(bot, 'load_validation_frame', lambda: pd.DataFrame({'signal': [1, -1]}))
    monkeypatch.setattr(bot, 'create_data_loaders', lambda **kwargs: (None, kwargs['target'], None))
    monkeypatch.setattr(bot, 'load_model_for_task', lambda model_name, task, device: (object(), {}, Path(f'/tmp/{task}.pt')))
    monkeypatch.setattr(bot, 'run_validation_scores', lambda model, val_loader, task, device: [0.1, 0.2])
    monkeypatch.setattr(
        bot,
        'evaluate_score_slices',
        lambda _frame, _score, task, top_pcts, min_year_trades: pd.DataFrame([
            {'task': task, 'top_pct': 0.10, 'score_threshold': 0.9, 'trades': 40, 'pf': 0.8,
             'stability_ratio': 0.0, 'eligible_years': 1, 'stable_years': 0, 'worst_year_pf': 0.8,
             'mean_pnl_atr': -0.2, 'yearly_detail_json': '{}'}
        ]),
    )

    result = bot.benchmark_outcome_targets(model_name='transformer', min_trades=80, min_stability_ratio=0.75)

    assert result['winner'] is None
    assert result['json_path'] is None
    assert (tmp_path / 'outcome_target_validation_benchmark.csv').exists()
    assert (tmp_path / 'outcome_target_validation_benchmark.md').exists()
    assert not (tmp_path / 'frozen_outcome_target.json').exists()
