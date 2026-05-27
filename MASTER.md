# Master

## Recipe Engine v1 (PlanAm)

Роль Recipe Engine: фундамент библиотеки рецептов, которая питает меню, покупки, запасы, нутрициолога и будущие сценарии (delivery и т.п.).

Документ архитектуры: `docs/RECIPE_ENGINE_V1.md`.

### Текущий статус

Этап 0 (документация) — зафиксирован коммитом с `docs/RECIPE_ENGINE_V1.md`.

Sprint 1 — завершён:
- `refactor(recipes): introduce repository and service layers` (коммит 1)
- `refactor(search): introduce recipe search abstraction` (коммит 2)
- `feat(recipe): add explainability foundation` (коммит 3)
- `feat(collections): add collection domain foundation` (коммит 4)
- `feat(history): add cooking history foundation` (коммит 5)
- `feat(family): add family compatibility foundation` (коммит 6)
- `feat(scenarios): add scenario framework` (коммит 7)
- `chore(flags): add recipe engine feature flags` (коммит 8)

В Sprint 1 **не добавлялись новые API роуты** и **не менялась БД** (только рефакторинг слоёв + контрактные сервисы/DTO + feature flags).

### Принятые архитектурные решения

- Explainability обязательна (Principle #13): пользователь должен видеть причины рекомендации и может игнорировать подсказку.
- Hard-exclude работает только по аллергии/медицинским/религиозным ограничениям (и влияет на рекомендации/автологику, но не ломает ручной выбор).
- `ultra_quick` (≤15 минут) и `almost_no_cooking` зарезервированы: в v1 не активны и без UI/без миграций.

### Ограничения (no-go)

Не делаем в рамках Recipe Engine v1:
- OCR / фото холодильника / доставка / AI Coach / новые тарифы.
- Новый большой редизайн или новые пользовательские экраны.
- Никаких изменений текущих API контрактов и текущей БД без отдельного этапа миграций.

### Feature flags (дефолт = OFF)

В backend: `apps/api/app/config.py`
- `recipe_engine_v1`
- `recipe_collections`
- `recipe_history`
- `recipe_scenarios`
- `recipe_explainability`
- `family_recipe_preferences`

Новые доменные сервисы/логика в Sprint 1 уже ссылаются на эти флаги, но поскольку wire-up в API/БД ещё не выполнен, поведение приложения не менялось.

### Roadmap (очень кратко)

Следующий спринт (Sprint 2, по документу):
- FTS/масштабирование поиска: только слой абстракций и wiring по фиче-флагам (без миграций в рамках шагов, которые ещё не согласованы).
- Появление endpoint’а explainability (`GET /recipes/{id}/why`) и первичная сборка причин на детерминированных данных.
- Подключение collections/history/scenarios к рекомендациям через feature flags.

