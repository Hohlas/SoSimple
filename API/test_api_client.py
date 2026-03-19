# =============================================================================
# Файл: API/test_api_client.py
# Назначение: Тестирование API-сервера для MT4
# Язык: Python 3.11+
# =============================================================================

import requests
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_FILE = PROJECT_ROOT / 'DATA' / 'Nero_test_labeled.csv'

def test_api():
    print(f"📖 Чтение тестового датасета: {TEST_FILE.name}")
    df = pd.read_csv(TEST_FILE, sep=';', low_memory=False)
    
    # Берем первую строку как пример
    row = df.iloc[0]
    
    print("\n🔍 Формирование полезной нагрузки (JSON)...")
    fractals = []
    for i in range(100):
        fractals.append(str(row[f'fractal{i}']))
        
    atr_slow = float(row['ATR'])
    
    payload = {
        "atr_slow": atr_slow,
        "fractals": fractals
    }
    
    print("🚀 Отправка POST запроса на http://127.0.0.1:8000/predict...")
    try:
        response = requests.post("http://127.0.0.1:8000/predict", json=payload)
        response.raise_for_status()
        result = response.json()
        
        print("\n✅ Ответ получен успешно!")
        print("Результат Предсказания:")
        print(f"  Signal: {result['signal']}")
        print(f"  Pred Up: {result['pred_up']}")
        print(f"  Pred Dn: {result['pred_dn']}")
        print(f"  Ratio Up: {result['ratio_up']}")
        print(f"  Ratio Dn: {result['ratio_dn']}")
        print(f"  Theta: {result['theta']}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Детали ошибки: {e.response.text}")

if __name__ == "__main__":
    test_api()
