# =============================================================================
# Файл: label_signals.py
# Назначение: Маркировка торговых сигналов, predict, up/dn fixed-horizon
#              таргетов и entry_path_v1 labels
# Язык: Python 3.10+
# Автор: Antigravity
# Создан: Неизвестно
# Обновлён: 2026-04-08
#
# Зависимости:
#   Входные данные:
#     - CSV файлы с колонками фракталов (22 полей: T:P:Dir:Frnt:Back:Strong:Brk:Rev:Pwr:Cnt:Imp:Up12:Dn12:Up24:Dn24:Up48:Dn48:Up3:Dn3:Up6:Dn6:FractalAtr)
#   Выходные данные:
#     - pd.DataFrame с колонками 'signal', 'predict', 'up_3'..'dn_48',
#       'ret_*_dir_atr', 'fav_*_atr', 'adv_*_atr', 'path_6_class'
# Внешние зависимости:
#   - pandas>=2.0.0
#
# Использование:
#   from label_signals import label_all, label_updn, label_entry_path_targets
#   labeled_df = label_all('input.csv', 'output.csv', debug=True)
#   labeled_df = label_updn(labeled_df, debug=True)
#   labeled_df = label_entry_path_targets(labeled_df, 'DATA/XAUUSD_H1_OHLC.csv')
#
# Примечания:
#   - Обратная совместимость: parse_fractal() принимает строки с 7..22 полями
#   - label_updn(): forward-scan до вытеснения фрактала, берёт последние накопленные Up/Dn
# =============================================================================

"""
Модуль для анализа и маркировки исторических данных котировок.

Этот модуль предоставляет функции для обнаружения сильных уровней (strong levels)
на основе фракталов и разметки обучающей выборки для нейронных сетей.
Включает расчет целевой переменной 'predict', которая отражает потенциал
движения цены против пробитого фрактала.
"""

import numpy as np
import pandas as pd


def parse_fractal(fractal_str):
    """
    Парсит строку фрактала и возвращает словарь с параметрами.

    Формат строки:
    - legacy 18 полей:
      `fractal_time:price:direction:front:back:strong:break:reverse:power:count:impulse:up_12:dn_12:up_24:dn_24:up_48:dn_48:fractal_atr`
    - current 22 поля:
      `fractal_time:price:direction:front:back:strong:break:reverse:power:count:impulse:up_12:dn_12:up_24:dn_24:up_48:dn_48:up_3:dn_3:up_6:dn_6:fractal_atr`

    Индексы в строке:
        [0]  time (int): Время формирования
        [1]  price (float): Цена фрактала
        [2]  direction (int): Направление (1 - верх, -1 - низ)
        [3]  front (float): Расстояние до фронтального бара
        [4]  back (float): Расстояние до заднего бара
        [5]  strong (int): Флаг сильного фрактала (1 - да, 0 - нет)
        [6]  break (int): Флаг пробития (1 - да, 0 - нет)
        [7]  reverse (float): Значение разворота
        [8]  power (float): Сила импульса
        [9]  count (int): Счетчик подтверждений
        [10] impulse (float): Значение импульса
        [11] up_12 (float): max(High - P) за 12 баров H1
        [12] dn_12 (float): max(P - Low) за 12 баров H1
        [13] up_24 (float): max(High - P) за 24 бара H1
        [14] dn_24 (float): max(P - Low) за 24 бара H1
        [15] up_48 (float): max(High - P) за 48 баров H1
        [16] dn_48 (float): max(P - Low) за 48 баров H1
        [17] up_3 (float): max(High - P) за 3 бара H1
        [18] dn_3 (float): max(P - Low) за 3 бара H1
        [19] up_6 (float): max(High - P) за 6 баров H1
        [20] dn_6 (float): max(P - Low) за 6 баров H1
        [21] fractal_atr (float): Atr.Fast в момент формирования фрактала

    Args:
        fractal_str (str): Строка с данными фрактала из CSV.

    Returns:
        Optional[Dict[str, Any]]: Словарь с распарсенными данными или None,
            если строка пуста или некорректна.
    """
    if pd.isna(fractal_str) or fractal_str == '':
        return None
    
    parts = str(fractal_str).split(':')
    if len(parts) < 7:  # Минимум нужны индексы 0-6 для базовой логики
        return None
    
    try:
        return {
            'time': int(parts[0]),
            'price': float(parts[1]),
            'direction': int(parts[2]),
            'front': float(parts[3]),
            'back': float(parts[4]),
            'strong': int(parts[5]),
            'break': int(parts[6]),
            'reverse': float(parts[7]) if len(parts) > 7 else 0.0,
            'power': float(parts[8]) if len(parts) > 8 else 0.0,
            'count': int(parts[9]) if len(parts) > 9 else 0,
            'impulse':     float(parts[10]) if len(parts) > 10 else 0.0,
            'up_12':       float(parts[11]) if len(parts) > 11 else 0.0,
            'dn_12':       float(parts[12]) if len(parts) > 12 else 0.0,
            'up_24':       float(parts[13]) if len(parts) > 13 else 0.0,
            'dn_24':       float(parts[14]) if len(parts) > 14 else 0.0,
            'up_48':       float(parts[15]) if len(parts) > 15 else 0.0,
            'dn_48':       float(parts[16]) if len(parts) > 16 else 0.0,
            'up_3':        float(parts[17]) if len(parts) > 21 else 0.0,
            'dn_3':        float(parts[18]) if len(parts) > 21 else 0.0,
            'up_6':        float(parts[19]) if len(parts) > 21 else 0.0,
            'dn_6':        float(parts[20]) if len(parts) > 21 else 0.0,
            'fractal_atr': float(parts[21]) if len(parts) > 21 else (float(parts[17]) if len(parts) > 17 else 0.0),
        }
    except (ValueError, IndexError):
        return None


