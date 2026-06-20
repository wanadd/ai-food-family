# PLANAM Recipe Menu Integration v1 — Report

Дата: 2026-06-05  
Ветка: `sprint-0/planam-2026-foundation`  
Базовый коммит: `777d016 feat(recipes): improve catalog quality and search`

## Архитектура (существующая)

Меню хранится в `family_menu_selections.menu_data` (JSONB) как `MenuVariant` с опциональным массивом `days[]`. Отдельных таблиц `menu_items` / `meal_slots` нет — используем текущую модель без новой архитектуры.

Поля слота в `MenuMeal` (расширены):

- `slot_id` — `{date}:{meal_type}` (например `2026-06-05:dinner`)
- `recipe_id`, `servings`, `calories_estimate`, `prep_time_minutes`

## Что сделано

### Backend

| Endpoint | Описание |
|----------|----------|
| `POST /recipes/{id}/add-to-menu` | Payload: `date`, `meal_type`, `servings`. Автосоздание плана на 7 дней, если меню пусто. Ответ: `{ item, created, menu }` |
| `GET /menus/today?date=YYYY-MM-DD` | Блюда с `recipe_id` на выбранную дату |
| `DELETE /menus/items/{slot_id}` | Сброс слота в «Свободно» (URL: `2026-06-05%3Adinner`) |

Сервис: `apps/api/app/services/menu_recipe_plan.py`

- Дубликат (тот же рецепт + дата + meal_type) → `created: false`, без 500
- Dev auth: `X-Telegram-Init-Data: planam-dev-local-v1` + `X-App-Mode: personal`

### Frontend

| Компонент | Изменение |
|-----------|-----------|
| `MenuSlotSheet2026` | Дата (7 дней), приём пищи, порции, прямой вызов API |
| `PlanToday2026` | Удаление блюда, toast, фильтр пустых слотов |
| `PlanMealCard2026` | Кнопки «Удалить», «Заменить» → `/plan/recipes?replaceSlot=...` |
| `RecipeDetail2026` | Toast успех/ошибка, редирект на `/plan/today?saved=1` |

### Тесты

`apps/api/tests/test_menu_recipe_plan.py` — 6 тестов (scaffold, add, duplicate, today, remove).

## Curl-проверки

```bash
# Добавить рецепт в ужин (dev)
curl -X POST http://localhost:8000/recipes/174/add-to-menu \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Init-Data: planam-dev-local-v1" \
  -H "X-App-Mode: personal" \
  -d "{\"date\":\"2026-06-05\",\"meal_type\":\"dinner\",\"servings\":2}"
# → HTTP 200, created=true, item.slot_id=2026-06-05:dinner

curl "http://localhost:8000/menus/today?date=2026-06-05" \
  -H "X-Telegram-Init-Data: planam-dev-local-v1" \
  -H "X-App-Mode: personal"
# → HTTP 200, items>=1

curl -X DELETE "http://localhost:8000/menus/items/2026-06-05%3Adinner" \
  -H "X-Telegram-Init-Data: planam-dev-local-v1" \
  -H "X-App-Mode: personal"
# → HTTP 200
```

Примечание: `X-App-Mode: dev` не поддерживается — используйте `personal` или `family`.

## UI-сценарии

1. `/plan/recipes/[id]` → «В меню» → sheet (дата / приём / порции) → добавить
2. `/plan/today` → блюдо в таймлайне (ужин/обед и т.д.)
3. «Удалить» → confirm → toast «Блюдо удалено из меню»
4. «Заменить» → каталог `/plan/recipes?replaceSlot=...` (минимальный flow)
5. `/plan/generate` — страница `PlanGenerate2026` без 404

## QA

| Команда | Результат |
|---------|-----------|
| `cd backend && python -m pytest` | 34 passed |
| `npm run lint` | OK |
| `npm run build` (UI_2026=true) | OK |
| `npm run build` (UI_2026=false) | OK |

## Backlog

- Полноценная замена блюда через каталог с `replaceSlot` query
- AI-генерация недельного меню
- Drag-and-drop календарь
- Отдельная таблица `menu_items` (если понадобится аналитика)

## Критерии готовности

| Критерий | Статус |
|----------|--------|
| POST /recipes/{id}/add-to-menu | OK |
| Рецепт в меню по дате | OK |
| /plan/today показывает блюдо | OK |
| Дубль без ошибки | OK |
| Удаление блюда | OK |
| Dev без Telegram (planam-dev-local-v1) | OK |
| pytest green | OK |
| lint / build | OK |
