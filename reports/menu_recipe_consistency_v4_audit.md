# PLANAM Menu & Recipe Consistency V4 — Read-Only Audit

**Дата:** 2026-06-10  
**Ветка:** `feat/recipe-gold-v3-original-planam-library`  
**Последний фикс меню:** `0c04d65 fix(menu): avoid recursive selection response wrapper`  
**SQL-аудит меню (до V4):** `total_meals=6`, `null_recipe_id=0`, `not_catalog_ready=0`, `missing_image_url=0`

---

## 1. Карта API и сервисов

| Область | Роуты / точки входа | Сервисы | Примечания |
|--------|---------------------|---------|------------|
| **Генерация меню** | `POST /menus/generate`, `POST /menus/quick-action` | `menu.py` → `menu_ai.py` → `ai.py` / `menu_recipe_builder.py` / `menu_recipe_plan.py` | При наличии OpenAI key — AI; иначе DB builder; иначе heuristic fallback |
| **Выбор варианта** | `POST /menus/select` | `menu.py:select_menu` → `finalize_menu_variant` → `shopping_list.sync_from_menu` | Рекурсивный wrapper исправлен в `0c04d65` |
| **Пересборка** | Нет отдельного `/regenerate` | `POST /menus/generate` (с параметрами), `replace-dish`, `replace-slot` | UI «пересобрать» вызывает generate |
| **Каталог рецептов** | `GET /recipes`, `GET /recipes/filters` | `routers/recipes.py`, `services/recipes/mapper.py` | `title` в API = публичное имя (`public_title`) |
| **Деталка рецепта** | `GET /recipes/{id}` | `mapper.to_detail` | `original_title` в ответе, но UI использует `title` (полное) |
| **Избранное** | `POST /recipes/{id}/favorite` | `recipes.py` + `RecipeFavorite` | В сборке меню **не используется как scoring** (только в промпте AI как текст) |
| **Покупки после выбора** | `shopping_list.sync_from_menu` | `shopping_list.py` | Срабатывает после `select_menu` |
| **AM-баланс** | `subscription.py` | `commit_menu_generation`, `AmaTransaction`, `AmaWallet` | Списание 5 AMS или квота тарифа |
| **AI / OpenAI usage** | `subscription.log_ai_usage` | `AiUsageLog` | **Токены и cost почти никогда не передаются** → админка $0 |
| **Админка затрат** | `routers/admin.py` | Агрегация `AiUsageLog` | Нет отдельного раздела AM-операций |

### Ключевые файлы

- Backend: `apps/api/app/services/menu.py`, `menu_ai.py`, `menu_context.py`, `family_menu_context.py`, `menu_catalog_pool.py`, `menu_catalog_enrichment.py`, `menu_recipe_builder.py`, `menu_recipe_plan.py`, `meal_attendance.py`, `menu_overview.py`, `subscription.py`
- Frontend: `MenuTodayV2.tsx`, `PlanWeek2026.tsx`, `RecipeCatalog2026.tsx`, `RecipeDetail2026.tsx`, `RecipeGridCard2026.tsx`, `lib/plan/plan-today.ts`, `lib/recipes/card-title.ts`

---

## 2. Поля рецептов по экранам

| Поле | Меню → Сегодня | Меню → Обзор | Каталог | Деталка | Покупки | Замена |
|------|----------------|--------------|---------|---------|---------|--------|
| `title` (DB) | через `meal.name` | не показывается | API `title` = public | **заголовок H1** | ингредиенты по recipe_id | карточка `title` |
| `display_title` | **не в типах** | нет | карточки | опционально | — | карточки |
| `original_title` | нет | нет | нет | в API, не в UI | — | нет |
| `normalized_title` | нет | нет | поиск backend | — | — | — |
| `description` | нет | нет | карточка | деталка | — | — |
| `image_url` | `meal.image_url` ✓ | **`null` в UI** | карточка | hero | — | карточка |
| `hero_image_url` | fallback в enrichment | не используется | карточка | hero | — | — |
| snapshot в menu_items | `meal.name` в JSONB | — | — | — | — | — |

