import numpy as np
import pandas as pd

from ML.tb_signal_logic import evaluate_tb_signal_rule
from ML.threshold_analysis import analyze_thresholds_tb

TP = 1.0
SL = 0.0
TIMEOUT = 0.5


def test_tb_signal_logic_loss_excludes_timeout():
    df_signals = pd.DataFrame(
        {
            'signal': [1, 1, 1],
            'sl_atr': [2.0, 3.0, 5.0],
            'tp_atr': [4.0, 6.0, 8.0],
            'prob': [0.9, 0.9, 0.9],
            'ev': [1.0, 1.0, 1.0],
            'target_index': [0, 0, 0],
            'target_name': ['buy_sl2_tp4', 'buy_sl2_tp4', 'buy_sl2_tp4'],
        }
    )
    y_true_raw = np.array([[TP], [SL], [TIMEOUT]], dtype=np.float32)

    result = evaluate_tb_signal_rule(df_signals, y_true_raw)

    assert result['wins'] == 1
    assert result['losses'] == 1
    assert result['timeouts'] == 1
    assert result['loss'] == 3.0


def test_threshold_analysis_loss_excludes_timeout():
    y_pred_proba = np.full((10, 1), 0.9, dtype=np.float32)
    y_true = np.array(
        [[TP], [TP], [TP], [TP], [SL], [SL], [SL], [TIMEOUT], [TIMEOUT], [TIMEOUT]],
        dtype=np.float32,
    )

    result = analyze_thresholds_tb(
        y_pred_proba=y_pred_proba,
        y_true=y_true,
        target_names=['buy_sl3_tp6'],
        n_thresholds=1,
    )

    assert len(result) == 1
    row = result.iloc[0]
    assert int(row['trades']) == 10
    assert int(row['wins']) == 4
    assert int(row['losses']) == 3
    assert int(row['timeouts']) == 3
    assert float(row['loss']) == 9.0
