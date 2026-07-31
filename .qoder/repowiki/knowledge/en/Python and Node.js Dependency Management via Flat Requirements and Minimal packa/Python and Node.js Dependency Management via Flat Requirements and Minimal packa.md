---
kind: dependency_management
name: Python and Node.js Dependency Management via Flat Requirements and Minimal package.json
category: dependency_management
scope:
    - '**'
source_files:
    - requirements.txt
    - package.json
    - .opencode/package.json
---

This repository manages dependencies through two simple, flat manifests with no vendoring, lockfiles, or private registries beyond a single PyTorch CUDA extra index.

**Python dependencies** are declared in the root `requirements.txt`. All packages use minimum version pins (`>=`) rather than exact versions, except `catboost==1.2.8` which is pinned to an exact release. The file pulls PyTorch from the official CUDA 12.1 wheel index via `--extra-index-url https://download.pytorch.org/whl/cu121`, indicating GPU-accelerated inference/training is expected. The dependency set covers data science (pandas, numpy, scipy, scikit-learn), visualization (matplotlib, seaborn), ML frameworks (torch, xgboost, lightgbm, catboost), optimization (optuna), and the FastAPI server stack (fastapi, uvicorn, pydantic). There is no `requirements-dev.txt`, `pyproject.toml`, `setup.py`, or pipenv/poetry lockfile — all Python tooling relies on this single flat file.

**Node.js dependencies** are split across two minimal `package.json` files:
- Root `package.json` declares only `opencode-queue@^0.11.1`.
- `.opencode/package.json` declares `@opencode-ai/plugin@1.15.5`.
Both use caret ranges (`^`) for semver-compatible updates. A `package-lock.json` exists at the repo root but not under `.opencode/`, so only the root Node dependencies are locked. There is no `node_modules` committed; the root `node_modules/` directory appears to be generated locally.

**No Go, Rust, or other language manifests** were found — no `go.mod`, `Cargo.lock`, or similar files exist. MQL4/MQL5 code in `MT/` has no external package manager; it uses MetaTrader's built-in library includes.

**Conventions observed:**
- Python: flat `requirements.txt` with `>=` pins for reproducibility flexibility; one exact pin (`catboost==1.2.8`).
- Node: minimal scope, caret ranges, lockfile only at root level.
- No vendoring of any kind (no `vendor/`, `third_party/`, or submodules for dependencies).
- No private PyPI registry configured beyond the PyTorch CUDA wheels URL.
- No dependency update automation (no Dependabot, Renovate, or CI steps visible for updating manifests).