def find_fractal_by_time(row, fractal_columns, target_time):
    """
    Ищет фрактал с заданным временем в текущей строке данных.

    Просматривает все колонки, начинающиеся на 'fractal', чтобы найти
    совпадение по времени формирования (time_val).

    Args:
        row (Union[pd.Series, NamedTuple]): Строка DataFrame.
        fractal_columns (List[str]): Список имен колонок, содержащих фракталы.
        target_time (int): Искомый временной отпечаток фрактала.

    Returns:
        Optional[Dict[str, Any]]: Данные найденного фрактала или None.
    """
    for col_name in fractal_columns:
        # Поддержка как namedtuple (itertuples), так и Series (iloc)
        if hasattr(row, '_asdict'):
            val = getattr(row, col_name, None)
        else:
            val = row[col_name]
        parsed = parse_fractal(val)
        if parsed and parsed['time'] == target_time:
            return parsed
    return None


def label_all(input_path, output_path, debug=False, label_signal=True, label_predict=True):
    """
    Выполняет комплексную маркировку данных: сигналы (signal) и прогнозы (predict).

    Алгоритм:
    1. Находит все фракталы с пометкой 'strong' во всем файле.
    2. Для каждой строки:
       - Если fractal0 является 'strong', ставит метку в 'signal'.
       - Рассчитывает 'predict' как максимальный откат (back) цены до момента
         пробития (break) этого фрактала в будущем.

    Args:
        input_path (str): Путь к исходному CSV файлу (разделитель ';').
        output_path (str): Путь для сохранения результата.
        debug (bool): Флаг включения подробного вывода в консоль.
        label_signal (bool): Нужно ли маркировать колонку 'signal'.
        label_predict (bool): Нужно ли маркировать колонку 'predict'.

    Returns:
        pd.DataFrame: DataFrame с добавленными метками.

    Note:
        Процесс маркировки 'predict' является ресурсоемким (O(N^2) в худшем случае),
        так как требует просмотра будущих строк для каждого фрактала.
    """
    if debug:
        print("=" * 60)
        mode = []
        if label_signal:
            mode.append("SIGNAL")
        if label_predict:
            mode.append("PREDICT")
        print(f"МАРКИРОВКА: {' + '.join(mode)}")
        print("=" * 60)
    
    import bisect

    # Загрузка данных
    df = pd.read_csv(input_path, sep=';')
    df.columns = [c.strip() for c in df.columns]

    # Инициализация и приведение типов для целевых колонок
    if 'signal' not in df.columns:
        df['signal'] = 0

    if 'predict' not in df.columns:
        df['predict'] = 0.0
    else:
        df['predict'] = df['predict'].astype(float)

    # Получаем список колонок с фракталами динамически
    fractal_columns = sorted(
        [col for col in df.columns if col.startswith('fractal')],
        key=lambda x: int(x.replace('fractal', ''))
    )
    total_rows = len(df)

    if debug:
        print(f"\n[ЗАГРУЗКА] Строк: {total_rows}, колонок фракталов: {len(fractal_columns)}")

    # === ПРЕДВАРИТЕЛЬНЫЙ СКАН O(n*K) ===
    # Для каждого fractal_time строим:
    #   timeline_rows[T]  — отсортированный список строк, где T виден
    #   timeline_back[T]  — back-значение на каждой строке
    #   timeline_break[T] — break-статус на каждой строке
    # Заодно собираем strong_levels и fractal0_data[i].

    print(f"\n[СКАН] Предварительный проход по {total_rows} строкам...")

    all_col_values = {col: df[col].values for col in fractal_columns}
    fractal0_raw = df['fractal0'].values

    timeline_rows  = {}   # T -> [row_idx, ...]
    timeline_back  = {}   # T -> [back, ...]
    timeline_break = {}   # T -> [break_status, ...]
    strong_levels  = set()
    fractal0_data  = [None] * total_rows  # (time, direction, back) per row

    for j in range(total_rows):
        for col in fractal_columns:
            parsed = parse_fractal(all_col_values[col][j])
            if parsed is None:
                continue
            t = parsed['time']
            if t not in timeline_rows:
                timeline_rows[t]  = []
                timeline_back[t]  = []
                timeline_break[t] = []
            timeline_rows[t].append(j)
            timeline_back[t].append(parsed['back'])
            timeline_break[t].append(parsed['break'])
            if label_signal and parsed['strong'] == 1:
                strong_levels.add(t)

        f0 = parse_fractal(fractal0_raw[j])
        if f0 is not None:
            fractal0_data[j] = (f0['time'], f0['direction'], f0['back'])

    if label_signal:
        print(f"[SIGNAL] Найдено {len(strong_levels)} уникальных strong фракталов")

    # === МАРКИРОВКА ===
    signals_marked  = 0
    predict_marked  = 0
    empty_fractal0  = 0
    fractals_dropped = 0

    signal_arr  = df['signal'].values.copy()
    predict_arr = df['predict'].values.copy().astype(float)

    for i in range(total_rows):
        f0 = fractal0_data[i]
        if f0 is None:
            empty_fractal0 += 1
            continue

        target_time, target_direction, f0_back = f0

        # --- Маркировка signal ---
        if label_signal and target_time in strong_levels:
            signal_arr[i] = target_direction
            signals_marked += 1
            if debug:
                print(f"  [Строка {i}] ✓ signal={target_direction}")

        # --- Маркировка predict ---
        if label_predict and target_time in timeline_rows:
            rows_t  = timeline_rows[target_time]
            backs_t = timeline_back[target_time]
            brks_t  = timeline_break[target_time]

            # Первый индекс в timeline строго после i
            start = bisect.bisect_right(rows_t, i)

            max_back  = f0_back
            was_broken = False
            dropped    = False
            prev_row   = i

            for k in range(start, len(rows_t)):
                row_j = rows_t[k]
                # Фрактал должен присутствовать в каждой последующей строке
                if row_j != prev_row + 1:
                    dropped = True
                    break
                if backs_t[k] > max_back:
                    max_back = backs_t[k]
                if brks_t[k] > 0:
                    was_broken = True
                    break
                prev_row = row_j

            if dropped and not was_broken:
                fractals_dropped += 1

            predict_value = -max_back * target_direction
            predict_arr[i] = predict_value
            predict_marked += 1

            if debug and i < 5:
                print(f"  [Строка {i}] ✓ predict={predict_value:.4f}")

    df['signal']  = signal_arr
    df['predict'] = predict_arr

    # === Статистика ===
    print(f"\n[РЕЗУЛЬТАТ]")
    if label_signal:
        print(f"  Signal помечено: {signals_marked}")
    if label_predict:
        print(f"  Predict помечено: {predict_marked}")
        print(f"  Фракталов выпало до пробития: {fractals_dropped}")
    print(f"  Пустых fractal0: {empty_fractal0}")

    # Сохранение результата
    df.to_csv(output_path, sep=';', index=False)
    print(f"[СОХРАНЕНО] {output_path}")

    return df


