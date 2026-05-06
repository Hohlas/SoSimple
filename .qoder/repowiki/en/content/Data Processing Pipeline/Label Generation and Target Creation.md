# Label Generation and Target Creation

<cite>
**Referenced Files in This Document**
- [label_signals.py](file://processing/label_signals.py)
- [label_main.py](file://processing/label_main.py)
- [generate_signals.py](file://API/generate_signals.py)
- [export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [signal_research.py](file://API/signal_research.py)
- [signal_quality_research.py](file://API/signal_quality_research.py)
- [take_skip_trailing_stop_v2_task.py](file://ML/take_skip_trailing_stop_v2_task.py)
- [trailing_stop_target_task.py](file://ML/trailing_stop_target_task.py)
- [trailing_stop_target_quantile_task.py](file://ML/trailing_stop_target_quantile_task.py)
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
10. [Appendices](#appendices)

## Introduction
This document explains the label generation system that creates supervised learning targets from market data. It covers:
- Signal labeling methodology (classification, regression, and outcome-aligned targets)
- Entry path classification and take/skip decisions
- Trailing stop target creation and quantile-based labeling
- Integration with the triple barrier method for position management, early timeout mechanisms, and volatility-adjusted targets
- Practical workflows, validation procedures, and performance impact analysis
- Label quality assessment, bias detection, and optimization strategies across market regimes

## Project Structure
The label generation system spans preprocessing, labeling, normalization, inference, and research/reporting:
- Preprocessing and labeling: processing/label_signals.py and processing/label_main.py
- Inference and export: API/generate_signals.py and API/export_*_signals.py
- Research and validation: API/signal_research.py and API/signal_quality_research.py
- Task-specific target definitions and evaluation: ML/*_task.py files

```mermaid
graph TB
subgraph "Preprocessing & Labeling"
LS["label_signals.py"]
LM["label_main.py"]
end
subgraph "Inference & Export"
GS["generate_signals.py"]
EP["export_entry_path_v1_signals.py"]
TS["export_take_skip_trailing_stop_v2_signals.py"]
end
subgraph "Research & Validation"
SR["signal_research.py"]
SQR["signal_quality_research.py"]
end
subgraph "Task Definitions"
TSK1["take_skip_trailing_stop_v2_task.py"]
TSK2["trailing_stop_target_task.py"]
TSK3["trailing_stop_target_quantile_task.py"]
end
LS --> LM
LM --> GS
GS --> EP
GS --> TS
SR --> GS
SQR --> GS
TSK1 --> GS
TSK2 --> GS
TSK3 --> GS
```

**Diagram sources**
- [label_signals.py:147-325](file://processing/label_signals.py#L147-L325)
- [label_main.py:205-332](file://processing/label_main.py#L205-L332)
- [generate_signals.py:342-745](file://API/generate_signals.py#L342-L745)
- [export_entry_path_v1_signals.py:72-123](file://API/export_entry_path_v1_signals.py#L72-L123)
- [export_take_skip_trailing_stop_v2_signals.py:179-323](file://API/export_take_skip_trailing_stop_v2_signals.py#L179-L323)
- [signal_research.py:170-210](file://API/signal_research.py#L170-L210)
- [signal_quality_research.py:75-116](file://API/signal_quality_research.py#L75-L116)
- [take_skip_trailing_stop_v2_task.py:37-111](file://ML/take_skip_trailing_stop_v2_task.py#L37-L111)
- [trailing_stop_target_task.py:13-25](file://ML/trailing_stop_target_task.py#L13-L25)
- [trailing_stop_target_quantile_task.py:12-107](file://ML/trailing_stop_target_quantile_task.py#L12-L107)

**Section sources**
- [label_signals.py:147-325](file://processing/label_signals.py#L147-L325)
- [label_main.py:205-332](file://processing/label_main.py#L205-L332)

## Core Components
- Fractal parsing and timeline construction for strong level detection and predict labeling
- Up/Dn horizon-based targets and outcome-aligned targets (trade outcomes)
- Triple barrier labels derived from raw MFE/MAE values
- Entry path v1 targets and frequency features
- Trailing stop targets with multiple horizons and x-multipliers
- Quantile-based trailing stop targets for distribution learning

Key responsibilities:
- label_signals.py: signal classification, predict regression, up/dn targets, outcome targets, triple barrier, entry path, trailing stop
- label_main.py: orchestration of sorting, labeling, normalization, splitting, saving datasets
- generate_signals.py: inference pipeline for generating ML signals and exporting predictions
- export_*_signals.py: applying frozen rules to convert predictions into runtime signals
- signal_research.py and signal_quality_research.py: post-hoc research and quality filtering
- ML/*_task.py: task-specific target definitions and evaluation metrics

**Section sources**
- [label_signals.py:43-118](file://processing/label_signals.py#L43-L118)
- [label_signals.py:360-529](file://processing/label_signals.py#L360-L529)
- [label_signals.py:548-587](file://processing/label_signals.py#L548-L587)
- [label_signals.py:614-755](file://processing/label_signals.py#L614-L755)
- [label_main.py:205-332](file://processing/label_main.py#L205-L332)
- [generate_signals.py:342-745](file://API/generate_signals.py#L342-L745)
- [export_entry_path_v1_signals.py:72-123](file://API/export_entry_path_v1_signals.py#L72-L123)
- [export_take_skip_trailing_stop_v2_signals.py:179-323](file://API/export_take_skip_trailing_stop_v2_signals.py#L179-L323)
- [signal_research.py:212-364](file://API/signal_research.py#L212-L364)
- [signal_quality_research.py:75-116](file://API/signal_quality_research.py#L75-L116)
- [take_skip_trailing_stop_v2_task.py:37-111](file://ML/take_skip_trailing_stop_v2_task.py#L37-L111)
- [trailing_stop_target_task.py:13-25](file://ML/trailing_stop_target_task.py#L13-L25)
- [trailing_stop_target_quantile_task.py:12-107](file://ML/trailing_stop_target_quantile_task.py#L12-L107)

## Architecture Overview
End-to-end pipeline from raw features to labeled datasets and inference:

```mermaid
sequenceDiagram
participant Raw as "Raw Features (Nero.csv)"
participant Sort as "Sort Fractals"
participant Label as "Label All"
participant Updn as "Label Up/Dn"
participant Outcome as "Outcome Targets"
participant TB as "Triple Barrier"
participant Entry as "Entry Path v1"
participant Trail as "Trailing Stop Targets"
participant Norm as "Normalize Rowwise"
participant Split as "Split Train/Val/Test"
participant Save as "Save Datasets"
Raw->>Sort : Load and sort fractals
Sort->>Label : Sorted CSV
Label->>Updn : Add up_3..dn_48
Updn->>Outcome : Compute trade outcomes
Outcome->>TB : Compute first-hit outcomes
TB->>Entry : Build entry path features
Entry->>Trail : Compute trailing stop PnL ATR
Trail->>Norm : Normalize features
Norm->>Split : Split datasets
Split->>Save : Write train/validation/test
```

**Diagram sources**
- [label_main.py:254-287](file://processing/label_main.py#L254-L287)
- [label_signals.py:360-529](file://processing/label_signals.py#L360-L529)
- [label_signals.py:548-587](file://processing/label_signals.py#L548-L587)
- [label_signals.py:614-755](file://processing/label_signals.py#L614-L755)

## Detailed Component Analysis

### Signal Classification and Predict Regression
- Strong level detection: identifies "strong" fractals and marks signal column (+1/-1)
- Predict regression: computes maximum adverse excursion until barrier break, adjusted by signal direction
- Complexity: O(N·K) pre-scan plus per-row timeline traversal; worst-case O(N^2) for predict scanning

```mermaid
flowchart TD
Start(["Start label_all"]) --> Scan["Scan all rows<br/>collect timelines"]
Scan --> MarkSignal{"fractal0 strong?"}
MarkSignal --> |Yes| SetSignal["Set signal"]
MarkSignal --> |No| NextRow["Next row"]
SetSignal --> NextRow
NextRow --> PredictScan["For each row:<br/>scan timeline after row"]
PredictScan --> TimelineCheck{"Timeline contiguous?"}
TimelineCheck --> |No| Drop["Drop fractal"]
TimelineCheck --> |Yes| MaxBack["Track max back"]
MaxBack --> WasBroken{"Barrier broken?"}
WasBroken --> |Yes| Stop["Stop scanning"]
WasBroken --> |No| Continue["Continue"]
Continue --> PredictScan
Stop --> ComputePredict["Compute predict = -max_back * direction"]
Drop --> ComputePredict
ComputePredict --> End(["Write outputs"])
```

**Diagram sources**
- [label_signals.py:147-325](file://processing/label_signals.py#L147-L325)

**Section sources**
- [label_signals.py:147-325](file://processing/label_signals.py#L147-L325)

### Up/Dn Horizon Targets and Outcome-Aligned Targets
- Up/Dn targets: cumulative favorable/ adverse excursions over horizons (3,6,12,24,48)
- Outcome-aligned targets: directional PnL over 12H, favorable/adverse ATR, archetype classification
- Volatility adjustment: ATR-based normalization and thresholds

```mermaid
flowchart TD
UStart(["Start label_updn"]) --> Pass1["Pass 1: bottom-up<br/>track last-seen up/dn per fractal_time"]
Pass1 --> Pass2["Pass 2: top-down lookup<br/>assign to fractal0 rows"]
Pass2 --> UEnd(["Add up_3..dn_48"])
OStart(["Start label_trade_targets"]) --> Fetch["Fetch signal and ATR"]
Fetch --> OHLC{"OHLC provided?"}
OHLC --> |Yes| ComputeOHLC["Compute 12H windows<br/>fav/adv/net PnL ATR"]
OHLC --> |No| ComputeHorizon["Use up_12/dn_12<br/>compute ATR ratios"]
ComputeOHLC --> Arch["Compute archetype_target<br/><= 1.0 adverse ATR"]
ComputeHorizon --> Arch
Arch --> OEnd(["Add trade_* and archetype_target"])
```

**Diagram sources**
- [label_signals.py:360-433](file://processing/label_signals.py#L360-L433)
- [label_signals.py:439-529](file://processing/label_signals.py#L439-L529)

**Section sources**
- [label_signals.py:360-433](file://processing/label_signals.py#L360-L433)
- [label_signals.py:439-529](file://processing/label_signals.py#L439-L529)

### Triple Barrier Method and Early Timeout
- Converts raw MFE/MAE to binary labels for multiple SL/TP grids in ATR units
- Handles ambiguous cases conservatively (both barriers reached)
- Supports path-ordered scanning with OHLC for first-touch outcomes

```mermaid
flowchart TD
TBStart(["Start label_triple_barrier"]) --> Read["Read up_24/dn_24 and ATR"]
Read --> Convert["Convert to ATR units"]
Convert --> Grid["Iterate SL/TP grid"]
Grid --> Buy["Buy: up_atr >= TP AND dn_atr < SL"]
Grid --> Sell["Sell: mirror"]
Buy --> TBEnd(["Add 12 binary labels"])
Sell --> TBEnd
```

**Diagram sources**
- [label_signals.py:548-587](file://processing/label_signals.py#L548-L587)

**Section sources**
- [label_signals.py:548-587](file://processing/label_signals.py#L548-L587)

### Entry Path Classification and Take/Skip Decisions
- Entry path v1 targets: directional returns and favorable/adverse measures over multiple horizons
- Frequency features: engineered features for entry path modeling
- Take/skip/trailing stop v2: converts trailing stop PnL ATR into take/skip decisions using thresholds

```mermaid
sequenceDiagram
participant L as "Labeler"
participant F as "Frequency Features"
participant T as "Take/Skip V2"
L->>F : Add entry path features
F->>T : Compute trail_*_pnl_atr_x*
T->>T : Apply threshold (>= 0.5 ATR)
T-->>L : Binary take/skip labels
```

**Diagram sources**
- [label_signals.py:614-755](file://processing/label_signals.py#L614-L755)
- [take_skip_trailing_stop_v2_task.py:37-111](file://ML/take_skip_trailing_stop_v2_task.py#L37-L111)

**Section sources**
- [label_signals.py:614-755](file://processing/label_signals.py#L614-L755)
- [take_skip_trailing_stop_v2_task.py:37-111](file://ML/take_skip_trailing_stop_v2_task.py#L37-L111)

### Trailing Stop Targets and Quantile-Based Labeling
- Trailing stop targets: PnL expressed in ATR units for multiple horizons and x-multipliers
- Quantile targets: pinball loss and interval coverage for distribution learning
- Evaluation metrics: BCE, Brier score, pinball loss, median interval width, Pearson correlation

```mermaid
flowchart TD
TrailStart(["Start label_trailing_stop_targets"]) --> OHLC["Load OHLC index"]
OHLC --> Iterate["Iterate rows"]
Iterate --> Simulate["Simulate trailing stop exit<br/>per horizon and x-value"]
Simulate --> TrailEnd(["Write trail_*_pnl_atr_x*"])
QuantStart(["Quantile Targets"]) --> Base["Base column: trail_48_pnl_atr_x3"]
Base --> Pinball["Pinball loss @ q10,q50,q90"]
Pinball --> Metrics["Coverage, width, MAE, R"]
Metrics --> QuantEnd(["Export quantile predictions"])
```

**Diagram sources**
- [label_signals.py:757-809](file://processing/label_signals.py#L757-L809)
- [trailing_stop_target_task.py:13-25](file://ML/trailing_stop_target_task.py#L13-L25)
- [trailing_stop_target_quantile_task.py:76-107](file://ML/trailing_stop_target_quantile_task.py#L76-L107)

**Section sources**
- [label_signals.py:757-809](file://processing/label_signals.py#L757-L809)
- [trailing_stop_target_task.py:13-25](file://ML/trailing_stop_target_task.py#L13-L25)
- [trailing_stop_target_quantile_task.py:76-107](file://ML/trailing_stop_target_quantile_task.py#L76-L107)

### Inference Pipeline and Signal Export
- Inference: loads trained models, runs loaders, applies thresholds, writes ml_signals.csv
- Triple barrier signals: probability calibration, expected value selection
- Entry path v1 and trailing stop quantile exports: research-focused CSVs

```mermaid
sequenceDiagram
participant Gen as "generate_signals.py"
participant Model as "Model"
participant Loader as "DataLoader"
participant Export as "Export"
Gen->>Model : Load checkpoint
Gen->>Loader : Create loaders (train/validation/test)
Loader->>Model : Run inference
Model-->>Gen : Predictions
Gen->>Gen : Apply thresholds / calibration
Gen->>Export : Write ml_signals.csv or research CSVs
```

**Diagram sources**
- [generate_signals.py:342-745](file://API/generate_signals.py#L342-L745)

**Section sources**
- [generate_signals.py:342-745](file://API/generate_signals.py#L342-L745)

### Rule-Based Signal Export
- Entry path v1: applies frozen rule to prediction CSV to produce time;signal
- Take/skip v2: supports prob >= threshold and top-k selectors with optional diagnostics

```mermaid
flowchart TD
RStart(["Start export_*"]) --> LoadPred["Load prediction CSV"]
LoadPred --> LoadRule["Load frozen rule"]
LoadRule --> Apply["Apply selector<br/>prob >= threshold or top-k"]
Apply --> Expand{"Expand to base CSV?"}
Expand --> |Yes| Merge["Merge with base time/signal"]
Expand --> |No| Keep["Keep sparse predictions"]
Merge --> Diagnostics{"Diagnostic mode?"}
Keep --> Diagnostics
Diagnostics --> |Yes| Build["Build diagnostic signals per year"]
Diagnostics --> |No| Export["Write CSV"]
Build --> Export
```

**Diagram sources**
- [export_entry_path_v1_signals.py:72-123](file://API/export_entry_path_v1_signals.py#L72-L123)
- [export_take_skip_trailing_stop_v2_signals.py:179-323](file://API/export_take_skip_trailing_stop_v2_signals.py#L179-L323)

**Section sources**
- [export_entry_path_v1_signals.py:72-123](file://API/export_entry_path_v1_signals.py#L72-L123)
- [export_take_skip_trailing_stop_v2_signals.py:179-323](file://API/export_take_skip_trailing_stop_v2_signals.py#L179-L323)

## Dependency Analysis
Inter-module dependencies and data flow:

```mermaid
graph TB
LS["label_signals.py"] --> LM["label_main.py"]
LM --> GS["generate_signals.py"]
GS --> EP["export_entry_path_v1_signals.py"]
GS --> TS["export_take_skip_trailing_stop_v2_signals.py"]
GS --> TSK1["take_skip_trailing_stop_v2_task.py"]
GS --> TSK2["trailing_stop_target_task.py"]
GS --> TSK3["trailing_stop_target_quantile_task.py"]
GS --> SR["signal_research.py"]
GS --> SQR["signal_quality_research.py"]
```

**Diagram sources**
- [label_signals.py:147-325](file://processing/label_signals.py#L147-L325)
- [label_main.py:205-332](file://processing/label_main.py#L205-L332)
- [generate_signals.py:342-745](file://API/generate_signals.py#L342-L745)
- [export_entry_path_v1_signals.py:72-123](file://API/export_entry_path_v1_signals.py#L72-L123)
- [export_take_skip_trailing_stop_v2_signals.py:179-323](file://API/export_take_skip_trailing_stop_v2_signals.py#L179-L323)
- [signal_research.py:170-210](file://API/signal_research.py#L170-L210)
- [signal_quality_research.py:75-116](file://API/signal_quality_research.py#L75-L116)
- [take_skip_trailing_stop_v2_task.py:37-111](file://ML/take_skip_trailing_stop_v2_task.py#L37-L111)
- [trailing_stop_target_task.py:13-25](file://ML/trailing_stop_target_task.py#L13-L25)
- [trailing_stop_target_quantile_task.py:12-107](file://ML/trailing_stop_target_quantile_task.py#L12-L107)

**Section sources**
- [label_main.py:205-332](file://processing/label_main.py#L205-L332)
- [generate_signals.py:342-745](file://API/generate_signals.py#L342-L745)

## Performance Considerations
- Label_all predict computation is O(N·K) pre-scan plus per-row timeline traversal; worst-case O(N^2) when scanning all futures for each fractal
- Triple barrier and trailing stop computations are vectorized and efficient
- Normalization is row-wise to prevent data leakage and maintain temporal order
- Splitting preserves chronological order to avoid leakage between sets

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Sorting quality: verify fractal ordering using verification routine; incorrect sorting leads to invalid labels
- Missing OHLC: ensure OHLC file exists and is properly formatted; otherwise fallbacks or NaNs may occur
- Empty fractal0: rows without fractal0 are skipped in predict labeling; check input data integrity
- Ambiguous triple barrier cases: both barriers hit are treated conservatively; review SL/TP grid selection
- Conformal quantiles: ensure conformal calibration JSON exists before enabling conformal filtering
- Rule application: verify required columns (time, signal, pred_* or pred_take_*) before applying frozen rules

**Section sources**
- [label_main.py:79-131](file://processing/label_main.py#L79-L131)
- [label_signals.py:147-325](file://processing/label_signals.py#L147-L325)
- [label_signals.py:548-587](file://processing/label_signals.py#L548-L587)
- [generate_signals.py:360-372](file://API/generate_signals.py#L360-L372)
- [export_entry_path_v1_signals.py:29-36](file://API/export_entry_path_v1_signals.py#L29-L36)
- [export_take_skip_trailing_stop_v2_signals.py:53-60](file://API/export_take_skip_trailing_stop_v2_signals.py#L53-L60)

## Conclusion
The label generation system provides a robust, modular framework for creating supervised learning targets from market data. It integrates fractal-based signal labeling, outcome-aligned targets, triple barrier methods, entry path classification, and trailing stop targets with quantile distributions. The pipeline supports rigorous validation, rule-based export, and comprehensive research workflows to assess label quality and optimize performance across market conditions.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Practical Workflows and Examples
- Labeling workflow: sort fractals → label_all → label_updn → label_trade_targets → label_first_barrier_hit → label_entry_path_targets → label_trailing_stop_targets → normalize → split → save
- Inference workflow: load checkpoint → run inference → apply thresholds → export ml_signals.csv or research CSVs
- Research workflow: load signals + OHLC → compute excursions → build barrier outcomes → summarize and validate

**Section sources**
- [label_main.py:254-287](file://processing/label_main.py#L254-L287)
- [generate_signals.py:342-745](file://API/generate_signals.py#L342-L745)
- [signal_research.py:212-364](file://API/signal_research.py#L212-L364)

### Label Quality Assessment and Bias Detection
- Multi-horizon prediction features as filters: ratio and spread families, short vs long divergences
- Univariate response maps, shallow tree discovery, pairwise combinations, and score-based holdout validation
- Year stability checks and cross-analysis with pullback entry scenarios

**Section sources**
- [signal_quality_research.py:75-116](file://API/signal_quality_research.py#L75-L116)
- [signal_research.py:1247-1599](file://API/signal_research.py#L1247-L1599)