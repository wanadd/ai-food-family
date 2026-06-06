# PLANAM V1 Recipe Image AI Budget

**Дата:** 2026-06-03  
**Статус:** модель расчёта готова; **фактические цифры — после pilot**

---

## Режимы генерации

| Режим | Описание | Calls / рецепт |
|-------|----------|----------------|
| `draft_low` | быстрый черновик, проверка композиции | 1 |
| `final_medium` | финал для каталога V1 | 1 |
| `final_high` | финал для Hero Top 10 | 1 |

### Рекомендуемый V1

| Сегмент | Режим |
|---------|-------|
| Каталог (bulk) | 1× draft_low + 1× final_medium |
| Hero Top 10 | 1× draft_low + 1× final_high |

**Итого:** ~2 API calls на рецепт (pilot batch: `estimated_calls: 2`).

---

## Формула (после pilot)

```text
cost_per_recipe = total_pilot_cost / pilot_recipe_count

top_50_cost     = cost_per_recipe × 50
catalog_150_cost = cost_per_recipe × 150
catalog_1000_cost = cost_per_recipe × 1000
```

---

## Прогноз (placeholder — заполнить после pilot)

| Сценарий | Рецептов | cost_per_recipe | Итого |
|----------|----------|-----------------|-------|
| Pilot | 10 | _TBD_ | _TBD_ |
| Top 50 Hero | 50 | _TBD_ | _TBD_ |
| Full V1 catalog | 150 | _TBD_ | _TBD_ |
| Scale catalog | 1000 | _TBD_ | _TBD_ |

### Как заполнить

1. Запустить pilot 10 (draft + final).
2. Суммировать `actual_cost` из `planam_v1_image_pilot_batch.json`.
3. Подставить в формулу выше.

---

## Пример расчёта (иллюстрация, не факт)

_Удалить или заменить после реального pilot._

| Допущение | Значение |
|-----------|----------|
| Pilot total | $4.00 |
| Pilot count | 10 |
| cost_per_recipe | $0.40 |
| Top 50 | $20.00 |
| Catalog 150 | $60.00 |
| Catalog 1000 | $400.00 |

---

## Экономия за счёт one-master rule

| Подход | Генераций на рецепт |
|--------|---------------------|
| ❌ Отдельно hero + card + thumb | 3+ |
| ✅ Один master + crop | 1–2 (draft + final) |

Crop бесплатен (`process_recipe_images.py`, Pillow).

---

## Решение после pilot

| quality_score avg | Рекомендация |
|-------------------|--------------|
| ≥ 4.0 | Top 50 → затем 150 |
| 3.0–3.9 | доработать prompts, повторить pilot |
| < 3.0 | стоп массовой генерации, ревизия style system |
