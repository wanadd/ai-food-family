# Recipe Import Pipeline v1

## Цель

`Recipe Import Pipeline v1` - безопасный фундамент для ручного пакетного добавления рецептов в существующий каталог PlanAm. В этой версии нет UX-изменений, API для массового импорта и фоновых job-runner'ов. Импорт запускается вручную backend-скриптом, пишет в уже существующие таблицы рецептов и пропускает дубли.

## Текущая архитектура рецептов

### Модели и таблицы

Основная модель находится в `apps/api/app/models/recipe.py`.

- `recipes` (`Recipe`) - карточка рецепта: название, описание, тип приема пищи, категория, кухня, сложность, времена, порции, КБЖУ, источник, признаки напитка/алкоголя/детского/спортивного/event-рецепта, JSONB-поля `diets`, `tags`, `ingredients`, `steps`.
- `recipe_ingredients` (`RecipeIngredientRow`) - нормализованные ингредиенты: `name`, `quantity`, `unit`, `category`, `is_optional`, `notes`.
- `recipe_steps` (`RecipeStepRow`) - шаги приготовления с `step_number`.
- `recipe_tags` (`RecipeTagRow`) - теги для поиска/сценариев.
- `recipe_allergens` (`RecipeAllergenRow`) - аллергены.
- `recipe_restrictions` (`RecipeRestrictionRow`) - ограничения/диеты; синхронизируются с `Recipe.diets`.
- `recipe_favorites` (`RecipeFavorite`) - избранное пользователя, уникально по `user_id + recipe_id`.
- `recipe_ratings` (`RecipeRating`) - пользовательские/семейные оценки и счетчик готовки.
- `recipe_import_jobs` (`RecipeImportJob`) - существующая таблица для будущего трекинга импортов; в v1 скрипт ее не использует, чтобы не менять поведение приложения.

Важная деталь: у рецепта есть и нормализованные rows, и legacy JSONB fallback. За синхронизацию отвечает `apps/api/app/services/recipe_storage.py`.

### Сервисы

- `apps/api/app/services/recipes/catalog.py` - список, фильтры, получение рецепта, seed при пустой базе.
- `apps/api/app/services/recipes/repository.py` - SQLAlchemy-доступ к рецептам без доменной логики.
- `apps/api/app/services/recipes/mapper.py` - преобразование ORM в DTO `RecipeSummary` / `RecipeDetail`.
- `apps/api/app/services/recipes/authoring.py` - создание/обновление, избранное, добавление рецепта в покупки.
- `apps/api/app/services/recipe_storage.py` - сохранение структуры рецепта: ингредиенты, шаги, теги, аллергены, ограничения; также сбор ингредиентов для shopping list.
- `apps/api/app/services/recipe_analysis.py` - оценка, совместимость с семьей, улучшения, добавление рецепта в меню.
- `apps/api/app/services/menu_recipe_builder.py`, `menu.py`, `menu_ai.py`, `menu_ai_legacy.py` - генерация и сборка меню с рецептами/ингредиентами.
- `apps/api/app/services/shopping_list.py` - синхронизация списка покупок из выбранного меню или из рецепта.

### Endpoint'ы рецептов

Файл: `apps/api/app/routers/recipes.py`, prefix `/recipes`.

- `GET /recipes/filters` - фильтры каталога.
- `GET /recipes/recommendations` - рекомендации.
- `POST /recipes` - ручное создание рецепта через API.
- `GET /recipes` - список с фильтрами: поиск, meal type, category, diet, difficulty, pantry, children/sport/event/drinks.
- `GET /recipes/{recipe_id}` - детальная карточка.
- `PATCH /recipes/{recipe_id}` - частичное обновление базовых полей.
- `POST /recipes/{recipe_id}/favorite` - избранное.
- `POST /recipes/{recipe_id}/add-to-shopping` - добавить ингредиенты рецепта в shopping list.
- `POST /recipes/{recipe_id}/add-to-menu` - добавить рецепт в меню.
- Recipe Engine endpoints: history, cooked, rate, why, evaluate, family-compatibility, improve, from-pantry, scenarios.

### Меню

Модель: `apps/api/app/models/menu_selection.py`.

