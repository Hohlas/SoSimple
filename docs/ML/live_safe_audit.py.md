# ML/live_safe_audit.py

Core definitions for the live-safe ML audit.

Purpose:
- define `PASS`, `FAIL`, `UNKNOWN`;
- describe one input feature through source, transformation, availability time,
  evidence, and notes;
- turn feature-level findings into a system verdict.

Main rule:
- `FAIL` means a concrete invalid or future-derived input was found;
- `UNKNOWN` means the source or timing is not proven yet;
- `PASS` means all audited inputs are proven available at decision time.

This module does not train models and does not export trading signals.
