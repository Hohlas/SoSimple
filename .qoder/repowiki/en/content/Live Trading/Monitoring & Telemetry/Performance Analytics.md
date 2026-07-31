# Performance Analytics

<cite>
**Referenced Files in This Document**
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)
- [EDA.ipynb](file://statistics/EDA.ipynb)
- [README.md](file://statistics/README.md)
- [feature_catalog.json](file://statistics/feature_catalog.json)
- [class_statistics.json](file://statistics/class_statistics.json)
- [statistics_summary.json](file://statistics/statistics_summary.json)
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)
- [analyze_path_ordering.py](file://statistics/analyze_path_ordering.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [evaluate_test.py](file://ML/evaluate_test.py)
- [run_live_safe_ml_audit.py](file://ML/run_live_safe_ml_audit.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [threshold_analysis.py](file://ML/threshold_analysis.py)
- [tb_probability_calibration.py](file://ML/tb_probability_calibration.py)
- [conformal/calibrate.py](file://ML/conformal/calibrate.py)
- [API/api_server.py](file://API/api_server.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [API/generate_signals.py](file://API/generate_signals.py)
- [API/signal_research.py](file://API/signal_research.py)
- [API/signal_quality_research.py](file://API/signal_quality_research.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)
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
This document provides comprehensive documentation for performance analytics and statistical analysis tools within the SoSimple system. It focuses on the EDA framework, statistical metrics calculation, performance attribution methods, report generation, visualization, and statistical significance testing. It also covers examples of custom analytics scripts, dashboard configurations, automated reporting workflows, integration with visualization libraries, data export capabilities, benchmarking, model comparison techniques, and continuous improvement methodologies.

## Project Structure
The performance analytics and statistics subsystem is primarily located under the statistics directory, with supporting ML benchmarks, evaluation utilities, and API-based signal export and telemetry components. Key elements include:
- Statistics core: metrics computation, path ordering analysis, data contract validation, and summary artifacts.
- EDA notebook: exploratory data analysis workflow and visualizations.
- ML benchmarks and audits: performance benchmarking, live-safe auditing, threshold analysis, probability calibration, and conformal prediction.
- API layer: signal generation, research utilities, telemetry watching, and export endpoints.

```mermaid
graph TB
subgraph "Statistics"
S1["statistics.py"]
S2["signal_tracer.py"]
S3["EDA.ipynb"]
S4["feature_catalog.json"]
S5["class_statistics.json"]
S6["statistics_summary.json"]
S7["data_contract_smoke_check.py"]
S8["analyze_path_ordering.py"]
end
subgraph "ML Benchmarks & Audits"
M1["benchmark_entry_path_v2.py"]
M2["evaluate_test.py"]
M3["run_live_safe_ml_audit.py"]
M4["live_safe_audit.py"]
M5["threshold_analysis.py"]
M6["tb_probability_calibration.py"]
M7["conformal/calibrate.py"]
end
subgraph "API Layer"
A1["api_server.py"]
A2["export_entry_path_v1_quantile_signals.py"]
A3["export_entry_path_v1_signals.py"]
A4["export_take_skip_trailing_stop_v2_signals.py"]
A5["generate_signals.py"]
A6["signal_research.py"]
A7["signal_quality_research.py"]
A8["telemetry_signal_watcher.py"]
end
S1 --> S2
S3 --> S1
S7 --> S1
S8 --> S1
M1 --> S1
M2 --> S1
M3 --> M4
M5 --> S1
M6 --> S1
M7 --> S1
A1 --> A2
A1 --> A3
A1 --> A4
A5 --> A6
A5 --> A7
A8 --> A1
```

**Diagram sources**
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)
- [EDA.ipynb](file://statistics/EDA.ipynb)
- [feature_catalog.json](file://statistics/feature_catalog.json)
- [class_statistics.json](file://statistics/class_statistics.json)
- [statistics_summary.json](file://statistics/statistics_summary.json)
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)
- [analyze_path_ordering.py](file://statistics/analyze_path_ordering.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [evaluate_test.py](file://ML/evaluate_test.py)
- [run_live_safe_ml_audit.py](file://ML/run_live_safe_ml_audit.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [threshold_analysis.py](file://ML/threshold_analysis.py)
- [tb_probability_calibration.py](file://ML/tb_probability_calibration.py)
- [conformal/calibrate.py](file://ML/conformal/calibrate.py)
- [API/api_server.py](file://API/api_server.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [API/generate_signals.py](file://API/generate_signals.py)
- [API/signal_research.py](file://API/signal_research.py)
- [API/signal_quality_research.py](file://API/signal_quality_research.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)

**Section sources**
- [README.md](file://statistics/README.md)

## Core Components
- Statistical Metrics Engine: Centralized functions to compute performance metrics, distributions, and summaries across signals and trades.
- Signal Tracing: Tools to trace signal lineage, execution paths, and outcomes for attribution and diagnostics.
- EDA Framework: Notebook-driven exploration with standardized plots, distribution checks, and correlation analyses.
- Data Contract Validation: Smoke checks ensuring feature schemas and class labels meet expected contracts before analysis.
- Path Ordering Analysis: Analytical routines to assess ordering properties of price paths and their impact on labeling and features.
- Benchmarking and Auditing: Scripts to run comparative experiments, evaluate models, and perform live-safe audits.
- Probability Calibration and Conformal Prediction: Methods to calibrate probabilities and produce statistically valid predictive intervals.
- API Integration: Endpoints and utilities to generate, export, and monitor signals, enabling automated reporting and dashboards.

**Section sources**
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)
- [EDA.ipynb](file://statistics/EDA.ipynb)
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)
- [analyze_path_ordering.py](file://statistics/analyze_path_ordering.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [evaluate_test.py](file://ML/evaluate_test.py)
- [run_live_safe_ml_audit.py](file://ML/run_live_safe_ml_audit.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [threshold_analysis.py](file://ML/threshold_analysis.py)
- [tb_probability_calibration.py](file://ML/tb_probability_calibration.py)
- [conformal/calibrate.py](file://ML/conformal/calibrate.py)
- [API/api_server.py](file://API/api_server.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [API/generate_signals.py](file://API/generate_signals.py)
- [API/signal_research.py](file://API/signal_research.py)
- [API/signal_quality_research.py](file://API/signal_quality_research.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)

## Architecture Overview
The analytics architecture integrates EDA, statistical computations, benchmarking, and API-driven exports into a cohesive pipeline. The flow typically starts with data ingestion and validation, proceeds through EDA and metric computation, then moves to benchmarking and auditing, and finally outputs reports and dashboards via API endpoints.

```mermaid
sequenceDiagram
participant User as "Analyst"
participant EDA as "EDA.ipynb"
participant Stats as "statistics.py"
participant Trace as "signal_tracer.py"
participant Bench as "benchmark_entry_path_v2.py"
participant Audit as "live_safe_audit.py"
participant API as "api_server.py"
participant Export as "export_*_signals.py"
User->>EDA : "Run exploratory analysis"
EDA->>Stats : "Compute distributions and correlations"
Stats-->>EDA : "Summaries and plots"
EDA->>Trace : "Trace signals and outcomes"
Trace-->>EDA : "Attribution details"
User->>Bench : "Execute benchmark experiment"
Bench->>Stats : "Aggregate metrics"
Bench->>Audit : "Perform live-safe audit"
Audit-->>Bench : "Audit results"
User->>API : "Request report or export"
API->>Export : "Generate signals and datasets"
Export-->>API : "Exported files"
API-->>User : "Report/Dashboard data"
```

**Diagram sources**
- [EDA.ipynb](file://statistics/EDA.ipynb)
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [API/api_server.py](file://API/api_server.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)

## Detailed Component Analysis

### Statistical Metrics Engine (statistics.py)
The statistical engine centralizes calculations for performance metrics, distributions, and summaries. It supports:
- Aggregation of returns, drawdowns, Sharpe ratios, and other standard trading metrics.
- Distribution analysis for features and labels, including skewness, kurtosis, and quantiles.
- Correlation matrices and pairwise relationships among features and outcomes.
- Summary JSON artifacts for downstream consumption by dashboards and reports.

```mermaid
flowchart TD
Start(["Input Data"]) --> Validate["Validate Schema and Contracts"]
Validate --> ComputeMetrics["Compute Performance Metrics"]
ComputeMetrics --> Distributions["Analyze Distributions"]
Distributions --> Correlations["Compute Correlations"]
Correlations --> Summarize["Generate Summary Artifacts"]
Summarize --> Output["Export JSON/CSV Reports"]
Output --> End(["Consumers: Dashboards, APIs, Audits"])
```

**Diagram sources**
- [statistics.py](file://statistics/statistics.py)
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)

**Section sources**
- [statistics.py](file://statistics/statistics.py)
- [statistics_summary.json](file://statistics/statistics_summary.json)
- [class_statistics.json](file://statistics/class_statistics.json)
- [feature_catalog.json](file://statistics/feature_catalog.json)

### Signal Tracing and Attribution (signal_tracer.py)
Signal tracing enables detailed attribution of trade outcomes to specific signals and execution paths. Capabilities include:
- Linking signals to entries, exits, and PnL outcomes.
- Tracking signal quality filters and thresholds applied at runtime.
- Producing trace logs and aggregated attribution tables for post-trade analysis.

```mermaid
classDiagram
class SignalTracer {
+trace(signal_id, entry, exit) dict
+aggregate_attribution(traces) DataFrame
+export_trace_log(path) void
+filter_by_quality(threshold) list
}
class TradeOutcome {
+pnl float
+duration int
+exit_reason string
}
SignalTracer --> TradeOutcome : "produces"
```

**Diagram sources**
- [signal_tracer.py](file://statistics/signal_tracer.py)

**Section sources**
- [signal_tracer.py](file://statistics/signal_tracer.py)

### EDA Framework (EDA.ipynb)
The EDA notebook orchestrates exploratory analysis workflows:
- Data loading and preprocessing steps.
- Distribution checks, missing value analysis, and outlier detection.
- Visualization of key metrics and feature-target relationships.
- Generation of initial insights that inform benchmarking and modeling decisions.

```mermaid
flowchart TD
Load["Load Dataset"] --> Clean["Clean and Normalize"]
Clean --> Explore["Explore Distributions"]
Explore --> Visualize["Plot Relationships"]
Visualize --> Insights["Extract Insights"]
Insights --> Report["Generate EDA Report"]
```

**Diagram sources**
- [EDA.ipynb](file://statistics/EDA.ipynb)

**Section sources**
- [EDA.ipynb](file://statistics/EDA.ipynb)

### Data Contract Validation (data_contract_smoke_check.py)
Ensures that incoming datasets adhere to expected schemas and label conventions:
- Validates feature names, types, and ranges.
- Checks class label consistency and balance.
- Raises informative errors when contracts are violated, preventing downstream failures.

```mermaid
flowchart TD
Input["Raw Data"] --> CheckSchema["Check Feature Schema"]
CheckSchema --> CheckLabels["Validate Class Labels"]
CheckLabels --> Pass{"Contracts Valid?"}
Pass --> |Yes| Proceed["Proceed to Analysis"]
Pass --> |No| Error["Raise Contract Violation Error"]
```

**Diagram sources**
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)

**Section sources**
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)

### Path Ordering Analysis (analyze_path_ordering.py)
Analyzes the ordering properties of price paths to support labeling and feature engineering:
- Detects monotonic segments and reversals.
- Computes ordering statistics relevant to triple-barrier labeling.
- Outputs diagnostics used in EDA and benchmarking.

```mermaid
flowchart TD
PricePath["Price Path Series"] --> Segment["Segment Detection"]
Segment --> OrderStats["Compute Ordering Statistics"]
OrderStats --> Diagnostics["Generate Diagnostics"]
Diagnostics --> EDA["Feed into EDA/Benchmarks"]
```

**Diagram sources**
- [analyze_path_ordering.py](file://statistics/analyze_path_ordering.py)

**Section sources**
- [analyze_path_ordering.py](file://statistics/analyze_path_ordering.py)

### Benchmarking and Model Comparison (benchmark_entry_path_v2.py, evaluate_test.py)
Benchmarking scripts execute controlled experiments to compare strategies and models:
- Run multiple seeds and parameter grids.
- Aggregate performance metrics across runs.
- Produce comparative reports and selection criteria.

```mermaid
sequenceDiagram
participant Runner as "Benchmark Runner"
participant Experiment as "Experiment Config"
participant Metrics as "statistics.py"
participant Report as "Report Generator"
Runner->>Experiment : "Load config and parameters"
Experiment-->>Runner : "Configured trials"
loop For each trial
Runner->>Metrics : "Compute metrics"
Metrics-->>Runner : "Aggregated stats"
end
Runner->>Report : "Generate comparison report"
Report-->>Runner : "PDF/HTML/JSON outputs"
```

**Diagram sources**
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [evaluate_test.py](file://ML/evaluate_test.py)
- [statistics.py](file://statistics/statistics.py)

**Section sources**
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [evaluate_test.py](file://ML/evaluate_test.py)

### Live-Safe Auditing (run_live_safe_ml_audit.py, live_safe_audit.py)
Auditing ensures robustness and safety of ML models in live environments:
- Performs out-of-sample and walk-forward validations.
- Monitors drift and stability over time.
- Generates audit reports with actionable recommendations.

```mermaid
flowchart TD
Model["Trained Model"] --> OOS["Out-of-Sample Test"]
OOS --> WalkForward["Walk-Forward Validation"]
WalkForward --> DriftCheck["Drift and Stability Checks"]
DriftCheck --> AuditReport["Generate Audit Report"]
AuditReport --> Action["Actionable Recommendations"]
```

**Diagram sources**
- [run_live_safe_ml_audit.py](file://ML/run_live_safe_ml_audit.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)

**Section sources**
- [run_live_safe_ml_audit.py](file://ML/run_live_safe_ml_audit.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)

### Threshold Analysis and Probability Calibration (threshold_analysis.py, tb_probability_calibration.py)
Threshold analysis tunes decision boundaries; probability calibration aligns predicted probabilities with observed frequencies:
- Grid search over thresholds to optimize performance metrics.
- Calibration curves and reliability diagrams.
- Integration with conformal prediction for valid intervals.

```mermaid
flowchart TD
Predictions["Model Predictions"] --> ThresholdSearch["Threshold Search"]
ThresholdSearch --> Optimal["Select Optimal Threshold"]
Predictions --> Calibration["Probability Calibration"]
Calibration --> Conformal["Conformal Intervals"]
Optimal --> Reporting["Reporting and Dashboards"]
Conformal --> Reporting
```

**Diagram sources**
- [threshold_analysis.py](file://ML/threshold_analysis.py)
- [tb_probability_calibration.py](file://ML/tb_probability_calibration.py)
- [conformal/calibrate.py](file://ML/conformal/calibrate.py)

**Section sources**
- [threshold_analysis.py](file://ML/threshold_analysis.py)
- [tb_probability_calibration.py](file://ML/tb_probability_calibration.py)
- [conformal/calibrate.py](file://ML/conformal/calibrate.py)

### API Integration and Automated Reporting (API/api_server.py, export_*_signals.py)
The API layer exposes endpoints for generating and exporting signals, facilitating automated reporting and dashboard updates:
- REST endpoints for signal generation and export.
- Telemetry watching for real-time monitoring.
- Export utilities for various signal formats compatible with MT platforms and external systems.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Server as "api_server.py"
participant Gen as "generate_signals.py"
participant Export as "export_*_signals.py"
participant Watch as "telemetry_signal_watcher.py"
Client->>Server : "POST /generate-signals"
Server->>Gen : "Invoke signal generation"
Gen-->>Server : "Signals payload"
Server->>Export : "Export signals to file"
Export-->>Server : "Export confirmation"
Server-->>Client : "Response with metadata"
Watch->>Server : "Monitor telemetry events"
Watch-->>Client : "Real-time updates"
```

**Diagram sources**
- [API/api_server.py](file://API/api_server.py)
- [API/generate_signals.py](file://API/generate_signals.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)

**Section sources**
- [API/api_server.py](file://API/api_server.py)
- [API/generate_signals.py](file://API/generate_signals.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)

## Dependency Analysis
The analytics stack exhibits clear separation of concerns:
- Statistics module depends on data validation and produces summaries consumed by benchmarks and audits.
- Benchmarks depend on statistics and feed results into audits and reporting.
- API layer depends on export utilities and telemetry watchers to serve clients.

```mermaid
graph TB
Stats["statistics.py"] --> Bench["benchmark_entry_path_v2.py"]
Stats --> Audit["live_safe_audit.py"]
Bench --> Audit
API["api_server.py"] --> Export["export_*_signals.py"]
Export --> Stats
API --> Watch["telemetry_signal_watcher.py"]
```

**Diagram sources**
- [statistics.py](file://statistics/statistics.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [API/api_server.py](file://API/api_server.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)

**Section sources**
- [statistics.py](file://statistics/statistics.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [API/api_server.py](file://API/api_server.py)

## Performance Considerations
- Vectorization and batching in statistical computations to reduce overhead.
- Caching intermediate results during EDA and benchmarking to speed up iterative development.
- Efficient I/O patterns for large datasets, using chunked processing where applicable.
- Parallelizing independent benchmark trials to accelerate comparisons.
- Minimizing memory footprint by streaming data and avoiding unnecessary copies.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Data contract violations: Ensure feature schemas and label conventions match expectations; use smoke checks to catch errors early.
- Missing or malformed signals: Verify signal generation pipelines and export formats; check telemetry logs for anomalies.
- Calibration mismatches: Re-run calibration procedures and validate probability estimates against observed frequencies.
- Benchmark inconsistencies: Confirm random seeds, data splits, and environment reproducibility settings.

**Section sources**
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)
- [tb_probability_calibration.py](file://ML/tb_probability_calibration.py)

## Conclusion
The SoSimple performance analytics and statistical analysis toolkit provides a robust foundation for EDA, metrics computation, benchmarking, auditing, and automated reporting. By integrating signal tracing, probability calibration, and API-driven exports, it supports continuous improvement and reliable decision-making in trading strategy development.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices
- Example EDA workflow: See [EDA.ipynb](file://statistics/EDA.ipynb) for step-by-step exploratory analysis.
- Custom analytics scripts: Extend [statistics.py](file://statistics/statistics.py) with domain-specific metrics and integrate with [signal_tracer.py](file://statistics/signal_tracer.py).
- Dashboard configuration: Use exported JSON/CSV from [statistics_summary.json](file://statistics/statistics_summary.json) and API endpoints in [API/api_server.py](file://API/api_server.py).
- Automated reporting: Schedule [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py) and [run_live_safe_ml_audit.py](file://ML/run_live_safe_ml_audit.py) to generate periodic reports.

**Section sources**
- [EDA.ipynb](file://statistics/EDA.ipynb)
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)
- [statistics_summary.json](file://statistics/statistics_summary.json)
- [API/api_server.py](file://API/api_server.py)
- [benchmark_entry_path_v2.py](file://ML/benchmark_entry_path_v2.py)
- [run_live_safe_ml_audit.py](file://ML/run_live_safe_ml_audit.py)