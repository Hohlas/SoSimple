# Signal Export & Integration Formats

<cite>
**Referenced Files in This Document**
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [ML/baseline/export_mt5_entry_signals.py](file://ML/baseline/export_mt5_entry_signals.py)
- [ML/baseline/mt5_signal_schema.py](file://ML/baseline/mt5_signal_schema.py)
- [tests/test_export_entry_path_v1_signals.py](file://tests/test_export_entry_path_v1_signals.py)
- [tests/test_export_entry_path_v1_quantile_signals.py](file://tests/test_export_entry_path_v1_quantile_signals.py)
- [tests/test_export_take_skip_trailing_stop_v2_signals.py](file://tests/test_export_take_skip_trailing_stop_v2_signals.py)
- [tests/test_mt5_signal_executor_schema.py](file://tests/test_mt5_signal_executor_schema.py)
- [API/api_server.py](file://API/api_server.py)
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
This document specifies the signal export and integration formats used by the SoSimple system. It covers:
- Entry path v1 signals (CSV, JSON), including field definitions, timestamp handling, and confidence scoring
- Take-skip-trailing-stop v2 signals (position sizing, stop-loss levels, trailing stops)
- Quantile-based signals with uncertainty bounds and probability distributions
- MT4/MT5 integration schemas and real-time streaming formats for live trading
- Examples, parsing utilities, validation procedures, versioning strategy, and backward compatibility considerations

## Project Structure
Signal exports are implemented as Python modules under API/, with corresponding tests under tests/. MT5-specific schema and export utilities are under ML/baseline/. Real-time streaming is exposed via an API server and a telemetry watcher.

```mermaid
graph TB
subgraph "API Exports"
A["export_entry_path_v1_signals.py"]
B["export_entry_path_v1_quantile_signals.py"]
C["export_take_skip_trailing_stop_v2_signals.py"]
end
subgraph "MT Integration"
D["export_mt5_entry_signals.py"]
E["mt5_signal_schema.py"]
end
subgraph "Runtime"
F["api_server.py"]
G["telemetry_signal_watcher.py"]
end
subgraph "Tests"
H["test_export_entry_path_v1_signals.py"]
I["test_export_entry_path_v1_quantile_signals.py"]
J["test_export_take_skip_trailing_stop_v2_signals.py"]
K["test_mt5_signal_executor_schema.py"]
end
A --> H
B --> I
C --> J
D --> K
E --> K
F --> G
```

**Diagram sources**
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [ML/baseline/export_mt5_entry_signals.py](file://ML/baseline/export_mt5_entry_signals.py)
- [ML/baseline/mt5_signal_schema.py](file://ML/baseline/mt5_signal_schema.py)
- [API/api_server.py](file://API/api_server.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)
- [tests/test_export_entry_path_v1_signals.py](file://tests/test_export_entry_path_v1_signals.py)
- [tests/test_export_entry_path_v1_quantile_signals.py](file://tests/test_export_entry_path_v1_quantile_signals.py)
- [tests/test_export_take_skip_trailing_stop_v2_signals.py](file://tests/test_export_take_skip_trailing_stop_v2_signals.py)
- [tests/test_mt5_signal_executor_schema.py](file://tests/test_mt5_signal_executor_schema.py)

**Section sources**
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [ML/baseline/export_mt5_entry_signals.py](file://ML/baseline/export_mt5_entry_signals.py)
- [ML/baseline/mt5_signal_schema.py](file://ML/baseline/mt5_signal_schema.py)
- [API/api_server.py](file://API/api_server.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)
- [tests/test_export_entry_path_v1_signals.py](file://tests/test_export_entry_path_v1_signals.py)
- [tests/test_export_entry_path_v1_quantile_signals.py](file://tests/test_export_entry_path_v1_quantile_signals.py)
- [tests/test_export_take_skip_trailing_stop_v2_signals.py](file://tests/test_export_take_skip_trailing_stop_v2_signals.py)
- [tests/test_mt5_signal_executor_schema.py](file://tests/test_mt5_signal_executor_schema.py)

## Core Components
- Entry Path v1 exporter: Produces CSV and JSON outputs for entry-path predictions with timestamps and confidence scores.
- Entry Path v1 Quantile exporter: Adds quantile-based uncertainty bounds and distributional outputs.
- Take-Skip-Trailing-Stop v2 exporter: Encodes position sizing, stop-loss, take-profit, and trailing stop parameters.
- MT5 signal exporter/schema: Maps SoSimple signals to MT5-compatible structures and validates schemas.
- API server and telemetry watcher: Provide endpoints and streaming for real-time signal consumption.

**Section sources**
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [ML/baseline/export_mt5_entry_signals.py](file://ML/baseline/export_mt5_entry_signals.py)
- [ML/baseline/mt5_signal_schema.py](file://ML/baseline/mt5_signal_schema.py)
- [API/api_server.py](file://API/api_server.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)

## Architecture Overview
The export pipeline transforms model outputs into standardized signal records, then serializes them to CSV/JSON or MT5-compatible structures. The API server exposes endpoints to trigger exports and stream signals; the telemetry watcher monitors and forwards signals for downstream consumers.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Server as "API Server"
participant Watcher as "Telemetry Watcher"
participant V1 as "Entry Path v1 Exporter"
participant QV1 as "Quantile v1 Exporter"
participant TSV2 as "Take-Skip-TS v2 Exporter"
participant MT5 as "MT5 Exporter/Schema"
Client->>Server : Request export/stream
Server->>Watcher : Start monitoring
Server->>V1 : Generate v1 signals
V1-->>Server : CSV/JSON records
Server->>QV1 : Generate quantile signals
QV1-->>Server : Quantile records
Server->>TSV2 : Generate v2 signals
TSV2-->>Server : Position/stop/trail records
Server->>MT5 : Convert to MT5 schema
MT5-->>Server : MT5-compatible payloads
Server-->>Client : Responses / Streamed events
```

**Diagram sources**
- [API/api_server.py](file://API/api_server.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [ML/baseline/export_mt5_entry_signals.py](file://ML/baseline/export_mt5_entry_signals.py)
- [ML/baseline/mt5_signal_schema.py](file://ML/baseline/mt5_signal_schema.py)

## Detailed Component Analysis

### Entry Path v1 Signals
- Output formats: CSV and JSON
- Key fields: instrument, timestamp, direction/side, confidence score, optional metadata
- Timestamp handling: ISO-like strings or epoch seconds; consistent timezone-aware serialization
- Confidence scoring: normalized probabilities or calibrated scores; thresholding rules applied downstream

Parsing and validation:
- CSV parser enforces required columns and types
- JSON validator checks schema completeness and value ranges
- Tests assert column presence, type correctness, and non-empty payloads

Example usage patterns:
- Batch export to file
- Streaming single-row events over HTTP/WebSocket

Backward compatibility:
- New optional fields appended without breaking existing parsers
- Version tag included when necessary

**Section sources**
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [tests/test_export_entry_path_v1_signals.py](file://tests/test_export_entry_path_v1_signals.py)

#### Sequence Diagram: v1 Export Flow
```mermaid
sequenceDiagram
participant Caller as "Caller"
participant Exporter as "v1 Exporter"
participant Validator as "Schema Validator"
participant Writer as "File/Stream Writer"
Caller->>Exporter : Build signals from model output
Exporter->>Validator : Validate fields and types
Validator-->>Exporter : OK or errors
Exporter->>Writer : Serialize to CSV/JSON
Writer-->>Caller : File path or streamed bytes
```

**Diagram sources**
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [tests/test_export_entry_path_v1_signals.py](file://tests/test_export_entry_path_v1_signals.py)

### Entry Path v1 Quantile Signals
- Output format: JSON (primary), CSV (optional)
- Fields: base signal fields plus quantiles (e.g., p10, p50, p90), uncertainty bounds, and distribution metadata
- Use cases: risk-aware execution, dynamic sizing based on uncertainty

Validation:
- Quantile ordering enforced (lower <= median <= higher)
- Bounds must be finite and within reasonable ranges

**Section sources**
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [tests/test_export_entry_path_v1_quantile_signals.py](file://tests/test_export_entry_path_v1_quantile_signals.py)

#### Class Diagram: Quantile Signal Record
```mermaid
classDiagram
class QuantileSignal {
+string instrument
+datetime timestamp
+float confidence
+float[] quantiles
+float uncertainty_lower
+float uncertainty_upper
+dict metadata
}
```

**Diagram sources**
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)

### Take-Skip-Trailing-Stop v2 Signals
- Purpose: Encode actionable trade parameters beyond direction
- Fields: position size, stop-loss level, take-profit level, trailing stop parameters, activation conditions
- Sizing: absolute units or fractional risk; supports per-instrument constraints

Validation:
- Stop-loss < entry < take-profit for long; reversed for short
- Trailing stop parameters must be positive and logically ordered

**Section sources**
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [tests/test_export_take_skip_trailing_stop_v2_signals.py](file://tests/test_export_take_skip_trailing_stop_v2_signals.py)

#### Flowchart: v2 Validation Logic
```mermaid
flowchart TD
Start(["Start"]) --> CheckSide["Determine side (long/short)"]
CheckSide --> CheckSL["Validate stop-loss vs entry"]
CheckSL --> SLValid{"SL valid?"}
SLValid --> |No| Error["Return validation error"]
SLValid --> |Yes| CheckTP["Validate take-profit vs entry"]
CheckTP --> TPValid{"TP valid?"}
TPValid --> |No| Error
TPValid --> |Yes| CheckTrail["Validate trailing stop params"]
CheckTrail --> TrailValid{"Trail valid?"}
TrailValid --> |No| Error
TrailValid --> |Yes| Emit["Emit v2 signal"]
Emit --> End(["End"])
Error --> End
```

**Diagram sources**
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)

### MT4/MT5 Integration Schemas
- Schema definition: Centralized schema for MT5-compatible payloads
- Export utility: Converts SoSimple signals to MT5 structures
- Field mapping: Ensures correct types and naming conventions for MT4/MT5 engines

Validation:
- Schema enforcement via tests
- Type checks and range validations for MT5 requirements

**Section sources**
- [ML/baseline/export_mt5_entry_signals.py](file://ML/baseline/export_mt5_entry_signals.py)
- [ML/baseline/mt5_signal_schema.py](file://ML/baseline/mt5_signal_schema.py)
- [tests/test_mt5_signal_executor_schema.py](file://tests/test_mt5_signal_executor_schema.py)

#### Class Diagram: MT5 Signal Mapping
```mermaid
classDiagram
class MQLSignal {
+string symbol
+string action
+double price
+double stopLoss
+double takeProfit
+double lotSize
+string comment
+int magicNumber
}
class SoSimpleSignal {
+string instrument
+string direction
+double entry
+double stopLoss
+double takeProfit
+double positionSize
}
SoSimpleSignal --> MQLSignal : "mapped to"
```

**Diagram sources**
- [ML/baseline/export_mt5_entry_signals.py](file://ML/baseline/export_mt5_entry_signals.py)
- [ML/baseline/mt5_signal_schema.py](file://ML/baseline/mt5_signal_schema.py)

### Real-Time Streaming Formats
- API server exposes endpoints to trigger exports and stream signals
- Telemetry watcher monitors signal generation and forwards events
- Formats: JSON messages with consistent schema; optional CSV batch endpoints

Usage:
- Subscribe to streaming endpoint for live signals
- Parse JSON payloads and apply client-side validation

**Section sources**
- [API/api_server.py](file://API/api_server.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)

#### Sequence Diagram: Live Streaming
```mermaid
sequenceDiagram
participant Client as "Client"
participant Server as "API Server"
participant Watcher as "Telemetry Watcher"
participant Exporters as "Export Modules"
Client->>Server : Connect and subscribe
Server->>Watcher : Initialize watcher
Watcher->>Exporters : Poll new signals
Exporters-->>Watcher : Signal records
Watcher-->>Server : Forwarded events
Server-->>Client : Streamed JSON messages
```

**Diagram sources**
- [API/api_server.py](file://API/api_server.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)

## Dependency Analysis
- Export modules depend on model outputs and shared validators
- MT5 exporter depends on schema definitions
- API server orchestrates exporters and watchers
- Tests validate each module’s contract and edge cases

```mermaid
graph LR
Model["Model Outputs"] --> V1["v1 Exporter"]
Model --> QV1["Quantile v1 Exporter"]
Model --> TSV2["v2 Exporter"]
V1 --> CSV["CSV Writer"]
V1 --> JSON["JSON Writer"]
QV1 --> JSON
TSV2 --> JSON
TSV2 --> MT5["MT5 Exporter"]
MT5 --> Schema["MT5 Schema"]
Server["API Server"] --> V1
Server --> QV1
Server --> TSV2
Watcher["Telemetry Watcher"] --> Server
```

**Diagram sources**
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [ML/baseline/export_mt5_entry_signals.py](file://ML/baseline/export_mt5_entry_signals.py)
- [ML/baseline/mt5_signal_schema.py](file://ML/baseline/mt5_signal_schema.py)
- [API/api_server.py](file://API/api_server.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)

**Section sources**
- [API/export_entry_path_v1_signals.py](file://API/export_entry_path_v1_signals.py)
- [API/export_entry_path_v1_quantile_signals.py](file://API/export_entry_path_v1_quantile_signals.py)
- [API/export_take_skip_trailing_stop_v2_signals.py](file://API/export_take_skip_trailing_stop_v2_signals.py)
- [ML/baseline/export_mt5_entry_signals.py](file://ML/baseline/export_mt5_entry_signals.py)
- [ML/baseline/mt5_signal_schema.py](file://ML/baseline/mt5_signal_schema.py)
- [API/api_server.py](file://API/api_server.py)
- [API/telemetry_signal_watcher.py](file://API/telemetry_signal_watcher.py)

## Performance Considerations
- Prefer streaming JSON for low-latency consumption; use CSV for batch processing
- Validate early to fail fast and reduce downstream overhead
- Cache schema definitions and avoid repeated parsing
- Limit payload size by filtering inactive signals and batching where appropriate

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Missing required fields: Ensure all mandatory columns exist in CSV and keys present in JSON
- Invalid timestamp formats: Normalize to ISO strings or epoch seconds consistently
- Quantile ordering violations: Enforce lower <= median <= upper before emitting
- MT5 schema mismatches: Verify type conversions and allowed value ranges
- Streaming interruptions: Reconnect clients and implement retry logic

Validation utilities:
- Use provided test suites to assert schema compliance and data integrity
- Log detailed error messages indicating failing fields and values

**Section sources**
- [tests/test_export_entry_path_v1_signals.py](file://tests/test_export_entry_path_v1_signals.py)
- [tests/test_export_entry_path_v1_quantile_signals.py](file://tests/test_export_entry_path_v1_quantile_signals.py)
- [tests/test_export_take_skip_trailing_stop_v2_signals.py](file://tests/test_export_take_skip_trailing_stop_v2_signals.py)
- [tests/test_mt5_signal_executor_schema.py](file://tests/test_mt5_signal_executor_schema.py)

## Conclusion
SoSimple’s signal export system provides robust, validated formats for entry path v1, quantile-based uncertainty, and take-skip-trailing-stop v2 strategies. MT5 integration ensures compatibility with MetaTrader engines, while the API server and telemetry watcher enable real-time streaming. Adhering to the documented schemas and validation procedures guarantees reliable downstream consumption and backward compatibility.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Versioning Strategy and Backward Compatibility
- Introduce new optional fields without breaking existing parsers
- Include version tags when schema changes are non-backward compatible
- Maintain deprecation timelines and migration guides for major updates
- Validate both old and new formats during transition periods

[No sources needed since this section provides general guidance]