# Recipe Engine — переменные окружения (API)

Добавить в `.env` на сервере API. Значения `true` включают фичу; `false` — отключает без деплоя кода.

После изменения — **перезапуск API**.

```bash
# Recipe Engine v1 (Phase 1 activation)
RECIPE_EXPLAINABILITY=true
RECIPE_HISTORY=true
RECIPE_COLLECTIONS=true
FAMILY_RECIPE_PREFERENCES=true
RECIPE_SCENARIOS=true

# Опционально — search facade без HTTP route (пока не влияет на UI)
# RECIPE_ENGINE_V1=false
```

## Rollback

При инциденте выставить нужный флаг в `false` и перезапустить API:

```bash
RECIPE_SCENARIOS=false
# … и т.д.
```

Данные в таблицах Engine (`recipe_history`, `recipe_collections`, …) при rollback **не удаляются**.

## Smoke после включения

1. Открыть рецепт → «Ещё» → «Почему рекомендован», «Я приготовил»
2. `/menu/collections` — создать коллекцию, открыть деталь с карточками
3. Family mode — оценка 👍❤️👎 на рецепте
4. `/menu/recipes` — чип «Из запасов» возвращает рецепты (при заполненных запасах)
