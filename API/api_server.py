# =============================================================================
# Файл: API/api_server.py
# Назначение: REST API Сервер для приема фракталов из MT4 и отдачи ML-сигналов
# Язык: Python 3.11+
# Обновлён: 2026-03-19
# =============================================================================

import json
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ML.data_loader import parse_fractals_to_3d, N_FRACTALS
from ML.models import get_model
from ML.utils import get_device
from processing.normalize import normalize_rowwise

# Конфигурация
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINTS_DIR = PROJECT_ROOT / 'ML' / 'checkpoints'
REPORTS_DIR = PROJECT_ROOT / 'ML' / 'reports'

# Чекпоинт и параметры по умолчанию (достигшие Profit Factor 4.5 на Test)
MODEL_NAME = 'transformer'
TASK = 'regression_updn'
HORIZON = 12
THETA = 2.665

# Глобальные переменные для модели
model = None
device = None

class MLServiceSettings:
    model_name: str = MODEL_NAME
    task: str = TASK
    horizon: int = HORIZON
    theta: float = THETA
    optuna_json: str | None = str(REPORTS_DIR / 'optuna_best_params_transformer_regression_updn.json')

class PredictRequest(BaseModel):
    atr_slow: float
    fractals: list[str]  # Ожидаем ровно 100 строк фракталов формата "T:P:Dir:Frnt:Back:..."

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл FastAPI: загрузка модели при запуске сервера."""
    global model, device
    print("🚀 Инициализация ML сервиса...")
    
    device = get_device()
    suffix = '_updn' if MLServiceSettings.task == 'regression_updn' else '_regression'
    ckpt_path = CHECKPOINTS_DIR / f'{MLServiceSettings.model_name}{suffix}_best.pt'
    
    if not ckpt_path.exists():
        raise FileNotFoundError(f"❌ Чекпоинт {ckpt_path} не найден! Обучите модель.")

    print(f"📥 Загрузка чекпоинта: {ckpt_path.name}")
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    
    ckpt_model_name = ckpt.get('model_name', MLServiceSettings.model_name)
    num_classes = ckpt.get('num_classes', 1)
    model_kwargs = ckpt.get('model_kwargs', {})
    
    if MLServiceSettings.optuna_json and Path(MLServiceSettings.optuna_json).exists():
        with open(MLServiceSettings.optuna_json, 'r', encoding='utf-8') as f:
            optuna_data = json.load(f)
        best_params = optuna_data.get('best_params', {})
        for k in ['hidden_size', 'num_layers', 'dropout', 'input_features']:
            if k in best_params:
                model_kwargs[k] = best_params[k]
        print(f"📥 Загружены параметры архитектуры из {Path(MLServiceSettings.optuna_json).name}")

    # Усечение последовательности
    seq_len = model_kwargs.get('seq_len', 20)
    MLServiceSettings.seq_len = seq_len
    
    model = get_model(ckpt_model_name, num_classes=num_classes, **model_kwargs)
    model.load_state_dict(ckpt['model_state_dict'])
    model = model.to(device)
    model.eval()
    
    print(f"✅ Модель {ckpt_model_name} успешно загружена (seq_len={seq_len})")
    print(f"📈 Рабочий горизонт: {MLServiceSettings.horizon}H, Порог (θ): {MLServiceSettings.theta}")
    
    yield
    
    # Очистка при завершении (опционально)
    print("🛑 Остановка сервиса...")

# Создаем приложение FastAPI
app = FastAPI(title="SoSimple MT4 ML Connector", version="1.0", lifespan=lifespan)

@app.get("/")
def read_root():
    """Health-check endpoint."""
    return {"status": "ok", "service": "SoSimple ML API"}

@app.post("/predict")
def predict_signal(request: PredictRequest):
    """
    Основной endpoint: принимает фракталы из MT4, прогоняет через препроцессинг и нейросеть,
    возвращает торговый сигнал (BUY, SELL, FLAT).
    """
    if len(request.fractals) != N_FRACTALS:
        raise HTTPException(
            status_code=400, 
            detail=f"Expected exactly {N_FRACTALS} fractals, got {len(request.fractals)}"
        )
    
    # 1. Формируем DataFrame в стиле Nero.csv
    row_data = {"ATR": request.atr_slow, "predict": 0.0} # `predict` нужен как заглушка для нормализации
    for i, seq_str in enumerate(request.fractals):
        row_data[f"fractal{i}"] = seq_str
    
    df = pd.DataFrame([row_data])
    
    # 2. Построчная нормализация (из processing.normalize)
    df_norm = normalize_rowwise(df)
    
    # 3. Парсинг в 3D тензор
    X_np, mask_np = parse_fractals_to_3d(df_norm)
    
    # Усекаем seq_len до нужного размера (как при обучении/тестировании)
    seq_len = getattr(MLServiceSettings, 'seq_len', 20)
    X_np = X_np[:, :seq_len, :]
    mask_np = mask_np[:, :seq_len]
    
    # 4. Inference
    X_tensor = torch.from_numpy(X_np).float().to(device)
    mask_tensor = torch.from_numpy(mask_np).bool().to(device)
    
    with torch.no_grad():
        preds = model(X_tensor, mask=mask_tensor).cpu().numpy()
        if preds.ndim > 1 and preds.shape[-1] == 1:
            preds = preds.squeeze(-1)
            
    # 5. Принятие торгового решения (Горизонт 12H)
    idx_map = {12: 0, 24: 2, 48: 4}
    if MLServiceSettings.horizon not in idx_map:
        raise HTTPException(status_code=500, detail="Invalid horizon configured.")
        
    idx = idx_map[MLServiceSettings.horizon]
    pred_up = float(preds[0, idx])
    pred_dn = float(preds[0, idx + 1])
    
    ratio_up = pred_up / (pred_dn + 1e-6)
    ratio_dn = pred_dn / (pred_up + 1e-6)
    
    # Сигнал: 1 (BUY), -1 (SELL), 0 (FLAT)
    signal = 0
    if ratio_up > MLServiceSettings.theta:
        signal = 1
    elif ratio_dn > MLServiceSettings.theta:
        signal = -1
        
    return {
        "signal": signal,
        "pred_up": round(pred_up, 4),
        "pred_dn": round(pred_dn, 4),
        "ratio_up": round(ratio_up, 4),
        "ratio_dn": round(ratio_dn, 4),
        "theta": MLServiceSettings.theta,
        "horizon": MLServiceSettings.horizon
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("API.api_server:app", host="127.0.0.1", port=8000, reload=False)
