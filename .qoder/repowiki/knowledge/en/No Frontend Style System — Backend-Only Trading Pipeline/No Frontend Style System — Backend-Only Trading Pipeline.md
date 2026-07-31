---
kind: frontend_style
name: No Frontend Style System — Backend-Only Trading Pipeline
category: frontend_style
scope:
    - '**'
---

This repository is a backend-only ML-driven Forex trading system with no frontend UI, CSS, or visual styling layer. The codebase consists of Python modules for signal generation and model training (API/, ML/, processing/, statistics/), MetaTrader MQL4/MQL5 expert advisors and indicators (MT/), and extensive test/documentation assets. There are no CSS files, SCSS/Less preprocessors, Tailwind configurations, design tokens, component libraries, or HTML templates that would constitute a frontend style system. The only HTML/CSS references found are in `.claude/skills/superpowers/brainstorming/scripts/frame-template.html` and `helper.js`, which are internal developer tooling scripts used by an LLM brainstorming helper server — not part of any user-facing interface. The API server (`API/api_server.py`) is a pure FastAPI REST service returning JSON responses to MT4 clients; it serves no HTML pages. Therefore, the `frontend_style` category does not apply to this repository.