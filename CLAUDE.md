# CLAUDE.md

Adapter для Claude Code. Canonical project contract: [`AGENTS.md`](AGENTS.md).

## Session Start

- Прочитай [`AGENTS.md`](AGENTS.md).

```bash
source .venv/bin/activate
python -m pytest tests/ -q
python processing/label_main.py --input MT/MQL4/Files/Nero.csv
```
