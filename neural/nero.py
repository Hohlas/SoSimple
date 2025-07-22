# %% Импорт необходимых библиотек
import numpy as np
import pandas as pd # pip install pandas
import tensorflow as tf # pip install tensorflow
from tensorflow.keras.models import Sequential
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler # pip install scikit-learn
from sklearn.model_selection import train_test_split
import tensorflow.python.platform.build_info as build_info

print("Tensorflow ver-",tf.__version__," CUDA ver-",build_info.build_info['cuda_version'])
# %% Подключение GPU
try:
    devices = tf.config.list_physical_devices('GPU')
    if len(devices) > 0:
        print('Running on GPU ', devices)
        tf.config.experimental.set_memory_growth(devices[0], True)
        strategy = tf.distribute.OneDeviceStrategy(device="/gpu:0")
    else:
        print('GPU not available, running on CPU')
        strategy = tf.distribute.OneDeviceStrategy(device="/cpu:0")
except ValueError:
    raise BaseException('ERROR: Not connected to a device!')
# %% Загрузка данных
history_data = 'EURUSD60.csv' # 'https://drive.google.com/uc?id=1_eYsMYv8L_rrFrNnVN39ugbSVvC12Mm5'
data = pd.read_csv(history_data, header=None, sep=',', names=['date', 'time', 'open', 'high', 'low', 'close', 'volume'])
data = data[['high', 'low']]

# Проверка на пустые строки
data.dropna(inplace=True)
print('read ',len(data),'lines in ',history_data)
# %% Создание набора данных для обучения и валидации
X = []
y = []
scaler_high = MinMaxScaler(feature_range=(0, 1))
scaler_low = MinMaxScaler(feature_range=(0, 1))
for i in range(100, len(data)):
    window_high = scaler_high.fit_transform(data['high'][i-100:i].values.reshape(-1, 1))
    window_low = scaler_low.fit_transform(data['low'][i-100:i].values.reshape(-1, 1))
    window = np.hstack((window_high, window_low))
    X.append(window)
    y.append(1 if data.iloc[i, 0] > data.iloc[i-1, 0] else 0)
X, y = np.array(X), np.array(y)
X = np.reshape(X, (X.shape[0], X.shape[1], 2))

# Разделение данных на обучающую и валидационную выборки
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
print('X_train, X_val, y_train, y_val:  are ready')
# %% Создание модели LSTM
# Создание обратных вызовов 
early_stopping = EarlyStopping(monitor='val_loss', patience=3) # для ранней остановки: останавливает обучение, когда val_loss не улучшается в течение трех эпох (patience=3) 
model_checkpoint = ModelCheckpoint('model_{epoch}.h5', save_freq='epoch') # для сохранения модели после каждой эпохи в файл model_{epoch}.h5

with strategy.scope():
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 2)))
    model.add(LSTM(units=50))
    model.add(Dense(1, activation='sigmoid'))

    # Компиляция и обучение модели
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=100, batch_size=32, callbacks=[early_stopping, model_checkpoint]) # Обучение модели
    model.save('result_model.h5') # Сохранение последней модели (необязательно, т.к. сохраняются какждую эпоху)
print('Learning complete')    
# %% Прогнозирование следующего бара и
model = load_model('result_model.h5') # загрузка модели с лучшими результатами
last_100_data_high = scaler_high.transform(data['high'][-100:].values.reshape(-1, 1))
last_100_data_low = scaler_low.transform(data['low'][-100:].values.reshape(-1, 1))
last_100_data = np.hstack((last_100_data_high, last_100_data_low))
predicted_price = model.predict(np.reshape(last_100_data, (1, last_100_data.shape[0], 2)))
predicted_direction = 'up' if predicted_price > 0.5 else 'down'
print(f'Предсказанное направление для следующего бара - {predicted_direction}.')

# %%
# создать файл setup.py или pyproject.toml 