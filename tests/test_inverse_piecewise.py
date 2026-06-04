# =============================================================================
# Файл: tests/test_inverse_piecewise.py
# Назначение: Round-trip тесты piecewise_linear_log_transform → inverse для normalize.py / signal_tracer.py
# Язык: Python 3.11+
# Обновлён: 2026-04-05
# Зависимости:
#   Входные данные:
#     - синтетические float-значения (линейная и log-зона)
#   Выходные данные:
#     - pytest assertions на восстановление исходных значений
# Внешние зависимости:
#   - pytest>=8.0, numpy>=1.24
# Использование:
#   ./.venv/bin/python -m pytest tests/test_inverse_piecewise.py -q
# Примечания:
#   - функции скопированы из normalize.py / signal_tracer.py для изоляции теста
#   - охватывает линейную зону, log-зону, beyond-cap, zero и реалистичные brk/cap из проекта
# =============================================================================

"""Тесты inverse_piecewise_linear_log: round-trip forward→inverse."""
import math
import numpy as np


def piecewise_linear_log_transform(x, lo, brk, cap,
                                   linear_max=0.85, tail_strength=9.0, eps=1e-12):
    """Копия из normalize.py для тестирования без импорта всего модуля."""
    x = np.asarray(x, dtype=np.float64)
    denom_lin = max(brk - lo, eps)
    y_lin = np.clip((x - lo) / denom_lin, 0.0, 1.0) * linear_max
    denom_tail = max(cap - brk, eps)
    excess = np.maximum(x - brk, 0.0)
    t = np.clip(excess / denom_tail, 0.0, 1.0)
    log_part = np.log1p(tail_strength * t) / np.log1p(tail_strength + eps)
    y_tail = linear_max + (1.0 - linear_max) * log_part
    out = np.where(x <= brk, y_lin, y_tail)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def inverse_piecewise_linear_log(y, brk, cap,
                                  linear_max=0.85, tail_strength=9.0):
    """Копия из signal_tracer.py."""
    if y <= 0:
        return 0.0
    if y <= linear_max:
        return y / linear_max * brk
    log_denom = math.log1p(tail_strength)
    t_log = (y - linear_max) / (1.0 - linear_max)
    t = (math.expm1(t_log * log_denom)) / tail_strength
    t = max(0.0, min(1.0, t))
    return brk + t * (cap - brk)


def test_round_trip_linear_zone():
    """Значения в линейной зоне [0, brk] должны восстанавливаться точно."""
    brk, cap = 20.0, 70.0
    originals = [0.0, 1.0, 5.0, 10.0, 15.0, 19.9]
    for x in originals:
        y = float(piecewise_linear_log_transform(np.array([x]), 0, brk, cap)[0])
        x_back = inverse_piecewise_linear_log(y, brk, cap)
        assert abs(x_back - x) < 0.01, f"x={x}, y={y}, x_back={x_back}"


def test_round_trip_log_zone():
    """Значения в логарифмической зоне (brk, cap] должны восстанавливаться."""
    brk, cap = 20.0, 70.0
    originals = [25.0, 35.0, 50.0, 65.0, 70.0]
    for x in originals:
        y = float(piecewise_linear_log_transform(np.array([x]), 0, brk, cap)[0])
        x_back = inverse_piecewise_linear_log(y, brk, cap)
        assert abs(x_back - x) < 0.1, f"x={x}, y={y}, x_back={x_back}"


def test_round_trip_beyond_cap():
    """Значения > cap клиппируются к 1.0, inverse даёт cap."""
    brk, cap = 20.0, 70.0
    y = float(piecewise_linear_log_transform(np.array([100.0]), 0, brk, cap)[0])
    assert y == 1.0
    x_back = inverse_piecewise_linear_log(y, brk, cap)
    assert abs(x_back - cap) < 0.01


def test_zero_stays_zero():
    """Нулевое значение остается нулем."""
    brk, cap = 20.0, 70.0
    y = float(piecewise_linear_log_transform(np.array([0.0]), 0, brk, cap)[0])
    assert y == 0.0
    x_back = inverse_piecewise_linear_log(y, brk, cap)
    assert x_back == 0.0


