---
kind: build_system
name: Build & Artifact Management for SoSimple ML Trading System
category: build_system
scope:
    - '**'
source_files:
    - requirements.txt
    - package.json
    - MT/tester/opt.set
    - .gitignore
---

The SoSimple project has no centralized build system (no Makefile, Dockerfile, CI pipeline, or packaging scripts). Build and deployment are handled through a collection of ad-hoc conventions across Python, MetaTrader MQL4/MQL5, and Node.js components:

**Python Environment & Dependencies**
- Dependencies are declared in `requirements.txt` with pinned minimum versions (pandas>=2.0.0, numpy>=1.24.0, torch>=2.0.0 via CUDA 12.1 index, fastapi>=0.110.0, etc.)
- Virtual environments are expected at `.venv/` (referenced throughout the codebase as `./.venv/bin/python -m pytest tests/ -q`)
- No pyproject.toml, setup.py, or tox configuration exists
- Testing uses pytest exclusively, invoked directly from the virtual environment

**MetaTrader Build & Optimization**
- MQL4/MQL5 code is compiled within the MetaTrader platforms themselves (no external build tools)
- Backtesting parameters are stored in `MT/tester/opt.set` with structured sections for different parameter groups (PIC Levels, Trend Signals, ATR, Inputs, Output, Time, ML Optimization)
- Multiple preset configurations exist in `MT/tester/files/*.set` files for different optimization runs
- The MT4/MT5 expert advisors (`$o$imple.mq4`, `$o$imple.mq5`) are the primary artifacts that get compiled by MetaEditor

**Node.js Components**
- Minimal Node.js dependency on `opencode-queue` (^0.11.1) declared in `package.json`
- Used only for the opencode AI agent framework, not for building the main system

**Artifact Management**
- Model checkpoints are stored in `ML/checkpoints/` as `.pt` PyTorch files and `.json` result files
- Training data and processed features live in `DATA/` with organized subdirectories for different spread scenarios
- Test results and reports are generated in `ML/reports/` with extensive directory structure per experiment
- No version control strategy for artifacts beyond git tracking of source code

**Testing & Validation**
- Comprehensive pytest suite in `tests/` covering all major components
- Tests are run using the local virtual environment rather than any CI pipeline
- No automated testing pipeline exists in `.github/workflows/` or other CI configuration

The build approach is essentially manual: developers install dependencies via pip into a local virtual environment, compile MQL code within MetaTrader, and run experiments/scripts directly. There is no containerization, continuous integration, or standardized release process documented.