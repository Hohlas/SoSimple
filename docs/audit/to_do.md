перед реализацией я бы правил план. Сейчас в нём есть несколько блокирующих несостыковок.      
                                                                                                 
  Что исправить обязательно                                                                      
                                                                                                 
  1. Имена колонок не соответствуют утверждённой спецификации.                                   
     В плане используются target_breach_buy_H6_off02 и т.п. docs/superpowers/plans/2026-06-10-   
     fractal-stop-breach-plan.md:48, а в спецификации утверждён стиль buy_stop_broken_H_flag /   
     sell_stop_broken_H_flag и суффикс _flag docs/superpowers/specs/2026-06-08-fractal-stop-fav- 
     target-design.md:78.                                                                        
     Предлагаю: buy_stop_broken_H6_off02_flag, sell_stop_broken_H12_off05_flag. И обязательно    
     явный denylist, потому что wildcard target_* их не поймает.                                 
                                                                                                 
  2. В плане неверное обращение к parse_fractal().                                               
     План пишет fractal0[2] и fractal0[1] docs/superpowers/plans/2026-06-10-fractal-stop-breach- 
     plan.md:77, но текущая функция возвращает словарь processing/label_signals.py:43. Нужно:    
                                                                                                 
  fractal_dir = fractal0['direction']                                                            
  fractal_price = fractal0['price']                                                              
                                                                                                 
  3. Путь данных смешан.                                                                         
     План заявляет DATA/Nero_{train,validation,test}_labeled.csv docs/superpowers/plans/2026-06- 
     10-fractal-stop-breach-plan.md:13, но smoke-check по умолчанию использует DATA/             
     Nero_XAUUSD_*_labeled.csv statistics/data_contract_smoke_check.py:30. Нужно выбрать один    
     канон. Я бы использовал DATA/Nero_XAUUSD_*_labeled.csv, чтобы совпасть с текущим smoke-check
     и XAUUSD OHLC.

  4. Не надо писать git commit в задачах.
     В AGENTS.md commit запрещён без явной просьбы пользователя. В плане есть несколько commit-
     шагов docs/superpowers/plans/2026-06-10-fractal-stop-breach-plan.md:95, docs/superpowers/
     plans/2026-06-10-fractal-stop-breach-plan.md:694. Нужно заменить на “проверить diff/status;
     commit не делать без явной команды”.

  5. Test нельзя использовать в обычном baseline-цикле до freeze.
     Спецификация говорит: test использовать один раз после freeze docs/superpowers/specs/2026-
     06-08-fractal-stop-fav-target-design.md:156. План сразу считает pred_test и печатает test-
     метрики docs/superpowers/plans/2026-06-10-fractal-stop-breach-plan.md:623. Для Stage 1
     лучше: train + validation для выбора вывода, test только если заранее заморожены target/
     offset/H/model params и критерии.

Что добавить

  - Явный feature contract: какие 10 каналов разрешены, почему break live-safe именно в состоянии
    строки, какие поля запрещены. Методология требует allowlist/denylist docs/methodology/03-
    feature-contract-leakage.md:57.

  - Dummy baseline: majority class / class prior / простое правило. Сейчас есть только RF, а
    методология baseline-first требует dummy и простой ML baseline docs/methodology/07-baseline-
    first.md:16.

  - Проверку случая “не хватает будущих баров” в самой функции: если для H нет ровно H баров,
    ставить NaN, а не считать по укороченному окну. Тест уже это ожидает docs/superpowers/
    plans/2026-06-10-fractal-stop-breach-plan.md:362, но логика функции в Task 1 этого явно не
    фиксирует.

  - Split manifest: даты/размеры train/validation/test и правило purge. Методология требует явные
    границы и embargo/purge при пересечении окна docs/methodology/06-temporal-split.md:16.

  С чем согласен

  - Проверять сначала только факт пробоя, без входов, TP, PnL и PF.
  - Размечать только сторону, соответствующую fractal0.dir, а противоположную оставлять NaN.
  - Считать BUY/SELL отдельно в отчётах.
  - Включить 0.2 и 0.5 как основные stop_offset_val, а 0.0 оставить диагностикой.
  - Делать тесты на BUY, SELL, разные offset, разные H и плохие данные.

  Главная правка: привести план к утверждённой терминологии и убрать преждевременное
  использование test. После этого план можно согласовывать как основу реализации.
