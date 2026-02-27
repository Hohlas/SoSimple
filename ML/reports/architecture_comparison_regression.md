# Architecture Comparison Report (REGRESSION)

**Дата**: 2026-02-27 09:40
**Задача**: Регрессия (target = predict)
**Loss**: Huber Loss (delta=1.0)
**Early stopping**: на val pearson_r (patience=10)
**Фреймворк**: PyTorch
**Optimizer**: AdamW (lr=1e-3, weight_decay=1e-4)

---

## 1. Сводная таблица

| Модель | Val Pearson r | MAE | RMSE | R² | DirAcc | Параметры | Время (с) | Best Epoch |
|--------|-------------|--------|-------|-------|--------|-----------|-----------|------------|
| bilstm ⭐ | **0.3236** | 0.1083 | 0.1819 | 0.1033 | 0.9748 | 147,073 | 344.4 | 25 |
| cnn1d | **0.2518** | 0.1047 | 0.1863 | 0.0595 | 0.9748 | 41,473 | 82.1 | 9 |
| transformer | **0.1143** | 0.1097 | 0.1922 | -0.0017 | 0.9748 | 69,889 | 341.0 | 1 |
| hybrid | **0.2825** | 0.1030 | 0.1845 | 0.0774 | 0.9748 | 83,073 | 90.9 | 7 |

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

**Лучшая модель**: bilstm (Pearson r = 0.3236)
