# PLANAM V1 — Агрегация КБЖУ на день/неделю

Этот этап превращает recipe-level КБЖУ (см.
[PLANAM_V1_RECIPE_NUTRITION_SUMMARY.md](PLANAM_V1_RECIPE_NUTRITION_SUMMARY.md))
в ответ на вопрос пользователя: **«Как я питаюсь сегодня и насколько это совпадает
с моей целью?»**

Принцип — честность. Если данных не хватает, PLANAM говорит «примерно» / «часть
рецептов требует уточнения», но **не** выдаёт приблизительное за точное и **не**
считает `unavailable` рецепты как 0.

## 1. Зачем нужна агрегация

Раньше КБЖУ были только на уровне отдельного рецепта. Теперь они складываются по
меню за день и за неделю, сравниваются с целью пользователя и готовятся как
контекст для AI-нутрициолога. Сырые ингредиенты и генерация меню **не трогаются**.

## 2. Откуда берётся recipe nutrition

Источник — уже сохранённые колонки `recipes.nutrition_*`:

- `nutrition_kcal_per_serving`, `nutrition_protein_per_serving`,
  `nutrition_fat_per_serving`, `nutrition_carbs_per_serving`;
- `nutrition_confidence` (`exact` / `estimated` / `low_confidence` / `unavailable`).

Меню хранится как JSON в `family_menu_selections.menu_data`
(`days[].meals[]` с `recipe_id`, `meal_type`, `servings`). День определяется по
`date_iso`. **Новых колонок и миграций этот этап не добавляет.**

## 3. Как считаются totals (день)

Сервис: `apps/api/app/services/nutrition/plan_aggregator.py`.

Для каждого приёма пищи в меню дня:

1. берём `nutrition_summary` рецепта по `recipe_id`;
2. используем `kcal_per_serving` (и БЖУ per serving);
3. умножаем на `serving_multiplier` — **по умолчанию 1 порция на человека**
   (поле `servings` в меню — это объём готовки, не персональный множитель;
   множитель параметризуем для будущего);
4. если рецепт `unavailable` или без КБЖУ — **не считаем как 0**, а увеличиваем
   `unavailable_items` и снижаем coverage;
5. `low_confidence` рецепты **считаются** в totals, но понижают общий confidence.

Приёмы группируются в `breakfast / lunch / dinner / snack / other`.

## 4. Как считаются targets

Резолвер целей (read-only, **ничего не пишет в БД**):

- если есть строка `nutrition_targets` пользователя — берём
  `calories_target / protein_target_g / fat_target_g / carbs_target_g`;
- если строки нет — безопасный fallback: `kcal: 2200`, белки/жиры/углеводы `null`.
  Fallback **не сохраняется** в профиль (только для отображения прогресса).

`progress.{kcal,protein,fat,carbs}_pct` считается там, где цель задана и > 0.

## 5. Что такое confidence (день/неделя)

`coverage = calculated_items / total_items`. Классификация:

| confidence | условие |
|------------|---------|
| `exact` | coverage ≥ 0.90, нет `unavailable`, доля `exact` ≥ 0.8 |
| `estimated` | coverage ≥ 0.70, `unavailable` ≤ 1, доля `low` ≤ 0.5 |
| `low_confidence` | coverage 0.40–0.70 либо много `low`/`unavailable` |
| `unavailable` | coverage < 0.40 либо нет рассчитанных позиций |

Неделя классифицируется по суммарным counts за 7 дней.

## 6. Empty state

Если в меню дня нет блюд с `recipe_id` (`total_items == 0`):

- totals = 0, confidence = `unavailable`, `warnings` пустой;
- UI показывает: **«Добавьте блюда в меню, и я посчитаю КБЖУ»**.

Если блюда есть, но КБЖУ не хватает (`unavailable`): UI пишет, что посчитать
пока нельзя — без нулей и без ложной точности.

## 7. API endpoints

Добавлены в роутер `/menus` (старые endpoints не меняются):

| Endpoint | Назначение |
|----------|------------|
| `GET /menus/nutrition?date=YYYY-MM-DD` | КБЖУ меню за день (по умолчанию сегодня) |
| `GET /menus/today/nutrition` | алиас для сегодняшнего дня |
| `GET /menus/nutrition/week?start=YYYY-MM-DD` | КБЖУ меню за 7 дней |

Day response: `{ date, totals, targets, progress, confidence, coverage, meals[], warnings[] }`.
Week response: `{ start_date, end_date, days[], weekly_total, weekly_average, days_with_full_calc, confidence, warnings[] }`.

Гарантии: пустое меню → totals 0 (не падает); нет recipe nutrition → не падает;
нет цели → fallback target.

## 8. Что показывает UI

`apps/web/components/plan-2026/DayNutritionCard2026.tsx` — компактный блок
**«Питание сегодня»** на странице `/plan/today` (под кнопками действий):

- `1850 / 2200 ккал` + полоса прогресса;
- белки / жиры / углеводы;
- метка «примерно» для `estimated`, «часть рецептов требует уточнения» для
  `low_confidence`;
- empty state при пустом меню;
- mobile-first, светлая/тёмная тема, стиль PLANAM 2026.

## 9. Связь с нутрициологом

`plan_aggregator.get_user_nutrition_context(db, user_id, scope, ...)` собирает
готовый контекст (без LLM): `day_totals`, `week_average`, `goals`, `deltas`
(deficit/excess по каждому макросу), `confidence`, `warnings`,
`top_low_confidence_recipes`. Сам нутрициолог в этом этапе не переписывается.

## 10. Read-only audit

`backend/scripts/audit_menu_nutrition_readiness.py` (только чтение):

```bash
python backend/scripts/audit_menu_nutrition_readiness.py --dry-run
python backend/scripts/audit_menu_nutrition_readiness.py --date 2026-06-07
python backend/scripts/audit_menu_nutrition_readiness.py --week-start 2026-06-03
```

Отчёты: `reports/menu_nutrition_readiness.md|json`. Показывает: сколько menu
items, сколько с `recipe_id`, сколько с usable nutrition, сколько `unavailable` /
`low_confidence`, сколько дней можно/нельзя посчитать, топ проблемных `recipe_id`.

## 11. Тесты

`apps/api/tests/test_menu_nutrition_aggregation.py`:

- пустое меню → totals 0, без падения;
- один `exact` рецепт → точные totals;
- два рецепта с множителем → корректная сумма;
- `unavailable` рецепт → не 0, ниже coverage;
- `low_confidence` → считается, но понижает confidence;
- нет цели → fallback target (без записи в БД);
- day/week response проходят валидацию схемы;
- контекст нутрициолога содержит ожидаемые поля.

## 12. Следующий этап

- персональные приёмы (multiplier из check-ins / member servings);
- недельный UI с динамикой;
- подключение `get_user_nutrition_context` к AI-нутрициологу (LLM).

См. также: [PLANAM_V1_RECIPE_NUTRITION_SUMMARY.md](PLANAM_V1_RECIPE_NUTRITION_SUMMARY.md),
[PLANAM_V1_NUTRITION_SHOPPING_PHOTO.md](PLANAM_V1_NUTRITION_SHOPPING_PHOTO.md).
