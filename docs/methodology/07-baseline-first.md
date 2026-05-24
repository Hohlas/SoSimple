## 7. Baseline-first этап

### Цель

Получить нижнюю планку качества и sanity checks до сложных моделей.

### Входы

- train/validation split;
- target contract;
- feature contract;
- выбранные метрики.

### Пошаговые действия

1. Запустить dummy baseline:
   - majority class;
   - random class с class prior;
   - always skip;
   - простое direction rule, если применимо.
2. Запустить простые ML baselines:
   - logistic/linear model;
   - tree model;
   - random forest или gradient boosting;
   - simple ranking/threshold rule.
3. Для sequence task сравнить flattened, engineered и sequence representations.
4. Считать classification metrics и trading metrics отдельно.
5. Проверить BUY/SELL отдельно.
6. Сохранить baseline report и confusion matrix.
7. Зафиксировать baseline, который должен быть побит новым кандидатом.

### Обязательные проверки

- Baseline использует тот же split и тот же live-safe feature contract.
- Baseline не подбирается на test.
- При дисбалансе смотреть precision/recall/F1/MCC, а не только accuracy.
- Trading baseline включает издержки или помечен gross diagnostic.

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

- Если baseline сильнее сложной модели: не усложнять, изучить target/features.
- Если baseline уже использует leakage: baseline invalid, начать с feature contract.
- Если простая модель даёт близкий результат: усложнение должно иметь практический смысл, а не только лучшую offline metric.

---

