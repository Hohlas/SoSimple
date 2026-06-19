# Анти-паттерны тестирования (Python, ML-инфраструктура)

**Загружай этот справочник:** когда пишешь или меняешь тесты, добавляешь моки
или испытываешь соблазн добавить test-only метод в production-код.

## Обзор

Тесты проверяют реальное поведение кода, а не поведение моков. Мок — средство
изоляции, не объект тестирования.

**Следование TDD (RED-GREEN-REFACTOR) предотвращает эти анти-паттерны.**

## Три железных правила

```
1. НИКОГДА не assert'ить на поведение мока — только на поведение кода
2. НИКОГДА не добавлять test-only методы в production-модули
3. НИКОГДА не мокать без понимания side effects зависимости
```

## Анти-паттерн 1: тестирование мока

**Нарушение:**
```python
# ❌ ПЛОХО: assert проверяет, что mock вернул заглушку, а не поведение load_csv
def test_load_csv(monkeypatch):
    monkeypatch.setattr(data_loader.pd, "read_csv", lambda *a, **k: fake_df)
    df = data_loader.load_split("train")
    assert df is fake_df  # тестируем мок, не load_split
```

**Почему плохо:** тест проходит независимо от логики `load_split` — assert
проверяет, что лямбда вернула `fake_df`, а это гарантировано самим моком.

**Исправление:**
```python
# ✅ ХОРОШО: assert на свойства, которые вычисляет реальный код
def test_load_split_returns_expected_columns(monkeypatch, tmp_path):
    tmp_path.joinpath("Nero_train_labeled.csv").write_text(
        "time;signal;ATR\n1;1;0.5\n", encoding="utf-8")
    monkeypatch.setattr(data_loader, "DATA_DIR", tmp_path)
    df = data_loader.load_split("train")
    assert list(df.columns) == ["time", "signal", "ATR"]
```

## Анти-паттерн 2: test-only методы в production

**Нарушение:**
```python
# ❌ ПЛОХО: _reset_for_tests() существует только ради afterEach
# ML/data_loader.py
def _reset_for_tests() -> None:
    global _cache
    _cache = None
```

**Почему плохо:** загрязняет production API, опасен при случайном вызове в
боевом коде (сбрасывает кэш под нагрузкой), нарушает YAGNI.

**Исправление:** вынести cleanup в `tests/conftest.py` или `tests/utils.py` —
production-модуль не должен знать про тестовую инфраструктуру.

## Анти-паттерн 3: мок без понимания зависимостей

**Нарушение (реальный паттерн из `tests/test_take_skip_trailing_stop_v2_task.py:149-151`):**
```python
# ❌ ПЛОХО: валидаторы замоканы как no-op, но тест зависит от того, что они проверили
monkeypatch.setattr(data_loader, "validate_data_contract", lambda *a, **k: None)
monkeypatch.setattr(data_loader, "validate_csv_columns",   lambda *a, **k: None)
monkeypatch.setattr(data_loader, "validate_fractal_format", lambda *a, **k: None)
df = data_loader.load_split("train")
assert "signal" in df.columns  # прошёл бы даже без колонки signal
```

**Почему плохо:** мок валидаторов убирает именно ту проверку, от которой
зависит корректность `df`. Тест проходит для пустого/битого датасета.

**Исправление:** мокать ниже — медленную I/O (`pd.read_csv` через файл в
`tmp_path`), а валидаторы оставить реальными. Если валидатор медленный —
разбить его, а не выключать целиком.

## Анти-паттерн 4: неполный мок

**Нарушение:**
```python
# ❌ ПЛОХО: одна lambda на все вызовы read_csv — train/val/test получают один df
monkeypatch.setattr(data_loader.pd, "read_csv", lambda *a, **k: train_df)
train = data_loader.load_split("train")
val   = data_loader.load_split("validation")  # вернёт train_df — тест врёт
test  = data_loader.load_split("test")        # то же
```

**Почему плохо:** downstream-код (split, leakage-check) ожидает разные
датасеты. Мок возвращает один — split-leakage остаётся непроверенным.

**Исправление:** мокать через словарь по пути файла, либо писать реальные
файлы в `tmp_path` (предпочтительно — честнее и проще).

## Анти-паттерн 5: тесты как follow-up

**Нарушение:** «implementation complete, ready for testing» — тесты
выносятся в отдельную задачу.

**Почему плохо:** тесты как afterthought проверяют то, что уже написано, а
не то, что код должен делать. TDD (RED сначала) заставляет думать о контракте
до реализации.

**Покрыто проектной TDD:** для ML-инфраструктуры RED-GREEN-REFACTOR
обязателен (см. `SKILL.md` раздел «Когда применять»).

## Быстрый справочник

| Анти-паттерн | Исправление |
|---|---|
| Assert на мок | Assert на свойства, вычисляемые реальным кодом |
| Test-only метод в production | Вынести в `tests/conftest.py` или `tests/utils.py` |
| Мок без понимания side effects | Мокать ниже (I/O), валидаторы оставить реальными |
| Неполный мок (один df на все вызовы) | Реальные файлы в `tmp_path` или мок по пути |
| Тесты как follow-up | TDD: RED сначала, потом GREEN |

## Red flags

- Assert проверяет `is fake_df` / `mock.called` вместо свойств данных
- Метод в `ML/` начинается с `_test_` или `_reset_`
- `monkeypatch.setattr(..., lambda *a, **k: None)` для валидаторов
- Одна lambda обслуживает несколько вызовов с разными аргументами
- «Сначала напишу код, потом тесты»

## Итог

Мок — инструмент изоляции, не объект тестирования. Если TDD выявил, что ты
тестируешь мок — ты пошёл не туда. Чини: тестируй реальное поведение или
поставь под вопрос, зачем тут мок вообще.