def test_round_trip_realistic_updn():
    """Round-trip с реалистичными brk/cap из статистики проекта."""
    # Из DATA/Nero_normalization_stats.csv (глобальные, но порядок величин верный)
    cases = [
        (19.2, 71.9, [0.0, 1.5, 4.3, 13.2, 19.2, 35.0, 71.9]),  # up_12
        (18.1, 73.8, [0.0, 2.8, 11.8, 18.1, 50.0, 73.8]),        # dn_12
    ]
    for brk, cap, values in cases:
        for x in values:
            y = float(piecewise_linear_log_transform(np.array([x]), 0, brk, cap)[0])
            x_back = inverse_piecewise_linear_log(y, brk, cap)
            assert abs(x_back - min(x, cap)) < 0.15, \
                f"brk={brk}, cap={cap}, x={x}, y={y}, x_back={x_back}"


def test_normalize_rowwise_returns_updn_params():
    """normalize_rowwise должен возвращать (df, updn_params) при return_updn_params=True."""
    import pandas as pd

    # Создаём строку с одним фракталом, у которого up_12=10.0
    fractal_str = "1700000000:1000.0:1:5.0:3.0:0:0:0:1.0:1:0.5:10.0:8.0:15.0:12.0:20.0:16.0:2.5"
    # Остальные 99 фракталов — с нулевыми updn
    empty_frac = "1699999000:999.0:1:2.0:1.0:0:0:0:0.5:0:0.3:0.0:0.0:0.0:0.0:0.0:0.0:2.0"

    cols = {'time': ['2025.01.01 00:00'], 'signal': [0], 'predict': [0.0], 'ATR': [2.5],
            'up_12': [10.0], 'dn_12': [8.0], 'up_24': [15.0], 'dn_24': [12.0],
            'up_48': [20.0], 'dn_48': [16.0]}
    for i in range(100):
        cols[f'fractal{i}'] = [fractal_str if i == 0 else empty_frac]

    df = pd.DataFrame(cols)

    from processing.normalize import normalize_rowwise
    result = normalize_rowwise(df, return_updn_params=True)

    assert isinstance(result, tuple) and len(result) == 2
    df_out, updn_params = result
    assert updn_params.shape == (1, 5, 2)  # 5 пар × (brk, cap)
    brk, cap = updn_params[0, 2]  # up_12/dn_12 = пара 2
    assert cap >= brk, f"cap должен быть >= brk, got cap={cap}, brk={brk}"


def test_normalize_rowwise_can_exclude_predict_from_front_back_pool():
    """Live-safe режим не должен давать predict менять front/back."""
    import pandas as pd

    def fractal(front, back):
        return (
            "1700000000:1000.0:1:"
            f"{front}:{back}:0:0:0:1.0:1:0.5:"
            "10.0:8.0:15.0:12.0:20.0:16.0:0.0:0.0:0.0:0.0:2.5"
        )

    base = {
        'time': ['2025.01.01 00:00'],
        'signal': [0],
        'ATR': [2.5],
        'fractal0': [fractal(10.0, 20.0)],
        'fractal1': [fractal(20.0, 30.0)],
        'fractal2': [fractal(30.0, 40.0)],
    }

    from processing.normalize import normalize_rowwise, parse_fractal

    low_predict = normalize_rowwise(
        pd.DataFrame({**base, 'predict': [0.0]}),
        include_predict_in_front_back_pool=False,
        verbose=False,
    )
    high_predict = normalize_rowwise(
        pd.DataFrame({**base, 'predict': [10_000.0]}),
        include_predict_in_front_back_pool=False,
        verbose=False,
    )

    for column in ('fractal0', 'fractal1', 'fractal2'):
        low = parse_fractal(low_predict.loc[0, column])
        high = parse_fractal(high_predict.loc[0, column])
        assert low is not None
        assert high is not None
        assert low[3] == high[3]
        assert low[4] == high[4]