**Источник правды сейчас:** для catalog-ready блюд backend кладёт в `meal.name` значение `recipe.title` (полное), а каталог/карточки показывают `display_title` через `public_title()`.

---

## 3. Почему названия расходятся

### Корневая причина

```python
# menu_recipe_builder._meal_from_recipe — использует recipe.title
name=recipe.title or "Блюдо"

# menu_recipe_plan.recipe_to_menu_meal — использует public_title ✓
name=public_title(recipe)
```

При финализации через `menu_catalog_pool.meal_from_catalog_recipe` → `_meal_from_recipe` в меню попадает **длинное `title`**, а каталог и деталка расходятся:

- **Каталог:** `recipeCardHeading` → `display_title ?? title` (короткое)
- **Деталка:** `recipeDetailHeading` → **полный `title`** (ещё одна ветка)

### Примеры (ожидаемые по отчёту пользователя)

| recipe_id | В меню (`meal.name` = `title`) | В деталке / каталоге |
|-----------|--------------------------------|----------------------|
| ~265 | Летний овощной суп с фасолью | Овощной суп с фасолью (`display_title`) |
| ~260 | Курица с брокколи под сыром | Курица с брокколи |

### Snapshot

`menu_items` хранят JSONB с `name`. После выбора меню snapshot **не перезаписывается** из актуального `display_title` рецепта, если `recipe_id` уже есть — enrichment добавляет только `image_url`.

---

## 4. Фото vs финальное блюдо

### Текущий контракт

- Gold V3: `image_prompt_data.dish_visual_summary` (JSONB) — описание для генерации
- **Нет** полей `final_dish_type`, `final_texture`, `visible_cut`, `must_show` / `must_not_show` в схеме Recipe
- Промпт фото: `image_generation_config.py`, quality gate в Gold V3 pipeline
- Риск: generic prompt → суп-пюре с кубиками овощей на фото

### Примеры несоответствий

| Рецепт | Проблема | Причина |
|--------|----------|---------|
| Овощной суп-пюре | Фото: кусочки | `dish_visual_summary` не запрещает chunks / title не в промпте |
| Салаты | Нет явной нарезки в шагах | Шаги не нормализованы по cut style |

**Действие V4:** read-only отчёт `recipe_visual_consistency_audit.md`; миграция visual contract — только после согласования.

---

## 5. Как собирается меню

| Вопрос | Ответ |
|--------|-------|
| OpenAI используется? | Да, если `OPENAI_API_KEY` задан и AI path не падает |
| AI при сборке? | `menu_ai.generate_menu_with_ai` — основной путь |
| Алгоритм без AI? | `menu_recipe_builder.build_menu_from_db` + heuristic |
| `family_id`? | Да, меню привязано к семье |
| Все члены семьи? | В **промпт AI** — да (`menu_context` + `family_menu_context`); в **DB builder** — частично (профиль запрашивающего + family members text) |
| Ограничения всех? | В AI prompt как текст; **deterministic hard filter** — только в catalog pool / builder scoring, не единый `FamilyMenuContext` |
| Избранное? | Не в scoring алгоритма |
| Остатки (pantry)? | Учитываются в AI prompt и в variant scoring (pantry overlap) |
| История готовки? | `meal_checkins` / recent — частично в контексте |

### Три варианта меню

Сейчас: `fast` / `economical` / `balanced` — разные **веса scoring** в `menu_recipe_plan`, но UI **не показывает** summary (ккал, pantry, favorites).

---

## 6. Почему AI-затраты = 0 в админке

