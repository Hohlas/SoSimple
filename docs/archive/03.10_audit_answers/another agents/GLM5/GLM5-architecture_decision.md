# Architecture Decision Record

**Date**: 2026-03-09  
**Status**: Draft — Pending Validation  
**Decision Phase**: 3.3 (Final Architecture Selection)

---

## Executive Summary

After comprehensive evaluation of 4 neural network architectures (Bi-LSTM, 1D-CNN, Transformer, Hybrid CNN+LSTM) for both classification and regression tasks, **no single architecture emerges as clearly superior**. All architectures converge to similar performance ceilings (~0.57 macro F1 for classification, ~0.55 Pearson r for regression), indicating the bottleneck is in data/features rather than model architecture.

**Primary Recommendation**: Focus on **regression task** with **Bi-LSTM or Transformer** architecture, after fixing critical data leakage issue.

---

## 1. Architecture Comparison Summary

### Classification Results

| Model | f1_macro | f1_minority | F1(-1) | F1(0) | F1(1) | Parameters | Training Time |
|-------|----------|-------------|--------|-------|-------|------------|---------------|
| **Hybrid** | 0.568 | 0.385 | 0.417 | 0.935 | 0.353 | 83K | 156s |
| Transformer | 0.567 | 0.376 | 0.392 | 0.949 | 0.359 | 70K | 641s |
| Bi-LSTM | 0.553 | 0.355 | 0.370 | 0.949 | 0.340 | 147K | 23s |
| 1D-CNN | 0.346* | 0.346 | 0.368 | 0.931 | 0.325 | 42K | 250s |

*Note: 1D-CNN trained with f1_minority metric mode

### Regression Results

| Model | pearson_r | MAE | RMSE | R² | DirAcc | Parameters | Training Time |
|-------|-----------|-----|------|----|--------|------------|---------------|
| **Transformer** | 0.563 | 0.114 | 0.185 | 0.306 | 97.5% | 70K | 1549s |
| **Bi-LSTM** | 0.555 | 0.103 | 0.185 | 0.306 | 97.5% | 147K | 128s |
| Hybrid | 0.546 | 0.115 | 0.188 | 0.283 | 97.2% | 83K | 75s |
| 1D-CNN | 0.519 | 0.103 | 0.195 | 0.232 | 93.1% | 42K | 60s |

**⚠️ Critical Issue**: DirAcc = 97.5% indicates data leakage via `direction` feature. See Section 3.

---

## 2. Architecture Selection Rationale

### For Classification Task

**Selected**: Hybrid CNN+LSTM (best f1_macro) OR Transformer (best f1_minority)

**Rationale**:
- Hybrid shows best F1(-1) = 0.417, indicating slightly better signal detection
- Transformer has more consistent performance across signal classes
- However, **classification is fundamentally limited** by extreme class imbalance (95% neutral)

**Limitation**: Even best architecture achieves only ~0.38-0.42 F1 for signal classes, which translates to ~60-70% false trading signals. This is not viable for production trading.

### For Regression Task

**Selected**: Bi-LSTM (efficiency) OR Transformer (best metrics)

**Rationale**:
- Transformer achieves highest Pearson r = 0.563
- Bi-LSTM is 12x faster with comparable metrics
- Both show similar MAE and RMSE

**Critical Caveat**: Current regression results are **invalid** due to data leakage. After fixing, expect:
- Pearson r to drop to ~0.30-0.40 (honest prediction)
- DirAcc to drop to ~50-55% (near random)

---

## 3. Critical Issues Identified

### 3.1 Data Leakage in Regression

**Problem**: The `predict` target is calculated as:
```
predict = -back * direction
```

The `direction` field of fractal[0] is a direct input feature. This allows the model to "cheat" by reading the sign directly.

**Evidence**:
- All regression models show DirAcc = 97.2-97.5%
- This is mathematically impossible for genuine prediction
- Pearson r = 0.55 is achievable because model knows the sign

**Fix Required**: Exclude `direction` from input features for regression task.

### 3.2 Class Imbalance in Classification

**Problem**: 95% of samples are neutral (class 0), only 5% are signals.

