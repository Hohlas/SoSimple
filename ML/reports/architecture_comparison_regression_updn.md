# Architecture Comparison Report (REGRESSION_UPDN)

**Дата**: 2026-03-19 15:01
**Задача**: Регрессия (target = predict)
**Loss**: Huber Loss (delta=1.0)
**Early stopping**: на val pearson_r (patience=10)
**Фреймворк**: PyTorch
**Optimizer**: AdamW (lr=1e-3, weight_decay=1e-4)

---

## 1. Сводная таблица

| Модель | Val Pearson r | MAE | RMSE | R² | Параметры | Время (с) | Best Epoch |
|--------|-------------|--------|-------|-------|-----------|-----------|------------|
| bilstm | **0.4262** | 0.1659 | 0.2133 | 0.1853 | 152,006 | 43.8 | 6 |
| cnn1d | **0.3751** | 0.1722 | 0.2189 | 0.1403 | 43,238 | 29.5 | 3 |
| transformer ⭐ | **0.4265** | 0.1691 | 0.2136 | 0.1833 | 70,630 | 256.3 | 23 |
| hybrid | **0.4099** | 0.1706 | 0.2180 | 0.1481 | 84,838 | 28.4 | 3 |

---

## 2. Visualizations

### bilstm
![bilstm Training Curves](../plots/training_curves_bilstm_regression.png)
![bilstm Residuals](../plots/regression_bilstm.png)

### cnn1d
![cnn1d Training Curves](../plots/training_curves_cnn1d_regression.png)
![cnn1d Residuals](../plots/regression_cnn1d.png)

### transformer
![transformer Training Curves](../plots/training_curves_transformer_regression.png)
![transformer Residuals](../plots/regression_transformer.png)

### hybrid
![hybrid Training Curves](../plots/training_curves_hybrid_regression.png)
![hybrid Residuals](../plots/regression_hybrid.png)

---

## 3. Сводное сравнение

![Architecture Comparison](../plots/architecture_comparison_regression.png)

---

## 4. Выводы

**Лучшая модель**: transformer (Pearson r = 0.4265)
