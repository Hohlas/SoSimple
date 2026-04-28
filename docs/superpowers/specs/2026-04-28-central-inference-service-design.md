# Central Multi-Profile Inference Service — Design Note

> **Date**: 2026-04-28
> **Status**: Deferred design note
> **Track**: MT4 online inference operations
> **Goal**: Replace manual per-watcher operation with one Python service that serves multiple MT4 experts while preserving the current Python training/inference pipeline.
> **Related materials**: `docs/API/telemetry_signal_watcher.py.md`, `docs/MT/ml_signal_integration.md`, `docs/superpowers/specs/2026-04-27-telemetry-frequency-demo-launch-design.md`

---

## 1. Context

The current online telemetry path is:

```text
MT4 expert -> Nero.csv -> telemetry_signal_watcher.py -> ml_signals.csv -> MT4 expert
```

This is operationally acceptable for one expert, but it does not scale well if
several experts run in parallel and each one has its own ML model, checkpoint,
rule file, runtime CSV and signal output.

The key requirement is to preserve the current research workflow:

- model search, training and feature construction stay in Python;
- the same inference code path is used for offline export and online runtime;
- MT4 remains a signal consumer and execution engine;
- no separate MQL/DLL implementation of the trained model is required after each
  training run.

Therefore the primary problem is not the ML pipeline. The problem is the
operational shape of the current watcher: one manually started process per
runtime contour.

---

## 2. Main Decision

When this track is implemented, replace the single-purpose watcher with one
central Python inference service that manages multiple runtime profiles.

Target shape:

```text
MT4 Expert A -> Nero_A.csv -> central ML service -> ml_signals_A.csv -> Expert A
MT4 Expert B -> Nero_B.csv -> central ML service -> ml_signals_B.csv -> Expert B
MT4 Expert C -> Nero_C.csv -> central ML service -> ml_signals_C.csv -> Expert C
```

The service should be configured through profile records. Each profile describes
one expert/model pair:

```yaml
profiles:
  telemetry_frequency_v1:
    input_csv: MT/MQL4/Files/Nero_telemetry.csv
    output_csv: MT/MQL4/Files/ml_signals_telemetry.csv
    runtime_dir: ML/reports/telemetry_frequency_v1/runtime
    checkpoint: ML/reports/take_skip_trailing_stop_v2_matrix/transformer_seq50/checkpoint.pt
    rule: ML/reports/telemetry_frequency_v1/calibration/selected_rule.json
    mode: original_contour
    feature_mode: original_baseline
    seq_len: 50
    direction_source: fractal0_direction
    max_runtime_rows: 12000
```

Changing or adding a model should mean adding or editing a profile, not rewriting
MQL code or duplicating the Python inference pipeline.

---

## 3. Why Not DLL First

DLL integration is not the preferred first implementation path.

Reasons:

- a DLL bridge to Python still requires a Python process, but is harder to debug
  than a managed Python service;
- a DLL that runs inference directly would require exporting and maintaining a
  second runtime stack, most likely ONNX/C++, plus exact feature parity;
- feature extraction parity is the main risk: duplicating feature construction
  outside Python can silently diverge from training;
- MT4 tester compatibility is already solved by CSV signal exports, while a live
  DLL path would add another runtime mode.

DLL can remain a later option only if file-based transport becomes a measured
bottleneck or if production deployment requires a single native runtime.

---

## 4. Why Not WebRequest First

An HTTP/WebRequest design is useful as a possible live-only transport:

```text
MT4 -> HTTP POST fractals -> Python API -> signal response
```

It removes `ml_signals.csv`, but it is not the first choice for this project
stage because:

- MQL4 `WebRequest()` is synchronous;
- the terminal requires allowed URL setup;
- Strategy Tester compatibility would still need offline CSV exports;
- a second live transport increases reconciliation complexity.

If CSV transport later becomes the main limitation, HTTP can be added as a
transport option behind the same profile/inference core.

---

## 5. Service Responsibilities

The central service should own operational orchestration only. It should not
become a new training pipeline.

Responsibilities:

- load profile configuration;
- watch each profile's `Nero*.csv` for new last `time` / file modification;
- build a per-profile runtime snapshot from the tail of the input CSV;
- call the same Python prediction exporter used by offline/tester workflows;
- apply the profile's frozen rule;
- write the profile's `ml_signals*.csv` atomically;
- maintain per-profile state, metadata and logs;
- expose enough status for server operation and troubleshooting.

Non-goals:

- no model training inside the service;
- no automatic model selection;
- no hidden rule search;
- no MQL reimplementation of feature extraction;
- no production verdict based only on service output.

---

## 6. Compatibility Requirements

The service must preserve these contracts:

- Strategy Tester keeps using generated `ml_signals.csv` files.
- Offline exports and online exports use the same model input builder and rule
  application code.
- Profile output files are independent, so several experts cannot overwrite one
  another's signals.
- Runtime metadata must include profile name, input path, output path, checkpoint
  path, rule path, row counts, nonzero signal counts and output hash.
- The service must support one-shot mode for debugging and continuous managed
  mode for server operation.

Recommended deployment target:

- Linux/server: `systemd` service or supervisor-managed process;
- local/manual debugging: CLI one-shot or foreground mode;
- no required `tmux` for normal operation.

---

## 7. Implementation Direction

When this becomes an active task, start from the existing
`API/telemetry_signal_watcher.py` behavior and generalize it.

Expected implementation path:

1. Introduce a profile config format and parser.
2. Extract the current single-profile rebuild logic into reusable functions.
3. Add a service loop over multiple profiles.
4. Add per-profile output/state/log/metadata paths.
5. Keep the existing single-profile CLI path as a compatibility wrapper or
   migrate it to a one-profile config.
6. Add tests for two profiles with different input/output files and rules.
7. Update `docs/API/`, `docs/MT/`, `CONTEXT_HANDOFF.md` and roadmap when the
   implementation track starts.

The first implementation should keep file transport. Transport changes
(`WebRequest`, DLL, shared memory) should be evaluated separately after the
multi-profile service removes the current manual watcher problem.

---

## 8. Open Questions

- Exact profile file location: `config/inference_profiles.yaml`,
  `ML/reports/*/runtime/profile.json`, or a project-level JSON under `API/`.
- Whether each MT4 expert should write a unique `Nero_<profile>.csv`, or whether
  the service should support one input feeding several profiles.
- Whether profile selection should be controlled by MT4 inputs or only by file
  paths and service config.
- How much status should be exposed: log files only, JSON status file, or a small
  local HTTP health endpoint.
- Whether old `telemetry_signal_watcher.py` should remain as a thin wrapper after
  the service exists.
