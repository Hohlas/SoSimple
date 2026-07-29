## 13b. MT5 execution parity

### Цель

Проверить, что MT5-эксперт собран из git-исходников и tester исполняет тот же
frozen-сигнал, который проверялся в Python.

Общие правила frozen export, hash, counts, reconciliation, запрета подгонки по
tester-результату и разделения parity от качества ML брать из
[`13-export-mt4-parity.md`](13-export-mt4-parity.md).

### Контур

- Терминал: `/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5`.
- `MQL5` внутри терминала является симлинком на `MT/MQL5`.
- Основной эксперт: `MT/MQL5/Experts/$o$imple.mq5`.
- Скомпилированный файл: `MT/MQL5/Experts/$o$imple.ex5`.

### Компиляция

```bash
WINEPREFIX=/home/hohla/.mt5 xvfb-run -a wine \
  '/home/hohla/.mt5/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe' \
  /compile:'/home/hohla/git/SoSimple/MT/MQL5/Experts/$o$imple.mq5' \
  /log:'/tmp/sosimple_mt5_compile.log'
```

Лог MetaEditor читать так:

```bash
iconv -f UTF-16LE -t UTF-8 /tmp/sosimple_mt5_compile.log | tail -n 20
```

Успех компиляции: в логе `Result: 0 errors, 0 warnings` и обновлён
`MT/MQL5/Experts/$o$imple.ex5`.

Не считать сам код возврата `wine` verdict-ом компиляции: в текущем окружении
MetaEditor может вернуть `1` при успешной сборке. Если `wine` в песочнице
возвращает `159` или не пишет лог, повторить запуск вне песочницы.

### Порядок

1. Проверить симлинк `MQL5 -> MT/MQL5`.
2. Скомпилировать `MT/MQL5/Experts/$o$imple.mq5`.
3. Проверить лог MetaEditor и время изменения `.ex5`.
4. Запускать MT5 tester только после успешной компиляции.
5. Сверять tester-исполнение по правилам
   [`13-export-mt4-parity.md`](13-export-mt4-parity.md): frozen export,
   opened/closed trades, missing opens, wrong direction, close reasons, PnL.
6. Если MT5 заменяет Python-симулятор, зафиксировать отдельно:
   - кто создаёт `Nero.csv`;
   - когда строка признаков доступна;
   - когда Python публикует сигнал;
   - когда MT5 может поставить, удалить или закрыть ордер.

### Обязательные проверки

- `.ex5` собран из текущего `$o$imple.mq5`.
- MetaEditor log сохранён и показывает `0 errors, 0 warnings`.
- MT5 tester читает проверенный frozen export.
- Все расхождения исполнения классифицированы.
- Tester-result не объявляется качеством ML без leakage, split, locked_test,
  robustness и reconciliation-проверок.

### Типовые ошибки

- Не экранировать `$o$imple.mq5` кавычками.
- Считать старый `.ex5` актуальным без проверки времени изменения.
- Считать `wine=1` ошибкой компиляции без чтения MetaEditor log.
- Подгонять модель или export по tester-результату.
- Переносить MT4-логику в MT5 без проверки отличий order API, tester model и
  путей файлов.

---
