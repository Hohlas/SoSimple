The `docs/` directory is a flat knowledge base organized by artifact type rather than code modules. Top-level anchors define scope and contracts: `PRD.md` (product requirements), `DATA_FLOW.md` (end-to-end pipeline from MT4 CSV through labeling, normalization, split, training, OOS evaluation, signal export, and reconciliation), and `dataset_description.md`. Subdirectories group related artifacts:
- `methodology/` — numbered stage documents (01–16) plus checklists (A1–A8) that form the canonical development methodology.
- `reports/` — dated markdown reports for completed research/experiment phases.
- `audit/` — independent audit gates, methodology reviews, and project structure modernization notes.
- `superpowers/plans/` and `superpowers/specs/` — executable task plans and design/spec materials, each with date-prefixed filenames.
- `API/`, `ML/`, `MT/`, `processing/`, `statistics/`, `tests/` — module-level `.py.md` or `.md` reference docs mirroring sibling code directories.
- `schemas/` — JSON Schema files (`fractal_v23.schema.json`, `fractal_v24_raw_price.schema.json`) and contract docs defining the MT4↔Python fractal interface.
- `archive/0726/` — frozen snapshot of an earlier iteration, not to be modified without explicit request.
The dependency direction is one-way: code modules reference these docs for contracts and methodology; docs do not import code.