def label_signals(input_path, output_path, debug=False):
    """
    Маркирует только столбец signal (для обратной совместимости).

    Args:
        input_path (str): Путь к входному CSV.
        output_path (str): Путь для сохранения.
        debug (bool): Режим отладки.

    Returns:
        pd.DataFrame: Обработанные данные.
    """
    return label_all(input_path, output_path, debug=debug, 
                     label_signal=True, label_predict=False)


def label_predict_only(input_path, output_path, debug=False):
    """
    Маркирует только столбец predict.

    Args:
        input_path (str): Путь к входному CSV.
        output_path (str): Путь для сохранения.
        debug (bool): Режим отладки.

    Returns:
        pd.DataFrame: Обработанные данные.
    """
    return label_all(input_path, output_path, debug=debug, 
                     label_signal=False, label_predict=True)


def label_updn(df, debug=False):
    """
    Извлекает up/dn таргеты для каждой строки из накопленных значений фрактала.

    Алгоритм: два прохода O(n*K) вместо O(n²).
    Проход 1 (снизу вверх): для каждой строки j парсим все K фракталов,
      обновляем словарь last_seen[fractal_time] = {up_3..dn_48}.
    Проход 2 (сверху вниз): для строки i берём fractal0.time,
      смотрим last_seen[time] — это и есть самые накопленные Up/Dn.

    Записывает в колонки up_3, dn_3, up_6, dn_6, up_12, dn_12, up_24, dn_24, up_48, dn_48.

    Args:
        df (pd.DataFrame): DataFrame с колонками fractalN.
        debug (bool): Флаг отладки.

    Returns:
        pd.DataFrame: DataFrame с добавленными колонками up/dn.
    """
    import numpy as np

    HORIZONS = [3, 6, 12, 24, 48]
    updn_keys = [f'up_{h}' for h in HORIZONS] + [f'dn_{h}' for h in HORIZONS]

    fractal_columns = sorted(
        [col for col in df.columns if col.startswith('fractal')],
        key=lambda x: int(x.replace('fractal', ''))
    )
    n_rows = len(df)

    # Проход 1: снизу вверх — для каждого fractal_time запоминаем последние (самые накопленные) Up/Dn.
    # "Последние" = из строки с наибольшим индексом, где фрактал ещё виден.
    # Идём снизу вверх: первое встреченное значение для каждого time — и есть самое накопленное.
    last_seen = {}  # {fractal_time: {up_3: float, ...}}
    fractal0_times = [None] * n_rows  # запоминаем time fractal0 каждой строки

    fractal0_col = df['fractal0'].values
    all_cols_values = {col: df[col].values for col in fractal_columns}

    for j in range(n_rows - 1, -1, -1):
        for col in fractal_columns:
            parsed = parse_fractal(all_cols_values[col][j])
            if parsed is None:
                continue
            t = parsed['time']
            if t not in last_seen:
                last_seen[t] = {k: parsed.get(k, 0.0) for k in updn_keys}

        f0 = parse_fractal(fractal0_col[j])
        if f0 is not None:
            fractal0_times[j] = f0['time']

    # Проход 2: сверху вниз — lookup O(1) по словарю
    result = {k: np.zeros(n_rows, dtype=np.float32) for k in updn_keys}
    found_count = 0

    for i in range(n_rows):
        t = fractal0_times[i]
        if t is None:
            continue
        best = last_seen.get(t)
        if best is None:
            continue
        for k in updn_keys:
            result[k][i] = best[k]
        found_count += 1

    for k in updn_keys:
        df[k] = result[k]

    if debug:
        print(f"[UPDN] Размечено строк: {found_count} / {n_rows}")

    return df


