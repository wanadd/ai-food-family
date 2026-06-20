# Recipe Rebuild V2 — Requirements Notes

**Status:** Out of scope for P0 hotfix PR.  
**Purpose:** Зафиксировать требования к отдельному этапу пересборки рецептов.

---

## Почему отдельный этап

Текущая база рецептов содержит legacy-данные: кривые единицы, дубли ингредиентов, неполные КБЖУ, странные категории. Удаление/reset в hotfix PR **запрещено** — риск для prod и для пользователей с активными меню.

---

## Scope Recipe Rebuild V2

### 1. Backup & safe migration

- Полный backup `recipes`, `recipe_ingredients`, связанных JSONB до любых изменений.
- Staging-прогон import pipeline.
- Rollback plan (restore from backup SQL).

### 2. Clean seed / import

- Удалить старые seed/import рецепты **безопасно** (не в prod без staging).
- Новая схема рецепта (версионирование: `recipe_schema_version`).
- 30 эталонных рецептов → QA → масштабирование до 500+.

### 3. Культурные / религиозные ограничения

| Ограничение | Поле / тег |
|-------------|------------|
| Халяль | `diet_tags: halal` |
| Кошер | `diet_tags: kosher` |
| Без свинины | `excludes: pork` |
| Постное | `diet_tags: lent` |
| Веган / вегетариан | `diet_tags` |
| Аллергены | `allergens[]` per ingredient |

Интеграция с nutrition profile пользователя при генерации меню.

### 4. Ингредиенты и единицы

- Нормализованные единицы: г, кг, мл, л, шт, ст.л., ч.л., «по вкусу».
- Связь с product taxonomy (canonical slug).
- UI guard (`productTaxonomy.ts`) — уже есть; backend должен отдавать чистые данные.
- Запрет «капуста 1 л» на уровне import validation.

### 5. Meal frequency

Поддержка планов:

- 3 приёма (завтрак / обед / ужин)
- 4 приёма (+ перекус)
- 5–6 приёмов (Pro / sport)
- Привязка рецепта к `meal_type` + `slot_id`

### 6. Спорт / диета / здоровье

- КБЖУ per serving + confidence (`verified` / `estimated` / `unavailable`)
- Макросы: белок / жир / углеводы / клетчатка
- Теги: high_protein, low_carb, recovery, pre_workout
- Связь с wellness targets

### 7. КБЖУ

- `nutrition_summary` на рецепт
- Пересчёт при изменении порций
- Backfill script для существующих рецептов (отдельно от hotfix)

### 8. Shopping & pantry categories

- Canonical category slug на каждый ингредиент
- Маппинг ingredient → shopping list category
- Маппинг ingredient → pantry category
- Согласованность с `category-suggest.ts` / `productTaxonomy.ts`

### 9. Cooking experience

- Пошаговые инструкции (structured steps, не plain text blob)
- Prep time / cook time раздельно
- Фото блюда (CDN или stable URL policy)
- «Начать готовить» → cooking mode (уже в UI V2)

### 10. Acceptance criteria (Recipe Rebuild V2)

- [ ] 30 эталонных рецептов проходят QA (единицы, КБЖУ, шаги, фото)
- [ ] Import pipeline валидирует единицы и категории
- [ ] Меню генерируется без «Свободно»-дыр из-за битых рецептов
- [ ] Shopping list из рецепта — без дублей и мусорных единиц
- [ ] Религиозные фильтры работают в generate menu
- [ ] Rollback tested on staging

---

## Связанные файлы (reference)

| Area | Path |
|------|------|
| UI taxonomy guard | `apps/web/lib/planam/productTaxonomy.ts` |
| Category suggest | `apps/web/lib/shopping/category-suggest.ts` |
| Recipe detail V2 | `apps/web/components/recipes-2026/RecipeDetail2026.tsx` |
| Import scripts | `backend/scripts/`, `apps/api/scripts/` |
| Sample data | `sample_recipes.json` |

---

## Не делать в hotfix PR

- DB reset
- Массовое DELETE recipes
- Изменение import pipeline без staging
- Удаление legacy recipe routes/components
