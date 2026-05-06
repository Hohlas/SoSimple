# Position Management and Exit Strategies

<cite>
**Referenced Files in This Document**
- [exit_policy_research.py](file://API/exit_policy_research.py)
- [test_exit_policy_research.py](file://tests/test_exit_policy_research.py)
- [export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [take_skip_trailing_stop_v2_task.py](file://ML/take_skip_trailing_stop_v2_task.py)
- [benchmark_take_skip_trailing_stop_v2.py](file://ML/benchmark_take_skip_trailing_stop_v2.py)
- [trailing_stop_target_task.py](file://ML/trailing_stop_target_task.py)
- [trailing_stop_target_quantile_task.py](file://ML/trailing_stop_target_quantile_task.py)
- [benchmark_trailing_stop_target.py](file://ML/benchmark_trailing_stop_target.py)
- [benchmark_trailing_stop_target_quantile.py](file://ML/benchmark_trailing_stop_target_quantile.py)
- [label_signals.py](file://processing/label_signals.py)
- [benchmark_execution_policy_v2.py](file://ML/benchmark_execution_policy_v2.py)
- [benchmark_take_skip_mt4_trailing_sequential.py](file://ML/benchmark_take_skip_mt4_trailing_sequential.py)
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
This document explains position management and exit strategy implementation in the ML Signal Library. It focuses on two primary exit modes:
- Trailing stop based on ATR multiples
- Fixed hold period timeout

It also covers best price tracking for trailing stops, position state management, multi-position coordination, reversal logic for allowing opposite-side entries when signals contradict existing positions, and performance metrics tracking. Edge cases such as partial exits and position blocking are addressed.

## Project Structure
The relevant components span three areas:
- API-level offline research and export utilities
- ML tasks for labeling and benchmarking trailing stop targets and take/skip rules
- Processing utilities for generating synthetic labels and simulating exits

```mermaid
graph TB
subgraph "API"
EPR["exit_policy_research.py"]
EXP["export_take_skip_trailing_stop_v2_signals.py"]
end
subgraph "ML Tasks"
TSK1["take_skip_trailing_stop_v2_task.py"]
TSK2["trailing_stop_target_task.py"]
TSK3["trailing_stop_target_quantile_task.py"]
BM1["benchmark_take_skip_trailing_stop_v2.py"]
BM2["benchmark_trailing_stop_target.py"]
BM3["benchmark_trailing_stop_target_quantile.py"]
end
subgraph "Processing"
LAB["label_signals.py"]
BMEP["benchmark_execution_policy_v2.py"]
BMT["benchmark_take_skip_mt4_trailing_sequential.py"]
end
EPR --> LAB
EXP --> TSK1
BM1 --> TSK1
BM2 --> TSK2
BM3 --> TSK3
BMEP --> LAB
BMT --> LAB
```

**Diagram sources**
- [exit_policy_research.py:1-416](file://API/exit_policy_research.py#L1-L416)
- [export_take_skip_trailing_stop_v2_signals.py:1-323](file://API/export_take_skip_trailing_stop_v2_signals.py#L1-L323)
- [take_skip_trailing_stop_v2_task.py:1-111](file://ML/take_skip_trailing_stop_v2_task.py#L1-L111)
- [trailing_stop_target_task.py:1-25](file://ML/trailing_stop_target_task.py#L1-L25)
- [trailing_stop_target_quantile_task.py:1-107](file://ML/trailing_stop_target_quantile_task.py#L1-L107)
- [benchmark_take_skip_trailing_stop_v2.py:1-144](file://ML/benchmark_take_skip_trailing_stop_v2.py#L1-L144)
- [benchmark_trailing_stop_target.py:1-32](file://ML/benchmark_trailing_stop_target.py#L1-L32)
- [benchmark_trailing_stop_target_quantile.py:1-248](file://ML/benchmark_trailing_stop_target_quantile.py#L1-L248)
- [label_signals.py:728-843](file://processing/label_signals.py#L728-L843)
- [benchmark_execution_policy_v2.py:271-299](file://ML/benchmark_execution_policy_v2.py#L271-L299)
- [benchmark_take_skip_mt4_trailing_sequential.py:135-162](file://ML/benchmark_take_skip_mt4_trailing_sequential.py#L135-L162)

**Section sources**
- [exit_policy_research.py:1-416](file://API/exit_policy_research.py#L1-L416)
- [export_take_skip_trailing_stop_v2_signals.py:1-323](file://API/export_take_skip_trailing_stop_v2_signals.py#L1-L323)
- [take_skip_trailing_stop_v2_task.py:1-111](file://ML/take_skip_trailing_stop_v2_task.py#L1-L111)
- [trailing_stop_target_task.py:1-25](file://ML/trailing_stop_target_task.py#L1-L25)
- [trailing_stop_target_quantile_task.py:1-107](file://ML/trailing_stop_target_quantile_task.py#L1-L107)
- [benchmark_take_skip_trailing_stop_v2.py:1-144](file://ML/benchmark_take_skip_trailing_stop_v2.py#L1-L144)
- [benchmark_trailing_stop_target.py:1-32](file://ML/benchmark_trailing_stop_target.py#L1-L32)
- [benchmark_trailing_stop_target_quantile.py:1-248](file://ML/benchmark_trailing_stop_target_quantile.py#L1-L248)
- [label_signals.py:728-843](file://processing/label_signals.py#L728-L843)
- [benchmark_execution_policy_v2.py:271-299](file://ML/benchmark_execution_policy_v2.py#L271-L299)
- [benchmark_take_skip_mt4_trailing_sequential.py:135-162](file://ML/benchmark_take_skip_mt4_trailing_sequential.py#L135-L162)

## Core Components
- Exit policy research engine: builds and evaluates policy variants offline, computes performance metrics, and exports a frozen policy suitable for runtime.
- Take/skip and trailing stop labeling and benchmarking: defines target columns, computes metrics, and supports rule-based selection of signals for MT4.
- Trailing stop simulation and labeling: generates synthetic trailing stop PnL labels for training and evaluation.
- Execution policy benchmarks: simulate fixed and shrinking trailing stops, and compare outcomes.

Key responsibilities:
- Policy library construction and ranking
- Best price tracking for trailing stops
- Position state transitions and multi-position coordination
- Reversal logic for opposite-side entries
- Metrics: profit factor, win rate, average hold, blocked signals

**Section sources**
- [exit_policy_research.py:81-122](file://API/exit_policy_research.py#L81-L122)
- [exit_policy_research.py:202-246](file://API/exit_policy_research.py#L202-L246)
- [exit_policy_research.py:259-283](file://API/exit_policy_research.py#L259-L283)
- [label_signals.py:728-843](file://processing/label_signals.py#L728-L843)
- [benchmark_execution_policy_v2.py:271-299](file://ML/benchmark_execution_policy_v2.py#L271-L299)

## Architecture Overview
The system separates offline research and labeling from runtime export and execution.

```mermaid
sequenceDiagram
participant Research as "Exit Policy Research"
participant Signals as "Signal Frame"
participant Policies as "Policy Library"
participant Metrics as "Ranking & Metrics"
participant Export as "Frozen Policy Export"
Research->>Signals : Load market frame and merge ATR/ratios
Research->>Policies : Build policy grid (reverse/keep/profit guard/timeout)
Research->>Research : Simulate trades per policy
Research->>Metrics : Summarize PF, win rate, avg hold, blocked signals
Metrics-->>Research : Ranked policies
Research->>Export : Save best policy JSON with MQL thresholds
```

**Diagram sources**
- [exit_policy_research.py:329-358](file://API/exit_policy_research.py#L329-L358)
- [exit_policy_research.py:360-370](file://API/exit_policy_research.py#L360-L370)

**Section sources**
- [exit_policy_research.py:329-370](file://API/exit_policy_research.py#L329-L370)

## Detailed Component Analysis

### Exit Policy Research Engine
This module:
- Loads market data and merges OHLC with ML signals
- Computes derived ratios and ATR fallbacks
- Builds a library of exit policies (timeout, reverse close, weak edge, profit guard, layered)
- Simulates trades per policy and aggregates performance metrics
- Exports a frozen policy with MQL-friendly thresholds

Key logic highlights:
- Trade frame construction tracks best favorable excursion (peak high/low) and net PnL in ATR terms
- Exit triggers include reverse ratio crossing, weak edge keep ratio, profit guard threshold, and timeout
- Multi-position coordination: after an exit, blocked signals between entry and exit are counted; reversal logic reprocesses the same bar when the signal flips

```mermaid
flowchart TD
Start(["Start Simulation"]) --> Load["Load Market Frame<br/>Merge Signals + OHLC + ATR"]
Load --> BuildPolicies["Build Policy Library"]
BuildPolicies --> IterateTrades["Iterate Entries"]
IterateTrades --> BuildTradeFrame["Build Trade Frame<br/>Compute net_atr, fav_atr"]
BuildTradeFrame --> LoopBars["Iterate Bars"]
LoopBars --> CheckReverse{"opposite_ratio >= threshold?"}
CheckReverse --> |Yes| ExitReverse["Exit: reverse_ratio"]
CheckReverse --> |No| CheckHold{"bar < min_hold_bars?"}
CheckHold --> |Yes| NextBar["Next Bar"]
CheckHold --> |No| CheckKeep{"same_ratio >= keep_ratio_min?"}
CheckKeep --> |No| ExitWeak["Exit: weak_edge"]
CheckKeep --> |Yes| CheckGuard{"profit_guard enabled?"}
CheckGuard --> |Yes| CheckFav{"fav_atr >= profit_start_atr?"}
CheckFav --> |Yes| ExitGuard["Exit: profit_guard"]
CheckFav --> |No| NextBar
CheckGuard --> |No| NextBar
NextBar --> LoopBars
LoopBars --> Timeout{"Reached end?"}
Timeout --> |Yes| ExitTimeout["Exit: timeout"]
ExitReverse --> Record["Record Trade + Blocked Signals"]
ExitWeak --> Record
ExitGuard --> Record
ExitTimeout --> Record
Record --> NextEntry["Advance by exit_bar or 1"]
NextEntry --> IterateTrades
IterateTrades --> Done(["Summarize Metrics"])
```

**Diagram sources**
- [exit_policy_research.py:47-72](file://API/exit_policy_research.py#L47-L72)
- [exit_policy_research.py:158-194](file://API/exit_policy_research.py#L158-L194)
- [exit_policy_research.py:202-246](file://API/exit_policy_research.py#L202-L246)

**Section sources**
- [exit_policy_research.py:47-72](file://API/exit_policy_research.py#L47-L72)
- [exit_policy_research.py:158-194](file://API/exit_policy_research.py#L158-L194)
- [exit_policy_research.py:202-246](file://API/exit_policy_research.py#L202-L246)
- [test_exit_policy_research.py:7-21](file://tests/test_exit_policy_research.py#L7-L21)
- [test_exit_policy_research.py:23-37](file://tests/test_exit_policy_research.py#L23-L37)
- [test_exit_policy_research.py:39-59](file://tests/test_exit_policy_research.py#L39-L59)
- [test_exit_policy_research.py:113-129](file://tests/test_exit_policy_research.py#L113-L129)

### Best Price Tracking for Trailing Stops
Two complementary mechanisms are used:
- Synthetic labels: compute trailing stop PnL under fixed ATR trails for training targets
- Runtime simulation: track best favorable price and compute active trailing stops

```mermaid
flowchart TD
Entry(["Entry Bar"]) --> TrackBest["Track Best Favorable Extreme"]
TrackBest --> ComputeStop["Compute Stop Price = Best Extreme ± Trail Multiplier × ATR"]
ComputeStop --> Compare["Compare Against Low/High"]
Compare --> Hit{"Stop Hit?"}
Hit --> |Yes| Close["Close At Stop Price"]
Hit --> |No| Hold["Hold to Next Bar"]
Hold --> TrackBest
Close --> PnL["Compute PnL in ATR Terms"]
```

**Diagram sources**
- [label_signals.py:728-754](file://processing/label_signals.py#L728-L754)
- [benchmark_execution_policy_v2.py:271-299](file://ML/benchmark_execution_policy_v2.py#L271-L299)
- [benchmark_take_skip_mt4_trailing_sequential.py:135-162](file://ML/benchmark_take_skip_mt4_trailing_sequential.py#L135-L162)

**Section sources**
- [label_signals.py:728-754](file://processing/label_signals.py#L728-L754)
- [label_signals.py:757-843](file://processing/label_signals.py#L757-L843)
- [benchmark_execution_policy_v2.py:271-299](file://ML/benchmark_execution_policy_v2.py#L271-L299)
- [benchmark_take_skip_mt4_trailing_sequential.py:135-162](file://ML/benchmark_take_skip_mt4_trailing_sequential.py#L135-L162)

### Position State Management and Multi-Position Coordination
- Position state transitions:
  - Enter: signal != 0 and bar is entry
  - Exit: triggered by reverse ratio, weak edge keep ratio, profit guard, or timeout
  - Reversal: when exiting due to reverse ratio on an opposite signal, the same bar is reprocessed to allow immediate opposite entry
- Multi-position coordination:
  - During a trade, blocked signals between entry and exit are counted to quantify interference
  - After exit, the iterator advances either by exit_bar (for reversals) or by 1 (for normal exits)

```mermaid
sequenceDiagram
participant S as "Signals"
participant R as "Research Engine"
participant T as "Trade Frame"
participant M as "Metrics"
S->>R : Entry signal detected
R->>T : Build trade frame (net_atr, fav_atr)
loop For each bar
T->>R : Evaluate exit conditions
alt Reverse ratio hit
R->>R : Mark exit reason = reverse_ratio
R->>R : Reprocess same bar for opposite entry
else Weak edge or profit guard or timeout
R->>R : Mark exit reason and record PnL
end
end
R->>M : Count blocked signals and summarize metrics
```

**Diagram sources**
- [exit_policy_research.py:202-246](file://API/exit_policy_research.py#L202-L246)
- [exit_policy_research.py:259-283](file://API/exit_policy_research.py#L259-L283)

**Section sources**
- [exit_policy_research.py:202-246](file://API/exit_policy_research.py#L202-L246)
- [exit_policy_research.py:259-283](file://API/exit_policy_research.py#L259-L283)
- [test_exit_policy_research.py:113-129](file://tests/test_exit_policy_research.py#L113-L129)

### Reversal Logic for Opposite Entry
- When a trade exits because the opposite ratio crosses the reverse threshold, the engine reprocesses the same bar to allow an immediate opposite entry
- This ensures that contradictory signals do not block profitable reversals

```mermaid
sequenceDiagram
participant Engine as "Engine"
participant TF as "Trade Frame"
participant Bar as "Current Bar"
Engine->>TF : Iterate bars
TF->>Engine : opposite_ratio >= reverse_ratio?
alt Yes
Engine->>Engine : Exit reason = reverse_ratio
Engine->>Bar : Reprocess same bar for opposite entry
else No
Engine->>TF : Continue
end
```

**Diagram sources**
- [exit_policy_research.py:241-244](file://API/exit_policy_research.py#L241-L244)
- [test_exit_policy_research.py:113-129](file://tests/test_exit_policy_research.py#L113-L129)

**Section sources**
- [exit_policy_research.py:241-244](file://API/exit_policy_research.py#L241-L244)
- [test_exit_policy_research.py:113-129](file://tests/test_exit_policy_research.py#L113-L129)

### Take/Skip and Trailing Stop Target Export
- Rule application selects signals based on probability thresholds or top-K selection among active rows
- Export pipeline writes atomic CSV files and optionally copies to MT4 tester/runtime locations
- Diagnostic mode can expand sparse predictions into full series using base CSV and direction source

```mermaid
flowchart TD
LoadPred["Load Predictions"] --> ApplyRule["Apply Frozen Rule<br/>prob_ge_threshold/top_k_probability"]
ApplyRule --> Mask["Mask Signals"]
Mask --> Expand{"Base CSV Provided?"}
Expand --> |Yes| Merge["Merge with Base Full Series"]
Expand --> |No| Keep["Keep Sparse Series"]
Merge --> Write["Write CSV (Atomic)"]
Keep --> Write
Write --> Copy{"Copy to MT4?"}
Copy --> |Yes| MT4["tester/runtime paths"]
Copy --> |No| Done["Done"]
```

**Diagram sources**
- [export_take_skip_trailing_stop_v2_signals.py:93-117](file://API/export_take_skip_trailing_stop_v2_signals.py#L93-L117)
- [export_take_skip_trailing_stop_v2_signals.py:179-250](file://API/export_take_skip_trailing_stop_v2_signals.py#L179-L250)

**Section sources**
- [export_take_skip_trailing_stop_v2_signals.py:93-117](file://API/export_take_skip_trailing_stop_v2_signals.py#L93-L117)
- [export_take_skip_trailing_stop_v2_signals.py:179-250](file://API/export_take_skip_trailing_stop_v2_signals.py#L179-L250)

### Benchmarking Targets and Metrics
- Take/skip trailing stop v2: define target columns and compute BCE, positive rates, and per-column metrics
- Trailing stop target v1: extract true PnL targets for training
- Quantile targets: compute pinball loss, interval coverage, median width, and correlation metrics

```mermaid
classDiagram
class TakeSkipV2Task {
+TAKE_SKIP_TRAILING_STOP_V2_COLUMNS
+split_take_skip_v2_targets(df)
+build_take_skip_v2_export_frame(...)
+compute_take_skip_v2_metrics(y_true, y_prob)
}
class TrailingStopTargetTask {
+TRAILING_STOP_TARGET_COLUMNS
+split_trailing_stop_targets(df)
+build_trailing_stop_export_frame(...)
}
class TrailingStopQuantileTask {
+TRAILING_STOP_TARGET_QUANTILE_TARGET
+split_trailing_stop_quantile_target(df)
+build_trailing_stop_quantile_export_frame(...)
+compute_trailing_stop_quantile_metrics(true_target, pred_q10, pred_q50, pred_q90)
}
class BenchmarkTakeSkipV2 {
+build_candidate_table(...)
+pick_validation_winner(...)
+run_benchmark(...)
}
class BenchmarkTrailingStopTarget {
+summarize_candidate(...)
+pick_validation_winner(...)
}
class BenchmarkTrailingStopQuantile {
+build_candidate_table(...)
+pick_validation_winner(...)
+run_benchmark(...)
}
BenchmarkTakeSkipV2 --> TakeSkipV2Task : "uses"
BenchmarkTrailingStopTarget --> TrailingStopTargetTask : "uses"
BenchmarkTrailingStopQuantile --> TrailingStopQuantileTask : "uses"
```

**Diagram sources**
- [take_skip_trailing_stop_v2_task.py:12-111](file://ML/take_skip_trailing_stop_v2_task.py#L12-L111)
- [trailing_stop_target_task.py:5-25](file://ML/trailing_stop_target_task.py#L5-L25)
- [trailing_stop_target_quantile_task.py:5-107](file://ML/trailing_stop_target_quantile_task.py#L5-L107)
- [benchmark_take_skip_trailing_stop_v2.py:71-144](file://ML/benchmark_take_skip_trailing_stop_v2.py#L71-L144)
- [benchmark_trailing_stop_target.py:4-32](file://ML/benchmark_trailing_stop_target.py#L4-L32)
- [benchmark_trailing_stop_target_quantile.py:150-248](file://ML/benchmark_trailing_stop_target_quantile.py#L150-L248)

**Section sources**
- [take_skip_trailing_stop_v2_task.py:12-111](file://ML/take_skip_trailing_stop_v2_task.py#L12-L111)
- [trailing_stop_target_task.py:5-25](file://ML/trailing_stop_target_task.py#L5-L25)
- [trailing_stop_target_quantile_task.py:5-107](file://ML/trailing_stop_target_quantile_task.py#L5-L107)
- [benchmark_take_skip_trailing_stop_v2.py:71-144](file://ML/benchmark_take_skip_trailing_stop_v2.py#L71-L144)
- [benchmark_trailing_stop_target.py:4-32](file://ML/benchmark_trailing_stop_target.py#L4-L32)
- [benchmark_trailing_stop_target_quantile.py:150-248](file://ML/benchmark_trailing_stop_target_quantile.py#L150-L248)

## Dependency Analysis
- The research engine depends on market data and computed ATR/ratio columns
- Labeling utilities depend on OHLC and ATR computation
- Export utilities depend on frozen rule payloads and optional base CSVs
- Benchmarking utilities depend on labeled frames and target columns

```mermaid
graph LR
EPR["exit_policy_research.py"] --> LAB["label_signals.py"]
EXP["export_take_skip_trailing_stop_v2_signals.py"] --> TSK1["take_skip_trailing_stop_v2_task.py"]
BM1["benchmark_take_skip_trailing_stop_v2.py"] --> TSK1
BM2["benchmark_trailing_stop_target.py"] --> TSK2["trailing_stop_target_task.py"]
BM3["benchmark_trailing_stop_target_quantile.py"] --> TSK3["trailing_stop_target_quantile_task.py"]
BMEP["benchmark_execution_policy_v2.py"] --> LAB
BMT["benchmark_take_skip_mt4_trailing_sequential.py"] --> LAB
```

**Diagram sources**
- [exit_policy_research.py:329-358](file://API/exit_policy_research.py#L329-L358)
- [export_take_skip_trailing_stop_v2_signals.py:179-250](file://API/export_take_skip_trailing_stop_v2_signals.py#L179-L250)
- [benchmark_take_skip_trailing_stop_v2.py:71-144](file://ML/benchmark_take_skip_trailing_stop_v2.py#L71-L144)
- [benchmark_trailing_stop_target.py:4-32](file://ML/benchmark_trailing_stop_target.py#L4-L32)
- [benchmark_trailing_stop_target_quantile.py:150-248](file://ML/benchmark_trailing_stop_target_quantile.py#L150-L248)
- [label_signals.py:728-843](file://processing/label_signals.py#L728-L843)
- [benchmark_execution_policy_v2.py:271-299](file://ML/benchmark_execution_policy_v2.py#L271-L299)
- [benchmark_take_skip_mt4_trailing_sequential.py:135-162](file://ML/benchmark_take_skip_mt4_trailing_sequential.py#L135-L162)

**Section sources**
- [exit_policy_research.py:329-358](file://API/exit_policy_research.py#L329-L358)
- [export_take_skip_trailing_stop_v2_signals.py:179-250](file://API/export_take_skip_trailing_stop_v2_signals.py#L179-L250)
- [benchmark_take_skip_trailing_stop_v2.py:71-144](file://ML/benchmark_take_skip_trailing_stop_v2.py#L71-L144)
- [benchmark_trailing_stop_target.py:4-32](file://ML/benchmark_trailing_stop_target.py#L4-L32)
- [benchmark_trailing_stop_target_quantile.py:150-248](file://ML/benchmark_trailing_stop_target_quantile.py#L150-L248)
- [label_signals.py:728-843](file://processing/label_signals.py#L728-L843)
- [benchmark_execution_policy_v2.py:271-299](file://ML/benchmark_execution_policy_v2.py#L271-L299)
- [benchmark_take_skip_mt4_trailing_sequential.py:135-162](file://ML/benchmark_take_skip_mt4_trailing_sequential.py#L135-L162)

## Performance Considerations
- Policy ranking prioritizes profit factor and applies a minimum trade floor to avoid overfitting to small samples
- Metrics include PF, win rate, average hold bars, and average blocked signals to balance expectancy and interference
- Export pipeline writes atomic CSVs and optionally mirrors to MT4 paths for parity testing

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and checks:
- Missing ATR column: fallback computation is applied during market frame loading
- Invalid rule selectors: only supported selectors are accepted; thresholds validated accordingly
- Non-finite values in metrics: strict validation prevents invalid inputs
- Split profile mismatch: test_final requires a frozen policy JSON; otherwise, a policy library is built

**Section sources**
- [exit_policy_research.py:286-289](file://API/exit_policy_research.py#L286-L289)
- [exit_policy_research.py:387-386](file://API/exit_policy_research.py#L387-L386)
- [export_take_skip_trailing_stop_v2_signals.py:60-91](file://API/export_take_skip_trailing_stop_v2_signals.py#L60-L91)
- [take_skip_trailing_stop_v2_task.py:82-94](file://ML/take_skip_trailing_stop_v2_task.py#L82-L94)

## Conclusion
The ML Signal Library provides a robust framework for position management and exit strategies. The research engine enables offline evaluation of multiple exit policies, while labeling and benchmarking utilities support reliable training and selection of trailing stop targets. The export pipeline integrates seamlessly with MT4 environments, and the reversal logic ensures dynamic responsiveness to contradictory signals. Together, these components deliver a production-ready foundation for disciplined trading with ATR-based exits and performance-driven policy selection.