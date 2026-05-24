## Verdict-статусы кандидатов

| Verdict | Значение | Разрешённые действия |
|---|---|---|
| `reject` | Гипотеза не прошла обязательные gates | Закрыть или сформулировать новую гипотезу |
| `diagnostic_only` | Проверялась механика, но ML quality не доказана | Использовать только для отладки pipeline |
| `research_only` | Есть сигнал, но не хватает устойчивости или contract неполный | Продолжать исследования, не подключать к production |
| `candidate` | Прошёл validation/test, но нет полного execution/forward подтверждения | Готовить parity, robustness, forward |
| `production_candidate` | Прошёл data contract, baseline comparison, frozen test, net-cost backtest, robustness или walk-forward, MT4 parity/reconciliation | Допускается controlled forward/online diagnostic; forward ещё не обязателен |
| `confirmed` | Forward подтвердил frozen rule на заранее заданных критериях | Поддерживать monitoring, rollback и periodic retrain policy |

