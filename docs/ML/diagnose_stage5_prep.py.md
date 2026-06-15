# diagnose_stage5_prep.py

## Purpose
Stage 5.0-prep diagnostic runner: проверяет две гипотезы перед Stage 5.0 Transformer — breach feature ablation (на каких группах признаков держится сигнал) и AUC→PF sensitivity (какой прирост ранжирования нужен для PF-gate).

## Input
- `DATA/Nero_XAUUSD_train_labeled.csv` — train/validation labeled rows
- `DATA/Nero_XAUUSD_validation_labeled.csv` — validation labeled rows
- `DATA/XAUUSD_H1_OHLC.csv` — H1 OHLC=Bid prices

## Output
- `ML/reports/stage5_prep_diagnostics.json` — structured diagnostic artifact

## Command
```bash
~/git/SoSimple/.venv/bin/python ML/baseline/diagnose_stage5_prep.py \
    --train DATA/Nero_XAUUSD_train_labeled.csv \
    --val DATA/Nero_XAUUSD_validation_labeled.csv \
    --ohlc DATA/XAUUSD_H1_OHLC.csv \
    --output ML/reports/stage5_prep_diagnostics.json \
    --spread 0.20 --seed 42
```

## Schema
- `status`: "DIAGNOSTIC_ONLY"
- `config`: target, split, spread, seed
- `baseline_reproduction`: breach_auc, pr_auc, auc_ok flag
- `feature_ablation`: list of 6 profiles, each with AUC, PR-AUC, delta, top5 features
- `auc_pf_sensitivity`: list of 7 alpha values, each with AUC, favTP PF/n/BS_p05, fixedR0.7 PF/n/BS_p05
- `sensitivity_summary`: gate values, first pass alpha/AUC for favTP and fixedR0.7
- `interpretation_guards`: mandatory non-conclusions

## Status
DIAGNOSTIC_ONLY — no test, no winner, oracle uses future info.

## Limitations
- Oracle-mix использует истинные breach-метки (post-hoc information)
- Feature ablation не изолирует вклад групп полностью: взаимодействия признаков не оцениваются
- Один seed (42): воспроизводимость подтверждена эталонным AUC
- Торговая симуляция использует тот же RF fav (фиксирован)
