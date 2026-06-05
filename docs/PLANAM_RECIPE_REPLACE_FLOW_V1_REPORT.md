# PLANAM Recipe Replace Flow v1 — Report

Дата: 2026-06-05  
Ветка: `sprint-0/planam-2026-foundation`  
Базовый коммит: `a288615 feat(menu): connect recipes to daily plan`

## Цель

Полный путь: `/plan/today` → «Заменить» → каталог → выбор рецепта → слот обновлён → возврат в `/plan/today`.

## Формат `replaceSlot`

```text
replaceSlot=YYYY-MM-DD:meal_type
```

Пример:

```text
/plan/recipes?replaceSlot=2026-06-05:dinner
/plan/recipes?replaceSlot=2026-06-05%3Adinner&currentRecipeId=174
```

`%3A` декодируется на фронте через `decodeURIComponent` (`parseReplaceSlot`).

## Backend

| Endpoint | Описание |
|----------|----------|
| `POST /menus/items/{slot_id}/replace` | Payload: `{ recipe_id, servings? }`. Заменяет или заполняет слот. Автосоздание меню при отсутствии. |

Сервис: `replace_recipe_in_slot` в `apps/api/app/services/menu_recipe_plan.py`

Ошибки:

- `recipe_id` не найден → **404**
- невалидная дата / slot_id → **400**
- dev auth: `X-Telegram-Init-Data: planam-dev-local-v1` + `X-App-Mode: personal`

## Frontend

| Файл | Изменение |
|------|-----------|
| `lib/menu/api.ts` | `replaceMenuSlot(slotId, recipeId, servings)` |
| `lib/menu/replace-slot.ts` | парсинг URL, построение ссылок |
| `RecipeCatalog2026` | режим замены: баннер, кнопка «Заменить», «Уже выбрано» |
| `RecipeGridCard2026` | кнопка замены на карточке |
| `RecipeDetail2026` | CTA «Заменить блюдо» при `?replaceSlot=` |
| `PlanMealCard2026` / `PlanToday2026` | «Заменить» → каталог с `replaceSlot` + `currentRecipeId` |

## UI-сценарии

1. `/plan/today` — кнопка «Заменить» на блюде → `/plan/recipes?replaceSlot=...&currentRecipeId=...`
2. Каталог — баннер «Выберите новое блюдо для замены», кнопка «Заменить» на карточках
3. Текущий рецепт — в конце списка, кнопка «Уже выбрано» (disabled)
4. Успех — toast «Блюдо заменено», redirect `/plan/today?saved=1`
5. Ошибка — toast «Не удалось заменить блюдо»
6. Карточка рецепта с `?replaceSlot=` — CTA «Заменить блюдо»
7. Удаление после замены — без изменений, работает

## Curl

```powershell
# replace.json: {"recipe_id": 173, "servings": 2}
curl.exe -X POST "http://localhost:8000/menus/items/2026-06-05%3Adinner/replace" `
  -H "Content-Type: application/json" `
  -H "X-App-Mode: personal" `
  -H "X-Telegram-Init-Data: planam-dev-local-v1" `
  --data-binary "@replace.json"
# → HTTP 200, item.recipe_id=173

curl.exe "http://localhost:8000/menus/today?date=2026-06-05" `
  -H "X-App-Mode: personal" `
  -H "X-Telegram-Init-Data: planam-dev-local-v1"
# → items: recipe_id=173, meal_type=dinner
```

## QA

| Команда | Результат |
|---------|-----------|
| `cd backend && python -m pytest` | **40 passed** |
| `npm run lint` | OK |
| `npm run build` (UI_2026=true) | OK |
| `npm run build` (UI_2026=false) | OK |

Новые тесты: `replace existing slot`, `replace empty slot`, `parse_slot_id` (valid/invalid).

## Backlog

- AI-замена блюда
- Автоподбор по КБЖУ
- Drag-and-drop календарь
- Полная замена через `ReplaceDishSheet2026` (legacy weekly flow)

## Критерии готовности

| Критерий | Статус |
|----------|--------|
| `/plan/today` → Заменить | OK |
| Каталог понимает `replaceSlot` | OK |
| Деталь рецепта понимает `replaceSlot` | OK |
| `POST /menus/items/{slot_id}/replace` | OK |
| Блюдо заменяется в `/plan/today` | OK |
| Удаление после замены | OK |
| pytest / lint / build | OK |