- `family_menu_selections` хранит выбранное меню в JSONB `menu_data`.
- Меню не ссылается FK на `recipes`; оно хранит сериализованный `MenuVariant`.
- Endpoint'ы: `apps/api/app/routers/menus.py`, prefix `/menus`.
- Ключевые операции: `POST /menus/generate`, `POST /menus/select`, `GET /menus/selected`, `POST /menus/replace-dish`, `GET /menus/overview`, `POST /menus/quick-action`.

Связь с рецептами прикладная: сервисы могут добавить рецепт в `MenuVariant`, после чего выбранное меню сохраняется как JSONB.

### Shopping list

Модель: `apps/api/app/models/shopping_list.py`.

- `family_shopping_lists` хранит актуальный список покупок в JSONB `items`.
- Может ссылаться на `family_menu_selections.id` через `menu_selection_id`.
- Endpoint'ы: `apps/api/app/routers/shopping_lists.py`, prefix `/shopping-lists`.
- `POST /recipes/{recipe_id}/add-to-shopping` использует `recipes.authoring.add_recipe_to_shopping`, масштабирует ингредиенты через `scale_ingredients`, агрегирует через `aggregate_ingredients_for_shopping` и синхронизирует список через `shopping_list.sync_from_menu`.

## JSON-формат импортируемого рецепта

Файл импорта - JSON-массив объектов. Минимально обязательны `title`, `meal_type`, `ingredients`, `steps`.

```json
[
  {
    "title": "Овсянка с яблоком и корицей",
    "description": "Быстрый завтрак на каждый день.",
    "meal_type": "breakfast",
    "category": "quick",
    "cuisine": "home",
    "difficulty": "easy",
    "prep_time_minutes": 5,
    "cooking_time_minutes": 10,
    "servings": 2,
    "calories_per_serving": 320,
    "protein_g": 10,
    "fat_g": 8,
    "carbs_g": 52,
    "fiber_g": 7,
    "sugar_g": 14,
    "source_type": "import",
    "source_url": null,
    "image_url": null,
    "is_drink": false,
    "is_alcoholic": false,
    "suitable_for_children": true,
    "suitable_for_sport": false,
    "suitable_for_event": false,
    "diets": ["vegetarian", "budget"],
    "tags": ["breakfast", "quick"],
    "allergens": ["gluten"],
    "restrictions": ["vegetarian"],
    "ingredients": [
      {
        "name": "Овсяные хлопья",
        "quantity": "80",
        "unit": "г",
        "amount": "80 г",
        "category": "grains",
        "is_optional": false,
        "notes": "долгой варки"
      }
    ],
    "steps": [
      "Сварить овсяные хлопья на воде или молоке.",
      "Добавить яблоко и корицу."
    ]
  }
]
```

Допустимые значения ориентированы на текущие фильтры:

- `meal_type`: `breakfast`, `lunch`, `dinner`, `snack`, `dessert`, `drink`, `cocktail`, `smoothie`, `protein_shake`, `tea`, `coffee`.
- `category`: `soup`, `main`, `salad`, `dessert`, `quick`, `kids`, `drink`, `event`, `bbq`.
- `difficulty`: `easy`, `medium`, `hard`.

## Безопасность импорта v1

- Идемпотентность: скрипт нормализует `title` (`lower`, trim, collapse spaces) и пропускает рецепт, если такой title уже есть в базе.
- Один плохой рецепт не ломает весь импорт: каждый объект валидируется и коммитится отдельно; при ошибке текущий рецепт откатывается, следующие продолжают импортироваться.
- По умолчанию включен `--dry-run`: можно проверить файл без записи и без подключения к базе. Проверка дублей в базе выполняется только при `--commit`.
- Массового API нет: запуск только из backend CLI.
- UX не меняется.
- Существующие рецепты не перезаписываются без флага `--update`.

## Команды

Проверить sample без записи и без подключения к базе:

```bash
python backend/scripts/import_recipes.py --input sample_recipes.json --dry-run
```

Импортировать:

```bash
python backend/scripts/import_recipes.py --input sample_recipes.json --commit
```

Обновить существующие рецепты с тем же normalized title:

```bash
python backend/scripts/import_recipes.py --input sample_recipes.json --commit --update
```
