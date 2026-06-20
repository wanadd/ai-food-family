# AI Usage vs AM Usage — Read-Only Audit

**Дата:** 2026-06-10

---

## Две экономики

| Сущность | Модель сейчас | Спецификация V4 |
|----------|---------------|-----------------|
| OpenAI cost | `AiUsageLog` | `ai_usage_events` |
| PLANAM AM | `AmaTransaction` + wallet | `am_usage_events` |

Сейчас **смешано**: `AiUsageLog.ams_spent` дублирует продуктовую метрику.

---

## Где списывается AM

| Операция | Функция | Сумма |
|----------|---------|-------|
| Генерация меню | `commit_menu_generation` | 5 AMS или квота |
| Замена блюда (catalog) | wallet debit | 3 AMS |
| AI chat / nutrition | различные | по тарифу |

Логирование: `AmaTransaction` с `reason` / `metadata_json`.

---

## Где логируется AI

| Операция | `log_ai_usage` | Токены | Cost |
|----------|----------------|--------|------|
| `menu.py` generate | ✓ | ✗ | ✗ |
| `menu.py` replace | ✓ (`ams_spent=0`) | ✗ | ✗ |
| `ai_client.chat_*` | — | не возвращает | — |

**Вывод:** админка показывает $0, потому что `estimated_cost` и токены **не заполняются**, даже когда OpenAI вызывается.

---

## Админка

- `routers/admin.py` — агрегаты по `AiUsageLog`
- Нет UI блока «AM-операции» отдельно от AI
- Нет сообщения «AI-вызовов за период нет» при ненулевом AM

---

## Feature flags (целевые)

```env
AI_MENU_PLANNER_ENABLED=false
AI_MENU_REVIEW_ENABLED=false
AI_NUTRITIONIST_MENU_ENABLED=false
AI_RECIPE_ASSISTANT_ENABLED=false
AI_IMAGE_GENERATION_ENABLED=false
```

**Сейчас:** gate только через `OPENAI_API_KEY` и runtime fallback.

---

## План исправления (Фаза 2)

1. `ai_client` возвращает `{text, usage}` с tokens
2. `log_ai_usage` всегда с tokens + `estimated_cost_usd`
3. `log_am_usage` отдельно от AI (новая таблица или чистое использование `AmaTransaction`)
4. Админка: две вкладки «Расходы AI» / «AM-операции»
5. QUICK_ALGORITHM: AM event, AI cost = 0 (честно)

---

## Acceptance после Фазы 2

- Быстрое меню → `am_usage_event`, AI cost = 0
- AI-меню → оба события
- Failed AI → refund или status `failed`