ARCHETYPE_MAX_ADVERSE_ATR = 1.0


def label_trade_targets(df: pd.DataFrame, ohlc_path=None) -> pd.DataFrame:
    """
    Строит outcome-aligned row-level таргеты из directional Up/Dn excursions.

    trade_outcome_h12:
        1, если directional PnL на 12H положительный, иначе 0.
    trade_pnl_h12_atr:
        (favorable - adverse) / ATR в направлении текущего signal.
    archetype_target:
        1 для "хорошего" path archetype: положительный directional PnL
        и неблагоприятный ход не глубже 1 ATR.
    """
    out = df.copy()

    signal = pd.to_numeric(out.get('signal', 0), errors='coerce').fillna(0).astype(np.int8).values
    atr = pd.to_numeric(out.get('ATR', 0.0), errors='coerce').fillna(0.0).astype(np.float32).values
    atr_safe = np.where(atr > 0, atr, 1.0).astype(np.float32)

    trade_fav_h12 = np.zeros(len(out), dtype=np.float32)
    trade_adv_h12 = np.zeros(len(out), dtype=np.float32)
    trade_pnl_h12_atr = np.zeros(len(out), dtype=np.float32)
    trade_fav_h12_atr = np.zeros(len(out), dtype=np.float32)
    trade_adv_h12_atr = np.zeros(len(out), dtype=np.float32)

    if ohlc_path is not None:
        ohlc = pd.read_csv(ohlc_path, sep=';', low_memory=False)
        ohlc['time'] = pd.to_datetime(ohlc['time'], format='%Y.%m.%d %H:%M', errors='coerce')
        ohlc = ohlc.dropna(subset=['time']).sort_values('time').reset_index(drop=True)

        time_to_idx = {t: i for i, t in enumerate(ohlc['time'])}
        highs = pd.to_numeric(ohlc['high'], errors='coerce').ffill().bfill().values
        lows = pd.to_numeric(ohlc['low'], errors='coerce').ffill().bfill().values
        closes = pd.to_numeric(ohlc['close'], errors='coerce').ffill().bfill().values
        ohlc_atr = pd.to_numeric(ohlc.get('atr14', 0.0), errors='coerce').fillna(0.0).values
        row_times = pd.to_datetime(out['time'], format='%Y.%m.%d %H:%M', errors='coerce')

        for i, (ts, sig) in enumerate(zip(row_times, signal)):
            if sig == 0 or pd.isna(ts):
                continue
            ohlc_idx = time_to_idx.get(ts)
            if ohlc_idx is None or ohlc_idx + 12 >= len(ohlc):
                continue

            entry_close = closes[ohlc_idx]
            exit_close = closes[ohlc_idx + 12]
            window_high = highs[ohlc_idx + 1: ohlc_idx + 13].max()
            window_low = lows[ohlc_idx + 1: ohlc_idx + 13].min()
            entry_atr = ohlc_atr[ohlc_idx] if np.isfinite(ohlc_atr[ohlc_idx]) and ohlc_atr[ohlc_idx] > 0 else atr_safe[i]
            entry_atr = float(entry_atr) if entry_atr > 0 else 1.0

            if sig == 1:
                fav = max(window_high - entry_close, 0.0)
                adv = max(entry_close - window_low, 0.0)
                net = exit_close - entry_close
            else:
                fav = max(entry_close - window_low, 0.0)
                adv = max(window_high - entry_close, 0.0)
                net = entry_close - exit_close

            trade_fav_h12[i] = fav
            trade_adv_h12[i] = adv
            trade_fav_h12_atr[i] = fav / entry_atr
            trade_adv_h12_atr[i] = adv / entry_atr
            trade_pnl_h12_atr[i] = net / entry_atr
    else:
        up_12 = pd.to_numeric(out.get('up_12', 0.0), errors='coerce').fillna(0.0).astype(np.float32).values
        dn_12 = pd.to_numeric(out.get('dn_12', 0.0), errors='coerce').fillna(0.0).astype(np.float32).values

        trade_fav_h12 = np.where(signal > 0, up_12, np.where(signal < 0, dn_12, 0.0)).astype(np.float32)
        trade_adv_h12 = np.where(signal > 0, dn_12, np.where(signal < 0, up_12, 0.0)).astype(np.float32)
        trade_fav_h12_atr = (trade_fav_h12 / atr_safe).astype(np.float32)
        trade_adv_h12_atr = (trade_adv_h12 / atr_safe).astype(np.float32)
        trade_pnl_h12_atr = ((trade_fav_h12 - trade_adv_h12) / atr_safe).astype(np.float32)

    trade_pnl_h12_atr = np.where(signal != 0, trade_pnl_h12_atr, 0.0).astype(np.float32)

    trade_outcome_h12 = ((signal != 0) & (trade_pnl_h12_atr > 0)).astype(np.int8)
    archetype_target = (
        (trade_outcome_h12 == 1) &
        (trade_adv_h12_atr <= ARCHETYPE_MAX_ADVERSE_ATR)
    ).astype(np.int8)

    out['trade_fav_h12'] = trade_fav_h12
    out['trade_adv_h12'] = trade_adv_h12
    out['trade_fav_h12_atr'] = trade_fav_h12_atr
    out['trade_adv_h12_atr'] = trade_adv_h12_atr
    out['trade_outcome_h12'] = trade_outcome_h12
    out['trade_pnl_h12_atr'] = trade_pnl_h12_atr
    out['archetype_target'] = archetype_target

    return out


