# Installation and Setup

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [requirements.txt](file://requirements.txt)
- [api_server.py](file://API/api_server.py)
- [$o$imple.mq4](file://MT/MQL4/Experts/$o$imple.mq4)
- [$o$imple.mq5](file://MT/MQL5/Experts/$o$imple.mq5)
- [INPUT.mqh](file://MT/MQL4/Include/INPUT.mqh)
- [OUTPUT.mqh](file://MT/MQL4/Include/OUTPUT.mqh)
- [$o$imple.ini](file://MT/tester/$o$imple.ini)
- [metaeditor.ini](file://MT/MQL4/Profiles/metaeditor.ini)
- [label_main.py](file://processing/label_main.py)
- [AGENTS.md](file://AGENTS.md)
- [API/README.md](file://API/README.md)
- [ML/README.md](file://ML/README.md)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Development Environment Setup](#development-environment-setup)
4. [Python Dependencies and Virtual Environment](#python-dependencies-and-virtual-environment)
5. [MetaTrader Platform Configuration](#metatrader-platform-configuration)
6. [Machine Learning Model Preparation](#machine-learning-model-preparation)
7. [API Service Configuration](#api-service-configuration)
8. [Trading Environment Validation](#trading-environment-validation)
9. [Platform-Specific Considerations](#platform-specific-considerations)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Configuration Reference](#configuration-reference)
12. [Initial Setup Validation](#initial-setup-validation)

## Introduction
This document provides comprehensive installation and setup instructions for the SoSimple trading bot. It covers environment preparation, dependency installation, MetaTrader platform configuration, API service setup, and trading environment validation. The guide is designed for developers and traders who want to deploy the ML-powered trading system across Windows, Linux, and macOS platforms.

## System Requirements
- Python 3.10+ (recommended: 3.11+ for API compatibility)
- Operating Systems: Windows, Linux, macOS
- GPU support recommended for ML inference (CUDA 12.1 compatible)
- Minimum RAM: 8GB (16GB+ recommended for training)
- Disk Space: 5GB+ for datasets and models
- Network connectivity for model downloads (if applicable)

## Development Environment Setup
Follow these steps to prepare your development environment:

### Step 1: Create Python Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate
```

### Step 2: Upgrade pip
```bash
python -m pip install --upgrade pip
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**Section sources**
- [README.md:11-19](file://README.md#L11-L19)
- [requirements.txt:1-17](file://requirements.txt#L1-L17)

## Python Dependencies and Virtual Environment
The project requires the following key dependencies:

### Core Scientific Stack
- pandas>=2.0.0: Data manipulation and analysis
- numpy>=1.24.0: Numerical computing foundation
- scikit-learn>=1.3.0: Machine learning utilities
- scipy>=1.10.0: Scientific computing
- matplotlib>=3.7.0 & seaborn>=0.12.0: Data visualization

### Machine Learning Frameworks
- torch>=2.0.0 (with CUDA 12.1 support): Neural network framework
- xgboost>=1.7.0: Gradient boosting
- lightgbm>=3.3.0: Fast gradient boosting
- optuna>=3.5.0: Hyperparameter optimization

### Web Services
- fastapi>=0.110.0: High-performance web framework
- uvicorn>=0.29.0: ASGI server for API deployment
- pydantic>=2.7.0: Data validation and settings management

### Development Tools
- jupyter>=1.0.0, ipykernel>=6.0.0: Interactive development
- nbconvert>=7.0.0: Notebook conversion

**Section sources**
- [requirements.txt:1-17](file://requirements.txt#L1-L17)

## MetaTrader Platform Configuration
Configure MetaTrader 4 and 5 for SoSimple trading bot integration:

### MT4 Configuration
1. **Expert Advisor Placement**
   - Copy `$o$imple.mq4` to `MT4/Experts/` directory
   - Place compiled expert in `MT4/Experts/` folder

2. **Library Dependencies**
   - Include required header files from `MT4/Include/`
   - Ensure `lib_PIC.mqh` and related libraries are available

3. **Input Parameters**
   - Configure trading parameters in expert advisor inputs
   - Set risk management settings (MM, Risk, MaxPositions)
   - Adjust ML optimization parameters (ML_MinRatio, ML_MaxRatio, etc.)

### MT5 Configuration
1. **Expert Advisor Setup**
   - Copy `$o$imple.mq5` to `MT5/Experts/` directory
   - Compile and place in `MT5/Experts/` folder

2. **Parameter Synchronization**
   - Use `SyncInputs()` function for parameter synchronization
   - Ensure compatibility between MT4 and MT5 parameter sets

### Signal Integration
The expert advisors support multiple signal types:
- ML_TRADE (ML regression_updn signals)
- ML_TRADE_TB (Triple Barrier with fixed SL/TP)
- Traditional pattern recognition signals

**Section sources**
- [$o$imple.mq4:1-149](file://MT/MQL4/Experts/$o$imple.mq4#L1-L149)
- [$o$imple.mq5:1-157](file://MT/MQL5/Experts/$o$imple.mq5#L1-L157)
- [INPUT.mqh:14-21](file://MT/MQL4/Include/INPUT.mqh#L14-L21)

## Machine Learning Model Preparation
Prepare ML models for real-time trading:

### Model Loading Process
1. **Checkpoint Location**
   - Models are loaded from `ML/checkpoints/` directory
   - Required files: `transformer_updn_best.pt` or equivalent

2. **Model Configuration**
   - Default settings: transformer architecture, regression_updn task
   - Horizon: 12 hours, Theta threshold: 2.665
   - Sequence length: 20 (from Optuna best parameters)

### Data Preprocessing Pipeline
The ML service expects preprocessed fractal sequences:
1. **Fractal Format**: Exactly 100 fractals per sequence
2. **ATR Parameter**: Slow ATR value for scaling
3. **Live-safe Processing**: Row-wise normalization without leakage

### Training and Evaluation
- Training scripts available in `ML/` directory
- Model evaluation with out-of-sample testing
- Hyperparameter optimization using Optuna

**Section sources**
- [api_server.py:28-88](file://API/api_server.py#L28-L88)
- [ML/README.md:88-108](file://ML/README.md#L88-L108)

## API Service Configuration
Configure the REST API for ML signal delivery:

### API Endpoints
- `GET /`: Health check endpoint
- `POST /predict`: Main prediction endpoint

### Request Format
The `/predict` endpoint accepts:
```json
{
  "atr_slow": 14.5,
  "fractals": [
    "T:P:Dir:Frnt:Back:...",
    // 100 fractal strings
  ]
}
```

### Response Format
```json
{
  "signal": 1,  // 1=BUY, -1=SELL, 0=FLAT
  "pred_up": 0.75,
  "pred_dn": 0.25,
  "ratio_up": 3.0,
  "ratio_dn": 0.33,
  "theta": 2.665,
  "horizon": 12
}
```

### Deployment Options
- Local development: `uvicorn API.api_server:app --host 127.0.0.1 --port 8000`
- Production deployment: Configure reverse proxy and SSL termination

**Section sources**
- [api_server.py:103-169](file://API/api_server.py#L103-L169)
- [API/README.md:25-92](file://API/README.md#L25-L92)

## Trading Environment Validation
Validate your trading setup before live deployment:

### MT4 Tester Configuration
1. **Configuration File**
   - Use `$o$imple.ini` for tester parameters
   - Set positions, deposit, and optimization settings

2. **Parameter Ranges**
   - ML optimization parameters: MinRatio (2.0-7.0), MaxRatio (3.5-6.0)
   - Risk parameters: Min_SL_ATR (1.0-6.0), Trail parameters (1.0-6.0)
   - Position sizing: MaxPositions (1-10)

### Signal Generation Workflow
1. **Data Preparation**
   ```bash
   python processing/label_main.py --input MT/MQL4/Files/Nero.csv
   ```

2. **Signal Export**
   ```bash
   python -m API.generate_signals --theta 3.0 --horizon 24
   ```

3. **Validation Steps**
   - Verify signal CSV generation in `MT/MQL4/Files/`
   - Check MT4 tester log for signal execution
   - Monitor API service health endpoint

### Real-time Monitoring
- API health check: `curl http://localhost:8000/`
- Signal validation: Compare generated signals with MT4 tester output
- Performance monitoring: Track inference latency and accuracy metrics

**Section sources**
- [$o$imple.ini:1-353](file://MT/tester/$o$imple.ini#L1-L353)
- [label_main.py:205-332](file://processing/label_main.py#L205-L332)
- [API/README.md:25-92](file://API/README.md#L25-L92)

## Platform-Specific Considerations

### Windows Configuration
- Python virtual environment activation: `.venv\Scripts\activate`
- MetaQuotes Terminal installation path: `C:\Program Files\MetaQuotes\Terminal\`
- File path separators: Use forward slashes or raw strings
- GPU drivers: Ensure CUDA 12.1 compatible drivers installed

### Linux/macOS Configuration
- Virtual environment: `source .venv/bin/activate`
- Home directory structure: `~/git/SoSimple/`
- Permission requirements: Ensure write access to project directories
- Package dependencies: Install system packages for PyTorch compilation if needed

### Cross-Platform Compatibility
- All Python scripts use forward slashes for paths
- Relative imports work consistently across platforms
- File encoding: UTF-8 for CSV and configuration files

## Troubleshooting Guide

### Common Installation Issues

**Virtual Environment Problems**
- Issue: `python: command not found`
  - Solution: Use `python3` or install Python 3.10+
- Issue: Permission denied during activation
  - Solution: Run `chmod +x .venv/bin/activate` (Linux/macOS)

**Dependency Installation Failures**
- Issue: PyTorch installation errors
  - Solution: Install appropriate CUDA version or use CPU-only build
- Issue: Compilation errors with scientific packages
  - Solution: Install system dependencies (BLAS, LAPACK) before pip install

**MetaTrader Integration Issues**
- Issue: Expert advisor not loading
  - Solution: Verify file placement in correct Experts directory
  - Check compiler warnings and ensure all required headers are included
- Issue: Signals not appearing in tester
  - Solution: Verify `ml_signals.csv` generation and proper file permissions

**API Service Problems**
- Issue: Port already in use
  - Solution: Change port in uvicorn command or kill existing process
- Issue: Model loading failures
  - Solution: Verify checkpoint file exists in `ML/checkpoints/` directory

### Validation Checklist
- [ ] Python version: 3.10+
- [ ] Virtual environment activated
- [ ] All dependencies installed successfully
- [ ] ML model checkpoint present
- [ ] API service running and responding to health checks
- [ ] MT4/MT5 expert advisor compiled and placed correctly
- [ ] Signal CSV generation working
- [ ] Tester configuration properly set up

**Section sources**
- [AGENTS.md:30-34](file://AGENTS.md#L30-L34)

## Configuration Reference

### Environment Variables
The system uses minimal environment configuration:
- Virtual environment path: `.venv/` (project-local)
- Project root: Repository base directory
- Data directories: Automatic creation under project root

### Configuration Files
1. **requirements.txt**: Dependency specification
2. **MT/tester/$o$imple.ini**: MT4 tester parameters
3. **MT/MQL4/Profiles/metaeditor.ini**: MetaQuotes editor settings
4. **API/api_server.py**: ML service configuration
5. **processing/label_main.py**: Data processing parameters

### Parameter Categories
- **Risk Management**: MM, Risk, MaxPositions, MaxRisk
- **ML Optimization**: ML_MinRatio, ML_MaxRatio, ML_MaxRR, ML_RR_Mode
- **Position Sizing**: D, Stp, Prf parameters
- **Time Filters**: tk, T0, T1, tp parameters
- **Output Controls**: oImp, oFlt, oGlb, oLoc parameters

**Section sources**
- [$o$imple.ini:9-333](file://MT/tester/$o$imple.ini#L9-L333)
- [metaeditor.ini:1-330](file://MT/MQL4/Profiles/metaeditor.ini#L1-L330)

## Initial Setup Validation

### Step-by-Step Verification
1. **Environment Check**
   ```bash
   # Verify Python and dependencies
   python --version
   pip list | grep -E "(torch|fastapi|pandas)"
   ```

2. **API Service Test**
   ```bash
   # Start API service
   uvicorn API.api_server:app --host 127.0.0.1 --port 8000 --log-level error
   
   # Test health endpoint
   curl http://localhost:8000/
   ```

3. **Data Processing Validation**
   ```bash
   # Generate sample labels
   python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug
   ```

4. **MT4 Integration Test**
   - Load expert advisor in MT4 terminal
   - Verify signal generation in `MT/MQL4/Files/ml_signals.csv`
   - Run basic tester with `$o$imple.ini` configuration

5. **Model Loading Verification**
   - Check model checkpoint availability
   - Verify tensor shape compatibility (100 fractals × 20 features)
   - Test inference with sample data

### Expected Outcomes
- API responds with status "ok"
- Data processing completes without errors
- MT4 expert advisor loads successfully
- ML signals appear in CSV output
- Model inference executes without loading errors

**Section sources**
- [README.md:11-19](file://README.md#L11-L19)
- [API/README.md:25-92](file://API/README.md#L25-L92)
- [ML/README.md:88-108](file://ML/README.md#L88-L108)