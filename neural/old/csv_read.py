from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pandas as pd
import csv
# %% считывание из файла csv в строковый формат с разделителями ':'
""" данные в файле csv имеют следующий вид (разделитель внутри ячеек ':')
25.09.2023 7:00     3:1924.2:1:1.6:1.5:0:0:0:29.0:7:360:2.0:1.6:2111	2:1922.6:-1:6.5:1.6:0:0:1:26.6:7:300:2.0:2.1:2222	...
25.09.2023 10:00	4:1924.2:1:1.6:1.5:0:3:0:29.0:7:360:2.0:1.6:3111	5:1922.6:-1:6.5:1.6:0:4:1:26.6:7:300:2.0:2.1:3222	...
25.09.2023 11:00	5:1924.2:1:1.6:1.5:0:4:0:29.0:7:360:2.0:1.6:4111	6:1922.6:-1:6.5:1.6:0:5:1:26.6:7:300:2.0:2.1:4222	...
"""
def read_data(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f, delimiter=';')# Создаем объект reader для чтения CSV-файла
        next(reader)  # Пропускаем строку с заголовком
        data = []
        empty_cells = []  # Список для хранения пустых ячеех
        for i, row in enumerate(reader, start=2):  # Читаем каждую строку CSV-файла, начиная со второй
            fractals = row[1:] # Получаем из строки данные о фракталах пропуская 'time' с индексом [0]
            # Проверяем каждую ячейку на пустоту
            for j, fractal in enumerate(fractals, start=1):  # Перебираем все фракталы в строке
                if not fractal: # Если фрактал пустой
                    empty_cells.append((i, j))  # Добавляем информацию о пустой ячейке
            fractals = [fractal for fractal in fractals if fractal] # Удаляем пустые фракталы из списка
            fractals = [list(map(float, fractal.split(':'))) for fractal in fractals] # Преобразуем текст с разделителями ':' в числа
            sorted_fractals = sorted(fractals, key=lambda x: x[0] if x else 0) # Сортируем фракталы по первому значению в строке
            data.append([row[0]] + sorted_fractals) # Добавляем отсортированные фракталы в список данных
        print("from ",filename,f" read {len(data)} lines.")  # Выводим сообщение внутри функции
        # Выводим информацию о пустых ячейках
        if empty_cells: # Если попались пустые ячейки
            print("Find empty cells in (row / column):")
            for cell in empty_cells:
                print(cell)
        else:
            print("OK: no empty cells in file ",filename)
    
    for row in data: # в каждой строке в данных после 'даты' 
        row.insert(1, [0, 0, 0]) # вставляем новый столбец predictor[0,0,0] чтобы записывать туда статус "ключевого" уровня
        row.insert(1, [0, 0])  # Добавляем новый столбец restore[0,0] для min_max_values
# после преобразований получили список списков 'data'
# ================================================================================= 
# data = [data[0], data[1], ... , data[m]]                                                          (m - кол-во фракталов в истории)            
#            0        1          2          3           4
# data[i]=[[time] [restore] [predictor] [fractal_0] [fractal_1] ... 99:[fractal_n]]    (n - кол-во фракталов в строке)
# =================================================================================