# ─── Triple Barrier Labels ────────────────────────────────────────────────

# SL/TP grid (in ATR units)
TB_SL_LEVELS = [2, 3]
TB_TP_LEVELS = [3, 6, 9]

# Column names for 12 binary targets
TB_TARGET_NAMES = []
for sl in TB_SL_LEVELS:
    for tp in TB_TP_LEVELS:
        TB_TARGET_NAMES.append(f'buy_sl{sl}_tp{tp}')
for sl in TB_SL_LEVELS:
    for tp in TB_TP_LEVELS:
        TB_TARGET_NAMES.append(f'sell_sl{sl}_tp{tp}')


def label_triple_barrier(df, debug=False):
    """
    Compute 12 binary Triple Barrier labels from raw MFE values.

    Must be called AFTER label_updn() and BEFORE normalize_rowwise().
    Uses raw up_24/dn_24 (price units) and ATR to determine if
    TP barrier was hit before SL barrier within 24 bars.

    Ambiguous cases (both barriers reached) → label = 0 (conservative).

    Args:
        df: DataFrame with raw up_24, dn_24, ATR columns.
        debug: Print statistics.

    Returns:
        DataFrame with 12 added binary columns.
    """
    up_raw = pd.to_numeric(df['up_24'], errors='coerce').fillna(0.0)
    dn_raw = pd.to_numeric(df['dn_24'], errors='coerce').fillna(0.0)
    atr = pd.to_numeric(df['ATR'], errors='coerce').fillna(1.0)

    # Convert to ATR units
    up_atr = up_raw / atr.replace(0, 1.0)
    dn_atr = dn_raw / atr.replace(0, 1.0)

    for sl in TB_SL_LEVELS:
        for tp in TB_TP_LEVELS:
            # BUY: price up >= TP*ATR AND price down < SL*ATR
            df[f'buy_sl{sl}_tp{tp}'] = ((up_atr >= tp) & (dn_atr < sl)).astype(int)
            # SELL: mirror
            df[f'sell_sl{sl}_tp{tp}'] = ((dn_atr >= tp) & (up_atr < sl)).astype(int)

    if debug:
        total = len(df)
        print(f"\n[TRIPLE BARRIER] Labels computed for {total} rows:")
        for name in TB_TARGET_NAMES:
            ones = df[name].sum()
            print(f"  {name}: {ones} ({ones/total*100:.1f}%)")

    return df