| Причина | Детали |
|---------|--------|
| Нет вызовов | Быстрый путь / fallback без OpenAI — честный $0 |
| Вызовы без логирования токенов | `ai_client.chat_text` / `chat_json` **не возвращают** `usage` в вызывающий код |
| `log_ai_usage` без cost | Вызовы из `menu.py` часто без `input_tokens`, `output_tokens`, `estimated_cost` |
| Replace dish | `log_ai_usage(ams_spent=0)` при списании 3 AMS через другой путь |

### Существующие модели

- `AiUsageLog` — AI + смешанное поле `ams_spent`
- `AmaTransaction` — внутренняя экономика
- **Нет** отдельных таблиц `ai_usage_events` / `am_usage_events` как в спецификации V4

### Feature flags (текущие)

Из `config.py` / env (частично):

- `OPENAI_API_KEY` — фактический gate
- Отдельные `AI_MENU_PLANNER_ENABLED` и т.д. — **не найдены** в коде (нужно добавить)

---

## 7. UX-аудит экранов

| Экран | Проблемы | Файл |
|-------|----------|------|
| Меню → Сегодня | «Итог дня» непонятно; `meal.name` ≠ деталка | `MenuTodayV2.tsx` |
| Меню → Обзор | H1 «Неделя» vs nav «План на неделю»; нет фото/названий; `2 блюд` | `PlanWeek2026.tsx` |
| Пересборка | Цели оторваны от профиля | generate UI |
| Выбор 3 меню | Нет объяснения разницы | selection sheet |
| Каталог | Только meal filter; нет category; нет list/grid; избранное внизу | `RecipeCatalog2026.tsx` |
| Деталка | Другой заголовок vs меню | `card-title.ts` |
| Back / scroll | Фильтры в URL ✓; **scroll не восстанавливается** | — |

---

## 8. Грамматика

- `PlanWeek2026.tsx`: `` `${n} блюд` `` — **всегда «блюд»** (ошибка для 2, 3, 4, 22…)
- Нет общего `pluralRu()` helper
- Аналогичные риски: «продуктов», «дней», «порций» — нужен проход по UI

---

## План изменений (фазы)

### Фаза 1 — безопасные быстрые исправления (текущий спринт)

1. **Единое имя:** `public_title` в `_meal_from_recipe` / `meal_from_catalog_recipe`; поле `display_title` на `MenuMeal`; frontend `menuMealHeading()`
2. **Деталка:** `recipeDetailHeading` → `display_title` first
3. **Обзор недели:** фото + названия + `pluralRu`; nav «План питания»
4. **Сегодня:** «Показать итог дня»
5. **Каталог:** избранное на фото; category filter (из API); scroll restore
6. **`pluralRu`** + unit tests

### Фаза 2 — архитектура

1. `FamilyMenuContext` dataclass + `build_family_menu_context()`
2. `MenuGenerationMode` enum + feature flags
3. Разделение `ai_usage_events` / `am_usage_events` (миграция)
4. Проброс токенов из `ai_client` → `log_ai_usage`
5. Favorites scoring в builder
6. Explainable variants в API response

### Фаза 3 — визуальный контракт

1. Миграция JSONB `visual_contract` на Recipe
2. Read-only audit script по каталогу
3. Обновление image prompts (без платной генерации)

### Фаза 4 — тесты и QA

1. Backend: DTO, family constraints, scoring, AM/AI events
2. Frontend: plural, scroll, filters
3. Отчёты: `implementation.md`, `qa.md`

---

## Риски

| Риск | Митигация |
|------|-----------|
| Старые menu JSONB с длинными `name` | `menu_catalog_enrichment` пересинхронизирует `display_title` при GET |
| Миграция usage tables | Только additive migrations |
| AI cost всё ещё 0 без токенов | Фаза 2 обязательна для честной админки |

---

## Ручная проверка после Фазы 1

1. Открыть меню → Сегодня: название = каталог = деталка для recipe 260/265
2. Обзор: видны мини-фото и «2 блюда»
3. Каталог: избранное на фото; назад из деталки — тот же scroll
4. Админка: пока может показывать AI $0 (ожидаемо до Фазы 2)
