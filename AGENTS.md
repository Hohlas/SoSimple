# AI Agent Configuration

## Project Context
- Type: Multi-language trading bot system
- Languages: Python, Rust, Shell
- Primary Tools: Cursor, Antigravity, Perplexity

## Documentation Sources
- Architecture: `docs/architecture.md`
- Scripts: `docs/scripts/*.md` + inline docstrings
- Workflows: `docs/workflows/*.md`
- Dependencies: See `docs/data-flow.md`

## Agent Instructions

### When modifying a script:
1. Read the script's docstring header
2. Check `docs/scripts/[script-name].md` for details
3. After changes, update BOTH the docstring AND the .md file
4. Update `docs/data-flow.md` if input/output changed

### When creating prompts:
1. Start with `docs/architecture.md` for context
2. Use `docs/data-flow.md` to understand dependencies
3. Reference specific script docs from `docs/scripts/`

## File Locations
- Data flow diagram: `docs/data-flow.md`
- Script inventory: `docs/scripts/README.md`
- Configuration examples: `docs/examples/`
