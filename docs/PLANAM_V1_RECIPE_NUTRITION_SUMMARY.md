# PLANAM V1 — Recipe nutrition summary (КБЖУ в БД + API + UI)

Этот этап сохраняет итоговую КБЖУ-оценку **на уровне рецепта**, отдаёт её через
API и мягко показывает в карточке и на детальной странице рецепта.

Строится поверх: нормализованных `recipe_ingredients`, to_taste-модели,
readiness-полей и nutrition facts (`backend/scripts/nutrition_data.py`).

> Безопасность: **не меняет** name/quantity/unit/category, `recipes.ingredients`
> JSONB, recipe images, меню/здоровье/нутрициолога. Все изменения БД — additive
> и идемпотентные. Commit — только после dry-run и backup.

## 1. Зачем

Раньше КБЖУ жили только в reports (`reports/nutrition_estimate.*`). Теперь
итоговая оценка хранится в рецепте как стабильная часть продукта и доступна
клиентам без пересчёта на лету.

## 2. Поля в `recipes` (все nullable / additive)

| поле | смысл |
|------|-------|
| `nutrition_kcal_total` / `_protein_total` / `_fat_total` / `_carbs_total` | КБЖУ на весь рецепт |
| `nutrition_kcal_per_serving` / `_protein_per_serving` / `_fat_per_serving` / `_carbs_per_serving` | КБЖУ на порцию |
| `nutrition_servings` | использованное число порций |
| `nutrition_serving_size_text` | напр. «1 порция» |
| `nutrition_confidence` | `exact` / `estimated` / `low_confidence` / `unavailable` |
| `nutrition_coverage_json` | детали покрытия (счётчики по ингредиентам) |
| `nutrition_calculated_at` | когда посчитано (обновляется только при изменении) |
| `nutrition_source` | `planam_v1_nutrition_facts` |
| `nutrition_needs_review` | требует ручной проверки |
| `nutrition_review_reason` | `low_coverage` / `unavailable_ingredient` / `insufficient_data` / … |

Старые поля (`calories_per_serving`, `protein_g`, …) **не удаляются** и
используются как fallback.

## 3. Как считается total

Для каждого `recipe_ingredient`:
* `nutrition_data.compute_row_nutrition` переводит количество+единицу в граммы
  (через density / piece weights) и берёт КБЖУ на 100 г;
* `to_taste` / generic / неизвестная единица → граммы **не выдумываются**;
* total = сумма по строкам, у которых граммы известны.

## 4. Как считается per serving

`per_serving = total / servings`, где servings:
* берётся из `recipes.servings`, если задано;
* иначе fallback: 1 для breakfast/snack/drink, 4 для lunch/dinner/main/soup/salad;
* иначе `None` → per_serving не заполняется (не выдумываем порции).

## 5. Confidence

| confidence | условие |
|------------|---------|
| `exact` | факты есть, покрытие ≥ 90%, нет unavailable, большинство строк exact |
| `estimated` | факты есть, покрытие ≥ 70%, unavailable ≤ 1 |
| `low_confidence` | покрытие 40–70%, много to_taste/generic/needs_review |
| `unavailable` | покрытие < 40% — посчитать нельзя, КБЖУ = null |

Покрытие считается по «считаемым» ингредиентам (исключая `to_taste`).

## 6. Почему to_taste не считается точно

«Соль по вкусу», «перец по вкусу» — это не граммовка. Считать их как «1 шт» или
любое число — обман. Поэтому они исключаются из обязательного покрытия и не
вносят вклад в КБЖУ, но и не топят confidence искусственно.

## 7. Что попадает в API

`RecipeSummary` / `RecipeDetail` получают объект `nutrition_summary` (или `null`,
если ещё не посчитано):

```json
"nutrition_summary": {
  "kcal_total": 1293, "protein_total": 100, "fat_total": 64, "carbs_total": 72,
  "kcal_per_serving": 323, "protein_per_serving": 25, "fat_per_serving": 16, "carbs_per_serving": 18,
  "servings": 4, "serving_size_text": "1 порция",
  "confidence": "exact", "needs_review": false, "review_reason": null,
  "calculated_at": "2026-06-07T09:31:20Z"
}
```

`null` nutrition не ломает старых клиентов.

## 8. Что показывается в UI

* **Карточка** (`RecipeGridCard2026`): `320 ккал`, для `low_confidence` —
  `≈320 ккал` + подпись «примерно»; для `unavailable` ккал не показывается.
  Fallback на `calories_per_serving` для старых рецептов.
* **Детальная** (`RecipeDetail2026`): блок «КБЖУ на порцию» (4 значения) + «на
  весь рецепт»; для `low_confidence` — мягкое предупреждение, для `unavailable` —
  «КБЖУ пока нельзя посчитать точно».

## 9. Запуск dry-run

```bash
python backend/scripts/calculate_recipe_nutrition_summary.py --dry-run
python backend/scripts/calculate_recipe_nutrition_summary.py --dry-run --limit 20
```

Отчёты: `reports/recipe_nutrition_summary_dry_run.md|json`.

## 10. Запуск commit (после backup)

```bash
python backend/scripts/calculate_recipe_nutrition_summary.py --commit --safe-only
```

Пишет только `nutrition_*` поля. Идемпотентно: повторный запуск = 0 изменений
(`nutrition_calculated_at` не трогается, если контент не изменился).
Отчёты: `reports/recipe_nutrition_summary_commit.md|json`.

## 11. Как проверить

* `python -m pytest` (backend) — тесты калькулятора, commit-идемпотентности, mapper;
* открыть карточку и детальную страницу рецепта — ккал отображается мягко;
* `curl .../recipes/<id>` — присутствует `nutrition_summary`.

## 12. Следующий этап

Recipe-level КБЖУ **подключены** к меню/дню/неделе и целям пользователя:
агрегация на день/неделю, прогресс по целям, подготовка контекста для
нутрициолога — см. [PLANAM_V1_MENU_NUTRITION_AGGREGATION.md](PLANAM_V1_MENU_NUTRITION_AGGREGATION.md).

См. также: [PLANAM_V1_NUTRITION_SHOPPING_PHOTO.md](PLANAM_V1_NUTRITION_SHOPPING_PHOTO.md),
[PLANAM_V1_TO_TASTE_AND_READINESS.md](PLANAM_V1_TO_TASTE_AND_READINESS.md).
