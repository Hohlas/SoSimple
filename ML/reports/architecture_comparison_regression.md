# Architecture Comparison Report (REGRESSION)

**Дата**: 2026-02-24 18:32
**Задача**: Регрессия (target = predict)
**Loss**: Huber Loss (delta=1.0)
**Early stopping**: на val pearson_r (patience=10)
**Фреймворк**: PyTorch
**Optimizer**: AdamW (lr=1e-3, weight_decay=1e-4)

---

## 1. Сводная таблица

| Модель | Val Pearson r | MAE | RMSE | R² | DirAcc | Параметры | Время (с) | Best Epoch |
|--------|-------------|--------|-------|-------|--------|-----------|-----------|------------|
| bilstm ⭐ | **0.5634** | 0.1025 | 0.1837 | 0.3156 | 0.9748 | 147,073 | 207.4 | 9 |
| cnn1d | **0.5273** | 0.1171 | 0.1938 | 0.2383 | 0.9590 | 41,473 | 58.4 | 3 |
| transformer | **0.0560** | 0.1116 | 0.2221 | -0.0001 | 0.4633 | 69,889 | 492.7 | 6 |
| hybrid | **0.5524** | 0.1108 | 0.1862 | 0.2972 | 0.9746 | 83,073 | 76.4 | 3 |

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

**Лучшая модель**: bilstm (Pearson r = 0.5634)
