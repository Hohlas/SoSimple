import pandas as pd

from ML.data_loader import (
    TRADE_OUTCOME_TARGET,
    TRADE_PNL_TARGET,
    ARCHETYPE_TARGET,
    TASK_TARGET_COLUMNS,
    BINARY_CLASSIFICATION_TARGETS,
    TRADE_OUTCOME_COLUMN,
    TRADE_PNL_COLUMN,
    ARCHETYPE_COLUMN,
    filter_signal_rows,
    target_uses_signal_rows,
)


def test_new_task_constants_exist():
    assert TRADE_OUTCOME_TARGET == 'trade_outcome_cls'
    assert TRADE_PNL_TARGET == 'trade_pnl_reg'
    assert ARCHETYPE_TARGET == 'signal_archetype_cls'


def test_outcome_tasks_map_to_expected_columns():
    assert TASK_TARGET_COLUMNS[TRADE_OUTCOME_TARGET] == 'trade_outcome_h12'
    assert TASK_TARGET_COLUMNS[TRADE_PNL_TARGET] == 'trade_pnl_h12_atr'
    assert TASK_TARGET_COLUMNS[ARCHETYPE_TARGET] == 'archetype_target'


def test_only_binary_outcome_tasks_are_marked_as_binary():
    assert TRADE_OUTCOME_TARGET in BINARY_CLASSIFICATION_TARGETS
    assert ARCHETYPE_TARGET in BINARY_CLASSIFICATION_TARGETS
    assert TRADE_PNL_TARGET not in BINARY_CLASSIFICATION_TARGETS


def test_outcome_target_columns_use_signal_only_profile():
    assert target_uses_signal_rows(TRADE_OUTCOME_COLUMN) is True
    assert target_uses_signal_rows(TRADE_PNL_COLUMN) is True
    assert target_uses_signal_rows(ARCHETYPE_COLUMN) is True
    assert target_uses_signal_rows('predict') is False


def test_filter_signal_rows_keeps_only_buy_sell_rows_for_outcome_targets():
    frame = pd.DataFrame({
        'signal': [1, 0, -1, 0],
        'value': [10, 20, 30, 40],
    })

    out = filter_signal_rows(frame, TRADE_OUTCOME_COLUMN)

    assert out['signal'].tolist() == [1, -1]
    assert out['value'].tolist() == [10, 30]
