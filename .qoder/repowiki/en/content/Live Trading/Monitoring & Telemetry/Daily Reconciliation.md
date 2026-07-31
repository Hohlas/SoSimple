# Daily Reconciliation

<cite>
**Referenced Files in This Document**
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [telemetry_daily_reconciliation.py](file://ML/telemetry_daily_reconciliation.py)
- [test_online_tester_reconciliation.py](file://tests/test_online_tester_reconciliation.py)
- [test_telemetry_daily_reconciliation.py](file://tests/test_telemetry_daily_reconciliation.py)
- [parse_mt5_execution_report.py](file://ML/baseline/parse_mt5_execution_report.py)
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [live_safe_audit_registry.py](file://ML/live_safe_audit_registry.py)
- [run_live_safe_ml_audit.py](file://ML/run_live_safe_ml_audit.py)
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)
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
This document explains the daily reconciliation process that validates paper trading results against live execution. It covers how predicted signals are compared with actual market outcomes, how discrepancies are identified and reported, and which statistical tools support performance validation, drift detection, and model accuracy assessment. It also documents configuration options for reconciliation parameters, data sources, and reporting formats, along with examples of reports, discrepancy analysis workflows, and automated correction procedures. Data quality checks, missing data handling, and failure recovery mechanisms are addressed to ensure robust operation.

## Project Structure
The reconciliation system spans several modules:
- Online tester reconciliation logic that aligns predicted signals with executed trades and computes metrics.
- Telemetry-driven daily reconciliation that ingests telemetry, performs comparisons, and generates reports.
- MT5 execution report parsing utilities used to normalize live trade records.
- Triple barrier execution utilities that define outcome labeling and exit mechanics.
- Live-safe audit orchestration that schedules and runs audits including reconciliation.
- Statistical utilities for EDA, drift detection, and signal tracing.

```mermaid
graph TB
subgraph "Reconciliation Core"
OTR["Online Tester Reconciliation"]
TDR["Telemetry Daily Reconciliation"]
end
subgraph "Execution & Signals"
PARSER["MT5 Execution Report Parser"]
TB["Triple Barrier Execution"]
SIGNALS["Predicted Signals (from API/Models)"]
end
subgraph "Audit & Reporting"
LSA["Live Safe Audit"]
REG["Audit Registry"]
STATS["Statistics & Signal Tracer"]
end
SIGNALS --> OTR
PARSER --> OTR
OTR --> TDR
TDR --> LSA
LSA --> REG
STATS --> TDR
STATS --> LSA
TB --> OTR
```

**Diagram sources**
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [telemetry_daily_reconciliation.py](file://ML/telemetry_daily_reconciliation.py)
- [parse_mt5_execution_report.py](file://ML/baseline/parse_mt5_execution_report.py)
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [live_safe_audit_registry.py](file://ML/live_safe_audit_registry.py)
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)

**Section sources**
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [telemetry_daily_reconciliation.py](file://ML/telemetry_daily_reconciliation.py)
- [parse_mt5_execution_report.py](file://ML/baseline/parse_mt5_execution_report.py)
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [live_safe_audit_registry.py](file://ML/live_safe_audit_registry.py)
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)

## Core Components
- Online Tester Reconciliation: Aligns predicted signals with executed trades, computes per-trade deltas, aggregates metrics, and flags discrepancies.
- Telemetry Daily Reconciliation: Consumes telemetry streams, orchestrates reconciliation steps, and produces daily audit reports.
- MT5 Execution Report Parser: Normalizes raw MT5 logs into structured trade records for comparison.
- Triple Barrier Execution: Provides consistent labeling and exit semantics used by both prediction and execution to ensure parity.
- Live Safe Audit: Orchestrates scheduled audits, including reconciliation, and manages registry entries.
- Statistics & Signal Tracer: Supplies statistical tests, drift detection, and traceability for signals and outcomes.

Key responsibilities:
- Data ingestion and normalization from multiple sources.
- Deterministic matching between predictions and executions using timestamps, instrument IDs, and trade keys.
- Discrepancy classification (missing trades, timing mismatches, price slippage, exit rule differences).
- Metric computation (hit rate, average slippage, PnL delta, drawdown variance).
- Reporting in configurable formats (CSV, JSON, Markdown).
- Automated correction procedures where possible (e.g., re-matching with relaxed tolerances, fallback rules).

**Section sources**
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [telemetry_daily_reconciliation.py](file://ML/telemetry_daily_reconciliation.py)
- [parse_mt5_execution_report.py](file://ML/baseline/parse_mt5_execution_report.py)
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [live_safe_audit_registry.py](file://ML/live_safe_audit_registry.py)
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)

## Architecture Overview
The reconciliation pipeline is designed as a staged workflow:
1. Ingest predicted signals from the model/API layer.
2. Ingest live execution records via MT5 parser or telemetry stream.
3. Normalize and validate data contracts.
4. Match predictions to executions deterministically.
5. Compute deltas and classify discrepancies.
6. Aggregate metrics and generate reports.
7. Trigger corrective actions or alerts based on thresholds.

```mermaid
sequenceDiagram
participant API as "Signal Provider"
participant OTR as "Online Tester Reconciliation"
participant PARSER as "MT5 Execution Report Parser"
participant TDR as "Telemetry Daily Reconciliation"
participant LSA as "Live Safe Audit"
participant STATS as "Statistics & Signal Tracer"
API->>OTR : "Provide predicted signals"
PARSER->>OTR : "Provide normalized execution records"
OTR->>OTR : "Match predictions to executions"
OTR->>STATS : "Compute metrics and drift checks"
OTR-->>TDR : "Return reconciliation results"
TDR->>LSA : "Submit daily audit report"
LSA-->>TDR : "Acknowledge and log"
TDR-->>API : "Trigger corrections if needed"
```

**Diagram sources**
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [telemetry_daily_reconciliation.py](file://ML/telemetry_daily_reconciliation.py)
- [parse_mt5_execution_report.py](file://ML/baseline/parse_mt5_execution_report.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)

## Detailed Component Analysis

### Online Tester Reconciliation
Responsibilities:
- Load predicted signals and execution records.
- Validate data contracts and handle missing fields.
- Perform deterministic matching using composite keys (instrument, timestamp, trade ID).
- Compute per-trade deltas (entry/exit prices, timing, slippage).
- Classify discrepancies and aggregate metrics.
- Output reconciliation artifacts (CSV/JSON) and summary statistics.

```mermaid
flowchart TD
Start(["Start Reconciliation"]) --> LoadSignals["Load Predicted Signals"]
LoadSignals --> LoadExecutions["Load Execution Records"]
LoadExecutions --> ValidateData["Validate Data Contracts"]
ValidateData --> MissingCheck{"Missing Data?"}
MissingCheck --> |Yes| HandleMissing["Apply Missing Data Handling Rules"]
MissingCheck --> |No| Match["Match Predictions to Executions"]
HandleMissing --> Match
Match --> ComputeDeltas["Compute Per-Trade Deltas"]
ComputeDeltas --> Classify["Classify Discrepancies"]
Classify --> Metrics["Aggregate Metrics"]
Metrics --> Reports["Generate Reports"]
Reports --> End(["End"])
```

**Diagram sources**
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)

Configuration options typically include:
- Matching tolerance windows (time, price).
- Discrepancy thresholds (slippage, exit rule deviation).
- Reporting format selection (CSV, JSON, Markdown).
- Data source paths and schemas.

Error handling:
- Graceful degradation when partial data is available.
- Retry logic for transient failures in data ingestion.
- Alerting on critical mismatches exceeding thresholds.

**Section sources**
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [test_online_tester_reconciliation.py](file://tests/test_online_tester_reconciliation.py)
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)

### Telemetry Daily Reconciliation
Responsibilities:
- Consume telemetry events for signals and executions.
- Orchestrate reconciliation steps and persist results.
- Generate daily audit reports and push to audit registry.
- Integrate with statistics module for drift detection and performance validation.

```mermaid
sequenceDiagram
participant Stream as "Telemetry Stream"
participant TDR as "Telemetry Daily Reconciliation"
participant OTR as "Online Tester Reconciliation"
participant LSA as "Live Safe Audit"
participant STATS as "Statistics & Signal Tracer"
Stream->>TDR : "Ingest telemetry events"
TDR->>OTR : "Run reconciliation"
OTR-->>TDR : "Return reconciliation results"
TDR->>STATS : "Perform drift and accuracy checks"
TDR->>LSA : "Submit daily audit report"
LSA-->>TDR : "Registry update confirmation"
```

**Diagram sources**
- [telemetry_daily_reconciliation.py](file://ML/telemetry_daily_reconciliation.py)
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)

Reporting formats:
- CSV for tabular metrics.
- JSON for machine-readable summaries.
- Markdown for human-readable audit narratives.

Automated correction procedures:
- Re-match with relaxed tolerances.
- Fallback to last known good state.
- Flag persistent discrepancies for manual review.

**Section sources**
- [telemetry_daily_reconciliation.py](file://ML/telemetry_daily_reconciliation.py)
- [test_telemetry_daily_reconciliation.py](file://tests/test_telemetry_daily_reconciliation.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)

### MT5 Execution Report Parser
Responsibilities:
- Parse raw MT5 logs into structured trade records.
- Normalize timestamps, symbols, and order identifiers.
- Ensure compatibility with reconciliation matching logic.

```mermaid
classDiagram
class MT5Parser {
+parse(raw_logs) list
+normalize(record) dict
+validate_schema(record) bool
}
class TradeRecord {
+timestamp datetime
+symbol string
+order_id string
+entry_price float
+exit_price float
+pnl float
}
MT5Parser --> TradeRecord : "produces"
```

**Diagram sources**
- [parse_mt5_execution_report.py](file://ML/baseline/parse_mt5_execution_report.py)

**Section sources**
- [parse_mt5_execution_report.py](file://ML/baseline/parse_mt5_execution_report.py)

### Triple Barrier Execution
Responsibilities:
- Define exit rules and labeling conventions used by both prediction and execution.
- Ensure parity between simulated and live outcomes.

```mermaid
flowchart TD
Entry["Entry Signal"] --> Barriers["Apply Triple Barriers"]
Barriers --> ExitRule{"Exit Condition Met?"}
ExitRule --> |Yes| Outcome["Label Outcome"]
ExitRule --> |No| Hold["Hold Position"]
Hold --> Barriers
```

**Diagram sources**
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)

**Section sources**
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)

### Live Safe Audit and Registry
Responsibilities:
- Schedule and run reconciliation audits.
- Maintain registry of audit runs and results.
- Provide hooks for automated corrections and alerts.

```mermaid
classDiagram
class LiveSafeAudit {
+schedule_audit() void
+run_audit() dict
+publish_report(report) void
}
class AuditRegistry {
+register(run_id, result) void
+query(date_range) list
}
LiveSafeAudit --> AuditRegistry : "updates"
```

**Diagram sources**
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [live_safe_audit_registry.py](file://ML/live_safe_audit_registry.py)
- [run_live_safe_ml_audit.py](file://ML/run_live_safe_ml_audit.py)

**Section sources**
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [live_safe_audit_registry.py](file://ML/live_safe_audit_registry.py)
- [run_live_safe_ml_audit.py](file://ML/run_live_safe_ml_audit.py)

### Statistics and Signal Tracer
Responsibilities:
- Provide statistical tests for performance validation.
- Detect distributional drift in features and outcomes.
- Trace signals through the pipeline for auditability.

```mermaid
classDiagram
class Statistics {
+compute_metrics(results) dict
+drift_test(data) bool
+accuracy_assessment(predictions, outcomes) dict
}
class SignalTracer {
+trace(signal_id) dict
+export_trace(trace) str
}
Statistics --> SignalTracer : "uses"
```

**Diagram sources**
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)

**Section sources**
- [statistics.py](file://statistics/statistics.py)
- [signal_tracer.py](file://statistics/signal_tracer.py)

## Dependency Analysis
The reconciliation system has clear dependencies:
- Online Tester Reconciliation depends on data contract validation and triple barrier execution semantics.
- Telemetry Daily Reconciliation depends on Online Tester Reconciliation and statistics utilities.
- MT5 Execution Report Parser provides normalized execution records consumed by reconciliation.
- Live Safe Audit orchestrates reconciliation and persists results via the audit registry.

```mermaid
graph TB
OTR["Online Tester Reconciliation"] --> STATS["Statistics"]
OTR --> TB["Triple Barrier Execution"]
TDR["Telemetry Daily Reconciliation"] --> OTR
TDR --> STATS
PARSER["MT5 Execution Report Parser"] --> OTR
LSA["Live Safe Audit"] --> TDR
REG["Audit Registry"] --> LSA
```

**Diagram sources**
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [telemetry_daily_reconciliation.py](file://ML/telemetry_daily_reconciliation.py)
- [parse_mt5_execution_report.py](file://ML/baseline/parse_mt5_execution_report.py)
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [live_safe_audit_registry.py](file://ML/live_safe_audit_registry.py)
- [statistics.py](file://statistics/statistics.py)

**Section sources**
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [telemetry_daily_reconciliation.py](file://ML/telemetry_daily_reconciliation.py)
- [parse_mt5_execution_report.py](file://ML/baseline/parse_mt5_execution_report.py)
- [triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [live_safe_audit.py](file://ML/live_safe_audit.py)
- [live_safe_audit_registry.py](file://ML/live_safe_audit_registry.py)
- [statistics.py](file://statistics/statistics.py)

## Performance Considerations
- Batch processing of large datasets to minimize I/O overhead.
- Efficient matching algorithms using indexed keys to reduce complexity.
- Streaming telemetry ingestion to avoid memory spikes.
- Caching intermediate results for repeated audits.
- Parallel computation of metrics where feasible.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Missing data: Apply predefined missing data handling rules; fall back to last known values; alert on persistent gaps.
- Mismatched timestamps: Adjust tolerance windows; verify clock synchronization across systems.
- Slippage anomalies: Review execution latency and liquidity conditions; flag outliers for review.
- Exit rule divergence: Confirm triple barrier configuration parity between prediction and execution.
- Reconciliation failures: Inspect logs, retry ingestion, and escalate to manual review if thresholds exceeded.

**Section sources**
- [online_tester_reconciliation.py](file://ML/online_tester_reconciliation.py)
- [telemetry_daily_reconciliation.py](file://ML/telemetry_daily_reconciliation.py)
- [data_contract_smoke_check.py](file://statistics/data_contract_smoke_check.py)

## Conclusion
The daily reconciliation process ensures alignment between predicted signals and live execution outcomes through robust data normalization, deterministic matching, and comprehensive statistical validation. By integrating telemetry, MT5 parsing, and live-safe auditing, the system provides actionable insights, automated corrections, and reliable reporting. Continuous monitoring and drift detection help maintain model accuracy and operational integrity.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices
- Example reconciliation report structure:
  - Summary metrics (hit rate, average slippage, PnL delta).
  - Discrepancy details (trade-level deltas, classification codes).
  - Drift detection results (feature distribution shifts, significance levels).
  - Corrective actions taken (re-matching, fallback rules, alerts).

- Configuration reference:
  - Reconciliation parameters (tolerance windows, thresholds).
  - Data sources (paths, schemas, authentication).
  - Reporting formats (CSV, JSON, Markdown).

[No sources needed since this section provides general guidance]