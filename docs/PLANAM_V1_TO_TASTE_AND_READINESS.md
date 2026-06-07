# PLANAM V1 — to_taste model & readiness (shopping / nutrition / photo)

**Дата:** 2026-06-07  
**Тип:** production-safe, additive, идемпотентный этап после safe-only commit
нормализации и JSONB resync.

**НЕ делает:** не меняет UI, не считает КБЖУ, не генерирует фото/prompts, не
трогает recipe images, не меняет shopping list logic, не авто-фиксит
needs_review, не меняет name/quantity/unit/category, не расширяет JSONB.

---

## 1. Зачем нужна to_taste-модель

Часть строк хранит `quantity = "по вкусу"` / `"немного"` / `"щепотка"` как
обычное количество. Для списка покупок, КБЖУ и фото это нужно различать. Мы
добавляем нейтральную модель качества ингредиента и размечаем строки, **не
трогая исходные данные**.

## 2. Почему нельзя стирать `quantity = "по вкусу"`

`get_structured_ingredients` и legacy JSONB строят `amount` из `quantity`+`unit`.
Стирание `quantity` сломало бы карточку/строку ингредиента. Поэтому raw-текст
сохраняется, а смысл выносится в отдельные поля.

## 3. Какие поля добавлены (в `recipe_ingredients`, все nullable/defaulted)

| поле | значения | назначение |
|------|----------|-----------|
| `quantity_mode` | exact / range / approximate / to_taste / unknown | тип количества |
| `quantity_text` | напр. "по вкусу" | сохранённый raw для to_taste |
| `is_to_taste` | bool (default false) | флаг «по вкусу» |
| `nutrition_precision` | exact / estimated / low_confidence / unavailable | точность для КБЖУ |
| `shopping_priority` | normal / low / optional / hidden | приоритет покупки |
| `needs_review` | bool (default false) | требует ручного решения |
| `needs_review_reason` | generic / ambiguous / unknown_unit / bad_quantity / low_nutrition_precision | причина |
| `photo_visibility` | visible / optional / hidden / unsafe | пригодность для фото |
| `manual_review_status` | pending / approved / rejected / fixed / ignored | статус ручной правки |

Миграция идемпотентна: колонки добавляются через `ADD COLUMN IF NOT EXISTS`
(Postgres) и через intro­спекцию (SQLite). Существующие строки не ломаются.
Эти поля **не отдаются** публичным API (сериализатор собирает ингредиент явно),
поэтому frontend/UI не меняется.

## 4. Как работает `nutrition_precision`

- `exact` — числовое quantity + canonical unit (г/кг/мл/л), не generic, не to_taste;
- `estimated` — штучные/ложечные единицы (шт, зубчик, ст.л., ч.л., стакан, пучок, упаковка);
- `low_confidence` — to_taste / generic / неточные;
- `unavailable` — нет quantity и unit, либо неизвестный продукт (`другое`).

## 5. Как работает `shopping_priority`

- `normal` — основной продукт с числом;
- `low` — соль/перец/специи/соусы, to_taste, масло для жарки;
- `optional` — generic, «по желанию»/«украшение» (по notes);
- `hidden` — вода, «для смазывания формы».

## 6. Как работает `photo_visibility`

- `visible` — конкретные мясо/рыба/овощи/крупы/сыр/яйца/фрукты;
- `optional` — зелень/петрушка/укроп/кинза/зелёный лук, орехи/кунжут как топпинг;
- `hidden` — соль/сахар/перец/масло/вода/уксус, категория специи_соусы, to_taste;
- `unsafe` — generic-продукты (овощи/мясо/рыба/специи/соус/грибы/бульон без конкретики).

## 7. Как запускать dry-run

```bash
python backend/scripts/migrate_to_taste_ingredients.py --dry-run
```

Отчёты: `reports/to_taste_ingredients_migration_dry_run.md` + `.json`,
`reports/ingredient_normalization_needs_review.md` + `.json`.

## 8. Как запускать commit (после backup)

```bash
./scripts/backup.sh
python backend/scripts/migrate_to_taste_ingredients.py --commit --safe-only
python backend/scripts/report_recipe_readiness.py
```

Commit-отчёт: `reports/to_taste_ingredients_migration_commit.md` + `.json`.
Readiness: `reports/recipe_readiness_after_to_taste.md` + `.json`.
Идемпотентность: повторный commit = 0 изменений; `manual_review_status`,
выставленный человеком, на повторе сохраняется.

## 9. Почему JSONB не расширяется

`recipes.ingredients` — legacy-копия формата `[{"name","amount"}]`, используемая
только как fallback. UI/API читают `recipe_ingredients` (источник истины) через
`get_structured_ingredients`. Новые технические поля в JSONB не нужны и не
добавляются, чтобы не ломать совместимость. `amount` уже синхронизирован на
предыдущем этапе (resync).

## 10. Что делать со `needs_review`

~82 строки требуют ручного решения. Они **не меняются автоматически** (кроме
безопасных размеченных полей качества). Список с подсказками —
`reports/ingredient_normalization_needs_review.md` (поле `suggested_action`:
`keep_as_generic`, `specify_product`, `exclude_from_nutrition`,
`low_priority_shopping`, `hide_from_photo_prompt`, `manual_fix_required`).
После ручной правки выставляйте `manual_review_status` = approved/fixed/…

## 11. Следующий этап

1. **Nutrition**: словарь КБЖУ на 100 г, конверсия единиц, оценка по рецепту
   (используя `nutrition_precision`).
2. **Shopping list**: группировка по category, скрытие `hidden`, мягкий показ
   generic, исключение to_taste из обязательных (используя `shopping_priority`).
3. **Photo**: RecipeVisualProfiler + PhotoPromptBuilder на основе
   `photo_visibility` (visible/optional), исключая hidden/unsafe.
