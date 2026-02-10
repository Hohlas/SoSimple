**Команда**: `doc this` или `document [файл]`
**Назначение**: Создать полную документацию для нового/недокументированного модуля

Шаги:
1. Проверить наличие file header в коде
   - Если нет → создать по шаблону 000-documentation.md
2. Создать docs/data_preprocessing/[модуль].md
   - Использовать шаблон из 000-documentation.md
3. Добавить запись в MODULE_INDEX.md
4. Обновить DATA_FLOW.md (если участвует в pipeline)
5. Показать diff и запросить подтверждение

Пример:
> doc this processing/normalize.py
Создаю документацию...
- ✅ File header добавлен
- ✅ docs/data_preprocessing/normalize.py.md создан
- ✅ MODULE_INDEX.md обновлён
