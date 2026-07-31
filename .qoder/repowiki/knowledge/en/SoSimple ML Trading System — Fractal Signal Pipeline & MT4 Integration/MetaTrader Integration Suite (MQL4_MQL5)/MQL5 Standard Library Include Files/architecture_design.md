The module is a flat collection of MQL5 `*.mqh` headers organized into logical sub-packages under `MT/MQL5/Include/`, each grouping related functionality:
- `Arrays/` — primitive typed array wrappers (`Array*.mqh`) plus `List`, `Tree`, `TreeNode`.
- `Generic/` — C#-style generic collection framework with `Interfaces/` (IList, IMap, ISet, etc.) and `Internal/` helpers (comparers, hash functions, introsort), implemented by concrete classes like `ArrayList`, `HashMap`, `RedBlackTree`.
- `Expert/` — multi-layered EA framework: `ExpertBase.mqh` (timeseries/margin abstraction) → `Expert.mqh` (event-driven orchestrator delegating to `ExpertTrade`, `ExpertSignal`, `ExpertMoney`, `ExpertTrailing`), with pluggable `Signal/*`, `Money/*`, `Trailing/*` implementations.
- `Indicators/`, `Math/` (with `Alglib/`, `Fuzzy/`, `Stat/`), `Charts/`, `ChartObjects/` — analysis primitives.
- `Controls/` — GUI widget set built on `Wnd*` base classes with embedded BMP resources in `Controls/res/`.
- `Canvas/` — 2D/3D drawing via `Canvas.mqh` and a DirectX backend under `Canvas/DX/` (shaders in HLSL, mesh/buffer/surface abstractions).
- `WinAPI/` — Windows API bindings grouped by DLL namespace (`winbase`, `wingdi`, `winuser`, etc.).
- Top-level files (`MAIN.mqh`, `FUNCTIONS.mqh`, `ERRORS.mqh`, `stderror.mqh`, `MovingAverages.mqh`, etc.) provide legacy-style global functions and the custom PIC indicator/expert entry point.
Dependency direction is strictly inward: higher layers include lower ones (e.g. `Expert.mqh` includes `ExpertBase.mqh`; `Canvas/DX/*` includes `<Object.mqh>`); there are no cross-dependencies between sibling packages except through shared bases like `CObject`.