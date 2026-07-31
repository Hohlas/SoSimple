# Core Concepts

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [multi_scale_fractal_features.py](file://ML/multi_scale_fractal_features.py)
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [entry_path_v1_quantile_task.py](file://ML/entry_path_v1_quantile_task.py)
- [lib_pic_geometry_feature_bank.py](file://ML/lib_pic_geometry_feature_bank.py)
- [lib_pic_path_reaction_feature_bank.py](file://ML/lib_pic_path_reaction_feature_bank.py)
- [fractal_preprocessing.py](file://processing/fractal_preprocessing.py)
- [label_main.py](file://processing/label_main.py)
- [train.py](file://ML/train.py)
- [conformal/calibrate.py](file://ML/conformal/calibrate.py)
- [models/entry_path_transformer.py](file://ML/models/entry_path_transformer.py)
- [models/entry_path_dual_stream_transformer.py](file://ML/models/entry_path_dual_stream_transformer.py)
- [models/entry_path_v1_quantile_transformer.py](file://ML/models/entry_path_v1_quantile_transformer.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [validation_freeze.py](file://ML/validation_freeze.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)

## Introduction
This document explains the core concepts of the SoSimple trading system with a focus on:
- Fractal analysis for multi-scale price pattern recognition
- Triple barrier method for label generation and exit strategies
- Entry path methodology for signal quality assessment
- Feature engineering using geometric and path-based indicators
- Machine learning paradigm including transformer models, conformal prediction for uncertainty quantification, and walk-forward validation

The goal is to provide both theoretical foundations and practical applications for traders and developers, grounded in the actual implementation files of the repository.

## Project Structure
SoSimple organizes its code into clear layers:
- Data processing and labeling (processing/)
- ML feature engineering and tasks (ML/)
- Model definitions (ML/models/)
- Conformal calibration utilities (ML/conformal/)
- Benchmarks and experiments (ML/baseline/, ML/reports/)
- API and telemetry (API/)
- MT4/MT5 integration (MT/)

```mermaid
graph TB
subgraph "Data Processing"
FP["fractal_preprocessing.py"]
LM["label_main.py"]
end
subgraph "ML Core"
MSF["multi_scale_fractal_features.py"]
LGB["lib_pic_geometry_feature_bank.py"]
LPB["lib_pic_path_reaction_feature_bank.py"]
EPT["entry_path_v1_quantile_task.py"]
TRN["train.py"]
end
subgraph "Models"
T1["entry_path_transformer.py"]
T2["entry_path_dual_stream_transformer.py"]
TQ["entry_path_v1_quantile_transformer.py"]
end
subgraph "Calibration & Validation"
CAL["conformal/calibrate.py"]
VF["validation_freeze.py"]
BENCH["benchmark_entry_path_v2.py"]
end
FP --> MSF
LM --> EPT
MSF --> LGB
MSF --> LPB
EPT --> T1
EPT --> T2
EPT --> TQ
TQ --> CAL
TRN --> T1
TRN --> T2
TRN --> TQ
BENCH --> VF
```

**Diagram sources**
- [fractal_preprocessing.py](file://processing/fractal_preprocessing.py)
- [label_main.py](file://processing/label_main.py)
- [multi_scale_fractal_features.py](file://ML/multi_scale_fractal_features.py)
- [lib_pic_geometry_feature_bank.py](file://ML/lib_pic_geometry_feature_bank.py)
- [lib_pic_path_reaction_feature_bank.py](file://ML/lib_pic_path_reaction_feature_bank.py)
- [entry_path_v1_quantile_task.py](file://ML/entry_path_v1_quantile_task.py)
- [train.py](file://ML/train.py)
- [entry_path_transformer.py](file://ML/models/entry_path_transformer.py)
- [entry_path_dual_stream_transformer.py](file://ML/models/entry_path_dual_stream_transformer.py)
- [entry_path_v1_quantile_transformer.py](file://ML/models/entry_path_v1_quantile_transformer.py)
- [calibrate.py](file://ML/conformal/calibrate.py)
- [validation_freeze.py](file://ML/validation_freeze.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)

**Section sources**
- [README.md](file://README.md)

## Core Components
- Multi-scale fractal features: Extracts hierarchical structures across timeframes to capture recurring patterns at multiple scales.
- Triple barrier labeling: Defines upper, lower, and time barriers to generate robust labels and exit conditions.
- Entry path methodology: Assesses signal quality by analyzing the trajectory from entry to outcome, enabling better filtering and ranking.
- Geometric and path-based features: Encodes shape and movement characteristics of price paths to enrich model inputs.
- Transformer models: Sequence models that attend over price paths and features to predict outcomes or quantiles.
- Conformal prediction: Provides calibrated uncertainty estimates around predictions.
- Walk-forward validation: Ensures temporal integrity during training and evaluation.

**Section sources**
- [multi_scale_fractal_features.py](file://ML/multi_scale_fractal_features.py)
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [entry_path_v1_quantile_task.py](file://ML/entry_path_v1_quantile_task.py)
- [lib_pic_geometry_feature_bank.py](file://ML/lib_pic_geometry_feature_bank.py)
- [lib_pic_path_reaction_feature_bank.py](file://ML/lib_pic_path_reaction_feature_bank.py)
- [entry_path_transformer.py](file://ML/models/entry_path_transformer.py)
- [entry_path_dual_stream_transformer.py](file://ML/models/entry_path_dual_stream_transformer.py)
- [entry_path_v1_quantile_transformer.py](file://ML/models/entry_path_v1_quantile_transformer.py)
- [calibrate.py](file://ML/conformal/calibrate.py)
- [validation_freeze.py](file://ML/validation_freeze.py)

## Architecture Overview
The SoSimple pipeline integrates data preprocessing, feature engineering, labeling, modeling, calibration, and validation into a cohesive workflow.

```mermaid
sequenceDiagram
participant Raw as "Raw Price Data"
participant Proc as "Fractal Preprocessing"
participant Label as "Label Generation"
participant Feat as "Feature Engineering"
participant Task as "Entry Path Task"
participant Model as "Transformer Models"
participant Calib as "Conformal Calibration"
participant Eval as "Walk-Forward Validation"
Raw->>Proc : "Load OHLCV series"
Proc-->>Feat : "Multi-scale fractal features"
Raw->>Label : "Triple barrier rules"
Label-->>Task : "Outcome labels and exits"
Feat-->>Task : "Geometric/path features"
Task-->>Model : "Sequence inputs + labels"
Model-->>Calib : "Predictions + residuals"
Calib-->>Eval : "Calibrated quantiles"
Eval-->>Eval : "Temporal splits and metrics"
```

**Diagram sources**
- [fractal_preprocessing.py](file://processing/fractal_preprocessing.py)
- [label_main.py](file://processing/label_main.py)
- [multi_scale_fractal_features.py](file://ML/multi_scale_fractal_features.py)
- [lib_pic_geometry_feature_bank.py](file://ML/lib_pic_geometry_feature_bank.py)
- [lib_pic_path_reaction_feature_bank.py](file://ML/lib_pic_path_reaction_feature_bank.py)
- [entry_path_v1_quantile_task.py](file://ML/entry_path_v1_quantile_task.py)
- [entry_path_transformer.py](file://ML/models/entry_path_transformer.py)
- [entry_path_v1_quantile_transformer.py](file://ML/models/entry_path_v1_quantile_transformer.py)
- [calibrate.py](file://ML/conformal/calibrate.py)
- [validation_freeze.py](file://ML/validation_freeze.py)

## Detailed Component Analysis

### Fractal Analysis for Multi-Scale Pattern Recognition
Fractals identify local extrema and structure across multiple timeframes, enabling the system to recognize patterns that repeat at different scales. The implementation extracts hierarchical peaks and troughs, aligns them temporally, and constructs features that capture their relative geometry and timing.

```mermaid
flowchart TD
Start(["Start"]) --> Load["Load OHLCV Series"]
Load --> Detect["Detect Local Extrema"]
Detect --> Scale{"Select Timeframe"}
Scale --> |Higher| BuildH["Build Higher-Level Fractals"]
Scale --> |Lower| BuildL["Build Lower-Level Fractals"]
BuildH --> Align["Align Across Scales"]
BuildL --> Align
Align --> Features["Compute Relative Geometry<br/>and Timing Features"]
Features --> Output["Output Multi-Scale Features"]
Output --> End(["End"])
```

**Diagram sources**
- [fractal_preprocessing.py](file://processing/fractal_preprocessing.py)
- [multi_scale_fractal_features.py](file://ML/multi_scale_fractal_features.py)

**Section sources**
- [fractal_preprocessing.py](file://processing/fractal_preprocessing.py)
- [multi_scale_fractal_features.py](file://ML/multi_scale_fractal_features.py)

### Triple Barrier Method for Labeling and Exit Strategies
The triple barrier method defines three boundaries: an upper take-profit barrier, a lower stop-loss barrier, and a time-based barrier. Labels are generated based on which barrier is hit first, providing robust targets and exit conditions.

```mermaid
flowchart TD
Start(["Start"]) --> Init["Initialize Barriers"]
Init --> Upper["Set Upper Take-Profit"]
Init --> Lower["Set Lower Stop-Loss"]
Init --> Time["Set Time Horizon"]
Upper --> Monitor["Monitor Price Path"]
Lower --> Monitor
Time --> Monitor
Monitor --> Hit{"Barrier Hit?"}
Hit --> |Upper| LabelTP["Label Take-Profit"]
Hit --> |Lower| LabelSL["Label Stop-Loss"]
Hit --> |Time| LabelTO["Label Time-Out"]
LabelTP --> End(["End"])
LabelSL --> End
LabelTO --> End
```

**Diagram sources**
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [label_main.py](file://processing/label_main.py)

**Section sources**
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [label_main.py](file://processing/label_main.py)

### Entry Path Methodology for Signal Quality Assessment
Entry path methodology evaluates the trajectory from entry to outcome, capturing how price moves after signals. It supports filtering low-quality entries and ranking signals based on path characteristics.

```mermaid
sequenceDiagram
participant Sig as "Signal Generator"
participant Path as "Entry Path Analyzer"
participant Q as "Quantile Estimator"
participant Filter as "Quality Filter"
Sig-->>Path : "Entry timestamp + initial state"
Path-->>Path : "Track price path until exit"
Path-->>Q : "Compute path statistics"
Q-->>Filter : "Quantile scores"
Filter-->>Sig : "Accept/Reject decision"
```

**Diagram sources**
- [entry_path_v1_quantile_task.py](file://ML/entry_path_v1_quantile_task.py)

**Section sources**
- [entry_path_v1_quantile_task.py](file://ML/entry_path_v1_quantile_task.py)

### Feature Engineering: Geometric and Path-Based Indicators
Geometric features encode shape properties like curvature, amplitude, and symmetry of price segments. Path-based features capture dynamics such as momentum, volatility, and directional persistence. Together, they form rich inputs for sequence models.

```mermaid
classDiagram
class GeometryFeatures {
+compute_curvature(path) float
+compute_amplitude(path) float
+compute_symmetry(path) float
}
class PathFeatures {
+compute_momentum(path) float
+compute_volatility(path) float
+compute_direction_persistence(path) float
}
class FeatureBank {
+combine(geometry, path) array
+normalize(features) array
}
GeometryFeatures <.. FeatureBank : "uses"
PathFeatures <.. FeatureBank : "uses"
```

**Diagram sources**
- [lib_pic_geometry_feature_bank.py](file://ML/lib_pic_geometry_feature_bank.py)
- [lib_pic_path_reaction_feature_bank.py](file://ML/lib_pic_path_reaction_feature_bank.py)

**Section sources**
- [lib_pic_geometry_feature_bank.py](file://ML/lib_pic_geometry_feature_bank.py)
- [lib_pic_path_reaction_feature_bank.py](file://ML/lib_pic_path_reaction_feature_bank.py)

### Transformer Models and Attention Mechanisms
Transformer models process sequences of price paths and features, using attention to weigh relevant parts of the history. Variants include single-stream and dual-stream architectures, with quantile output heads for uncertainty-aware predictions.

```mermaid
classDiagram
class EntryPathTransformer {
+encode_sequence(inputs) tensor
+attention_heads() list
+predict(output_head) tensor
}
class DualStreamTransformer {
+encode_price_stream(price_seq) tensor
+encode_feature_stream(feature_seq) tensor
+fuse_streams() tensor
+predict(output_head) tensor
}
class QuantileTransformer {
+quantile_heads(num_q) list
+calibrate_residuals(residuals) dict
+predict_quantiles(inputs) array
}
EntryPathTransformer <|-- DualStreamTransformer : "extends"
EntryPathTransformer <|-- QuantileTransformer : "specialized"
```

**Diagram sources**
- [entry_path_transformer.py](file://ML/models/entry_path_transformer.py)
- [entry_path_dual_stream_transformer.py](file://ML/models/entry_path_dual_stream_transformer.py)
- [entry_path_v1_quantile_transformer.py](file://ML/models/entry_path_v1_quantile_transformer.py)

**Section sources**
- [entry_path_transformer.py](file://ML/models/entry_path_transformer.py)
- [entry_path_dual_stream_transformer.py](file://ML/models/entry_path_dual_stream_transformer.py)
- [entry_path_v1_quantile_transformer.py](file://ML/models/entry_path_v1_quantile_transformer.py)

### Conformal Prediction for Uncertainty Quantification
Conformal prediction calibrates model outputs to produce statistically valid prediction intervals. It uses residuals from a calibration set to adjust quantile estimates, improving reliability under distribution shifts.

```mermaid
flowchart TD
Start(["Start"]) --> Train["Train Base Model"]
Train --> CalSet["Prepare Calibration Set"]
CalSet --> Resid["Compute Residuals"]
Resid --> Quant["Estimate Quantiles"]
Quant --> Apply["Apply to Test Predictions"]
Apply --> Intervals["Generate Prediction Intervals"]
Intervals --> End(["End"])
```

**Diagram sources**
- [calibrate.py](file://ML/conformal/calibrate.py)

**Section sources**
- [calibrate.py](file://ML/conformal/calibrate.py)

### Walk-Forward Validation
Walk-forward validation ensures temporal integrity by training on past data and testing on future windows. It prevents look-ahead bias and provides realistic performance estimates.

```mermaid
flowchart TD
Start(["Start"]) --> Split["Split Data Chronologically"]
Split --> TrainWin["Train on Window 1"]
TrainWin --> TestWin["Test on Window 2"]
TestWin --> Shift["Shift Windows Forward"]
Shift --> TrainWin
Shift --> End(["End"])
```

**Diagram sources**
- [validation_freeze.py](file://ML/validation_freeze.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)

**Section sources**
- [validation_freeze.py](file://ML/validation_freeze.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)

## Dependency Analysis
The system exhibits modular dependencies with clear separation between data processing, feature engineering, modeling, and validation.

```mermaid
graph LR
FP["fractal_preprocessing.py"] --> MSF["multi_scale_fractal_features.py"]
LM["label_main.py"] --> EPT["entry_path_v1_quantile_task.py"]
MSF --> LGB["lib_pic_geometry_feature_bank.py"]
MSF --> LPB["lib_pic_path_reaction_feature_bank.py"]
EPT --> T1["entry_path_transformer.py"]
EPT --> T2["entry_path_dual_stream_transformer.py"]
EPT --> TQ["entry_path_v1_quantile_transformer.py"]
TQ --> CAL["conformal/calibrate.py"]
TRN["train.py"] --> T1
TRN --> T2
TRN --> TQ
BENCH["benchmark_entry_path_v2.py"] --> VF["validation_freeze.py"]
```

**Diagram sources**
- [fractal_preprocessing.py](file://processing/fractal_preprocessing.py)
- [label_main.py](file://processing/label_main.py)
- [multi_scale_fractal_features.py](file://ML/multi_scale_fractal_features.py)
- [lib_pic_geometry_feature_bank.py](file://ML/lib_pic_geometry_feature_bank.py)
- [lib_pic_path_reaction_feature_bank.py](file://ML/lib_pic_path_reaction_feature_bank.py)
- [entry_path_v1_quantile_task.py](file://ML/entry_path_v1_quantile_task.py)
- [entry_path_transformer.py](file://ML/models/entry_path_transformer.py)
- [entry_path_dual_stream_transformer.py](file://ML/models/entry_path_dual_stream_transformer.py)
- [entry_path_v1_quantile_transformer.py](file://ML/models/entry_path_v1_quantile_transformer.py)
- [calibrate.py](file://ML/conformal/calibrate.py)
- [train.py](file://ML/train.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [validation_freeze.py](file://ML/validation_freeze.py)

**Section sources**
- [train.py](file://ML/train.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)

## Performance Considerations
- Use efficient fractal detection algorithms to minimize computational overhead.
- Optimize feature computation by caching intermediate results where possible.
- Employ mixed precision training for transformers to accelerate convergence.
- Leverage parallelization in walk-forward validation to reduce total runtime.
- Monitor memory usage when handling large sequences in dual-stream models.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Fractal misalignment: Ensure consistent timeframe selection and extremum detection parameters.
- Label leakage: Verify that triple barrier logic does not peek into future data.
- Overfitting in transformers: Regularize attention heads and use dropout appropriately.
- Calibration drift: Recalibrate quantiles periodically as market conditions change.
- Walk-forward errors: Confirm chronological splits and avoid data leakage between windows.

**Section sources**
- [fractal_preprocessing.py](file://processing/fractal_preprocessing.py)
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [entry_path_v1_quantile_transformer.py](file://ML/models/entry_path_v1_quantile_transformer.py)
- [calibrate.py](file://ML/conformal/calibrate.py)
- [validation_freeze.py](file://ML/validation_freeze.py)

## Conclusion
SoSimple integrates fractal analysis, triple barrier labeling, entry path methodology, and transformer-based modeling within a robust framework that emphasizes uncertainty quantification and temporal integrity. By combining geometric and path-based features with conformal prediction and walk-forward validation, it offers a comprehensive approach to algorithmic trading that balances theoretical rigor with practical applicability.

[No sources needed since this section summarizes without analyzing specific files]