def load_ohlc_index(ohlc_path):
    """
    Загружает H1 OHLC в dict {datetime: (open, high, low, close)} и sorted list.
    Формат файла: time;open;high;low;close;volume  (DATA/XAUUSD_H1_OHLC.csv)
    """
    import csv
    from datetime import datetime, timezone

    ohlc = {}
    with open(ohlc_path, newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            t = datetime.strptime(row['time'], "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
            ohlc[t] = (
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
            )
    times = sorted(ohlc.keys())
    time_idx = {t: i for i, t in enumerate(times)}
    return ohlc, times, time_idx


def compute_entry_path_slice(bars, direction, entry_price, atr, horizon):
    window = bars.iloc[:horizon]
    if direction not in (-1, 1) or horizon <= 0 or len(window) < horizon or atr <= 0:
        return {'ret_dir_atr': 0.0, 'fav_atr': 0.0, 'adv_atr': 0.0}

    close_h = float(window.iloc[-1]['close'])
    high_h = float(window['high'].max())
    low_h = float(window['low'].min())

    if direction == 1:
        ret_dir_atr = (close_h - entry_price) / atr
        fav_atr = (high_h - entry_price) / atr
        adv_atr = (entry_price - low_h) / atr
    else:
        ret_dir_atr = (entry_price - close_h) / atr
        fav_atr = (entry_price - low_h) / atr
        adv_atr = (high_h - entry_price) / atr

    return {
        'ret_dir_atr': float(ret_dir_atr),
        'fav_atr': float(fav_atr),
        'adv_atr': float(adv_atr),
    }


def first_touch_barrier_outcome(bars, direction, entry_price, sl_price, tp_price):
    """
    Return first-touch outcome for a path of OHLC bars.

    Returns:
        1  -> TP hit first
        0  -> SL hit first
        -1 -> timeout (neither barrier touched)
    """
    del entry_price  # kept for API clarity with labeling call sites

    for _, row in bars.iterrows():
        row_open = float(row['open'])
        row_high = float(row['high'])
        row_low = float(row['low'])

        if direction == 1:
            hit_sl = row_low <= sl_price
            hit_tp = row_high >= tp_price
            if hit_sl and hit_tp:
                return 0 if abs(row_open - sl_price) <= abs(tp_price - row_open) else 1
        else:
            hit_sl = row_high >= sl_price
            hit_tp = row_low <= tp_price
            if hit_sl and hit_tp:
                return 0 if abs(row_open - sl_price) <= abs(row_open - tp_price) else 1

        if hit_tp:
            return 1
        if hit_sl:
            return 0

    return -1


def first_touch_path_class(bars, direction, entry_price, atr, threshold_atr=1.0):
    if direction not in (-1, 1) or atr <= 0 or len(bars) == 0:
        return 0

    if direction == 1:
        sl_price = entry_price - threshold_atr * atr
        tp_price = entry_price + threshold_atr * atr
    else:
        sl_price = entry_price + threshold_atr * atr
        tp_price = entry_price - threshold_atr * atr

    outcome = first_touch_barrier_outcome(
        bars=bars,
        direction=direction,
        entry_price=entry_price,
        sl_price=sl_price,
        tp_price=tp_price,
    )
    if outcome == 1:
        return 1
    if outcome == 0:
        return -1
    return 0


TRAILING_STOP_HORIZONS = (12, 24, 48)
TRAILING_STOP_X_VALUES = (2, 4, 8, 10, 12)
TRAILING_STOP_HOLD_BARS = 48


def _safe_numeric_scalar(value, default=0.0):
    numeric = pd.to_numeric(value, errors='coerce')
    if pd.isna(numeric):
        return default
    return float(numeric)


def _safe_signal_scalar(value):
    numeric = pd.to_numeric(value, errors='coerce')
    if pd.isna(numeric):
        return 0
    return int(numeric)


def simulate_trailing_stop_exit(bars, direction, entry_price, atr, trail_atr):
    if atr <= 0:
        return 0.0

    trail_distance = float(trail_atr) * float(atr)
    entry_price = float(entry_price)
    exit_price = entry_price
    best_high = entry_price
    best_low = entry_price

    for bar in bars:
        high = float(bar['high'])
        low = float(bar['low'])
        close = float(bar['close'])

        if direction == 1:
            # Canonical convention: same-bar favorable extreme is observed first,
            # then the trailing stop is evaluated against best_high - X * ATR.
            best_high = max(best_high, high)
            stop_price = best_high - trail_distance
            if low <= stop_price:
                exit_price = stop_price
                break
            exit_price = close
        else:
            # Mirror rule for shorts: same-bar favorable extreme is the low,
            # then the stop is evaluated against best_low + X * ATR.
            best_low = min(best_low, low)
            stop_price = best_low + trail_distance
            if high >= stop_price:
                exit_price = stop_price
                break
            exit_price = close

    if direction == 1:
        return float((exit_price - entry_price) / float(atr))
    return float((entry_price - exit_price) / float(atr))


def label_trailing_stop_targets(
    df: pd.DataFrame,
    ohlc_path: str | None = None,
    hold_bars: int = TRAILING_STOP_HOLD_BARS,
    atr_col: str = 'ATR',
    x_values: tuple[int, ...] = TRAILING_STOP_X_VALUES,
) -> pd.DataFrame:
    from datetime import datetime, timezone

    out = df.copy()
    for horizon in TRAILING_STOP_HORIZONS:
        for x_value in x_values:
            out[f'trail_{horizon}_pnl_atr_x{x_value}'] = 0.0

    ohlc = times = time_idx = None
    if ohlc_path is not None:
        ohlc, times, time_idx = load_ohlc_index(ohlc_path)

    for row_label in out.index:
        signal = _safe_signal_scalar(out.at[row_label, 'signal'])
        if signal == 0:
            continue
        atr = _safe_numeric_scalar(out.at[row_label, atr_col], default=0.0)
        bars = []
        if ohlc is not None and times is not None and time_idx is not None:
            row_time = out.at[row_label, 'time']
            if pd.isna(row_time) or row_time == '':
                continue
            if hasattr(row_time, 'to_pydatetime'):
                row_time = row_time.to_pydatetime()
            if isinstance(row_time, datetime):
                row_dt = row_time.astimezone(timezone.utc) if row_time.tzinfo else row_time.replace(tzinfo=timezone.utc)
            else:
                try:
                    row_dt = datetime.strptime(str(row_time), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue

            base_idx = time_idx.get(row_dt)
            if base_idx is None or base_idx + 1 >= len(times):
                continue

            entry_dt = times[base_idx + 1]
            entry_bar = ohlc.get(entry_dt)
            if entry_bar is None:
                continue
            entry_price = float(entry_bar[3])

            future_times = times[base_idx + 1:base_idx + 1 + hold_bars]
            for future_dt in future_times:
                bar = ohlc.get(future_dt)
                if bar is None:
                    break
                bars.append(
                    {
                        'open': float(bar[0]),
                        'high': float(bar[1]),
                        'low': float(bar[2]),
                        'close': float(bar[3]),
                    }
                )
        else:
            entry_price = _safe_numeric_scalar(out.at[row_label, 'Close'], default=0.0)
            for step in range(1, hold_bars + 1):
                suffix = f'_{step}'
                high_col = f'High{suffix}'
                low_col = f'Low{suffix}'
                close_col = f'Close{suffix}'
                if high_col not in out.columns or low_col not in out.columns or close_col not in out.columns:
                    break
                bars.append(
                    {
                        'high': _safe_numeric_scalar(out.at[row_label, high_col], default=entry_price),
                        'low': _safe_numeric_scalar(out.at[row_label, low_col], default=entry_price),
                        'close': _safe_numeric_scalar(out.at[row_label, close_col], default=entry_price),
                    }
                )
        for horizon in TRAILING_STOP_HORIZONS:
            horizon_bars = bars[:horizon]
            for x_value in x_values:
                out.at[row_label, f'trail_{horizon}_pnl_atr_x{x_value}'] = simulate_trailing_stop_exit(
                    bars=horizon_bars,
                    direction=signal,
                    entry_price=entry_price,
                    atr=atr,
                    trail_atr=float(x_value),
                )

    return out


def add_entry_path_frequency_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    def numeric_series(column: str) -> pd.Series:
        if column in out.columns:
            return pd.to_numeric(out[column], errors='coerce')
        return pd.Series(0.0, index=out.index, dtype=float)

    parsed_time = pd.to_datetime(out.get('time'), format='%Y.%m.%d %H:%M', errors='coerce')
    atr = numeric_series('ATR').replace(0.0, np.nan)

    high_rolling_6 = numeric_series('high_rolling_6')
    low_rolling_6 = numeric_series('low_rolling_6')
    close_lag_3 = numeric_series('close_lag_3')
    open_lag_3 = numeric_series('open_lag_3')
    ret_6_dir_atr = numeric_series('ret_6_dir_atr')

    out['session_hour'] = parsed_time.dt.hour.fillna(0).astype(int)
    out['weekday'] = parsed_time.dt.weekday.fillna(0).astype(int)
    out['range_atr_6'] = ((high_rolling_6 - low_rolling_6) / atr).fillna(0.0)
    out['body_atr_3'] = ((close_lag_3 - open_lag_3).abs() / atr).fillna(0.0)
    out['ret_dir_atr_lag1'] = ret_6_dir_atr.shift(1).fillna(0.0)
    out['vol_regime_24'] = numeric_series('ATR').rolling(24, min_periods=1).mean().fillna(0.0)
    return out


def label_entry_path_targets(
    df: pd.DataFrame,
    ohlc_path: str,
    ret_horizons=(6, 12, 24),
    path_horizons=(3, 6, 12, 24),
    debug=False,
):
    from datetime import datetime, timezone

    ohlc, times, time_idx = load_ohlc_index(ohlc_path)

    out = df.copy()
    for h in ret_horizons:
        out[f'ret_{h}_dir_atr'] = 0.0
    for h in path_horizons:
        out[f'fav_{h}_atr'] = 0.0
        out[f'adv_{h}_atr'] = 0.0
    out['path_6_class'] = 0

    found = skipped = 0
    for row_idx, row in out.iterrows():
        signal_raw = row.get('signal', 0)
        signal = 0 if pd.isna(signal_raw) else int(signal_raw)
        if signal not in (-1, 1):
            continue

        row_time = row.get('time')
        if pd.isna(row_time) or row_time == '':
            skipped += 1
            continue

        if hasattr(row_time, 'to_pydatetime'):
            row_time = row_time.to_pydatetime()

        if isinstance(row_time, datetime):
            row_dt = row_time.astimezone(timezone.utc) if row_time.tzinfo else row_time.replace(tzinfo=timezone.utc)
        else:
            try:
                row_dt = datetime.strptime(str(row_time), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
            except ValueError:
                skipped += 1
                continue

        base_idx = time_idx.get(row_dt)
        if base_idx is None or base_idx + 1 >= len(times):
            skipped += 1
            continue

        try:
            atr = float(row['ATR'])
        except (ValueError, KeyError, TypeError):
            skipped += 1
            continue
        if atr <= 0:
            skipped += 1
            continue

        entry_bar = ohlc[times[base_idx + 1]]
        entry_price = float(entry_bar[0])

        for h in sorted(set(ret_horizons) | set(path_horizons)):
            end_idx = base_idx + 1 + h
            if end_idx > len(times):
                continue
            bars = pd.DataFrame(
                [
                    {
                        'open': ohlc[times[k]][0],
                        'high': ohlc[times[k]][1],
                        'low': ohlc[times[k]][2],
                        'close': ohlc[times[k]][3],
                    }
                    for k in range(base_idx + 1, end_idx)
                ],
                columns=['open', 'high', 'low', 'close'],
            )
            stats = compute_entry_path_slice(bars, signal, entry_price, atr, h)
            if h in ret_horizons:
                out.at[row_idx, f'ret_{h}_dir_atr'] = stats['ret_dir_atr']
            if h in path_horizons:
                out.at[row_idx, f'fav_{h}_atr'] = stats['fav_atr']
                out.at[row_idx, f'adv_{h}_atr'] = stats['adv_atr']

        bars6_end = base_idx + 7
        if bars6_end <= len(times):
            bars6 = pd.DataFrame(
                [
                    {
                        'open': ohlc[times[k]][0],
                        'high': ohlc[times[k]][1],
                        'low': ohlc[times[k]][2],
                        'close': ohlc[times[k]][3],
                    }
                    for k in range(base_idx + 1, bars6_end)
                ],
                columns=['open', 'high', 'low', 'close'],
            )
            out.at[row_idx, 'path_6_class'] = first_touch_path_class(
                bars=bars6,
                direction=signal,
                entry_price=entry_price,
                atr=atr,
                threshold_atr=1.0,
            )

        found += 1

    if debug:
        print(f"\n[ENTRY_PATH_V1] Обработано: {found}, пропущено: {skipped}")

    return out


def label_first_barrier_hit(df, ohlc_path, scan_bars=24, debug=False):
    """
    Path-ordered Triple Barrier labels: bar-by-bar scan по H1 OHLC.

    Заменяет label_triple_barrier() для корректного определения порядка ударов.
    Должна вызываться ПОСЛЕ label_updn() и ДО normalize_rowwise().

    Алгоритм для каждой строки:
      - entry_price = Close[row_time] из H1 OHLC
      - ATR = raw ATR из строки DataFrame
      - Для BUY: SL = entry - sl_atr*ATR, TP = entry + tp_atr*ATR
      - Для SELL: SL = entry + sl_atr*ATR, TP = entry - tp_atr*ATR
      - Скан баров [row_time+1 .. row_time+scan_bars]:
          High >= TP → TP_FIRST → label = 1
          Low  <= SL → SL_FIRST → label = 0
          Оба в одном баре → порядок по Open (ближе к SL → SL_FIRST)
          Ни одного за scan_bars → TIMEOUT → label = 0.5

    Args:
        df:        DataFrame с колонками fractal0, ATR (до нормализации).
        ohlc_path: Путь к DATA/XAUUSD_H1_OHLC.csv.
        scan_bars: Окно поиска в барах (рекомендуется 24).
        debug:     Печатать статистику.

    Returns:
        DataFrame с теми же колонками TB_TARGET_NAMES (перезаписывает path-independent).
    """
    from datetime import datetime, timezone

    ohlc, times, time_idx = load_ohlc_index(ohlc_path)

    # Инициализация колонок
    for name in TB_TARGET_NAMES:
        df[name] = 0.5  # default: TIMEOUT

    fractal_columns = [col for col in df.columns if col.startswith('fractal')]
    found = skipped = 0

    for i, row in df.iterrows():
        fractal0 = parse_fractal(row.get('fractal0'))
        if fractal0 is None:
            skipped += 1
            continue

        row_time = row.get('time')
        if pd.isna(row_time) or row_time == '':
            skipped += 1
            continue

        # Якорь для TB label = время строки, потому что именно по нему потом
        # строятся CSV-сигналы и на следующем баре открывается сделка в MT4.
        try:
            row_dt = datetime.strptime(str(row_time), "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            skipped += 1
            continue

        idx0 = time_idx.get(row_dt)
        if idx0 is None:
            skipped += 1
            continue

        # Цена входа = Close сигнального бара (row_time), а не fractal0.time.
        entry_price = ohlc[row_dt][3]  # close

        try:
            atr = float(row['ATR'])
        except (ValueError, KeyError):
            skipped += 1
            continue
        if atr <= 0:
            skipped += 1
            continue

        scan_rows = []
        for k in range(idx0 + 1, min(idx0 + 1 + scan_bars, len(times))):
            o, h, l, c = ohlc[times[k]]
            scan_rows.append({
                'open': o,
                'high': h,
                'low': l,
                'close': c,
            })
        bars = pd.DataFrame(scan_rows, columns=['open', 'high', 'low', 'close'])

        # Скан для каждой пары (SL_ATR, TP_ATR)
        for sl in TB_SL_LEVELS:
            for tp in TB_TP_LEVELS:
                buy_sl = entry_price - sl * atr
                buy_tp = entry_price + tp * atr
                sell_sl = entry_price + sl * atr
                sell_tp = entry_price - tp * atr

                buy_result = first_touch_barrier_outcome(
                    bars=bars,
                    direction=1,
                    entry_price=entry_price,
                    sl_price=buy_sl,
                    tp_price=buy_tp,
                )
                sell_result = first_touch_barrier_outcome(
                    bars=bars,
                    direction=-1,
                    entry_price=entry_price,
                    sl_price=sell_sl,
                    tp_price=sell_tp,
                )

                df.at[i, f'buy_sl{sl}_tp{tp}'] = 0.5 if buy_result == -1 else float(buy_result)
                df.at[i, f'sell_sl{sl}_tp{tp}'] = 0.5 if sell_result == -1 else float(sell_result)

        found += 1

    if debug:
        total = len(df)
        print(f"\n[FIRST_BARRIER_HIT] Обработано: {found}, пропущено: {skipped}")
        for name in TB_TARGET_NAMES:
            vals = df[name]
            win  = (vals == 1).sum()
            loss = (vals == 0).sum()
            tout = (vals == 0.5).sum()
            print(f"  {name:20s}: WIN={win:5d} ({win/total*100:.1f}%)  "
                  f"LOSS={loss:5d} ({loss/total*100:.1f}%)  "
                  f"TIMEOUT={tout:5d} ({tout/total*100:.1f}%)")

    return df


if __name__ == "__main__":
    # Пример использования модуля при прямом запуске
    # label_all('Nero.csv', 'Nero_full.csv', debug=True)
    pass
