# PLANAM V1 — Recipe Image Pilot Budget Report

**Дата:** 2026-06-06  
**Модель:** `gpt-image-1`  
**Размер master:** `1536x1024`  
**Статус стоимости:** оценочная (по таблице gpt-image-1); уточнить по `usage` после реального pilot.

---

## Стоимость за 1 изображение (1536×1024)

| Quality | USD / image |
|---------|-------------|
| low | $0.016 |
| **medium (V1 default)** | **$0.063** |
| high | $0.25 |

Одно master image на рецепт. Crop в hero/card/thumb — **бесплатно** (Pillow, локально).

---

## Прогноз стоимости

| Объём | low | medium | high |
|-------|-----|--------|------|
| **Pilot (10)** | $0.16 | **$0.63** | $2.50 |
| Top 50 | $0.80 | **$3.15** | $12.50 |
| Каталог 150 | $2.40 | **$9.45** | $37.50 |
| Масштаб 1000 | $16.00 | $63.00 | $250.00 |

### Рекомендация V1

| Сегмент | Режим | Стоимость |
|---------|-------|-----------|
| Pilot 10 | medium | $0.63 |
| Hero Top 10 | high | $2.50 |
| Каталог 150 | medium | $9.45 |

---

## Формула (уточнить после pilot)

```text
cost_per_recipe = total_pilot_cost / pilot_recipe_count
top_50_cost      = cost_per_recipe × 50
catalog_150_cost = cost_per_recipe × 150
catalog_1000_cost = cost_per_recipe × 1000
```

При наличии `usage` (input/output tokens) стоимость считается точно:

```text
cost = input_tokens × $5/1M + image_output_tokens × $40/1M
```

(см. `estimate_cost` в `openai_recipe_image_client.py`)

---

## Как получить фактические цифры

1. Запустить pilot 10 (`--commit`).
2. Открыть `reports/planam_v1_recipe_image_pilot_results.json` → `total_cost_usd`.
3. `cost_per_recipe = total_cost_usd / generated`.
4. Подставить в формулу выше и обновить этот отчёт.

---

## Решение после pilot

| avg quality_score | Рекомендация |
|-------------------|--------------|
| ≥ 4.0 | Top 50 → затем 150 (medium) |
| 3.0–3.9 | доработать prompts, повторить pilot |
| < 3.0 | стоп, ревизия style system |