**Evidence**:
- F1(0) = 0.93-0.95 (excellent)
- F1(-1) = 0.37-0.42 (poor)
- F1(1) = 0.32-0.36 (poor)

**Mitigations Available**:
1. `--metric_mode f1_minority` — train on signal classes specifically
2. `--use_weighted_sampler` — balance batch composition
3. Higher `focal_gamma` (3.0-5.0) — focus on hard examples

---

## 4. Final Architecture Decision

### Primary Recommendation: Regression with Bi-LSTM

**Architecture**: Bi-LSTM (2 layers, hidden_size=64)

**Justification**:
1. Fast training (128s vs 1549s for Transformer)
2. Good for sequential data (fractals have temporal dependencies)
3. After leakage fix, regression is more viable than classification
4. Pearson r ~0.30-0.40 (honest) is potentially usable for trading

**Configuration**:
```python
{
    "model": "bilstm",
    "task": "regression",
    "hidden_size": 64,
    "num_layers": 2,
    "dropout": 0.3,
    "lr": 1e-3,
    "weight_decay": 1e-4,
    "batch_size": 256,
    "patience": 10,
    "loss": "HuberLoss(delta=1.0)",
    "exclude_direction": True  # NEW: Fix data leakage
}
```

### Secondary Recommendation: Classification with Hybrid

**Architecture**: Hybrid CNN+LSTM

**Justification**:
1. Best F1(-1) = 0.417 among all models
2. Combines local (CNN) and global (LSTM) pattern recognition
3. Reasonable training time (156s)

**Configuration**:
```python
{
    "model": "hybrid",
    "task": "classification",
    "metric_mode": "f1_minority",
    "use_weighted_sampler": True,
    "focal_gamma": 3.0,  # Increased from 2.0
    "focal_minority_weight": 0.495,  # Higher weight for signals
    "lr": 1e-3,
    "batch_size": 256,
    "patience": 10
}
```

---

## 5. Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Extreme class imbalance (95% neutral) | Classification ceiling ~0.57 F1 | Focus on regression; two-stage classification |
| Data leakage in regression | Invalid DirAcc metrics | Exclude direction feature |
| Small signal sample size (~2,200) | Overfitting on signals | Strong regularization; data augmentation |
| No feature engineering for NN | May miss predictive signals | Add technical indicators |
| No ensemble | May leave performance on table | Combine Bi-LSTM + 1D-CNN predictions |

---

## 6. Recommendations for Next Phase

### Immediate (Before Further Training)

1. **Fix data leakage**: Modify `data_loader.py` to exclude `direction` for regression
2. **Re-run regression**: Train Bi-LSTM with fixed data loader
3. **Document honest metrics**: Update checkpoint JSONs with real DirAcc

### Short-term (Validation Experiments)

4. **Train classification with f1_minority + weighted_sampler**
5. **Run Optuna HPO for Bi-LSTM regression** (after leakage fix)
6. **Compare with baseline**: Ensure NN beats Random Forest (0.556 F1)

### Medium-term (If Results Promising)

7. **Test on held-out test set**
8. **Implement ensemble**: Average Bi-LSTM + Transformer predictions
9. **Feature engineering**: Add technical indicators as additional features

---

## 7. Success Criteria

| Metric | Current (Leaky) | Target (Honest) | Decision |
|--------|-----------------|-----------------|----------|
| Regression: Pearson r | 0.55 | > 0.35 | Continue if met |
| Regression: DirAcc | 97.5% | 50-60% | Should drop after fix |
| Classification: f1_minority | 0.35 | > 0.45 | Continue if met |
| Classification: signal_precision | 0.25 | > 0.40 | Required for trading |

---

## 8. Conclusion

The architecture comparison reveals that **model choice is secondary to data quality issues**. All four architectures perform similarly, hitting a ceiling determined by:

1. Extreme class imbalance (95% neutral)
2. Data leakage in regression (direction feature)
3. Limited signal samples (~2,200)

**Primary path forward**: Fix data leakage, focus on regression with Bi-LSTM, and reassess honest metrics before deciding on further investment in this approach.

---

**Approved by**: _Pending Review_  
**Next Review Date**: After leakage fix and re-training
