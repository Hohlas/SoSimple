from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pandas as pd
import csv
# %% считывание из файла csv в строковый формат с разделителями ':'
time 	 fractal1 	 fractal2 	 fractal3 	 fractal4 
25.09.2023 7:00	3:1924.2:1:1.6:1.5:0:0:0:29.0:7:360:2.0:1.6:2111	2:1922.6:-1:6.5:1.6:0:0:1:26.6:7:300:2.0:2.1:2222	7:1925.3:1:2.2:2.7:0:0:0:6.0:3:240:2.1:2.3:2333	9:1926.2:1:2.0:3.6:1:0:0:3.6:2:60:2.0:1.7:2444
25.09.2023 10:00	4:1924.2:1:1.6:1.5:0:3:0:29.0:7:360:2.0:1.6:3111	5:1922.6:-1:6.5:1.6:0:4:1:26.6:7:300:2.0:2.1:3222	6:1925.3:1:2.2:4.5:0:0:0:6.0:3:240:2.1:2.3:3333	9:1926.2:1:2.0:5.4:0:0:0:3.6:2:60:2.0:1.7:3444
25.09.2023 11:00	5:1924.2:1:1.6:1.5:0:4:0:29.0:7:360:2.0:1.6:4111	6:1922.6:-1:6.5:1.6:0:5:1:26.6:7:300:2.0:2.1:4222	7:1925.3:1:2.2:4.5:0:3:0:6.0:3:240:2.1:2.3:4333	10:1926.2:1:2.0:5.4:0:3:0:3.6:2:60:2.0:1.7:4444

def read_data(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)  # Пропускаем строку с заголовком
        data = []
        empty_cells = []  # Список для хранения информации о пустых ячейках
        for i, row in enumerate(reader, start=2):  # Начинаем с 2, так как пропустили строку с заголовком
            fractals = row[1:]
            # Проверяем каждую ячейку на пустоту
            for j, fractal in enumerate(fractals, start=1):  # Начинаем с 1, так как пропустили ячейку со временем
                if not fractal:
                    empty_cells.append((i, j))  # Добавляем информацию о пустой ячейке
            fractals = [fractal for fractal in fractals if fractal]
            sorted_fractals = sorted(fractals, key=lambda x: int(x.split(':')[0]) if x.split(':')[0] else 0)
            data.append([row[0]] + sorted_fractals)
        print("from ",filename,f" read {len(data)} lines.")  # Выводим сообщение внутри функции
        # Выводим информацию о пустых ячейках
        if empty_cells:
            print("Find empty cells in (row / column):")
            for cell in empty_cells:
                print(cell)
        else:
            print("OK: no empty cells in file ",filename)
    
# %% преобразование из текста с разделителямми ':' в списки 

    for i in range(len(data)):
        for j in range(1, len(data[i])): # пропускаем первый столбец со временем
            data[i][j] = np.array(data[i][j].split(':')).astype(float) # преобразование из текста в списки
    for row in data: # в каждой строке в данных вставляем после 'даты'
        row.insert(1, [0, 0]) # список predictor, содержащий статус текущего фрактала в будущем и значение следующего "первого уровня"
        row.insert(2, [0, 0]) # список restore, содержащий данные для восстановления нормализованной цены

    keys = ["date"] + ["predict"] + ["restore"] + ["fr" + str(i) for i in range(1, len(data[0]))]
    dic = [dict(zip(keys, sublist)) for sublist in data]
    

# %% проверка каждого фрактала "не станет ли он в будущем первым уровнем" и запись статуса в доп. столбец.    
    # time[0] predictor[0] restore[0] fractal[0][0] fractal[0][1] ... fractal[0][n]
    # time[1] predictor[1] restore[1] fractal[1][0] fractal[1][1] ... fractal[1][n]  
    # ...........................
    # time[m] predictor[m] restore[m] fractal[m][0] fractal[m][1] ... fractal[m][n]   
    first_levels_counter=np.zeros(len(data),dtype=int) # просто счетчик-индикатор количества первых уровней в данных
    for i in range(len(data)): # каждую строку
        for j in range(i + 1, len(data)): # сверяем со следующей и ниже
            for k in range(3, len(data[j])): # начиная со третьего индекса 'fractal0' [time predictor restore fractal0...]
                # поиск ближайшего первого уровня в будущем
                if data[j][k][5] > 0 and data[i][1][1] ==0: # в будущей истории найден первый уровень, и ни один уровень еще не сохранен
                    data[i][1][1] =  data[j][k][1] # сохраняем значение ближайшего в будущем первого уровня
                # проверка, будет ли текущий фрактал в будущем "первым уровнем"
                if data[i][2][13] == data[j][k][13] and data[j][k][5] > 0: # время терущего фрактала совпало со временем фрактала из будущего, и тот со статусом "первый"
                    data[i][1][0] = 1 # говорит о том, что в будущем этот фрактал будет "первым уровнем"
                    
                    first_levels_counter[i]=1 # счеткик количества найденных первых уровней
                    break
    print('find ',sum(first_levels_counter)," first levels")                 
    
# %% нормализация всех данных к диапазону 0..1
  
    for row in data:
        for index in [0, 1, 6, 7, 8, 9, 10, 11, 12]:  # индексы для нормализации
            values = [float(item[index]) for item in row[3:]]  # извлекаем значения для нормализации
            min_val, max_val = min(values), max(values) # минимальное и максимальное значения
            # выполняем нормализацию
            for item in row[3:]:
                item[index] = (float(item[index]) - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            if index == 1: # минимальное и максимальное значения для индекса 1 (цена)
                restore = [min_val, max_val - min_val]
        # Нормализация данных с индексами 3 и 4 вместе
        values_3 = [float(item[3]) for item in row[2:]]
        values_4 = [float(item[4]) for item in row[2:]]
        min_val = min(min(values_3), min(values_4))
        max_val = max(max(values_3), max(values_4))
        for item in row[2:]:
            item[3] = (float(item[3]) - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            item[4] = (float(item[4]) - min_val) / (max_val - min_val) if max_val > min_val else 0.5
        row.insert(1, restore) # Добавляем минимальное и максимальное значения в data после столбца с временем
    print('OK: data normalized')
    return data   
 
check = read_data('Nero_XAUUSD60.csv') # Nero_XAUUSD60.csv    Nero_5.csv
          
# %% save to csv
df = pd.DataFrame(check) # Создаем объект DataFrame из массива данных
df.to_csv('normalized.csv', index=False) # Сохраняем DataFrame в файл normalized.csv  

# %% нормализация