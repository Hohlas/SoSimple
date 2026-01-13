#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование функции label_signals на примере файла Nero.csv
"""

from label_signals import label_signals

def main():
    # Пути к файлам
    input_file = r'c:\Users\hohla\Desktop\Nero.csv'
    output_file = r'c:\Users\hohla\Desktop\Nero_labeled.csv'
    
    print(f"Обработка файла: {input_file}")
    
    try:
        # Вызов функции
        result_df = label_signals(input_file, output_file)
        
        print(f"\nРезультаты обработки:")
        print(f"Всего строк: {len(result_df)}")
        print(f"Колонки: {list(result_df.columns)}")
        
        # Проверка сигналов
        signal_counts = result_df['signal'].value_counts()
        print(f"\nРаспределение сигналов:")
        print(signal_counts)
        
        # Показать первые несколько строк
        print(f"\nПервые 5 строк результата:")
        print(result_df.head())
        
    except Exception as e:
        print(f"Ошибка при обработке: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()