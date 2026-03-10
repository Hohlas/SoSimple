# Project Audit and Strategic Plan: SoSimple ML Component

**Date**: 2026-03-09  
**Author**: Claude (AI Architect)  
**Status**: Draft for Review

---

## Executive Summary

This audit analyzes the current state of the SoSimple ML project for Forex reversal prediction (XAUUSD, H1). The project has completed phases 1-3.2 (data preprocessing, EDA, baseline models, and neural network architecture comparison), but faces critical challenges related to class imbalance and potential data leakage.

**Key Findings:**
1. **Classification is at a ceiling**: ~0.57 macro F1, with signal classes (F1 ≈ 0.35-0.42) far below trading-viable thresholds
2. **Regression shows DirAcc = 97.5%**: This is **data leakage** — the model "cheats" by reading direction from fractal[0]
3. **Root cause identified**: With ~2,200 signal samples (-1: 1,084, +1: 1,119) vs ~41,390 neutral samples, the class imbalance is extreme
4. **Architecture ceiling confirmed**: All 4 NN architectures hit the same ~0.57 macro F1 limit — the problem is data/features, not model choice

---

## Phase 1: Comprehensive Audit

### 1.1 Data Audit

#### Dataset Statistics

| Split | Total Samples | Class -1 | Class 0 | Class +1 |
|-------|--------------|----------|---------|----------|
| Train | 43,593 | 1,084 (2.5%) | 41,390 (94.9%) | 1,119 (2.6%) |
| Validation | 9,341 | 232 (2.5%) | 8,865 (94.9%) | 244 (2.6%) |

#### Assessment

| Question | Finding | Severity |
|----------|---------|----------|
| Is data sufficient? | ~2,200 signal samples is borderline for deep learning | Medium |
| How critical is imbalance? | **Critical** — 95% neutral makes learning signals nearly impossible without aggressive balancing | **Critical** |
| Data leakage present? | **Yes** — in regression: DirAcc=97.5% due to direction in features | **Critical** |

#### Data Leakage Analysis

**Critical leakage in regression task:**

The `predict` target is calculated as:
```
predict = -back * direction
```

Where `direction` (of fractal[0]) is a direct input feature. This means the model can trivially learn the sign of `predict` by reading the `direction` field of the first fractal.

Evidence:
- All regression models show **DirAcc = 97.2-97.5%** (see checkpoint results)
- This is mathematically impossible for a genuinely predictive model
- Pearson r = 0.55 is achievable because the model essentially "cheats"

**Recommended fix**: Exclude `direction` from input features for regression task, OR reformulate the problem.

#### Potential Additional Leakage

The `back` feature (price movement after fractal) may also leak information:
- `back` is calculated post-factum and may correlate with future price action
- This is more subtle and harder to fix without domain expertise

### 1.2 Model Audit

#### Classification Results (Latest Checkpoints)

| Model | f1_macro | f1_minority | signal_precision | F1(-1) | F1(0) | F1(1) | Best Epoch |
|-------|----------|-------------|------------------|--------|-------|-------|------------|
| hybrid | 0.568 | 0.385 | ~0.27 | 0.417 | 0.935 | 0.353 | 10 |
| transformer | 0.567 | 0.376 | ~0.28 | 0.392 | 0.949 | 0.359 | 11 |
| bilstm | 0.553 | 0.355 | ~0.25 | 0.370 | 0.949 | 0.340 | 2 |
| cnn1d | 0.346* | 0.346 | 0.236 | 0.368 | 0.931 | 0.325 | 34 |

*Note: cnn1d trained with `--metric_mode f1_minority`, hence lower f1_macro

#### Regression Results (Latest Checkpoints)

| Model | pearson_r | MAE | RMSE | R² | DirAcc | Best Epoch |
|-------|-----------|-----|------|----|--------|------------|
| transformer | **0.563** | 0.114 | 0.185 | 0.306 | 97.5% | 49 |
| bilstm | **0.555** | 0.103 | 0.185 | 0.306 | 97.5% | 3 |
| hybrid | **0.546** | 0.115 | 0.188 | 0.283 | 97.2% | 3 |
| cnn1d | **0.519** | 0.103 | 0.195 | 0.232 | 93.1% | 5 |

#### Assessment

