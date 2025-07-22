
# %%
import pandas as pd  # pip install pandas
import matplotlib.pyplot as plt # pip install matplotlib
import matplotlib.dates as mdates
from mpl_finance import candlestick_ohlc  # pip install mpl_finance
import numpy as np

print("Hello, Nero!")
# %%
def PLOT(plot_data):
    data = pd.read_csv(plot_data, header=None, sep=',', names=['date', 'time', 'open', 'high', 'low', 'close', 'volume'])
    data = data.tail(400) # Выбор последних 100 строк
    # Выбираем только столбцы 'high' и 'low'
    data_hl = data[['high', 'low']]
    fig, ax = plt.subplots()
    # Строим бары по высоте
    ax.bar(range(len(data_hl)), data_hl['high'] - data_hl['low'], bottom=data_hl['low'], width=0.3, color='black')
    fig.set_size_inches(20, 5)# Установка размера окна
    ax.set_xlabel('Time (index)')
    ax.set_ylabel('Price')
    ax.set_title('High-Low Bar Chart')
    plt.show(block=True)
# %%
history_data='EURUSD60.csv' # 'https://drive.google.com/uc?id=1_eYsMYv8L_rrFrNnVN39ugbSVvC12Mm5'
PLOT(history_data)
aaa=567
# %%
