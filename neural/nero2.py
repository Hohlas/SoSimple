# %% Импорт необходимых библиотек
import numpy as np
from csv_read import read_input_data, normalize_input_data
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

csv_data = read_input_data('Nero_5.csv') # Nero_XAUUSD60.csv    Nero_5.csv
input_data=normalize_input_data(csv_data)

# %% Разделите данные на тренировочную и проверочную выборки
train_data, test_data = train_test_split(input_data, test_size=0.2)

# %% Разделите данные на признаки и метки
X_train = [item[2:] for item in train_data]
y_train = [item[1] for item in train_data]

X_test = [item[2:] for item in test_data]
y_test = [item[1] for item in test_data]

# %% Преобразуйте списки в массивы numpy для обучения модели
X_train = np.array(X_train)
y_train = np.array(y_train)

X_test = np.array(X_test)
y_test = np.array(y_test)

# %% Создайте модель нейронной сети
model = Sequential()
model.add(Dense(32, input_dim=len(X_train[0]), activation='relu'))
model.add(Dense(16, activation='relu'))
model.add(Dense(1, activation='linear'))
"""
# %% Скомпилируйте модель
model.compile(loss='mean_squared_error', optimizer='adam')

# %% Обучите модель
model.fit(X_train, y_train, epochs=10, batch_size=32)

# %% Оцените модель
loss = model.evaluate(X_test, y_test)
print('Test loss:', loss)
 """