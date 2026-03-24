import argparse
import sys
import os

def trace_signal(target_time, nero_path, signals_path):
    print(f"=== ДОСЬЕ СИГНАЛА: {target_time} ===")
    
    # 1. Загрузка ml_signals.csv
    signal_data = None
    if os.path.exists(signals_path):
        print(f"\n[1] Поиск интерпретации ML в {signals_path}...")
        try:
            with open(signals_path, 'r', encoding='utf-8') as f:
                headers = f.readline().strip().split(';')
                for line in f:
                    row = line.strip().split(';')
                    if row[0] == target_time:
                        signal_data = dict(zip(headers, row))
                        break
        except Exception as e:
            print(f"  Ошибка чтения {signals_path}: {e}")
            
    if signal_data:
        print("\n--- ML Оценка (То, что подумал Питон) ---")
        for k, v in signal_data.items():
            print(f"  {k:<10}: {v}")
        
        # Расчет теоретического R:R (из lib_ML_Signal.mqh)
        ML_MinRatio = 2.665
        ML_MaxRR = 4.0
        sig = 0
        rr_Multiplier = 1.0
        try:
            ratio_up = float(signal_data.get('ratio_up', 0))
            ratio_dn = float(signal_data.get('ratio_dn', 0))
            ratio = max(ratio_up, ratio_dn)
            rr_Multiplier = min(max(ratio / ML_MinRatio, 1.0), ML_MaxRR)
            sig = int(signal_data.get('signal', 0))
            direction = "BUY (1)" if sig == 1 else "SELL (-1)" if sig == -1 else "FLAT (0)"
            
            print(f"\n--- Ожидаемая математика MT4 (при ML_MinRatio={ML_MinRatio}) ---")
            print(f"  Направление : {direction}")
            print(f"  Множитель TP: {rr_Multiplier:.2f}x (SL * {rr_Multiplier:.2f})")
            print(f"  Асимметрия  : R:R = 1 : {rr_Multiplier:.2f}")
        except Exception as e:
            print(f"  Ошибка парсинга ожиданий MT4: {e}")
    else:
        print(f"\n[!] Сигнал для времени '{target_time}' не найден в {signals_path}. Проверьте точный формат.")

    # 2. Загрузка Nero.csv
    nero_data = None
    f0 = None
    if os.path.exists(nero_path):
        print(f"\n[2] Поиск сырого фрактала в {nero_path} (файл большой, может занять пару секунд)...")
        encodings = ['utf-16-le', 'utf-8']
        
        for enc in encodings:
            try:
                with open(nero_path, 'r', encoding=enc) as f:
                    for line in f:
                        if line.startswith(target_time):
                            nero_data = line.strip().split(';')
                            break
                if nero_data:
                    break
            except UnicodeError:
                continue
    
    if nero_data:
        print("\n--- Сырые данные фрактала (То, что увидел Питон в момент обучения) ---")
        print(f"  Строка Nero [Atr] (col 3): {nero_data[3] if len(nero_data) > 3 else 'N/A'}")
        
        if len(nero_data) > 4 and nero_data[4]:
            f0 = nero_data[4].split(':')
            if len(f0) >= 18:
                fields = ['T (Время фрактала)', 'P (Цена пика)', 'Dir (+1=High, -1=Low)', 'FrntVal', 'BackVal', 'Strong', 'Brk', 'Rev', 'PwrSum', 'Cnt', 'Imp (Импульс)', 'Up_12 (MFE за 12ч)', 'Dn_12 (MAE за 12ч)', 'Up_24', 'Dn_24', 'Up_48', 'Dn_48', 'Fractal_ATR (Локальный)']
                
                print("\n  [Структура Fractal 0]")
                for i in range(min(len(fields), len(f0))):
                    print(f"  {fields[i]:<25}: {f0[i]}")
                
                print("\n--- Ground Truth (Абсолютная траектория MFE/MAE после формирования) ---")
                
                try:
                    price = float(f0[1])
                    up_12 = float(f0[11])
                    dn_12 = float(f0[12])
                    atr = float(f0[17])
                    
                    # Дефолтный SL в MT4 = 1.6 * ATR
                    sl_dist = 1.6 * atr
                    tp_dist = sl_dist * rr_Multiplier
                        
                    print(f"  Входная цена (Price) : {price:.5f}")
                    print(f"  Уровень SL (1.6*ATR) : {sl_dist:.5f} пунктов от входа")
                    print(f"  Уровень TP           : {tp_dist:.5f} пунктов от входа")
                    print(f"  Реальный ход ВВЕРХ   : {up_12:.5f}")
                    print(f"  Реальный ход ВНИЗ    : {dn_12:.5f}")
                    
                    print("\n  [ДИАГНОЗ ПО ВЫЖИВАЕМОСТИ ТРАЕКТОРИИ ЗА 12 ЧАСОВ]:")
                    if sig == 1:
                        if dn_12 >= sl_dist:
                            print("  ⚠️ КРИТИЧЕСКИЙ РИСК (MFE/MAE Иллюзия): Ход цены вниз (Dn_12) превысил SL до конца H12.")
                            print("     Если это движение 'вниз' было ДО пика 'вверх', MT4 закрыл сделку по стопу до профита.")
                        if up_12 >= tp_dist:
                            print("  ✅ Цель (TP) была физически достигнута за эти 12 часов.")
                        elif up_12 < tp_dist:
                            print("  ⏳ Цель (TP) НЕ была достигнута. MT4 закрыл бы сделку по TimeOut или Trailing.")
                    elif sig == -1:
                        if up_12 >= sl_dist:
                            print("  ⚠️ КРИТИЧЕСКИЙ РИСК (MFE/MAE Иллюзия): Ход цены вверх (просадка для SELL) превысил SL до конца H12.")
                            print("     Если это движение 'вверх' было ДО провала 'вниз', MT4 закрыл сделку по стопу.")
                        if dn_12 >= tp_dist:
                            print("  ✅ Цель (TP) была физически достигнута за эти 12 часов.")
                        elif dn_12 < tp_dist:
                            print("  ⏳ Цель (TP) НЕ была достигнута. MT4 закрыл бы сделку по TimeOut или Trailing.")
                except Exception as e:
                    print(f"  Ошибка расчетов траектории: {e}")
        else:
            print("  [!] Фрактал 0 пуст или строка повреждена.")
    else:
        print(f"\n[!] Данные для времени '{target_time}' не найдены в Nero.csv.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Анализ конкретной сделки (Разбор полетов)")
    parser.add_argument("--time", required=True, help="Время фрактала в формате 'YYYY.MM.DD HH:MM'")
    parser.add_argument("--nero", default="../MT/MQL4/Files/Nero.csv", help="Путь к Nero.csv (относительно скрипта)")
    parser.add_argument("--signals", default="../MT/MQL4/Files/ml_signals.csv", help="Путь к ml_signals.csv (относительно скрипта)")
    
    args = parser.parse_args()
    trace_signal(args.time, args.nero, args.signals)