| Question | Finding | Severity |
|----------|---------|----------|
| Is current quality sufficient for trading? | **No** — F1_minority ≈ 0.35 means 65% of signals are wrong | **Critical** |
| Is this an architecture or data problem? | **Data/features problem** — all architectures hit same ceiling | **Critical** |
| Should we focus on classification or regression? | **Regression** is more viable (Pearson r ≈ 0.55) but needs leakage fix | Medium |
| Is the DirAcc=97.5% a real result? | **No** — data leakage via direction feature | **Critical** |

### 1.3 Pipeline Audit

#### Data Loader (data_loader.py)

| Aspect | Finding | Assessment |
|--------|---------|------------|
| Fractal parsing | Correctly parses 100 fractals × 11 fields | ✅ Good |
| fractal_time exclusion | Correctly excluded (line 107-108) | ✅ Good |
| ATR handling | Broadcast correctly | ✅ Good |
| NaN handling | Fills with 0, creates mask | ✅ Good |
| StandardScaler | Optional (default off) | ⚠️ Document reason |

#### Training (train.py)

| Aspect | Finding | Assessment |
|--------|---------|------------|
| Loss functions | Focal Loss (classification), Huber (regression) | ✅ Appropriate |
| Early stopping | Correctly on metrics, not loss | ✅ Good |
| WeightedRandomSampler | Implemented but underutilized | ⚠️ Opportunity |
| Gradient clipping | max_norm=1.0 | ✅ Good |
| Scheduler | ReduceLROnPlateau | ✅ Good |

#### Issues Found

1. **WeightedRandomSampler not used by default**: Available but needs `--use_weighted_sampler` flag
2. **metric_mode='f1_minority' not used**: Training uses f1_macro by default (misleading)
3. **No systematic ablation**: Haven't tested effect of sampler, different gamma values

### 1.4 Overfitting Analysis

All models show clear overfitting:
- Train loss decreases, validation loss increases/plateaus
- Best epochs: 2-10 (very early), indicating rapid overfitting

**Contributing factors:**
1. Small signal sample size (~2,200)
2. Model capacity exceeds data complexity for signals
3. Limited regularization (dropout=0.3 may be insufficient)

---

## Phase 2: Strategic Plan

### 2.1 Strategic Direction Recommendation

**Primary recommendation: Focus on regression task**

Rationale:
1. Regression shows Pearson r ≈ 0.55, which is potentially usable
2. After fixing data leakage, regression may show genuine predictive power
3. Classification is fundamentally limited by extreme class imbalance (~95% neutral)
4. Even with perfect classification (F1=1.0 for signals), precision ≈ 0.30 means 70% false trades

**Classification as secondary:**
- Consider two-stage approach: Signal/NoSignal → Sell/Buy
- Or treat classification as probability estimation for risk management

### 2.2 Prioritized Action Plan

#### Quick Wins (Can implement with existing code)

| # | Action | Expected Result | Files/Commands |
|---|--------|----------------|---------------|
| Q1 | Train with `--metric_mode f1_minority` for all models | Better signal F1 (expected +0.05-0.10) | `train.py` already supports this |
| Q2 | Enable `--use_weighted_sampler` for classification | More balanced batch composition | `data_loader.py:38` |
| Q3 | Test with higher focal_gamma (3.0-5.0) | Focus more on hard examples | Add to CLI args |
| Q4 | Re-run regression WITHOUT direction feature | Remove leakage, get honest metrics | Requires code change |

#### Medium Effort (Requires new modules/changes)

| # | Action | Expected Result | Files/Commands |
|---|--------|----------------|---------------|
| M1 | Implement two-stage classification: Signal vs NoSignal | May improve signal detection | New model or data loader |
| M2 | Downsample neutral class (10-20%) | More balanced training | `data_loader.py` modification |
| M3 | Run Optuna HPO for bilstm classification | Find better hyperparameters | `optimize.py` |
| M4 | Run Optuna HPO for regression (after leakage fix) | Better pearson_r | `optimize.py` |

#### Structural Changes (Requires rethinking approach)

