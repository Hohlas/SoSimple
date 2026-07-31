# MetaTrader Platform Deployment

<cite>
**Referenced Files in This Document**
- [MT/README.md](file://MT/README.md)
- [API/api_server.py](file://API/api_server.py)
- [API/test_api_client.py](file://API/test_api_client.py)
- [ML/export_mt5_entry_signals.py](file://ML/export_mt5_entry_signals.py)
- [ML/triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [tests/test_triple_barrier_mt4_execution.py](file://tests/test_triple_barrier_mt4_execution.py)
- [tests/test_mt5_signal_executor_schema.py](file://tests/test_mt5_signal_executor_schema.py)
- [tests/test_parse_mt5_execution_report.py](file://tests/test_parse_mt5_execution_report.py)
- [tests/test_mql_telemetry_params_csv_contract.py](file://tests/test_mql_telemetry_params_csv_contract.py)
- [tests/test_signal_export_parity.py](file://tests/test_signal_export_parity.py)
- [tests/test_online_tester_reconciliation.py](file://tests/test_online_tester_reconciliation.py)
- [tests/test_telemetry_signal_watcher.py](file://tests/test_telemetry_signal_watcher.py)
- [docs/API/api_server.py.md](file://docs/API/api_server.py.md)
- [docs/API/telemetry_signal_watcher.py.md](file://docs/API/telemetry_signal_watcher.py.md)
- [docs/schemas/mt5_nero_csv_contract.md](file://docs/schemas/mt5_nero_csv_contract.md)
- [docs/schemas/mt5_open_position_feature_contract.md](file://docs/schemas/mt5_open_position_feature_contract.md)
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
This document provides comprehensive deployment guidance for running the trading system on MetaTrader 4 (MT4) and MetaTrader 5 (MT5). It covers Expert Advisor installation, indicator compilation, library setup, platform configuration, signal integration with the Python API server, live trading setup, troubleshooting, performance optimization, multi-account deployment, VPS setup, and maintenance procedures. The content is derived from the repository’s MT codebase, Python API server, ML export utilities, tests, and documentation schemas.

## Project Structure
The project organizes MetaTrader components under MT/MQL4 and MT/MQL5, with a Python API server under API/, ML utilities for exporting signals and execution parity checks, and extensive tests validating contracts and behavior. Documentation and schemas define data contracts used by MQL components and the Python side.

```mermaid
graph TB
subgraph "Python Side"
API["API Server<br/>api_server.py"]
TEST_API["API Client Test<br/>test_api_client.py"]
ML_EXPORT["Export Signals<br/>export_mt5_entry_signals.py"]
PARITY["Parity Checks<br/>triple_barrier_mt4_execution.py"]
end
subgraph "MetaTrader 4"
MQL4_EXP["Experts (MQL4)"]
MQL4_IND["Indicators (MQL4)"]
MQL4_LIB["Libraries (MQL4)"]
MQL4_INC["Include (MQL4)"]
MQL4_FILES["Files (MQL4)"]
end
subgraph "MetaTrader 5"
MQL5_EXP["Experts (MQL5)"]
MQL5_IND["Indicators (MQL5)"]
MQL5_LIB["Libraries (MQL5)"]
MQL5_INC["Include (MQL5)"]
MQL5_FILES["Files (MQL5)"]
end
subgraph "Tests & Docs"
T_PARITY["Test Parity<br/>test_triple_barrier_mt4_execution.py"]
T_SCHEMA["Test Schema<br/>test_mt5_signal_executor_schema.py"]
T_REPORT["Parse Report<br/>test_parse_mt5_execution_report.py"]
T_TELEMETRY["Telemetry Contract<br/>test_mql_telemetry_params_csv_contract.py"]
SCHEMA_NERO["Schema: MT5 Nero CSV<br/>mt5_nero_csv_contract.md"]
SCHEMA_POS["Schema: Open Position Features<br/>mt5_open_position_feature_contract.md"]
end
API --> MQL4_FILES
API --> MQL5_FILES
ML_EXPORT --> MQL5_FILES
PARITY --> MQL4_FILES
T_PARITY --> PARITY
T_SCHEMA --> MQL5_FILES
T_REPORT --> MQL5_FILES
T_TELEMETRY --> API
SCHEMA_NERO --> MQL5_FILES
SCHEMA_POS --> MQL5_FILES
```

**Diagram sources**
- [MT/README.md](file://MT/README.md)
- [API/api_server.py](file://API/api_server.py)
- [API/test_api_client.py](file://API/test_api_client.py)
- [ML/export_mt5_entry_signals.py](file://ML/export_mt5_entry_signals.py)
- [ML/triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [tests/test_triple_barrier_mt4_execution.py](file://tests/test_triple_barrier_mt4_execution.py)
- [tests/test_mt5_signal_executor_schema.py](file://tests/test_mt5_signal_executor_schema.py)
- [tests/test_parse_mt5_execution_report.py](file://tests/test_parse_mt5_execution_report.py)
- [tests/test_mql_telemetry_params_csv_contract.py](file://tests/test_mql_telemetry_params_csv_contract.py)
- [docs/schemas/mt5_nero_csv_contract.md](file://docs/schemas/mt5_nero_csv_contract.md)
- [docs/schemas/mt5_open_position_feature_contract.md](file://docs/schemas/mt5_open_position_feature_contract.md)

**Section sources**
- [MT/README.md](file://MT/README.md)

## Core Components
- Python API Server: Provides endpoints for signal generation, telemetry ingestion, and control commands consumed by MQL components.
- MQL4 Experts and Indicators: Implement strategy logic, charting, and execution hooks for MT4.
- MQL5 Experts and Indicators: Implement strategy logic, execution, and reporting for MT5.
- Signal Export Utilities: Generate entry signals compatible with MT5 consumption.
- Telemetry and Contracts: Validate CSV formats and ensure parity between Python and MQL execution paths.

Key responsibilities:
- Data synchronization via file-based or API-driven mechanisms.
- Execution parameters passed from Python to MQL through configuration files or runtime messages.
- Risk management enforced at both Python and MQL layers.

**Section sources**
- [API/api_server.py](file://API/api_server.py)
- [docs/API/api_server.py.md](file://docs/API/api_server.py.md)
- [ML/export_mt5_entry_signals.py](file://ML/export_mt5_entry_signals.py)
- [ML/triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)

## Architecture Overview
The system integrates a Python API server with MT4/MT5 platforms. Python generates signals and telemetry; MQL components consume these signals and execute trades according to configured risk rules. Communication can be file-based (CSV/JSON) or API-driven. Tests validate schema contracts and execution parity.

```mermaid
sequenceDiagram
participant Python as "Python API Server"
participant FileSys as "File System / Shared Storage"
participant MT4 as "MT4 Expert/Indicator"
participant MT5 as "MT5 Expert/Indicator"
participant Broker as "Broker Engine"
Python->>FileSys : "Write signals/config"
MT4->>FileSys : "Read signals/config"
MT5->>FileSys : "Read signals/config"
MT4->>Broker : "Place orders per strategy"
MT5->>Broker : "Place orders per strategy"
MT4-->>FileSys : "Write telemetry/logs"
MT5-->>FileSys : "Write telemetry/logs"
Python->>FileSys : "Ingest telemetry/logs"
Python-->>MT4 : "Control commands (optional)"
Python-->>MT5 : "Control commands (optional)"
```

**Diagram sources**
- [API/api_server.py](file://API/api_server.py)
- [API/test_api_client.py](file://API/test_api_client.py)
- [ML/export_mt5_entry_signals.py](file://ML/export_mt5_entry_signals.py)
- [ML/triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)

## Detailed Component Analysis

### Python API Server Integration
The API server exposes endpoints for generating signals and ingesting telemetry. Clients interact via HTTP requests. Tests verify client behavior and contract compliance.

```mermaid
sequenceDiagram
participant Client as "Client/Test"
participant API as "API Server"
participant FS as "Shared Files"
participant MQL as "MQL Components"
Client->>API : "Request signal generation"
API->>FS : "Write signal payload"
MQL->>FS : "Poll/read signals"
MQL-->>FS : "Write telemetry"
API->>FS : "Read telemetry"
API-->>Client : "Response/status"
```

**Diagram sources**
- [API/api_server.py](file://API/api_server.py)
- [API/test_api_client.py](file://API/test_api_client.py)
- [docs/API/api_server.py.md](file://docs/API/api_server.py.md)

**Section sources**
- [API/api_server.py](file://API/api_server.py)
- [API/test_api_client.py](file://API/test_api_client.py)
- [docs/API/api_server.py.md](file://docs/API/api_server.py.md)

### MT5 Signal Export and Consumption
Signal export utilities generate entry signals compatible with MT5 consumption. Schemas define expected CSV structures for robust parsing and validation.

```mermaid
flowchart TD
Start(["Start Export"]) --> Prepare["Prepare features and targets"]
Prepare --> ModelRun["Run model inference"]
ModelRun --> Format["Format signals per schema"]
Format --> Write["Write CSV to shared path"]
Write --> Notify["Notify MT5 consumer (optional)"]
Notify --> End(["End"])
```

**Diagram sources**
- [ML/export_mt5_entry_signals.py](file://ML/export_mt5_entry_signals.py)
- [docs/schemas/mt5_nero_csv_contract.md](file://docs/schemas/mt5_nero_csv_contract.md)

**Section sources**
- [ML/export_mt5_entry_signals.py](file://ML/export_mt5_entry_signals.py)
- [docs/schemas/mt5_nero_csv_contract.md](file://docs/schemas/mt5_nero_csv_contract.md)

### MT4 Execution Parity Validation
Parity checks ensure that MT4 execution behaves consistently with Python expectations. Tests validate trade lifecycle and barrier logic.

```mermaid
classDiagram
class TripleBarrierMT4 {
+run_backtest()
+validate_barriers()
+compare_with_python()
}
class TestTripleBarrierMT4 {
+test_execution_paths()
+test_barrier_logic()
}
TripleBarrierMT4 <.. TestTripleBarrierMT4 : "validated by"
```

**Diagram sources**
- [ML/triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [tests/test_triple_barrier_mt4_execution.py](file://tests/test_triple_barrier_mt4_execution.py)

**Section sources**
- [ML/triple_barrier_mt4_execution.py](file://ML/triple_barrier_mt4_execution.py)
- [tests/test_triple_barrier_mt4_execution.py](file://tests/test_triple_barrier_mt4_execution.py)

### MT5 Schema and Reporting
Contracts define CSV formats for MT5 telemetry and open position features. Tests parse reports and validate schema adherence.

```mermaid
flowchart TD
A["MT5 Execution"] --> B["Generate report CSV"]
B --> C["Validate against schema"]
C --> D{"Valid?"}
D --> |Yes| E["Ingest into Python"]
D --> |No| F["Flag error and halt"]
E --> G["Update dashboard/state"]
F --> H["Alert operator"]
```

**Diagram sources**
- [tests/test_parse_mt5_execution_report.py](file://tests/test_parse_mt5_execution_report.py)
- [docs/schemas/mt5_nero_csv_contract.md](file://docs/schemas/mt5_nero_csv_contract.md)
- [docs/schemas/mt5_open_position_feature_contract.md](file://docs/schemas/mt5_open_position_feature_contract.md)

**Section sources**
- [tests/test_parse_mt5_execution_report.py](file://tests/test_parse_mt5_execution_report.py)
- [docs/schemas/mt5_nero_csv_contract.md](file://docs/schemas/mt5_nero_csv_contract.md)
- [docs/schemas/mt5_open_position_feature_contract.md](file://docs/schemas/mt5_open_position_feature_contract.md)

### Telemetry and Contract Compliance
Telemetry ingestion ensures consistent logging and monitoring across platforms. Tests validate parameter contracts and watcher behavior.

```mermaid
sequenceDiagram
participant MQL as "MQL Telemetry"
participant FS as "File System"
participant API as "API Server"
participant Watcher as "Telemetry Watcher"
MQL->>FS : "Write telemetry CSV"
Watcher->>FS : "Monitor new entries"
Watcher->>API : "Forward telemetry"
API->>API : "Validate params per contract"
API-->>Watcher : "Ack/Reject"
```

**Diagram sources**
- [tests/test_mql_telemetry_params_csv_contract.py](file://tests/test_mql_telemetry_params_csv_contract.py)
- [docs/API/telemetry_signal_watcher.py.md](file://docs/API/telemetry_signal_watcher.py.md)

**Section sources**
- [tests/test_mql_telemetry_params_csv_contract.py](file://tests/test_mql_telemetry_params_csv_contract.py)
- [docs/API/telemetry_signal_watcher.py.md](file://docs/API/telemetry_signal_watcher.py.md)

### Signal Export Parity
Parity tests ensure exported signals match expected patterns and are compatible with MT5 consumers.

```mermaid
flowchart TD
Start(["Start Parity Test"]) --> LoadSignals["Load exported signals"]
LoadSignals --> Compare["Compare with reference"]
Compare --> Match{"Match?"}
Match --> |Yes| Pass["Pass test"]
Match --> |No| Fail["Fail test and log diff"]
Pass --> End(["End"])
Fail --> End
```

**Diagram sources**
- [tests/test_signal_export_parity.py](file://tests/test_signal_export_parity.py)

**Section sources**
- [tests/test_signal_export_parity.py](file://tests/test_signal_export_parity.py)

### Online Tester Reconciliation
Reconciliation tests align online tester results with backtesting expectations, ensuring consistency across environments.

```mermaid
flowchart TD
A["Backtest Results"] --> B["Online Tester Run"]
B --> C["Compare metrics"]
C --> D{"Within tolerance?"}
D --> |Yes| E["Mark reconciled"]
D --> |No| F["Investigate drift"]
E --> G["Proceed to live"]
F --> H["Adjust models/config"]
```

**Diagram sources**
- [tests/test_online_tester_reconciliation.py](file://tests/test_online_tester_reconciliation.py)

**Section sources**
- [tests/test_online_tester_reconciliation.py](file://tests/test_online_tester_reconciliation.py)

## Dependency Analysis
The system exhibits clear separation between Python services and MQL components, with file-based communication and schema contracts ensuring interoperability. Tests enforce correctness and parity.

```mermaid
graph TB
API["API Server"] --> FS["Shared Files"]
ML_EXPORT["Signal Export"] --> FS
MQL4["MT4 Components"] --> FS
MQL5["MT5 Components"] --> FS
TESTS["Tests"] --> API
TESTS --> ML_EXPORT
TESTS --> MQL4
TESTS --> MQL5
```

**Diagram sources**
- [API/api_server.py](file://API/api_server.py)
- [ML/export_mt5_entry_signals.py](file://ML/export_mt5_entry_signals.py)
- [tests/test_triple_barrier_mt4_execution.py](file://tests/test_triple_barrier_mt4_execution.py)
- [tests/test_mt5_signal_executor_schema.py](file://tests/test_mt5_signal_executor_schema.py)

**Section sources**
- [API/api_server.py](file://API/api_server.py)
- [ML/export_mt5_entry_signals.py](file://ML/export_mt5_entry_signals.py)
- [tests/test_triple_barrier_mt4_execution.py](file://tests/test_triple_barrier_mt4_execution.py)
- [tests/test_mt5_signal_executor_schema.py](file://tests/test_mt5_signal_executor_schema.py)

## Performance Considerations
- Minimize file I/O latency by batching signal writes and using efficient CSV formats.
- Use asynchronous polling in MQL components to avoid blocking the terminal thread.
- Cache frequently accessed symbols and configuration to reduce overhead.
- Optimize model inference pipelines in Python to meet real-time constraints.
- Monitor CPU and memory usage on VPS to prevent resource contention.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Signal not received by MT4/MT5: Verify file paths, permissions, and polling intervals. Check schema validity.
- Execution discrepancies: Run parity tests and reconcile online tester results. Inspect telemetry logs.
- API connectivity failures: Validate endpoint URLs, authentication, and network policies.
- Telemetry gaps: Ensure watchers are active and contracts are correctly implemented.

Diagnostic steps:
- Review MQL logs and Python API logs for errors.
- Validate CSV schemas against documented contracts.
- Reproduce issues in controlled environments using tests.

**Section sources**
- [tests/test_parse_mt5_execution_report.py](file://tests/test_parse_mt5_execution_report.py)
- [tests/test_mql_telemetry_params_csv_contract.py](file://tests/test_mql_telemetry_params_csv_contract.py)
- [docs/API/api_server.py.md](file://docs/API/api_server.py.md)

## Conclusion
This deployment guide outlines the integration of Python services with MT4/MT5 platforms, emphasizing robust signal exchange, execution parity, and telemetry. By following the outlined procedures and leveraging the provided tests and schemas, operators can deploy reliable automated trading systems across multiple accounts and environments.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### MT4 Installation and Configuration
- Install Experts and Indicators under MT4 directories.
- Compile indicators and libraries before attaching to charts.
- Configure symbol settings, chart timeframes, and execution parameters.
- Set up file paths for signal ingestion and telemetry output.

[No sources needed since this section provides general guidance]

### MT5 Installation and Configuration
- Install Experts and Indicators under MT5 directories.
- Compile components and verify dependencies.
- Configure broker connections, account credentials, and risk parameters.
- Align symbol configurations and timeframe settings with Python exports.

[No sources needed since this section provides general guidance]

### Live Trading Setup
- Connect to broker via MT4/MT5 terminals.
- Configure account-specific parameters (lot sizes, stops, take profits).
- Enable auto-trading and verify order routing.
- Monitor telemetry and adjust risk thresholds as needed.

[No sources needed since this section provides general guidance]

### Multi-Account Deployment
- Deploy separate MT4/MT5 instances per account.
- Isolate file paths and ports to prevent conflicts.
- Use environment variables or config files for account-specific settings.
- Automate startup and monitoring scripts.

[No sources needed since this section provides general guidance]

### VPS Setup and Maintenance
- Provision a low-latency VPS near broker servers.
- Install MT4/MT5 terminals and required dependencies.
- Schedule regular updates and backups.
- Monitor system health and alert on anomalies.

[No sources needed since this section provides general guidance]