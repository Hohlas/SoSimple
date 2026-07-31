---
kind: external_dependency
name: Optuna — hyperparameter optimization framework
slug: optuna
category: external_dependency
category_hints:
    - vendor_identity
    - framework_behavior
scope:
    - '**'
---

### Optuna
- Role: hyperparameter search engine for transformer models and other experiments, invoked via `ML/optimize.py`.
- Usage pattern: defines search spaces, runs trials, stores best parameters in JSON reports under `ML/reports/`.
- Stable behavior: Optuna studies are persisted and can be resumed; best parameters are referenced in training commands documented in DATA_FLOW.md.
- Verify exact study serialization format and trial callbacks against Optuna API.