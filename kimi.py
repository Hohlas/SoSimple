import pandas as pd

def label_signals(input_path: str, output_path: str) -> None:
    """
    Читает Nero.csv, находит все фракталы с strong==1 во всех столбцах fractal*,
    собирает их time в множество StrongLevels, затем для каждой строки проверяет
    первый фрактал (fractal0) и, если его time в StrongLevels, записывает в
    столбец signal значение direction этого фрактала. Результат сохраняет в output_path.
    """
    # 1. загрузка
    df = pd.read_csv(input_path, sep=';')

    # аккуратно убираем возможные пробелы в названиях колонок
    df.columns = [c.strip() for c in df.columns]

    # найдём все колонки с фракталами
    fractal_cols = [c for c in df.columns if c.startswith('fractal')]

    # 2. первый проход: собираем StrongLevels по всем фракталам
    strong_levels = set()

    for col in fractal_cols:
        # строка вида "time:price:direction:front:back:strong:break:reverse:power:count:impulse"
        # берём только не-пустые значения
        series = df[col].astype(str)

        # парсим в 11 полей
        parts = series.str.split(':', expand=True)

        # защитимся от некорректных строк
        if parts.shape[1] < 6:
            continue

        # time — поле 0, strong — поле 5
        time_series = parts[0]
        strong_series = parts[5]

        # фильтруем только strong == 1
        mask_strong = strong_series.astype(float) == 1.0

        strong_times = time_series[mask_strong].dropna()

        for t in strong_times:
            # t должно быть целым числом секунд (может прийти как строка float-подобная)
            try:
                strong_levels.add(int(float(t)))
            except ValueError:
                continue

    # 3. второй проход: построчно, смотрим fractal0 и проставляем signal
    if 'fractal0' not in df.columns:
        raise ValueError("В файле нет столбца 'fractal0'")

    f0 = df['fractal0'].astype(str)
    parts0 = f0.str.split(':', expand=True)

    if parts0.shape[1] < 3:
        raise ValueError("Столбец 'fractal0' имеет некорректный формат")

    time0 = parts0[0]         # time
    direction0 = parts0[2]    # direction

    new_signal = []

    for idx in range(len(df)):
        t_str = time0.iloc[idx]
        d_str = direction0.iloc[idx]

        try:
            t_val = int(float(t_str))
        except ValueError:
            t_val = None

        if t_val is not None and t_val in strong_levels:
            # используем направление сделки как сигнал: 1 (sell) или -1 (buy)
            try:
                sig = int(float(d_str))
            except ValueError:
                sig = 0
        else:
            # оставляем существующее значение (обычно 0)
            sig = df.at[idx, 'signal']

        new_signal.append(sig)

    df['signal'] = new_signal

    # 4. сохранение результата
    df.to_csv(output_path, sep=';', index=False)
