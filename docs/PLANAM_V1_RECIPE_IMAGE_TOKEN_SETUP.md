# PLANAM V1 — Recipe Image OpenAI Token Setup

**Дата:** 2026-06-06  
**Назначение:** отдельный OpenAI API key для image pipeline (не основной ключ приложения).

---

## Зачем отдельный ключ

- Изоляция биллинга image-генерации от основного приложения.
- Возможность отдельных лимитов / отзыва ключа без влияния на API.
- Безопасность: основной ключ не используется для тяжёлых image-запросов.

---

## Переменные окружения

| Переменная | Роль | Приоритет |
|------------|------|-----------|
| `PLANAM_IMAGE_OPENAI_API_KEY` | Ключ image pipeline | **1 (основной)** |
| `OPENAI_API_KEY` | Ключ приложения | 2 (fallback, с предупреждением) |

Резолвер (`backend/scripts/openai_recipe_image_client.py` → `resolve_image_api_key`) берёт первый непустой по приоритету. При использовании fallback пишется warning в лог.

Также добавлено в `apps/api/app/config.py`:

```python
image_openai_api_key: str = Field(
    default="",
    validation_alias=AliasChoices(
        "PLANAM_IMAGE_OPENAI_API_KEY", "IMAGE_OPENAI_API_KEY"
    ),
)
# settings.effective_image_openai_api_key → image key, иначе app key
```

---

## Локальная настройка

`.env` в корне или `apps/api/.env` (НЕ коммитить):

```env
PLANAM_IMAGE_OPENAI_API_KEY=sk-...ваш-отдельный-ключ...
DATABASE_URL=postgresql://user:pass@localhost:5432/planam
```

Проверка резолвинга без вызова API:

```bash
python -c "import os; os.environ.setdefault('PLANAM_IMAGE_OPENAI_API_KEY','test'); \
import sys; sys.path.insert(0,'backend/scripts'); \
from openai_recipe_image_client import is_image_pipeline_configured; \
print('configured:', is_image_pipeline_configured())"
```

---

## Настройка на сервере

Добавить в `.env`, который читает `docker-compose.prod.yml` для сервиса `api`:

```env
PLANAM_IMAGE_OPENAI_API_KEY=sk-...
```

Пересборка:

```bash
docker compose -f docker-compose.prod.yml build --no-cache api
docker compose -f docker-compose.prod.yml up -d
```

Pilot-скрипт можно запускать внутри контейнера api (ключ и `DATABASE_URL` уже в окружении):

```bash
docker compose -f docker-compose.prod.yml exec api \
  python backend/scripts/run_recipe_image_pilot.py \
  --pilot-file data/planam_v1_image_pilot_batch.json --limit 10 --commit
```

---

## Безопасность

- Реальные ключи никогда не коммитятся (`.env` в `.gitignore`).
- Сгенерированные изображения не коммитятся (`apps/web/public/recipe-images/**` в `.gitignore`).
- Ключ не логируется — логируются только `recipe_id`, `title`, `duration`, `cost`, `usage`.
