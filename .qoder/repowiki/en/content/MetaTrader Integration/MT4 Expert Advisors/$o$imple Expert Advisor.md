# $o$imple Expert Advisor

<cite>
**Referenced Files in This Document**
- [README.md](file://MT/MQL4/README.md)
- [$o$imple.mq4](file://MT/MQL4/Experts/$o$imple.mq4)
- [signal_parser.mqh](file://MT/MQL4/Include/signal_parser.mqh)
- [risk_manager.mqh](file://MT/MQL4/Include/risk_manager.mqh)
- [order_executor.mqh](file://MT/MQL4/Include/order_executor.mqh)
- [logger.mqh](file://MT/MQL4/Include/logger.mqh)
- [position_manager.mqh](file://MT/MQL4/Include/position_manager.mqh)
- [ml_signal_bridge.mqh](file://MT/MQL4/Include/ml_signal_bridge.mqh)
- [config.mqh](file://MT/MQL4/Include/config.mqh)
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
This document provides comprehensive documentation for the $o$imple expert advisor (EA), the primary MQL4 trading robot implementation. It explains initialization and deinitialization routines, the start loop behavior on tick events, signal processing from Python-generated signals, position management strategies, risk controls, order execution mechanisms, MT4-specific event handling, chart interactions, configuration options, error handling, logging, and debugging techniques within the MQL4 environment.

## Project Structure
The EA resides under the MQL4 Experts directory and integrates with include modules for parsing ML signals, managing positions, executing orders, logging, and configuration. The structure follows a modular design where the EA orchestrates components via well-defined interfaces.

```mermaid
graph TB
subgraph "MQL4 Experts"
EA["$o$imple.mq4"]
end
subgraph "MQL4 Include"
SP["signal_parser.mqh"]
RM["risk_manager.mqh"]
OE["order_executor.mqh"]
LG["logger.mqh"]
PM["position_manager.mqh"]
MSB["ml_signal_bridge.mqh"]
CFG["config.mqh"]
end
EA --> SP
EA --> RM
EA --> OE
EA --> PM
EA --> MSB
EA --> CFG
SP --> LG
RM --> LG
OE --> LG
PM --> LG
MSB --> SP
MSB --> CFG
```

**Diagram sources**
- [$o$imple.mq4:1-200](file://MT/MQL4/Experts/$o$imple.mq4#L1-L200)
- [signal_parser.mqh:1-150](file://MT/MQL4/Include/signal_parser.mqh#L1-L150)
- [risk_manager.mqh:1-120](file://MT/MQL4/Include/risk_manager.mqh#L1-L120)
- [order_executor.mqh:1-180](file://MT/MQL4/Include/order_executor.mqh#L1-L180)
- [logger.mqh:1-100](file://MT/MQL4/Include/logger.mqh#L1-L100)
- [position_manager.mqh:1-160](file://MT/MQL4/Include/position_manager.mqh#L1-L160)
- [ml_signal_bridge.mqh:1-140](file://MT/MQL4/Include/ml_signal_bridge.mqh#L1-L140)
- [config.mqh:1-110](file://MT/MQL4/Include/config.mqh#L1-L110)

**Section sources**
- [README.md:1-50](file://MT/MQL4/README.md#L1-L50)

## Core Components
- Initialization and Deinitialization:
  - OnInit sets up inputs, loads configuration, initializes logging, validates symbols/timeframes, and prepares state for signal processing and order execution.
  - OnDeinit cleans up resources, flushes logs, and releases any allocated memory or handles.
- Start Loop:
  - OnTick processes incoming ticks, updates market data, checks for new signals, evaluates risk and position constraints, and executes orders when conditions are met.
- Signal Processing:
  - Parses Python-generated signals from files or streams, validates schema, maps to internal representations, and triggers entry logic.
- Position Management:
  - Tracks open positions, manages exits based on trailing stops, take-profit, skip rules, and time-based closures; enforces one-position-per-symbol policy if configured.
- Risk Management:
  - Enforces maximum lot size, per-trade risk limits, daily loss caps, spread filters, and slippage tolerances.
- Order Execution:
  - Places market/limit orders, handles partial fills, retries with backoff, and records trade results.
- Logging and Diagnostics:
  - Centralized logger writes to file and/or terminal, supports verbosity levels, and includes diagnostic snapshots for debugging.

**Section sources**
- [$o$imple.mq4:1-300](file://MT/MQL4/Experts/$o$imple.mq4#L1-L300)
- [signal_parser.mqh:1-150](file://MT/MQL4/Include/signal_parser.mqh#L1-L150)
- [risk_manager.mqh:1-120](file://MT/MQL4/Include/risk_manager.mqh#L1-L120)
- [order_executor.mqh:1-180](file://MT/MQL4/Include/order_executor.mqh#L1-L180)
- [position_manager.mqh:1-160](file://MT/MQL4/Include/position_manager.mqh#L1-L160)
- [ml_signal_bridge.mqh:1-140](file://MT/MQL4/Include/ml_signal_bridge.mqh#L1-L140)
- [config.mqh:1-110](file://MT/MQL4/Include/config.mqh#L1-L110)

## Architecture Overview
The EA operates as an event-driven system driven by tick events. Each tick triggers market data refresh, signal validation, risk checks, and potential order placement. Signals originate from Python pipelines and are consumed via a bridge module that ensures schema compatibility and robust parsing.

```mermaid
sequenceDiagram
participant MT4 as "MT4 Terminal"
participant EA as "$o$imple.mq4"
participant Bridge as "ml_signal_bridge.mqh"
participant Parser as "signal_parser.mqh"
participant Risk as "risk_manager.mqh"
participant Pos as "position_manager.mqh"
participant Exec as "order_executor.mqh"
participant Log as "logger.mqh"
MT4->>EA : OnTick()
EA->>Log : log("tick received")
EA->>Bridge : fetch_signals(symbol)
Bridge-->>EA : validated_signals[]
EA->>Parser : parse(signal)
EA->>Risk : check_risk(signal)
Risk-->>EA : approved?
EA->>Pos : evaluate_position(signal)
Pos-->>EA : action (enter/hold/close)
alt enter
EA->>Exec : place_order(signal)
Exec-->>EA : result
else close
EA->>Exec : close_position(signal)
Exec-->>EA : result
end
EA->>Log : log("action completed")
```

**Diagram sources**
- [$o$imple.mq4:1-300](file://MT/MQL4/Experts/$o$imple.mq4#L1-L300)
- [ml_signal_bridge.mqh:1-140](file://MT/MQL4/Include/ml_signal_bridge.mqh#L1-L140)
- [signal_parser.mqh:1-150](file://MT/MQL4/Include/signal_parser.mqh#L1-L150)
- [risk_manager.mqh:1-120](file://MT/MQL4/Include/risk_manager.mqh#L1-L120)
- [position_manager.mqh:1-160](file://MT/MQL4/Include/position_manager.mqh#L1-L160)
- [order_executor.mqh:1-180](file://MT/MQL4/Include/order_executor.mqh#L1-L180)
- [logger.mqh:1-100](file://MT/MQL4/Include/logger.mqh#L1-L100)

## Detailed Component Analysis

### Initialization and Deinitialization
- OnInit:
  - Validates input parameters, loads configuration from config.mqh, initializes logger, sets symbol and timeframe context, and preloads necessary market data.
  - Registers periodic tasks such as heartbeat logging and signal polling intervals.
- OnDeinit:
  - Flushes pending logs, closes file handles, and resets global state to ensure clean shutdown.

```mermaid
flowchart TD
Start([OnInit Entry]) --> ValidateInputs["Validate Inputs"]
ValidateInputs --> LoadConfig["Load Config"]
LoadConfig --> InitLogger["Initialize Logger"]
InitLogger --> SetupMarket["Setup Market Data"]
SetupMarket --> RegisterTasks["Register Periodic Tasks"]
RegisterTasks --> Ready([Ready])
Ready --> OnDeinit([OnDeinit Entry])
OnDeinit --> FlushLogs["Flush Logs"]
FlushLogs --> Cleanup["Cleanup Resources"]
Cleanup --> End([Exit])
```

**Diagram sources**
- [$o$imple.mq4:1-120](file://MT/MQL4/Experts/$o$imple.mq4#L1-L120)
- [config.mqh:1-110](file://MT/MQL4/Include/config.mqh#L1-L110)
- [logger.mqh:1-100](file://MT/MQL4/Include/logger.mqh#L1-L100)

**Section sources**
- [$o$imple.mq4:1-120](file://MT/MQL4/Experts/$o$simple.mq4#L1-L120)
- [config.mqh:1-110](file://MT/MQL4/Include/config.mqh#L1-L110)

### Tick Processing and Event Handling
- OnTick:
  - Updates bid/ask, spreads, and session filters.
  - Invokes signal bridge to retrieve new signals since last processed timestamp.
  - Applies risk and position constraints before order submission.
  - Handles partial fills and retry logic with exponential backoff.
  - Emits telemetry and diagnostic snapshots for monitoring.

```mermaid
flowchart TD
TickStart([OnTick Entry]) --> UpdateData["Update Market Data"]
UpdateData --> CheckSpread{"Spread OK?"}
CheckSpread --> |No| SkipTick["Skip Tick"]
CheckSpread --> |Yes| FetchSignals["Fetch New Signals"]
FetchSignals --> ParseSignals["Parse & Validate Signals"]
ParseSignals --> RiskCheck["Risk Checks"]
RiskCheck --> Approved{"Approved?"}
Approved --> |No| LogReject["Log Rejection"]
Approved --> |Yes| PositionEval["Evaluate Position"]
PositionEval --> Action{"Action"}
Action --> |Enter| PlaceOrder["Place Order"]
Action --> |Close| CloseOrder["Close Order"]
PlaceOrder --> HandleResult["Handle Result"]
CloseOrder --> HandleResult
HandleResult --> EmitTelemetry["Emit Telemetry"]
EmitTelemetry --> TickEnd([OnTick Exit])
LogReject --> TickEnd
SkipTick --> TickEnd
```

**Diagram sources**
- [$o$imple.mq4:120-300](file://MT/MQL4/Experts/$o$imple.mq4#L120-L300)
- [ml_signal_bridge.mqh:1-140](file://MT/MQL4/Include/ml_signal_bridge.mqh#L1-L140)
- [signal_parser.mqh:1-150](file://MT/MQL4/Include/signal_parser.mqh#L1-L150)
- [risk_manager.mqh:1-120](file://MT/MQL4/Include/risk_manager.mqh#L1-L120)
- [position_manager.mqh:1-160](file://MT/MQL4/Include/position_manager.mqh#L1-L160)
- [order_executor.mqh:1-180](file://MT/MQL4/Include/order_executor.mqh#L1-L180)
- [logger.mqh:1-100](file://MT/MQL4/Include/logger.mqh#L1-L100)

**Section sources**
- [$o$imple.mq4:120-300](file://MT/MQL4/Experts/$o$imple.mq4#L120-L300)

### Signal Processing from Python-Generated Signals
- ml_signal_bridge:
  - Polls or receives signals from Python pipeline outputs (files or network).
  - Ensures schema compliance and normalizes fields across versions.
  - Deduplicates signals and maintains a cursor for incremental consumption.
- signal_parser:
  - Converts raw payloads into typed structures used by the EA.
  - Applies validation rules and rejects malformed entries.

```mermaid
classDiagram
class MLSignalBridge {
+fetch_signals(symbol) Signal[]
+validate_schema(payload) bool
+normalize_fields(signal) Signal
+deduplicate(signals) Signal[]
}
class SignalParser {
+parse(raw) Signal
+validate(signal) bool
+map_to_internal(signal) InternalSignal
}
MLSignalBridge --> SignalParser : "uses"
```

**Diagram sources**
- [ml_signal_bridge.mqh:1-140](file://MT/MQL4/Include/ml_signal_bridge.mqh#L1-L140)
- [signal_parser.mqh:1-150](file://MT/MQL4/Include/signal_parser.mqh#L1-L150)

**Section sources**
- [ml_signal_bridge.mqh:1-140](file://MT/MQL4/Include/ml_signal_bridge.mqh#L1-L140)
- [signal_parser.mqh:1-150](file://MT/MQL4/Include/signal_parser.mqh#L1-L150)

### Position Management Strategies
- position_manager:
  - Tracks active positions per symbol, including entry price, stop-loss, take-profit, and trailing stop parameters.
  - Implements exit policies: fixed TP/SL, trailing stops, time-based closure, and skip rules.
  - Enforces single-position policy and prevents overexposure.

```mermaid
stateDiagram-v2
[*] --> Idle
Idle --> Opened : "entry signal approved"
Opened --> Trailing : "update trailing stop"
Opened --> Closed_TP : "take-profit hit"
Opened --> Closed_SL : "stop-loss hit"
Opened --> Closed_Time : "time-based closure"
Opened --> Closed_Skip : "skip rule triggered"
Closed_TP --> Idle
Closed_SL --> Idle
Closed_Time --> Idle
Closed_Skip --> Idle
```

**Diagram sources**
- [position_manager.mqh:1-160](file://MT/MQL4/Include/position_manager.mqh#L1-L160)

**Section sources**
- [position_manager.mqh:1-160](file://MT/MQL4/Include/position_manager.mqh#L1-L160)

### Risk Management Parameters
- risk_manager:
  - Enforces per-trade risk limits, maximum lot sizes, daily drawdown caps, spread thresholds, and slippage tolerance.
  - Integrates with account equity and margin checks to prevent over-leverage.

```mermaid
flowchart TD
Start([Risk Check Entry]) --> LoadParams["Load Risk Params"]
LoadParams --> CheckEquity["Check Equity & Margin"]
CheckEquity --> SpreadOK{"Spread Within Limit?"}
SpreadOK --> |No| Reject["Reject Trade"]
SpreadOK --> |Yes| LotSize["Compute Lot Size"]
LotSize --> DailyCap{"Within Daily Cap?"}
DailyCap --> |No| Reject
DailyCap --> |Yes| Approve["Approve Trade"]
Approve --> End([Exit])
Reject --> End
```

**Diagram sources**
- [risk_manager.mqh:1-120](file://MT/MQL4/Include/risk_manager.mqh#L1-L120)

**Section sources**
- [risk_manager.mqh:1-120](file://MT/MQL4/Include/risk_manager.mqh#L1-L120)

### Order Execution Mechanisms
- order_executor:
  - Submits market and limit orders with retry logic and exponential backoff.
  - Handles partial fills, rejections, and errors; logs detailed diagnostics.
  - Supports order modifications (modify SL/TP) and cancellations.

```mermaid
sequenceDiagram
participant EA as "$o$imple.mq4"
participant Exec as "order_executor.mqh"
participant Server as "Broker Server"
EA->>Exec : place_order(type, symbol, lots, sl, tp)
Exec->>Server : send_request()
Server-->>Exec : response
alt success
Exec-->>EA : order_id
else failure
Exec->>Exec : retry_with_backoff()
Exec-->>EA : error details
end
```

**Diagram sources**
- [order_executor.mqh:1-180](file://MT/MQL4/Include/order_executor.mqh#L1-L180)

**Section sources**
- [order_executor.mqh:1-180](file://MT/MQL4/Include/order_executor.mqh#L1-L180)

### Configuration Options and Customization Points
- config.mqh:
  - Defines input parameters for strategy tuning: signal thresholds, risk limits, position sizing, spread filters, logging verbosity, and feature toggles.
  - Provides defaults and validation functions to ensure safe runtime configuration.

```mermaid
classDiagram
class Config {
+double signal_threshold
+double max_lot_size
+double daily_loss_cap
+int spread_limit_points
+bool enable_trailing_stop
+bool single_position_per_symbol
+int log_verbosity_level
+validate_inputs() bool
}
```

**Diagram sources**
- [config.mqh:1-110](file://MT/MQL4/Include/config.mqh#L1-L110)

**Section sources**
- [config.mqh:1-110](file://MT/MQL4/Include/config.mqh#L1-L110)

### Error Handling, Logging, and Debugging
- logger.mqh:
  - Centralized logging with file and terminal output, supports severity levels, timestamps, and structured messages.
  - Includes diagnostic snapshots for state inspection during failures.
- Debugging Techniques:
  - Use Print() and Comment() for quick diagnostics.
  - Enable verbose logging and capture tick-level traces.
  - Inspect signal files and parsed outputs for correctness.

**Section sources**
- [logger.mqh:1-100](file://MT/MQL4/Include/logger.mqh#L1-L100)

## Dependency Analysis
The EA depends on several include modules for modularity and separation of concerns. Dependencies are designed to minimize coupling while enabling clear interfaces.

```mermaid
graph TB
EA["$o$imple.mq4"]
SP["signal_parser.mqh"]
RM["risk_manager.mqh"]
OE["order_executor.mqh"]
PM["position_manager.mqh"]
MSB["ml_signal_bridge.mqh"]
CFG["config.mqh"]
LG["logger.mqh"]
EA --> SP
EA --> RM
EA --> OE
EA --> PM
EA --> MSB
EA --> CFG
SP --> LG
RM --> LG
OE --> LG
PM --> LG
MSB --> SP
MSB --> CFG
```

**Diagram sources**
- [$o$imple.mq4:1-300](file://MT/MQL4/Experts/$o$imple.mq4#L1-L300)
- [signal_parser.mqh:1-150](file://MT/MQL4/Include/signal_parser.mqh#L1-L150)
- [risk_manager.mqh:1-120](file://MT/MQL4/Include/risk_manager.mqh#L1-L120)
- [order_executor.mqh:1-180](file://MT/MQL4/Include/order_executor.mqh#L1-L180)
- [position_manager.mqh:1-160](file://MT/MQL4/Include/position_manager.mqh#L1-L160)
- [ml_signal_bridge.mqh:1-140](file://MT/MQL4/Include/ml_signal_bridge.mqh#L1-L140)
- [config.mqh:1-110](file://MT/MQL4/Include/config.mqh#L1-L110)
- [logger.mqh:1-100](file://MT/MQL4/Include/logger.mqh#L1-L100)

**Section sources**
- [$o$imple.mq4:1-300](file://MT/MQL4/Experts/$o$imple.mq4#L1-L300)

## Performance Considerations
- Efficient tick processing:
  - Avoid heavy computations inside OnTick; defer to background tasks where possible.
  - Cache frequently accessed market data and reduce redundant function calls.
- Signal polling:
  - Implement incremental consumption and deduplication to minimize overhead.
- Order execution:
  - Use batch operations and avoid excessive retries; implement exponential backoff.
- Memory management:
  - Free temporary arrays and objects promptly to prevent memory leaks.
- Logging:
  - Control verbosity levels to balance observability and performance.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Common Issues:
  - Signal parsing failures: verify schema and payload format; inspect parsed outputs.
  - Order rejections: check spread limits, margin requirements, and broker restrictions.
  - Position not closing: validate exit conditions and trailing stop updates.
- Debugging Steps:
  - Increase log verbosity and capture tick-level traces.
  - Use Print() and Comment() to monitor critical variables.
  - Inspect signal files and parsed structures for anomalies.
- Recovery Actions:
  - Reset state and reload configuration if corrupted.
  - Restart the EA after resolving external dependencies (e.g., Python pipeline).

**Section sources**
- [logger.mqh:1-100](file://MT/MQL4/Include/logger.mqh#L1-L100)
- [$o$imple.mq4:1-300](file://MT/MQL4/Experts/$o$imple.mq4#L1-L300)

## Conclusion
The $o$imple EA is a modular, event-driven MQL4 trading robot that integrates Python-generated ML signals with robust risk management, position control, and order execution. Its architecture emphasizes clarity, maintainability, and performance, making it suitable for live trading environments. Proper configuration, logging, and debugging practices are essential for reliable operation.

[No sources needed since this section summarizes without analyzing specific files]