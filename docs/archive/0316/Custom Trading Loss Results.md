# Walkthrough: Custom Trading Loss (ME-5) Results

We have completed the implementation, optimization, and evaluation of the **Asymmetric Loss** (Custom Trading Loss).

## 1. Accomplishments
- **AsymmetricLoss**: Implemented a core PyTorch module that penalizes under-predictions (FN) more heavily than over-predictions (FP).
- **Pipeline Integration**: Integrated the new loss into [train.py](file:///home/hohla/git/SoSimple/ML/train.py) (CLI arguments) and [optimize.py](file:///home/hohla/git/SoSimple/ML/optimize.py) (Optuna search space).
- **Optimization**: Ran 50 trials for BiLSTM Regression. Optuna found a stable configuration with `Pearson r ≈ 0.33` and `num_layers: 3`.
- **Infrastructure Fix**: Updated [threshold_analysis.py](file:///home/hohla/git/SoSimple/ML/threshold_analysis.py) to automatically detect model architecture (layers, hidden size) from checkpoints, preventing "state_dict mismatch" errors in the future.

## 2. Quantitative Results

| Experiment | Method | Best Pearson r (val) | Optimal θ | Profit Factor (val) |
|------------|--------|----------------------|-----------|--------------------|
| Baseline | Huber Loss (1 layer) | 0.310 | ~0.50 | 0.6180 |
| **ME-5** | **Asymmetric Loss (3 layers)** | **0.327** | **0.625** | **0.7280** |

> [!NOTE]
> **Conclusion**: We achieved a **~19% improvement** in Profit Factor. However, PF 0.728 is still below the breakeven point (1.0).

## 3. Visualizations

````carousel
![Scatter Plot](/home/hohla/git/SoSimple/ML/plots/regression_bilstm.png)
Correlation remains decent, but predictions are still clustered.
<!-- slide -->
![PF vs Threshold](/home/hohla/git/SoSimple/ML/plots/threshold_profit_factor.png)
Profit Factor peaks at high thresholds but hasn't broken 1.0 yet.
````

## 4. Key Learnings
- **Loss alone is not enough**: While Asymmetric Loss helps focus on larger moves, it cannot create a signal where features are insufficient.
- **Deeper architecture**: Optuna consistently favors 3-layer BiLSTM for this task, suggesting that 1 layer was underfitting.
- **Threshold**: The "trading edge" appears only at very high thresholds (top 1% of predictions), where Precision reaches ~32%.

## 5. Next Steps
The current bottleneck is likely the **Target Variable** (`predict`). It is currently too variable in horizon length.
We recommend:
1. **Pipeline Audit**: Quick check for hidden bugs in normalization/masking.
2. **Fixed Horizon Targets**: Predicting the maximum move within exactly the next 24 or 48 bars.
