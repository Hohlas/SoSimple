## 7. Baseline-first этап

### Цель

Получить нижнюю планку качества и sanity checks до сложных моделей.

### Входы

- train/validation split;
- target contract;
- feature contract;
- выбранные метрики.
- oracle-preflight report, если задача включает торговую механику входа/выхода.

### Пошаговые действия

0. Убедиться, что [07b-predictability-gate.md](07b-predictability-gate.md) пройден; `FAIL` гейта запрещает обучение и baseline.
1. Запустить dummy baseline:
   - majority class;
   - random class с class prior;
   - always skip;
   - простое direction rule, если применимо.
   - Для торговых постановок с явным entry/exit сначала убедиться, что [06b-oracle-preflight.md](06b-oracle-preflight.md) не дал `FAIL`.
2. Запустить простые ML baselines:
   - logistic/linear model;
   - tree model;
   - random forest или gradient boosting;
   - simple ranking/threshold rule.
3. Для sequence task сравнить flattened, engineered и sequence representations.
4. Считать classification metrics и trading metrics отдельно.
5. Проверить BUY/SELL отдельно.
6. Для execution-aware задач считать trading metrics по той же `entry_price`, spread, fill policy и PnL convention, что указаны в target contract.
7. Сохранить baseline report и confusion matrix.
8. Зафиксировать baseline, который должен быть побит новым кандидатом.

### Уровни и роль baseline-сравнения

Требование «сложная модель должна побить простую» обязательно на **проверочном уровне** (см. [00-research-management.md](00-research-management.md)). На **поисковом уровне** слабый результат сложной модели относительно baseline может быть полезен: он может указать на новую гипотезу (например, профиль стабильно около лидера на двух целях, хотя не превосходит XGBoost). Такой результат не становится кандидатом, но может породить следующий проверочный цикл.

### Честное сравнение моделей

Для честного ответа на вопрос «какая модель лучше» простая и сложная модель должны получать **те же признаки**. Если baseline обучается на одном наборе признаков (`base_raw_plus_time`), а сложная модель — на другом (sequence-профиль), сравнение смешивает два вопроса: «какие признаки лучше» и «какая архитектура лучше». Для проверки нужен вариант простой модели на тех же признаках, хотя бы в плоском (flattened) виде.

### Обязательные проверки

- Baseline использует тот же split и тот же live-safe feature contract.
- Если сравниваются разные архитектуры (например, Transformer vs XGBoost), сравнение включает вариант baseline на тех же признаках, что и сложная модель (flattened). Иначе вывод «модель слабее baseline» не отделён от вывода «признаки слабее».
- Если oracle-preflight применим, его результат не используется как модельный baseline и не попадает в признаки.
- Baseline использует тот же execution convention, что и будущий winner.
- Baseline не подбирается на `locked_test`.
- При дисбалансе смотреть precision/recall/F1/MCC, а не только accuracy.
- Trading baseline включает издержки или помечен gross diagnostic.
- Если canonical spread уже влияет на labels/fill, baseline без него имеет статус `DIAGNOSTIC_ONLY`.
- Zero-spread baseline не является baseline для final verdict, если production execution имеет ненулевой spread.

### Критерии успешного завершения

- Есть минимум один dummy и один простой ML baseline.
- Известно, насколько модель превосходит или не превосходит baseline.
- Есть baseline для сравнения в final verdict.

### Типовые ошибки

- Сразу обучать Transformer/ensemble без baseline.
- Сравнивать сложную модель с неправильной метрикой.
- Считать низкое число сделок высоким PF без статистической базы.
- Не проверять, не держится ли результат только на BUY или SELL.

### Ветвления

- Если baseline сильнее сложной модели на проверочном уровне: не усложнять, изучить target/features.
- Если baseline сильнее сложной модели на поисковом уровне, но сложная модель показала стабильный диагностический сигнал: это не кандидат, а гипотеза для нового проверочного цикла.
- Если baseline уже использует leakage: baseline invalid, начать с feature contract.
- Если простая модель даёт близкий результат: усложнение должно иметь практический смысл, а не только лучшую offline metric.

---