| # | Action | Expected Result | Impact |
|---|--------|----------------|--------|
| S1 | Feature engineering: add technical indicators | May break ceiling | High |
| S2 | Ensemble: average predictions from bilstm + cnn1d | +0.02-0.05 F1 | Medium |
| S3 | Different problem formulation: predict price movement magnitude only | Removes direction leakage | High |

---

### 2.3 Detailed Implementation Plan

#### Task 1: Fix Regression Data Leakage (Critical)

**Problem**: `direction` feature in fractal[0] directly predicts sign of `predict` target

**Solution**: Create variant of data loader that excludes `direction` from features

```python
# In data_loader.py, add parameter:
def parse_fractals_to_3d(df, exclude_direction=False):
    # If exclude_direction=True, skip extracting direction (feature index 1)
```

**Expected outcome**: Honest DirAcc (~50-55%), true pearson_r assessment

**Success criteria**: DirAcc drops to near-random, pearson_r recalculated

#### Task 2: Train with f1_minority metric mode

**Command**:
```bash
# Retrain all models with f1_minority
python -m ML.train --model bilstm --task classification --metric_mode f1_minority --epochs 50
python -m ML.train --model transformer --task classification --metric_mode f1_minority --epochs 50
python -m ML.train --model hybrid --task classification --metric_mode f1_minority --epochs 50
python -m ML.train --model cnn1d --task classification --metric_mode f1_minority --epochs 50
```

**Expected**: f1_minority should improve from ~0.35 to ~0.40-0.45

#### Task 3: Enable WeightedRandomSampler

**Command**:
```bash
# Train with weighted sampler
python -m ML.train --model bilstm --task classification --metric_mode f1_minority --use_weighted_sampler --epochs 50
```

**Expected**: Better balance of classes in each batch

#### Task 4: Two-Stage Classification (Optional)

**Approach**:
1. Train binary classifier: Signal (classes -1, +1) vs NoSignal (class 0)
2. If Signal, train second classifier: Sell (-1) vs Buy (+1)

**Implementation**: Requires new training script or modification of data_loader

#### Task 5: Feature Engineering

**Ideas from EDA**:
- Price slopes at different windows (already in engineered features but not used by NN)
- Volatility features beyond ATR
- Pattern recognition (e.g., consecutive directions)

**Recommendation**: Use engineered features from `statistics/nero_features_engineered.csv` with a simpler model (Random Forest) as baseline comparison

---

### 2.4 MVP Feasibility Assessment

#### Target: Accuracy > 65% on test set

| Scenario | Feasibility | Notes |
|----------|-------------|-------|
| Classification (3-class) | ❌ Very unlikely | At best ~40-45% with current data |
| Binary: Signal/NoSignal | ⚠️ Possible | ~60-70% with better balancing |
| Regression (honest) | ⚠️ Uncertain | Needs leakage fix first |

#### Target: Sharpe Ratio > 1.5

| Scenario | Feasibility | Notes |
|----------|-------------|-------|
| Current models | ❌ No | Precision ~0.25-0.30 too low |
| With fixes | ⚠️ Uncertain | Need backtest to verify |

**Realistic assessment**:
- With proper regression (no leakage) showing pearson_r ~0.30-0.40, Sharpe 1.5 may be achievable with good risk management
- Classification alone cannot achieve this due to precision limitations

---

## Recommendations Summary

### Immediate Actions (This Session)

1. **Fix regression leakage**: Create modified data loader excluding `direction` feature
2. **Re-run classification** with `--metric_mode f1_minority --use_weighted_sampler`
3. **Document honest results** in updated checkpoint JSONs

### If Results Improve

4. Run Optuna HPO for best model
5. Consider ensemble of top 2 models
6. Test on test set only after all validation experiments done

### If Results Don't Improve

7. Accept that current features have limited predictive power
8. Focus on feature engineering (technical indicators)
9. Consider external data sources (if available)

---

## Appendix: Key Metrics Reference

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Classification: f1_macro | 0.57 | N/A | Misleading |
| Classification: f1_minority | 0.35 | >0.50 | Need work |
| Classification: signal_precision | 0.25-0.30 | >0.50 | Need work |
| Regression: pearson_r | 0.55 (leaky) | >0.40 (honest) | Need fix |
| Regression: DirAcc | 97.5% (leaky) | ~50-55% | Will fix |

---

*Document created as part of Phase 3.3: Architecture Decision*