# [restore]=[min , max-min] - данные для восстановления цены после нормализации
# [predictor]=['статус фрактала в будущем' , 'ближайший в будущем ключевой уровень']
#              0     1    2    3    4     5      6    7   8   9     10       11     12    13
# [fractal]=[shift price dir front back status break rev pwr cnt day_minutes atr impulse time]       
              
    first_levels_counter=np.zeros(len(data),dtype=int)
    for i in range(len(data)): # перебираем каждую строку (список) списка 'data'
        # проверка каждого фрактала "не станет ли он в будущем ключевым уровнем" и поиск "ближайшего ключевого уровня".         
        for j in range(i + 1, len(data)): # сверяем со следующими ниже строками
            values = [float(item[1]) for item in data[i][3:]] # формируем массив из значений цены (индекс[1]) текущей строки
            Low,Hi = min(values), max(values) # находим диапазон Hi/Low, в пределах которого будем искать "ключевой" уровень
            for k in range(3, len(data[j])): # начиная со индекса [3] пошли фракталы (3:fractal_0) 
                # поиск ближайшего "ключевого" уровня в будущем
                if data[i][2][1]==0 and data[j][k][5]>0 and data[j][k][13]>data[i][3][13] and data[j][k][1]>Low and data[j][k][1]<Hi: 
                # первый попавшийся, "ключевой" уровень, из будущего, в пределах диапазона Hi/Low   
                    data[i][2][1] =  data[j][k][1] # сохраняем цену ближайшего в будущем "ключевого" уровня
                    data[i][2][2] = (data[j][k][13]-data[i][3][13])/3600 # через сколько часов уровень станет "ключевым"
                # проверка, будет ли текущий фрактал в будущем "ключевым уровнем"
                if data[i][3][13] == data[j][k][13] and data[j][k][5] > 0: # время текущего фрактала совпало со временем фрактала из будущего, и тот со статусом "ключевой"
                    data[i][2][0] = 1 # говорит о том, что в будущем этот фрактал будет "ключевым уровнем"
                    first_levels_counter[i]=1 # счеткик количества найденных ключевых уровней
                    break
        # нормализация к диапазону 0..1 и сохранение коэффициентов нормализации цены в массив restore[min_val, max_val - min_val]
        for index in [0, 1, 6, 7, 8, 9, 10, 11, 12]:  # индексы для нормализации
            values = [float(item[index]) for item in data[i][3:]]  # в строке 'i' извлекаем значения [index] начиная со списка[3] (это списки fractal) 
            min_val, max_val = min(values), max(values) # мин и макс значения во всей строке
            # выполняем нормализацию
            for item in data[i][3:]: # по всей строке 'i' начиная со списка[3]
                item[index] = (float(item[index]) - min_val) / (max_val - min_val) if max_val > min_val else 0.5 # нормализуем значения [index]
            if index == 1: # в индекс[1] записана цена, нужно сохранить коэффициенты нормализации (min, max-min) для последующего ее восстановления
                data[i][1] = [min_val, max_val - min_val]  # Добавляем их в список [restore] после столбца с временем
                data[i][2][1] = (data[i][2][1] - min_val) / (max_val - min_val) if max_val > min_val else 0.5 # нормализуем к тому же диапазону значение ближайшего в будущем "ключевого" уровня
                if data[i][2][1]<0 or data[i][2][1]>1: 
                    print('warning, StrongLevel[',data[i][0],']=',data[i][2][1],' out of range[0..1]')
        # Нормализация данных с индексами 3 и 4 (front и back) к общему диапазону
        values_3 = [float(item[3]) for item in data[i][3:]]
        values_4 = [float(item[4]) for item in data[i][3:]]
        min_val = min(min(values_3), min(values_4))
        max_val = max(max(values_3), max(values_4))
        for item in data[i][3:]:
            item[3] = (float(item[3]) - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            item[4] = (float(item[4]) - min_val) / (max_val - min_val) if max_val > min_val else 0.5            
    print('find ',sum(first_levels_counter)," first levels")                 
    print('OK: data normalized')
    return data   
 
check = read_data('Nero_XAUUSD60.csv') # Nero_XAUUSD60.csv    Nero_5.csv     
# %% save to csv для проверок
with open('normalized.csv', 'w', newline='') as f:  # Открываем файл для записи
    writer = csv.writer(f, delimiter=';')  # Создаем объект writer для записи в CSV-файл
    for row in check:  # Перебираем каждую строку в данных
        new_row = [row[0]]  # Время сохраняется без изменений
        #new_row += [':'.join(map(str, item)) for item in row[1:]]  # Преобразуем списки в строки, разделенные ':'
        counter=0 # счетчик столбцов
        for item in row[1:]:
            counter+=1 
            if counter>1: # начиная со второго столбца восстанавливаем из нормализованных значений
                item[1]=item[1]*row[1][1]+row[1][0] # цену ближайшего ключевого уровня и цены фракталов  
            
            new_row += [':'.join(map(str, item))]
        writer.writerow(new_row)  # Записываем строку в файл

print(f"Data saved to {'normalized.csv'}")

# %% нормализация
