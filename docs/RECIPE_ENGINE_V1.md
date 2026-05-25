# Recipe Engine v1 — Архитектурный документ и план внедрения

**Ветка:** `planam-recipe-engine-v1`
**Статус:** финальная архитектурная спецификация. Этап 0 — фиксация документа в репозитории.
**Скоуп:** дизайн фундамента библиотеки рецептов ПланАм + поэтапная реализация на ~2 спринта.

**История ревизий:**
- **v1** — первичный аудит и архитектура (модель, поиск, импорт, AI-enrichment).
- **v2** — коллекции, история приготовления, расширенные оценки, сценарии, «Из запасов».
- **v3** — Product Principles (12 пунктов), family preference scoring (веса вместо порога), cooking effort profile (резерв), life mode (резерв), расширенные системные коллекции, explainability, дорожная карта 0–9.
- **v3.1 (этот документ)** — Principle #13 (право проигнорировать рекомендацию + обязательность Explainability), сценарий-резерв `ultra_quick` (≤15 мин), сценарий-резерв `almost_no_cooking`.

---

## Оглавление

- [0. PlanAm Product Principles](#0-planam-product-principles)
- [1. Аудит (краткая сводка)](#1-аудит-краткая-сводка)
- [2. Архитектура Recipe Engine v1](#2-архитектура-recipe-engine-v1)
  - [2.1 Концепция](#21-концепция)
  - [2.2 ER-схема (логическая)](#22-er-схема-логическая)
  - [2.3 Таблицы и поля](#23-таблицы-и-поля)
  - [2.4 Индексы и поиск](#24-индексы-и-поиск)
  - [2.5 Слой сервисов](#25-слой-сервисов)
  - [2.6 API endpoints (сводка)](#26-api-endpoints-сводка)
  - [2.7 Family Preference Scoring](#27-family-preference-scoring)
  - [2.8 Совместимость с семьёй](#28-совместимость-с-семьёй)
  - [2.9 Cooking Effort Profile (резерв)](#29-cooking-effort-profile-резерв)
  - [2.10 Life Mode (резерв)](#210-life-mode-резерв)
  - [2.11 Интеграция с меню](#211-интеграция-с-меню)
  - [2.12 Интеграция с покупками](#212-интеграция-с-покупками)
  - [2.13 Интеграция с запасами](#213-интеграция-с-запасами)
  - [2.14 Интеграция с нутрициологом](#214-интеграция-с-нутрициологом)
  - [2.15 Сценарий «Что приготовить из дома?»](#215-сценарий-что-приготовить-из-дома)
  - [2.16 Сценарии (recipe_scenarios)](#216-сценарии-recipe_scenarios)
  - [2.17 Коллекции](#217-коллекции)
  - [2.18 История приготовления и оценки](#218-история-приготовления-и-оценки)
  - [2.19 Авторские рецепты, ревизии, AI-обогащение](#219-авторские-рецепты-ревизии-ai-обогащение)
  - [2.20 Admin импорт](#220-admin-импорт)
  - [2.21 Explainability — обязательная часть Recipe Engine](#221-explainability--обязательная-часть-recipe-engine)
- [3. Дорожная карта внедрения](#3-дорожная-карта-внедрения)
- [4. Что НЕ трогаем (зафиксированный no-go)](#4-что-не-трогаем-зафиксированный-no-go)
- [5. Что откладываем на v1.1 / v1.2](#5-что-откладываем-на-v11--v12)
- [6. Сводный чек-лист](#6-сводный-чек-лист)

---

## 0. PlanAm Product Principles

Эти принципы фиксируются как **архитектурные ограничения** Recipe Engine. Любое нарушение принципа в коде/UI считается багом, а не фичей. В код-ревью допустимая аргументация: «нарушает Principle #N».

| # | Принцип | Где отражён в архитектуре Recipe Engine |
|---|---|---|
| 1 | Пользователь управляет жизнью сам. | В `/recipes` всегда доступен ручной поиск без сценариев. Все CTA — необязательны. `from-pantry` — подсказка, а не предписание. |
| 2 | AI предлагает варианты, но не принимает решения. | AI вызывается только по явному действию: `evaluate`, `improve`, `enrich`. Результат AI кладётся в `recipe_ai_enrichments` со `status=success, applied=false` — пользователь/админ должен подтвердить. |
| 3 | Любое AI-предложение должно иметь ручную альтернативу. | На все AI-операции есть детерминированный fallback (`_evaluate_recipe_heuristic`, `_suggest_improvements_heuristic`, `menu_recipe_builder` после `menu_ai`). |
| 4 | Пользователь может изменить любой результат вручную. | `PUT /recipes/{id}` для владельца; `duplicate` системного → personal с правкой; ревизии (`recipe_revisions`) с откатом; ручной выбор блюда в меню всегда доступен. |
| 5 | Нет скрытых списаний Амов. | Все AI-эндпоинты идут через `subscription_service.require_ai_action` + UI-подтверждение `AmaConfirmDialog`. История списаний в `ai_usage_logs`/`ama_transactions`. |
| 6 | Нет навязчивого paywall. | Recipe Engine v1 — преимущественно бесплатные действия: поиск, коллекции, история готовки, оценки, from-pantry, scenarios. Paywall только на AI-обогащение/анализ. |
| 7 | Пользователь понимает причину рекомендации. | Раздел [2.21 Explainability](#221-explainability--обязательная-часть-recipe-engine): `GET /recipes/{id}/why` + плашка причин в карточке. Без AI, на доменных данных. |
| 8 | Простота важнее количества функций. | Сценарии (фиксированный словарь) и коллекции (CRUD) — простые сущности. Никаких ML/skill-trees в v1. |
| 9 | Забота важнее монетизации. | Бесплатные сценарии «Из запасов», «Постное», «Детям нравится» — не закрыты paywall'ом. |
| 10 | Семья важнее алгоритма. | Семейные оценки членов в `recipe_ratings.family_member_id` влияют на score, но **не исключают** (см. [2.7](#27-family-preference-scoring)). Hard-исключения только по аллергии/медицине/религии. |
| 11 | Автоматизация никогда не блокирует ручной сценарий. | `from_pantry`, scenario-фильтры, авто-проставленные сценарии — это **подсказки**. Все ручные пути работают всегда (`GET /recipes` без фильтров — полный каталог в scope). |
| 12 | Рецепт всегда может быть выбран пользователем независимо от рекомендаций. | `add-to-menu` и `add-to-shopping` работают для любого `recipes.id`, видимого пользователю, даже если recommender оценил его как `not_recommended`. Запрет — только при hard-исключении (аллергия/мед/религия), и то на уровне предупреждения, не блока. |
| **13** | **Пользователь может понять, почему система рекомендует рецепт, и может проигнорировать рекомендацию.** | Рекомендация — это **подсказка, а не приказ**. Пользователь всегда может выбрать другой рецепт. Пользователь всегда может увидеть причины через `GET /recipes/{id}/why` (см. [2.21](#221-explainability--обязательная-часть-recipe-engine)). Логика принятия решения **не скрыта**: все веса в `services/recipes/scoring.py`, все факты — в `explainability.py`. **Explainability — обязательная часть Recipe Engine** (не опциональная фича) и условие готовности любого этапа дорожной карты, который меняет рекомендации (этапы 3, 6, 7, 8). |

**Принцип #13 — комментарии к реализации:**
- Любой коммит, добавляющий новый сигнал в `scoring.py`, обязан также добавить соответствующий `ExplanationReason` в `explainability.py`. Это enforce-ится при ревью.
- Hard-исключение по аллергии/медицине/религии в UI оформляется как **предупреждение с активной кнопкой «Всё равно добавить»**, а не как блокировка (см. [2.8](#28-совместимость-с-семьёй)).
- В `RecipeDetailModal` плашка «Почему рекомендован» — всегда видна (collapsed по умолчанию), а не скрыта в админ-меню.

---

## 1. Аудит (краткая сводка)

Полный аудит — в первой ревизии чата. Сжато:

**Уже есть в БД:** `recipes`, `recipe_ingredients`, `recipe_steps`, `recipe_tags`, `recipe_allergens`, `recipe_restrictions`, `recipe_ratings`, `recipe_favorites`, `recipe_import_jobs`. FK: `meal_checkins.recipe_id`, soft-link `MenuMeal.recipe_id` в JSONB `family_menu_selections.menu_data`.

**Уже есть в API:** 13 эндпоинтов под `/recipes/*` (filters, recommendations, CRUD-lite, favorite toggle, evaluate, family-compatibility, improve, add-to-shopping, add-to-menu).

**Уже есть в UI:** каталог с поиском/чипами/секциями + детальная карточка с evaluate / family-compat / improve / add-to-menu / add-to-shopping.

**Главные проблемы:**
- `ILIKE`-поиск без FTS на потенциально 100k+ рецептов.
- Нет владельца / visibility (`source_type` — слабая string-метка).
- Нет стоимости, сезонности, истории готовки, сценариев, коллекций.
- Дубль избранного (`recipe_favorites` vs `recipe_ratings.is_favorite`).
- AI-обогащение не версионируется (нет rollback).
- `from_pantry` фильтрует в Python после полной выборки.

**Что переиспользуем:**
- Все 13 API-эндпоинтов (additive-расширения DTO; контракт не ломаем).
- Нормализованные подтаблицы рецептов.
- `recipe_storage.*`, `menu_recipe_builder`, `recipe_analysis`.
- Frontend-компоненты (`RecipeCard`, `RecipeCatalog`, `RecipeCatalogSections`, `RecipeDetailModal`).

---

## 2. Архитектура Recipe Engine v1

### 2.1 Концепция

Recipe Engine — доменный фундамент ПланАм, единый источник правды для блюд. Все домены (меню, покупки, нутрициолог, чек-ины, доставка в будущем) ссылаются на `recipes.id`.

Три уровня видимости: `system` / `personal` / `family`.

Три уровня вкусовой памяти:
- **Личное избранное** (`recipe_favorites`) — мой быстрый shortcut.
- **Коллекции** (`recipe_collections`) — мои/семейные тематические подборки.
- **Предпочтения членов семьи** (`recipe_ratings` per `family_member_id`) — кому нравится / не нравится / любимое.

История приготовления (`recipe_cooked_events`) — отдельный домен, питающий рекомендации.

Сценарии (`recipe_scenarios`) — «pre-set views» каталога: быстро, дёшево, для гостей, постное, на работу и т.д.

Recommendations всегда **детерминированы и объяснимы**. AI используется только для обогащения данных, никогда — для принятия решения за пользователя.

### 2.2 ER-схема (логическая)

```
                          ┌──────────────────┐
                          │      users       │
                          └──────┬───────────┘
                                 │ owner_user_id (NULL для system)
                                 │
   ┌─────────────────┐           │
   │    families     │           │
   └────────┬────────┘           │
            │ owner_family_id    │
            │                    │
            ▼                    ▼
        ┌─────────────────────────────────────────┐
        │                recipes                  │
        │ + owner_user_id / owner_family_id       │
        │ + visibility, slug, estimated_cost_rub  │
        │ + seasons[], image_thumb_url, …         │
        │ + revision_no, popularity_score,        │
        │   cooked_total, ai_enrichment_version   │
        │ + search_tsv (GENERATED)                │
        └─┬───────────────────────────────────────┘
          │
   ┌──────┼────────────┬───────────┬──────────────┬─────────────┬──────────────────┬─────────────────────┐
   ▼ N    ▼ N          ▼ N         ▼ N            ▼ N           ▼ N                ▼ N                   ▼ N
recipe_  recipe_      recipe_     recipe_        recipe_       recipe_           recipe_              recipe_ai_
ingred…  steps        tags        allergens      restrictions  scenarios         revisions            enrichments

       ┌───────────────────────────────┐
       │      recipe_favorites         │  ← shortcut пользователя
       └───────────────────────────────┘

       ┌──────────────────────────────────────────┐
       │           recipe_ratings  (extended)     │  ← subject = user_id ИЛИ family_member_id
       │ + family_member_id, liked, disliked,     │     поля: rating, liked, disliked, is_loved,
       │   is_loved, note, updated_at             │     note, cooked_count (cache), last_cooked_at
       │ partial UNIQUE per scope                 │
       └──────────────────────────────────────────┘

       ┌──────────────────────────────────────────┐
       │      recipe_cooked_events                │  ← append-only журнал
       │ recipe_id, user_id, family_id,           │
       │ family_member_id, servings,              │
       │ cooked_on, source, meal_checkin_id?,     │
       │ notes, created_at                        │
       └──────────────────────────────────────────┘

       ┌─────────────────────────┐    1:N    ┌──────────────────────────┐
       │   recipe_collections    │──────────►│   collection_recipes     │
       │ + is_dynamic            │           │                          │
       └─────────────────────────┘           └──────────────────────────┘

       ┌──────────────────────────────────────────┐
       │      user_life_mode  (резерв, v1.1+)      │
       │ user_id ИЛИ family_id, mode, period      │
       └──────────────────────────────────────────┘

       ┌─────────────────────┐
       │ recipe_import_jobs  │ + admin_id + payload + errors
       └─────────────────────┘

Внешние FK на recipes (без изменений):
  meal_checkins.recipe_id  (FK SET NULL, добавляем индекс)
  family_menu_selections.menu_data → JSONB-soft (MenuMeal.recipe_id)
```

### 2.3 Таблицы и поля

#### 2.3.1 Расширение `recipes`

| Поле | Тип | Назначение |
|---|---|---|
| `owner_user_id` | INT NULL FK users.id CASCADE | Владелец personal |
| `owner_family_id` | INT NULL FK families.id CASCADE | Владелец family |
| `visibility` | VARCHAR(16) NOT NULL DEFAULT 'system' | `system` / `personal` / `family` |
| `slug` | VARCHAR(220) NULL UNIQUE | Admin/SEO |
| `estimated_cost_rub` | INT NULL | Оценка стоимости порции |
| `seasons` | JSONB DEFAULT '[]' | `[spring/summer/autumn/winter]` или `[any]` |
| `image_thumb_url` | VARCHAR(512) NULL | Превью |
| `image_attribution` | VARCHAR(255) NULL | Источник изображения |
| `ai_enriched_at` | TIMESTAMPTZ NULL | Когда последний раз обогащали |
| `ai_enrichment_version` | INT NOT NULL DEFAULT 0 | Счётчик обогащений |
| `revision_no` | INT NOT NULL DEFAULT 1 | Версия рецепта |
| `popularity_score` | DOUBLE PRECISION NOT NULL DEFAULT 0 | Для рекомендаций |
| `cooked_total` | INT NOT NULL DEFAULT 0 | Кеш по `recipe_cooked_events` |
| `search_tsv` | tsvector GENERATED | FTS |

**CHECK инварианты:**
- `visibility='system'` ⇒ оба owner_* NULL.
- `visibility='personal'` ⇒ `owner_user_id NOT NULL`, `owner_family_id NULL`.
- `visibility='family'` ⇒ `owner_family_id NOT NULL`, `owner_user_id NULL`.

#### 2.3.2 Расширение `recipe_ratings`

Добавляем: `family_member_id INT NULL FK family_members CASCADE`, `liked BOOL DEFAULT FALSE`, `disliked BOOL DEFAULT FALSE`, `is_loved BOOL DEFAULT FALSE`, `note VARCHAR(200) NULL`, `updated_at TIMESTAMPTZ DEFAULT now()`.

**Инварианты:**
- Subject — либо `user_id`, либо `family_member_id` (XOR).
- `liked` и `disliked` взаимоисключаются на уровне сервиса (БД допускает обе false).
- `is_loved=true` ⇒ `liked=true` (нормализуется в сервисе).
- partial UNIQUE `(family_member_id, recipe_id)` WHERE `family_member_id IS NOT NULL`.
- partial UNIQUE `(user_id, recipe_id)` WHERE `family_member_id IS NULL`.

Старая колонка `is_favorite` — deprecated, остаётся (data preservation), не пишется/не читается.

#### 2.3.3 Новые таблицы

`recipe_cooked_events` (append-only журнал):
- `id, recipe_id (CASCADE), user_id (SET NULL), family_id (SET NULL), family_member_id (SET NULL), servings INT NULL, cooked_on DATE NOT NULL DEFAULT CURRENT_DATE, source VARCHAR(16) DEFAULT 'manual' (manual/menu/bot/meal_checkin), meal_checkin_id INT NULL FK SET NULL, notes VARCHAR(200) NULL, created_at`
- Индексы: `(recipe_id, cooked_on DESC)`, `(user_id, cooked_on DESC) WHERE NOT NULL`, `(family_id, cooked_on DESC) WHERE NOT NULL`, `(family_member_id, cooked_on DESC) WHERE NOT NULL`.

`recipe_collections`:
- `id, owner_user_id, owner_family_id, visibility (system/personal/family), name VARCHAR(120), description VARCHAR(500) DEFAULT '', emoji VARCHAR(8) NULL, color VARCHAR(16) NULL, is_pinned BOOL DEFAULT FALSE, is_dynamic BOOL DEFAULT FALSE, position INT DEFAULT 0, created_at, updated_at`
- CHECK инварианты как у `recipes`.
- `is_dynamic=true` означает: состав резолвится сервисом, не из `collection_recipes` (используется для «Из запасов»).

`collection_recipes`:
- `id, collection_id (CASCADE), recipe_id (CASCADE), position INT, added_by_user_id (SET NULL), added_at, note VARCHAR(200) NULL`
- UNIQUE `(collection_id, recipe_id)`.

`recipe_scenarios`:
- `id, recipe_id (CASCADE), scenario VARCHAR(32) NOT NULL, score DOUBLE PRECISION DEFAULT 1.0, source VARCHAR(16) DEFAULT 'auto' (auto/admin/user)`
- UNIQUE `(recipe_id, scenario)`. Индекс `(scenario)`.

`recipe_revisions`:
- `id, recipe_id (CASCADE), version INT, snapshot_json JSONB, edited_by_user_id (SET NULL), edit_reason VARCHAR(120) NULL (ai_improve/manual/import), created_at`
- UNIQUE `(recipe_id, version)`.

`recipe_ai_enrichments`:
- `id, recipe_id (CASCADE), version INT, model VARCHAR(64), status VARCHAR(16) (success/failed/skipped), payload_json JSONB, applied BOOL DEFAULT FALSE, ams_spent INT DEFAULT 0, triggered_by VARCHAR(16) (admin/user/auto), created_at`.

`user_life_mode` **(резерв, создаётся пустой, см. [2.10](#210-life-mode-резерв))**:
- `id, user_id NULL FK users CASCADE, family_id NULL FK families CASCADE, mode VARCHAR(24) (normal/budget_saving/active_sport/vacation/holiday), starts_on DATE NULL, ends_on DATE NULL, is_active BOOL DEFAULT TRUE, note VARCHAR(200) NULL, created_at`
- partial UNIQUE `(user_id) WHERE family_id IS NULL AND is_active`; `(family_id) WHERE is_active`.

`recipe_import_jobs` (расширение существующей): `+ created_by_admin_id, payload_json, errors_json`.

#### 2.3.4 Что НЕ трогаем структурно

`recipe_ingredients`, `recipe_steps`, `recipe_tags`, `recipe_allergens`, `recipe_restrictions`, `recipe_favorites`.

### 2.4 Индексы и поиск

- `CREATE EXTENSION IF NOT EXISTS pg_trgm`.
- GIN: `recipes.search_tsv`, `recipes.title gin_trgm_ops`, `recipe_ingredients.name gin_trgm_ops`.
- Composite: `(meal_type, is_active)`, `(category, is_active)`, `(visibility, is_active)`.
- Partial: `(owner_user_id) WHERE NOT NULL`, `(owner_family_id) WHERE NOT NULL`, `(popularity_score DESC) WHERE is_active`.
- `meal_checkins(recipe_id) WHERE NOT NULL`.

`search_tsv` (формула уточняется при имплементации):
```
setweight(to_tsvector('russian', coalesce(title,'')), 'A')
  || setweight(to_tsvector('russian', coalesce(description,'')), 'B')
  || setweight(to_tsvector('simple', tags_text), 'C')
```

### 2.5 Слой сервисов

```
services/recipes/
  __init__.py            # фасад для обратной совместимости
  catalog.py             # list / get / filters / seed
  search.py              # FTS + фильтры + сортировка
  storage.py             # persist/get/scale/aggregate
  authoring.py           # CRUD + владение + visibility
  revisions.py           # snapshot + restore
  compat.py              # fit_level + family_compatibility
  scoring.py             # центральный калькулятор score (см. 2.7)
  improvements.py        # AI suggest/apply
  recommendations.py     # рекомендации + объяснение
  cooked.py              # запись/чтение событий + кеш cooked_total
  ratings.py             # like/dislike/loved/rating
  collections.py         # CRUD коллекций + состав
  scenarios.py           # словарь + автопроставление + meta
  from_pantry.py         # сценарий «Что приготовить из дома»
  explainability.py      # сервис "почему рекомендован" (см. 2.21)
  import_pipeline.py     # admin импорт
  ai_enrich.py           # AI-обогащение каталога
  hooks/
    menu_link.py             # add_to_menu
    shopping_link.py         # add_to_shopping
    meal_checkin_link.py     # авто-запись cooked event при чек-ине
```

Фасад `services/recipes.py` сохраняется и реэкспортирует функции — существующие импорты не ломаются.

### 2.6 API endpoints (сводка)

**Существующие 13 — НЕ меняем сигнатуру.** Расширяем DTO (опциональные поля) и принимаем дополнительные query-параметры.

`GET /recipes` дополнительные query (все опциональные, additive):
- `mine_only`, `family_only`, `season`, `max_cost_rub`, `cuisine`, `cooked_recently`
- `scenario` (см. словарь в [2.16](#216-сценарии-recipe_scenarios))
- `collection_id`, `loved_by_member_id`
- `not_disliked` (default `true` в семейном режиме — **только** для сортировки и предупреждений, не для исключения; см. [2.7](#27-family-preference-scoring))

**Новые пользовательские эндпоинты:**

| Метод | Путь | Назначение |
|---|---|---|
| PUT | `/recipes/{id}` | Полное редактирование (владелец) |
| DELETE | `/recipes/{id}` | Soft/hard delete |
| GET | `/recipes/mine` | Personal + family |
| POST | `/recipes/{id}/duplicate` | Копия в personal |
| GET | `/recipes/{id}/revisions` | История |
| POST | `/recipes/{id}/revisions/{ver}/restore` | Откат |
| POST | `/recipes/{id}/cooked` | Записать «приготовлено» |
| GET | `/recipes/{id}/history` | История этого рецепта |
| GET | `/recipes/history` | Журнал scope |
| POST | `/recipes/{id}/rate` | liked/disliked/is_loved + опц. `family_member_id` |
| GET | `/recipes/from-pantry` | «Что приготовить из дома» |
| GET | `/recipes/scenarios` | Список сценариев + meta |
| GET | `/recipes/{id}/why` | Объяснение рекомендации (см. [2.21](#221-explainability--обязательная-часть-recipe-engine)) |

**Коллекции:**

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/collections` | List scope (system + my personal + family) |
| POST | `/collections` | Create |
| GET | `/collections/{id}` | Detail + recipes |
| PATCH | `/collections/{id}` | Update |
| DELETE | `/collections/{id}` | Delete |
| POST | `/collections/{id}/recipes` | Add (bulk) |
| DELETE | `/collections/{id}/recipes/{recipe_id}` | Remove |
| POST | `/collections/{id}/reorder` | Reorder |

**Admin (`/admin/recipes`, `/admin/collections`):** list/detail/patch, import (dry-run+commit), import-jobs, ai-enrich + history, promote-to-system, scenarios override, recompute-scenarios, recompute-popularity, system-collections CRUD.

### 2.7 Family Preference Scoring

Цель: не исключать рецепт из-за «не нравится». Использовать систему весов и оставить выбор пользователю.

#### Архитектура расчёта score

Для каждого рецепта в контексте scope считаем `recipe_score(recipe, scope) → ScoreResult`:

```
ScoreResult {
  total: float          # итоговый балл (может быть отрицательным)
  breakdown: [
    { code, label, points, kind }   # позиционно учтённые слагаемые
  ]
  hard_exclude: bool    # если true — рецепт нарушает hard-правило
  hard_reasons: [{ code, label }]  # причины hard-исключения
}
```

#### Веса (стартовые, выставлены в `scoring.py` как константы)

**Предпочтения членов семьи** (применяются per active member, суммируются):

| Сигнал | Вес |
|---|---|
| `recipe_ratings.is_loved=true` (любимое) | **+3** |
| `recipe_ratings.liked=true` | **+1** |
| `recipe_ratings.disliked=true` | **−2** |
| `rating` (1–5) | `(rating − 3)` — от −2 до +2 |

**Совместимость с целью пользователя:**

| Сигнал | Вес |
|---|---|
| Соответствует `nutrition_goal=lose` (низкокалорийный, fiber, низкий sugar) | +2 |
| Соответствует `nutrition_goal=sport/gain` (protein ≥ 25г или `suitable_for_sport`) | +2 |
| Соответствует `nutrition_goal=kids` и `suitable_for_children` | +2 |
| Не соответствует цели (например, dessert при `lose`) | −1 |

**Сценарии и контекст:**

| Сигнал | Вес |
|---|---|
| Активен `from_pantry` и `pantry_coverage ≥ 80%` | +2 |
| Активен сценарий, который выставлен у рецепта (`recipe_scenarios.score` × 1) | +1..+2 |
| Сезон совпадает (`recipes.seasons` содержит текущий) | +1 |
| `popularity_score` (нормированный 0..1) | ×1 |
| `cooked_total > 0` для текущего scope (часто готовим) | +1 |
| Время с последнего приготовления > 30 дней | +0.5 (соскучились) |
| `estimated_cost_rub` в пределах `budget` пользователя | +1, иначе −0.5 |

**Cooking effort** (зарезервировано, в v1 = 0; см. [2.9](#29-cooking-effort-profile-резерв)):

| Сигнал | Вес |
|---|---|
| `cooking_effort=minimum_time` и `cooking_time_minutes ≤ 30` | +2 |
| `cooking_effort=minimum_time` и `cooking_time_minutes > 60` | −2 |
| `cooking_effort=love_cooking` и `difficulty ≥ medium` | +1 |

**Life mode** (зарезервировано, в v1 = 0; см. [2.10](#210-life-mode-резерв)):

| Сигнал | Вес |
|---|---|
| `life_mode=budget_saving` и `cheap` сценарий у рецепта | +2 |
| `life_mode=active_sport` и `suitable_for_sport` | +2 |
| `life_mode=vacation` и `quick` сценарий | +1 |
| `life_mode=holiday` и `holiday`/`guests` сценарий | +2 |

Все веса хранятся в одном модуле `services/recipes/scoring.py` как именованные константы — легко тюнить без миграции.

#### Hard-исключения (единственные допустимые)

Рецепт **полностью исключается** из автоматических рекомендаций (Menu Builder и `/recipes/from-pantry`), если выполняется хотя бы одно:

1. **Аллергия:** ингредиент / `recipe_allergens` содержит вещество из `user_profile.allergies` любого активного члена семьи.
2. **Медицинское ограничение:** ингредиент / `recipe_restrictions` пересекается с медицинскими ограничениями (`user_profile.medical_restrictions` ключевые слова: «диабет», «гипертония», «целиакия» и т.п. — словарь в `compat.py`).
3. **Религиозное ограничение:** `user_profile.restrictions` / `family_member.restrictions` содержит `halal`, `kosher`, `lenten`, и рецепт **не** имеет соответствующего сценария.

**Важно (Principle #12 и #13):** даже при hard-исключении рецепт **остаётся видимым** в каталоге через прямой поиск/ручной фильтр. При попытке `add-to-menu` пользователь увидит предупреждение, но действие **не блокируется**. Hard-исключение действует **только** в автоматической логике (Menu Builder, recommendations, from-pantry).

#### Где используется ScoreResult

- `menu_recipe_builder.build_menus_from_recipes`: при отборе кандидатов вместо «отбросить если disliked ≥ 2» — сортировка `ORDER BY score DESC`; hard-exclude фильтрует.
- `recipes_service.get_recommendations`: возвращает топ-N по score.
- `from_pantry`: score участвует в `suggested_score = pantry_coverage × 0.5 + score × 0.3 + recent_unused_bonus × 0.2`.
- `compat.family_compatibility`: возвращает per-member breakdown (см. [2.8](#28-совместимость-с-семьёй)).
- `explainability`: каждое слагаемое из `breakdown` превращается в человеко-читаемую причину.

#### Принцип нейтральности

Если у рецепта нет ни одного сигнала (нейтральный для всех) — `total=0`, не отрицательный. Никаких «штрафов по умолчанию».

### 2.8 Совместимость с семьёй

`family_compatibility(recipe)` возвращает:

```
{
  members: [
    {
      member_id, name, status (ok|warning|conflict),
      preference (loved|liked|neutral|disliked|none),
      note, score_contribution (float)
    }
  ],
  total_score: float,
  hard_exclude: bool,
  hard_reasons: [...]
}
```

UI в `RecipeDetailModal`:
- Плашка «Реакция семьи»: аватары с эмодзи (`❤ / 👍 / · / 👎`).
- При `hard_exclude=true` — красная плашка «⚠ Не рекомендуется: содержит аллерген орехов для Маши. Выбор всё равно за вами.» с **активной** кнопкой «Всё равно добавить в меню» (Principle #12, #13).

### 2.9 Cooking Effort Profile (резерв)

Цель: дать пользователю выбрать стиль готовки, не перепиливая схему позже.

**Где хранится:**
- `user_profiles.cooking_effort VARCHAR(16) NULL` — новое поле, добавляется в миграции M1 рядом с `cooking_time` (legacy).
- Допустимые значения: `love_cooking`, `normal`, `minimum_time`, NULL (нейтрально).

**Как используется** (в v1 — no-op; в v1.1+ — включается):
- В `scoring.py` уже есть слагаемые «Cooking effort» (см. [2.7](#27-family-preference-scoring)), но множитель `EFFORT_WEIGHTS_ENABLED=False` в v1.
- В `RecipeRecommendationContext` (внутренний DTO в `recommendations.py`) поле `cooking_effort: str | None` всегда заполняется из профиля; в weighted-сумме игнорируется при выключенном флаге.
- UI v1.1: добавляется в `/profile` или `/menu/settings` (вне Recipe Engine).

**Что нужно сейчас:**
- Колонка в `user_profiles`.
- Поле в `RecipeRecommendationContext`.
- Слагаемые в `scoring.py` за флагом `EFFORT_WEIGHTS_ENABLED`.
- DTO `RecipeSummary` опциональное поле `effort_match: 'good'|'neutral'|'bad'` (в v1 всегда `null`).

Включение в v1.1 — только тоггл флага, никаких миграций и API-изменений.

### 2.10 Life Mode (резерв)

Цель: режим жизни влияет на рекомендации, может меняться часто (отпуск 1 неделю, праздники 3 дня).

**Где хранится:** отдельная таблица `user_life_mode` (см. [2.3.3](#233-новые-таблицы)).

**Допустимые значения:** `normal` / `budget_saving` / `active_sport` / `vacation` / `holiday`.

**Как используется** (в v1 — no-op):
- В `scoring.py` слагаемые «Life mode» уже описаны (см. [2.7](#27-family-preference-scoring)), но за флагом `LIFE_MODE_WEIGHTS_ENABLED=False`.
- В `RecipeRecommendationContext.life_mode: str | None` — заполняется в v1 константно `'normal'`.
- В `services/recipes/scoring.py` — функция `compute_life_mode_bonus(recipe, mode) -> float` стаб (возвращает 0), включается флагом.

**API в v1.1** (резерв, эндпоинтов в v1 нет):
- `GET /life-mode/active`
- `POST /life-mode/activate` (mode, starts_on, ends_on)
- `POST /life-mode/deactivate`

В Recipe Engine v1 — таблица создаётся пустой, ни один сервис её не пишет. UI ничего не показывает.

**Почему не JSONB-флаг в `user_preferences`:**
- Life mode имеет период (`starts_on/ends_on`) и историю — кладётся именно в строки таблицы.
- Отдельная таблица не требует миграции `user_preferences` при последующих расширениях.

### 2.11 Интеграция с меню

- `MenuMeal.recipe_id` обязательно проставляется при добавлении из БД.
- `menu_recipe_builder.build_menus_from_recipes`:
  - Hard-exclude (аллергии/мед/религия) — фильтр.
  - Остальное — сортировка по `recipe_score(recipe, scope)` DESC.
  - `disliked` рецепт может попасть в меню, если у него высокий общий score (например, любимое блюдо одного перевешивает дизлайк другого) — это **сознательное** решение по Principle #10.
- Замена блюда — приоритет рецептов того же сценария.
- `ai_context._recipe_catalog_slice` — топ-200 по `score`-функции, потом подмножество 40 для AI.

### 2.12 Интеграция с покупками

Без структурных изменений. `add_recipe_to_shopping` рефакторится в `hooks/shopping_link.py`. В шопинг-айтемы передаётся `metadata.from_recipe={id, title}` (только в payload, без отдельной таблицы).

### 2.13 Интеграция с запасами

`from_pantry` — основной сценарий (см. [2.15](#215-сценарий-что-приготовить-из-дома)). `list_recipes(from_pantry=True)` переписывается в SQL и алиасится на `/recipes/from-pantry?simple=true`.

### 2.14 Интеграция с нутрициологом

В AI-контекст нутрициолога передаются:
- Топ-5 рецептов из `recipe_cooked_events` за последний месяц.
- Топ-5 «любимых» (`is_loved=true`).
- Список dislike-блюд (honest awareness).
- Активные сценарии в каталоге scope.

`recipe_to_ai_dict` расширяется. Усечение полей: не более 5 любимых, 5 dislike, 10 cooked — чтобы не раздувать промпт.

### 2.15 Сценарий «Что приготовить из дома?»

Endpoint `GET /recipes/from-pantry?max_missing=2&meal_type=&servings=`.

Алгоритм (одним SQL roundtrip):

1. Из `family_pantry_items` собираем `pantry_patterns`.
2. JOIN `recipes` ⨝ `recipe_ingredients` GROUP BY `recipe_id`, считаем `have_count` / `total_ings`.
3. HAVING `total_ings - have_count ≤ max_missing`.
4. Применяем hard-exclude из [2.7](#27-family-preference-scoring) (аллергии/мед/религия).
5. ORDER BY `pantry_coverage DESC, recipe_score(scope) DESC, cooking_time ASC`.
6. Возвращаем `RecipeFromPantryItem` с `missing_ingredients[]` и `suggested_score`.

UI:
- Главная: карточка «🏠 Что приготовить из дома?» с превью топ-3.
- Экран `/recipes/from-pantry`: слайдер «можно докупить N продуктов», чипы meal_type.
- Из `/shopping` и `/pantry` — кнопки «Из запасов».

Цена: бесплатно, не AI.

### 2.16 Сценарии (`recipe_scenarios`)

#### Активный словарь (v1)

Авто-проставляется или ставится админом. Хранится в `recipe_scenarios` со `source ∈ {auto, admin, user}`.

| Код | Правило / описание |
|---|---|
| `quick` | `cooking_time_minutes ≤ 25` |
| `cheap` | `estimated_cost_rub ≤ 250` |
| `kids_loved` | `suitable_for_children=true` + положительные оценки детей |
| `lose` | для похудения (низкая калорийность + клетчатка) |
| `gain` | для набора массы (калории ≥ 600 + белок ≥ 25г) |
| `guests` | `servings ≥ 6, suitable_for_event=true` |
| `holiday` | праздничные блюда |
| `on_the_go` | в дорогу (portable, не разваливается) |
| `work_lunch` | на работу (boxed-friendly, разогревается) |
| `lenten` | постное (без мяса/рыбы/молока/яиц) |
| `kosher` | кошерное (правила kashrut) |
| `halal` | халяль |
| `from_pantry` | динамический, не хранится в таблице |

Авто-проставление: `scenarios.recompute(recipe_id)` при создании/обновлении рецепта. `kosher`/`halal`/`lenten` — **только admin вручную** (никакого `source='auto'`), AI может предложить через `recipe_ai_enrichments` для админ-аппрува.

#### Зарезервированные сценарии (v1.1+, в v1 не используются)

Зарезервированные сценарии **не требуют миграций** (используется существующая таблица `recipe_scenarios`), **не требуют UI** в v1, но **должны быть учтены в словаре констант** `SCENARIOS_RESERVED` в `services/recipes/scenarios.py`, чтобы:
- предотвратить случайное переиспользование кода;
- задокументировать намерение;
- разрешить admin вручную проставлять такие сценарии заранее (опционально).

| Код | Правило / описание | Причина выделения |
|---|---|---|
| `ultra_quick` | `cooking_time_minutes ≤ 15` | Между 15 и 30 минутами есть заметная пользовательская разница: «успеть до того, как ребёнок проснулся / до встречи через 20 минут». `quick` (≤25 мин) слишком широкий для таких случаев. |
| `almost_no_cooking` | Минимальная готовка: разогреть, собрать, открыть, смешать, полуготовые решения. Не равно `minimum_time` (это профиль пользователя). | Отдельный пользовательский сценарий, ортогональный к скорости. Бывает, что пользователь не хочет «20 минут активной готовки», а хочет «достал, разогрел, поел» — это другой UX. Рассмотренные альтернативы названия: `ready_to_eat` (стандартный food-industry термин, но семантически уже — подразумевает «совсем без готовки»). Выбрано `almost_no_cooking` — точнее отражает «разогреть/собрать/смешать», где минимальная активность допустима. |

**Что нужно зарезервировать в v1:**
- В `services/recipes/scenarios.py` константы:
  ```
  SCENARIOS_ACTIVE = {quick, cheap, kids_loved, lose, gain, guests, holiday,
                      on_the_go, work_lunch, lenten, kosher, halal, from_pantry}
  SCENARIOS_RESERVED = {ultra_quick, almost_no_cooking}
  SCENARIOS_ALL = SCENARIOS_ACTIVE ∪ SCENARIOS_RESERVED
  ```
- Валидация при импорте/admin override принимает только `SCENARIOS_ALL`.
- В `GET /recipes/scenarios` возвращаются **только** `SCENARIOS_ACTIVE` (с meta-полем `recipes_count`).
- При активации в v1.1: добавить в `SCENARIOS_ACTIVE`, добавить правило в `scenarios.recompute()`, добавить UI-чип и иконку. **Никаких миграций, никаких API-изменений.**

### 2.17 Коллекции

- Один рецепт может быть в N коллекциях.
- Не дублируют избранное (`recipe_favorites`).
- В UI `/recipes`: карусель «Мои коллекции» над сценариями.
- В `RecipeDetailModal`: кнопка «🗂 В коллекцию».

#### Seed системных коллекций

| Коллекция | Состав (отбор по правилам) | Тип |
|---|---|---|
| Топ-10 быстрых | `scenario=quick` ORDER BY popularity DESC LIMIT 10 | system |
| Топ-10 экономных | `scenario=cheap` ORDER BY popularity DESC LIMIT 10 | system |
| Постное меню | `scenario=lenten` LIMIT 12 | system |
| Праздничный стол | `scenario=holiday` LIMIT 12 | system |
| Детям нравится | `scenario=kids_loved` LIMIT 12 | system |
| Семейные классики | `popularity_score ≥ p80` + `cooked_total > 0` агрегированный по семьям, top 12 | system |
| Ужин за 30 минут | `meal_type='dinner' AND cooking_time_minutes ≤ 30 AND is_active` ORDER BY popularity LIMIT 15 | system |
| Для спортсменов | `(suitable_for_sport=true OR scenario IN ('gain')) AND protein_g ≥ 25` LIMIT 15 | system |
| Из запасов | **Динамическая** (`is_dynamic=true`). Состав резолвится сервисом `from_pantry`, а не из `collection_recipes`. | system, dynamic |

Seed-составы для не-динамических системных коллекций — генерируются в `seed_system_collections()` после прохода `scenarios.recompute_all()`.

### 2.18 История приготовления и оценки

Без изменений по сравнению с v2 (см. [2.3.2](#232-расширение-recipe_ratings), [2.3.3](#233-новые-таблицы) и эндпоинты в [2.6](#26-api-endpoints-сводка)).

**Запись:**
1. Пользователь нажимает «Я приготовил» → `POST /recipes/{id}/cooked` с опц. `family_member_id`, `servings`, `notes`.
2. При чек-ине блюда в `MealCheckinPanel` со статусом `ate_planned` хук `meal_checkin_link.on_planned_eaten` создаёт `recipe_cooked_event` со `source='meal_checkin'` (с дедупом по `(recipe_id, scope, cooked_on)` в окне 4 часов).
3. Бот: `source='bot'`.

**Чтение:**
- `GET /recipes/{id}/history` — последние N приготовлений рецепта в scope.
- `GET /recipes/history` — общий журнал scope.
- В `RecipeDetail`: «Готовили N раз. Последний — DD.MM.YYYY». В family-режиме — список членов.

Цена: бесплатно, не AI.

### 2.19 Авторские рецепты, ревизии, AI-обогащение

**Создание:** `POST /recipes` с `visibility ∈ {personal, family}` (системные — только admin).
**Редактирование:** `PUT /recipes/{id}` (только владелец). Каждое редактирование создаёт ревизию в `recipe_revisions`.
**Удаление:** `DELETE` — soft (`is_active=false`) для никогда не использовавшихся, жёсткое — только если нет ссылок.
**Дублирование:** `POST /recipes/{id}/duplicate` — копирует системный/семейный в `personal`.

**AI Enrichment:** обогащаем КБЖУ, аллергены, `cuisine`, `seasons`, `estimated_cost_rub`, теги, корректность шагов. Сервис `ai_enrich.enrich_recipe()` создаёт запись в `recipe_ai_enrichments` со `status='success', applied=false`. Применение — отдельный шаг (admin/user подтверждает). При `applied=true` создаётся `recipe_revisions`.

**AMA-цена:** существующие `recipe_analyze=2`, `recipe_improve=3`. Новый `recipe_enrich_full=4` (admin — без списания; user — да).

### 2.20 Admin импорт

UI `/admin/recipes` — таблица, фильтры (system/personal/family, есть AI-enrichment, нет картинки, нет калорий).

Endpoint: `POST /admin/recipes/import` с `dry_run=true|false`.

Алгоритм:
1. Создаётся `recipe_import_jobs` со `status=running`, `created_by_admin_id`.
2. Для каждого item: валидация (Pydantic), дедуп (по `slug` или нормализованному `title+meal_type+cooking_time_minutes`), создание `Recipe` с `visibility='system', source_type='import'`, `persist_recipe_structure` для ингредиентов/шагов/тегов/аллергенов, опц. триггер AI-обогащения.
3. Поддерживает `scenarios[]` в payload — записывается в `recipe_scenarios` со `source='import'`. После — `scenarios.recompute(recipe_id)` для auto-сценариев.
4. В конце — `imported_count`, `failed_count`, `errors_json`, `status`.

Аудит: каждое действие пишется в `admin_audit` (существует) с `target_type='recipe'`.

### 2.21 Explainability — обязательная часть Recipe Engine

**Статус:** обязательная часть Recipe Engine (Principle #13). Не опциональная фича.

Цель: пользователь всегда видит, **почему** ПланАм предлагает этот рецепт. Без AI, на детерминированных данных.

#### DTO

```
Explanation {
  recipe_id: int
  summary: string                # короткая фраза в 1 строку
  positives: ExplanationReason[] # ✓ почему рекомендован
  warnings:  ExplanationReason[] # ⚠ на что обратить внимание
  hard_blocks: ExplanationReason[] # ⛔ почему НЕ рекомендован (но всё ещё доступен)
  score_total: float
}

ExplanationReason {
  code: string        # machine-readable: pantry_match | kid_loved | goal_lose | …
  icon: string        # ✓ / ❤ / 🏠 / ⚡ / ⚠ / ⛔
  label: string       # «есть в запасах 4 из 5 ингредиентов»
  weight: float       # вклад в score (положительный/отрицательный)
}
```

#### Источники данных (все детерминированные, БД-уровень, без AI)

| Code | Когда добавляется | Источник |
|---|---|---|
| `pantry_match` | от ≥1 ингредиента совпадает | `recipe_ingredients` ⨝ `family_pantry_items` |
| `loved_by_member` | у активного члена `is_loved=true` | `recipe_ratings` |
| `liked_by_member` | у активного члена `liked=true` | `recipe_ratings` |
| `disliked_by_member` | у активного члена `disliked=true` | `recipe_ratings` |
| `goal_match` | подходит nutrition_goal | `user_profile.nutrition_goal` + поля рецепта |
| `quick_to_cook` | `cooking_time_minutes ≤ 25` | `recipes` |
| `cheap_for_budget` | `estimated_cost_rub ≤ budget_threshold` | `recipes` + `user_profile.budget` |
| `season_match` | сезон совпадает | `recipes.seasons` + дата |
| `popular_in_family` | `cooked_total > 0` для scope | `recipe_cooked_events` |
| `not_cooked_long_time` | >30 дней не готовили | `recipe_ratings.last_cooked_at` |
| `kid_friendly` | `suitable_for_children=true` и в семье есть child | `recipes` + `family_members` |
| `sport_friendly` | `suitable_for_sport=true` и goal=sport/gain | `recipes` + `user_profile` |
| `scenario_match` | активный сценарий совпадает | `recipe_scenarios` |
| `allergen` (hard) | hard-exclude по аллергии | `recipe_allergens` + `user_profile.allergies` |
| `medical_restriction` (hard) | hard-exclude по медицине | `recipe_restrictions` + `user_profile.medical_restrictions` |
| `religious_restriction` (hard) | hard-exclude по религии | `user_profile.restrictions` + `recipe_scenarios` |
| `cost_too_high` | `estimated_cost_rub > 2 × budget_threshold` | `recipes` + `user_profile.budget` |
| `goal_mismatch` | не подходит nutrition_goal | `user_profile` + `recipes` |

#### Endpoint

`GET /recipes/{id}/why` — возвращает `Explanation`. Бесплатно, без AI, без AMA.

#### UI

- В `RecipeCard`: одна строка `summary` под названием (опционально, в v1.1).
- В `RecipeDetailModal`: секция «Почему рекомендован» — список `positives` зелёным, `warnings` жёлтым, `hard_blocks` красным с пометкой «Но выбор всё равно за вами» (Principle #12, #13). Всегда видна (collapsed по умолчанию).

#### Принцип «explainability without AI»

Все source-коды выше реализуются в одном сервисе `services/recipes/explainability.py` через простые SQL/Python функции:

```
def explain_recommendation(db, user, scope, recipe) -> Explanation:
    score = recipe_score(recipe, scope)        # из scoring.py
    facts = collect_facts(db, user, scope, recipe)  # детерминированный сбор
    return render_explanation(score, facts)
```

`collect_facts` объединяет данные из `recipe_ratings`, `recipe_cooked_events`, `recipe_allergens`, `recipe_restrictions`, `recipe_scenarios`, `family_pantry_items`, `user_profiles`, `family_members` и возвращает структурированный набор фактов. AI не вызывается.

#### Контракт ревью (enforce Principle #13)

При код-ревью любой PR, добавляющий новый сигнал в `scoring.py`, должен также добавить:
1. Соответствующий `ExplanationReason` в `explainability.py`.
2. Метку в `services/recipes/explainability_codes.py` (центральный реестр кодов).

PR без этих двух пунктов — отклоняется.

---

## 3. Дорожная карта внедрения

Принцип: каждый этап заканчивается продовым деплоем. Между этапами — git tag (`recipe-v1.X`). Все этапы — additive, обратимы.

### Этап 0. Документация и подготовка

**Что:** этот документ принят, положен в репозиторий, согласованы все пункты чек-листа.
**Коммиты:** 1.
**Миграции:** нет.
**Деплой:** только документация.
**Риски:** —
**Точка отката:** `git revert` коммита 1.
**Выход:** есть `docs/RECIPE_ENGINE_V1.md`, все стороны видят финальную архитектуру.

### Этап 1. Безрисковые рефакторинги (без миграций)

**Что:** разбить `services/recipes.py` на пакет с фасадом; вынести `quick_recipe_fit_level` в один батч-вычислитель.
**Коммиты:** 2, 3.
**Миграции:** нет.
**Деплой:** одним релизом после этапа 0.
**Риски:** регресс листинга — митигация: smoke-тест на staging «открыть `/recipes`, открыть карточку, добавить в избранное».
**Точка отката:** `git revert` коммитов 2–3.
**Выход:** поведение идентично, код подготовлен к расширениям.

### Этап 2. Миграции базы

**Что:** последовательный прогон M1 → M2 → M3 → M4 → M5.
**Коммиты:** 4 (M1), 5 (M2), 6 (M3), 7 (M4), 8 (M5).
**Деплой:** **отдельным окном** после согласования. Сначала dev → staging → smoke (EXPLAIN на `recipes`, `recipe_ingredients`) → prod.
**Риски:**

| Миграция | Риск | Митигация |
|---|---|---|
| M1 (поля на `recipes`) | Большая таблица — ALTER может занять секунды | Все ALTER — `ADD COLUMN` с DEFAULT/NULL, без переписывания строк |
| M2 (`recipe_revisions`, `recipe_ai_enrichments`, `user_life_mode`) | Создание пустых таблиц | Никакого |
| M3 (расширение `recipe_ratings`) | Partial UNIQUE может конфликтовать с существующими дублями | Pre-check: `SELECT user_id, recipe_id, count(*) FROM recipe_ratings GROUP BY ... HAVING count>1` — должно быть пусто |
| M4 (`recipe_cooked_events`, collections, scenarios) | Создание пустых таблиц | Никакого |
| M5 (pg_trgm + GIN + tsvector) | tsvector backfill на 100k записей — может занять минуты | Создаём `CONCURRENTLY` где возможно; в downtime — миграция запустится в lifespan startup, чуть подольше |

**Точки отката:**
- Каждая миграция обратима (`DROP COLUMN` / `DROP TABLE` / `DROP INDEX`). Rollback SQL — рядом с каждым шагом в `database_migrations.py` (комментарий).
- В случае проблем — откат миграции + откат коммита; остальные этапы продолжают работать (у них пока нет зависимостей от новых полей в коде).

**Выход:** БД готова к этапам 3–9, новых API/UI пока нет — пользователь ничего не замечает.

### Этап 3. Базовый Recipe Engine

**Что:** расширение DTO (опциональные поля), новый `recipe_search` поверх tsvector + новые query-параметры; владельческие правки рецептов (`PUT`, `duplicate`, ревизии); централизованный `scoring.py` (с выключенными флагами effort/life_mode); сервис `explainability` + `GET /recipes/{id}/why`.

**Коммиты:** 9, 10, 11 (search), 12 (authoring + revisions), 13 (scoring + why).
**Миграции:** уже все есть.
**Деплой:** мини-релизами по 1–2 коммита.
**Риски:**
- Регресс существующего поиска (ILIKE → tsvector). Митигация: feature-flag `RECIPE_SEARCH_FTS_ENABLED` в `settings`. По умолчанию — `true` на dev, `false` на prod до проверки.
- Скоринг даст «другую» сортировку. Митигация: явно задокументировать; для совместимости — старая сортировка остаётся доступной при отсутствии query.
- `PUT /recipes/{id}` для системных рецептов — должно блокироваться по visibility. Митигация: тест.

**Точки отката:**
- FTS — feature-flag, при проблеме переключается за минуты.
- `PUT` — `git revert`.
- Scoring — `RECIPE_SCORING_ENABLED` (default true), при проблеме выключается, возвращается старая логика.

**Выход:** поиск масштабируется, пользователь может редактировать свои рецепты, скоринг централизован, `why` отвечает.

### Этап 4. Коллекции

**Что:** CRUD коллекций + bulk add + system seed (включая «Ужин за 30 минут», «Для спортсменов», «Из запасов»). UI — карусель + кнопка «🗂 В коллекцию».

**Коммиты:** 14 (бэкенд), 15 (UI), 16 (seed system collections).
**Миграции:** уже все есть.
**Риски:** дублирование с избранным (UI-нечёткость). Митигация: разные иконки (★ favorite vs 🗂 collection), разные place в UI.
**Точка отката:** revert коммитов 14–16; данные в `recipe_collections`/`collection_recipes` сохраняются (пустые таблицы — не вредят).

**Выход:** работают мои/семейные/системные коллекции, динамическая «Из запасов» ведёт на from-pantry.

### Этап 5. История приготовления + оценки

**Что:** `POST /recipes/{id}/cooked`, `GET /recipes/{id}/history`, `GET /recipes/history`, `POST /recipes/{id}/rate`. UI — кнопка «Я приготовил», ряд аватарок «Реакция семьи». Хук `meal_checkin_link.on_planned_eaten`.

**Коммиты:** 17 (cooked), 18 (ratings), 19 (UI).
**Миграции:** уже все есть.
**Риски:**
- Двойная запись «приготовил» — митигация: при чек-ине ищем event этого же дня и не дублируем.
- `is_loved` без `liked` — нормализуем на сервисе (`is_loved=true → liked=true`).

**Точка отката:** revert; журнал `recipe_cooked_events` остаётся, кеши `cooked_total` можно пересчитать.

**Выход:** работает полная семейная история готовки, видна вкусовая память членов семьи.

### Этап 6. Сценарии

**Что:** словарь активных сценариев (см. [2.16](#216-сценарии-recipe_scenarios)), авто-проставление при create/update, `GET /recipes/scenarios`, `?scenario=` в поиске. UI: карусель сценариев + бейджи в карточке. Резервы `ultra_quick` и `almost_no_cooking` остаются только в константах, без UI и без авто-правил.

**Коммиты:** 20 (бэкенд + словарь + резервы), 21 (UI), 22 (рекомпьют для существующих рецептов).
**Миграции:** уже все есть.
**Риски:**
- Авто-проставление спорное для `kosher`/`halal`/`lenten`. Митигация: только admin override, в `scenarios.recompute` для этих кодов — только `source=admin`, не `auto`.

**Точка отката:** очистка `recipe_scenarios` (`DELETE WHERE source='auto'`) + revert.

**Выход:** работают 12 активных сценариев + динамический `from_pantry`. Резервы зарегистрированы.

### Этап 7. From Pantry

**Что:** `GET /recipes/from-pantry`, динамическая системная коллекция «Из запасов» оживает, кнопки «Из запасов» из `/shopping` и `/pantry`, карточка на главной.

**Коммиты:** 23 (бэкенд), 24 (UI экран), 25 (точки входа из других экранов).
**Миграции:** уже все есть.
**Риски:**
- Производительность на 100k рецептов. Митигация: GIN trigram-индекс на `recipe_ingredients.name` уже создан в M5; протестируем EXPLAIN заранее.
- Слишком много «не хватает 5 продуктов» при пустых запасах — UI-сообщение «Заполните запасы, и ПланАм подскажет, что приготовить».

**Точка отката:** revert коммитов 23–25; пользователь возвращается к ручному `?from_pantry=true`-фильтру (legacy).

**Выход:** реальный сценарий «Что приготовить из дома?» работает на главной и в трёх входных точках.

### Этап 8. Интеграция с меню

**Что:** Menu Builder использует `recipe_score(scope)` (с учётом семейных preferences), `disliked` понижает, `is_loved` повышает; hard-exclude фильтрует; replace prefers same scenario; `ai_context._recipe_catalog_slice` отдаёт топ-200 по score; авто-запись `recipe_cooked_event` при `meal_checkin status=ate_planned`.

**Коммиты:** 26 (scoring в menu_builder), 27 (replace by scenario), 28 (ai_context update), 29 (meal_checkin hook).
**Миграции:** нет.
**Риски:**
- Семейное меню «уезжает» по сравнению с прошлым поведением (разные рекомендации). Митигация: feature-flag `RECIPE_SCORING_IN_MENU_BUILDER` (default true); при проблеме — выключаем, возвращается старый алгоритм.
- Авто-запись cooked events — может дублировать ручные. Митигация — дедуп по `(recipe_id, scope, cooked_on)` в окне 4 часов.

**Точка отката:** feature-flag → off.

**Выход:** меню учитывает вкусы семьи без блокировок; все принципы P10/P12/P13 соблюдены.

### Этап 9. Интеграция с нутрициологом и финальная полировка

**Что:** `recipe_to_ai_dict` расширен (включает кулинарную историю, любимое, не нравится, сценарии); промпт нутрициолога знает про сценарии (даёт ответы вида «вот 3 быстрых рецепта на работу»); admin-роуты `/admin/recipes/*` и `/admin/recipes/import` поверх существующих коллекций/обогащений; UI «+ Создать рецепт».

**Коммиты:** 30 (ai_context), 31 (admin read-only + audit), 32 (admin import + AI-enrich), 33 (UI создания пользовательского рецепта).
**Миграции:** нет.
**Риски:**
- Расширенный AI-промпт = больше токенов. Митигация: трукация — не более 5 любимых, 5 dislike, 10 cooked.
- Импорт может загрузить дубли. Митигация: dedup по `slug` или нормализованному `title+meal_type+cooking_time`.

**Точка отката:** все коммиты независимы; revert одного из 30–33 не сломает остальные.

**Выход:** Recipe Engine v1 закрыт целиком. Все домены подключены.

### Порядок деплоя (компактно)

```
[0] Docs                               (1 коммит, без миграций)
        │
        ▼
[1] Refactor                           (2 коммита, без миграций)
        │
        ▼
[2] Migrations M1→M2→M3→M4→M5          (5 коммитов, отдельное окно)
        │
        ▼
[3] Базовый engine: DTO + search +     (5 коммитов, feature-flags для FTS и scoring)
    authoring + scoring + why
        │
        ▼
[4] Коллекции + seed                   (3 коммита)
        │
        ▼
[5] История + оценки                   (3 коммита)
        │
        ▼
[6] Сценарии                           (3 коммита)
        │
        ▼
[7] From Pantry                        (3 коммита)
        │
        ▼
[8] Интеграция с меню                  (4 коммита, feature-flag в Menu Builder)
        │
        ▼
[9] Нутрициолог + admin + UI           (4 коммита)
```

Между этапами 1↔2, 2↔3 — обязательная пауза для smoke-тестов.
Между этапами 8↔9 — пауза для замера latency и ошибок.

### Сводная таблица рисков и точек отката

| Этап | Главный риск | Митигация | Точка отката |
|---|---|---|---|
| 0 | — | — | git revert |
| 1 | Регресс листинга | smoke-тест staging | git revert |
| 2.M1 | ALTER на большой таблице | ADD COLUMN с DEFAULT | DROP COLUMN |
| 2.M3 | Дубли при partial UNIQUE | Pre-check select | DROP COLUMN + INDEX |
| 2.M5 | tsvector backfill | CONCURRENTLY где возможно | DROP INDEX |
| 3 | FTS-регресс | feature-flag `RECIPE_SEARCH_FTS_ENABLED` | flag off |
| 3 | Скоринг меняет сортировку | feature-flag `RECIPE_SCORING_ENABLED` | flag off |
| 4 | UI-путаница favorites vs collections | разные иконки, тестирование UX | revert UI |
| 5 | Двойная запись cooked | dedup window 4 часа | revert |
| 6 | Авто-проставление религиозных сценариев | только admin-ручной | revert + cleanup `recipe_scenarios WHERE source='auto' AND scenario IN ('kosher','halal','lenten')` |
| 7 | Latency from-pantry | предварительный EXPLAIN | feature-flag `RECIPE_FROM_PANTRY_ENABLED` |
| 8 | Меню меняется | feature-flag `RECIPE_SCORING_IN_MENU_BUILDER` | flag off |
| 9 | Дубли при импорте | dedup по slug/title | revert импортной джобы |

---

## 4. Что НЕ трогаем (зафиксированный no-go)

- OCR / фото холодильника / доставка / AI Coach / новые тарифы.
- Контракт публичных эндпоинтов `/recipes/*`, `/menus/*`, `/shopping-lists/*`, `/pantry`, `/nutritionist/*`.
- `recipe_favorites` (структура и поведение).
- `MenuVariant`, `MenuMeal`, `MenuGenerateResponse`, `SelectedMenuResponse`.
- `shopping_list.sync_from_menu` (внутренняя логика).
- `family_menu_selections`.
- `subscription_service.require_ai_action` + `AmaConfirmDialog`.
- Существующие индексы и FK.

---

## 5. Что откладываем на v1.1 / v1.2

- Активация `cooking_effort` (UI + влияние на score).
- Активация `life_mode` (UI + API + влияние на score).
- Активация `ultra_quick` и `almost_no_cooking` сценариев (правила автопроставления + UI-чипы).
- `ingredient_dictionary` (нормализация имён).
- Семейное общее «избранное».
- Cursor-based пагинация в `GET /recipes`.
- Nightly auto-enrichment cron.
- Импорт из внешних источников (TheMealDB / Edamam / CSV).
- UI-конструктор по фото.
- Семейный дашборд «что готовим чаще всего».
- ML-рекомендации.
- Партиционирование `recipe_cooked_events`.
- Команды бота `/quick`, `/cheap`, `/lenten`.
- Дашборд «Не готовили давно» (90+ дней).
- Drag-and-drop reorder в коллекции.
- Унификация `category=kids` / `tags=kids_friendly` / `diets=kids_friendly`.

---

## 6. Сводный чек-лист

Подтверждённые на этапе согласования пункты (фиксируются как «принято» в момент создания этого документа):

1. **13 продуктовых принципов** в разделе [0](#0-planam-product-principles) — приняты.
2. **Family scoring веса** в разделе [2.7](#27-family-preference-scoring) (loved=+3, liked=+1, disliked=−2, goal=+2 и т.д.) — приняты как стартовые, тюнятся без миграций.
3. **Hard-exclude список** — только аллергия / медицина / религия. `banned_foods` уходит в обычный negative weight, не в hard-exclude.
4. **Cooking effort** — резерв в `user_profiles.cooking_effort` + `EFFORT_WEIGHTS_ENABLED=false`. Принято.
5. **Life mode** — отдельная таблица `user_life_mode` (создаётся пустой в M2) + `LIFE_MODE_WEIGHTS_ENABLED=false`. Принято.
6. **Системные коллекции** — 9 штук (6 базовых + «Ужин за 30 минут», «Для спортсменов», «Из запасов»). «Из запасов» — динамическая. Принято.
7. **Explainability** — `GET /recipes/{id}/why`, без AI, без AMA. **Обязательная часть Recipe Engine** (Principle #13). Принято.
8. **Миграции M1–M5** — запускать отдельным окном после этапа 1. Принято.
9. **Feature-flags** — `RECIPE_SEARCH_FTS_ENABLED`, `RECIPE_SCORING_ENABLED`, `RECIPE_SCORING_IN_MENU_BUILDER`, `RECIPE_FROM_PANTRY_ENABLED` — все default `true`, при инцидентах выключаются. Принято.
10. **Порядок этапов 0–9** + точки отката — принято.
11. **`recipe_ratings.is_favorite`** — deprecated, не удаляется. Источник правды избранного — `recipe_favorites`. Принято.
12. **AMA-цены v1**: «Я приготовил», коллекции, рейтинги, история, from-pantry, explainability — все **бесплатно**. AI-обогащение для админа — без списания. Принято.
13. **Сценарии-резервы** `ultra_quick` (≤15 мин) и `almost_no_cooking` (разогреть/собрать/смешать/полуготовое) — зарегистрированы в `SCENARIOS_RESERVED`, в v1 не активны, без UI, без миграций. Принято.

После согласования этого документа — начинается этап 1 (рефакторинги без миграций).
