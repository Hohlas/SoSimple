## Verdict-статусы кандидатов

| Verdict | Значение | Разрешённые действия |
|---|---|---|
| `reject` | Гипотеза не прошла обязательные gates | Закрыть или сформулировать новую гипотезу |
| `diagnostic_only` | Проверялась механика, но ML quality не доказана | Использовать только для отладки pipeline |
| `research_only` | Есть сигнал, но не хватает устойчивости или contract неполный | Продолжать исследования, не подключать к production |
| `candidate` | Прошёл validation/test, но нет полного execution/forward подтверждения | Готовить parity, robustness, forward |
| `production_candidate` | Прошёл data contract, baseline comparison, frozen test, net-cost backtest, robustness и walk-forward, MT4 parity/reconciliation | Допускается controlled forward/online diagnostic; forward ещё не обязателен |
| `confirmed` | Forward подтвердил frozen rule на заранее заданных критериях | Поддерживать monitoring, rollback и periodic retrain policy |

## Stop conditions

Остановить текущий cycle и не продолжать model sweep, если:

- data contract не прошёл leakage gate;
- online features недоступны;
- candidate-source не live-safe;
- test уже был использован для выбора;
- validation gate не пройден;
- oracle-preflight для торговой механики не прошёл канонические издержки;
- единственный плюс кандидата держится на одной стороне, одном году или очень малом N;
- cost-aware result отрицателен;
- MT4 parity показывает critical mismatch;
- forward data отсутствуют, но требуется forward verdict.

Oracle-preflight может остановить неудачную механику до обучения модели, но не может повысить verdict кандидата: это future-derived diagnostic, а не evidence качества модели.

Если кандидат получил `reject`, но до этого oracle-preflight показывал сильный потолок или модель имела заметный ranking-сигнал, следующий шаг — [A5-post-mortem-diagnostics.md](A5-post-mortem-diagnostics.md). Такой разбор не отменяет `reject`, а только формулирует новую ограниченную гипотезу.

Правильный следующий шаг в этих случаях: написать reject/diagnostic report и сформулировать новую ограниченную гипотезу.
