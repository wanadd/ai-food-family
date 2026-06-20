# PLANAM V1 Recipe Image AI Pilot

**Дата:** 2026-06-03  
**Размер pilot:** 10 рецептов из Top 50 Hero  
**Данные:** `data/planam_v1_image_pilot_batch.json`  
**Статус:** `planned` — генерация **не запускалась** (по требованию V1)

---

## Цель pilot

Проверить до масштабирования:

- единый стиль PlanAm на реальных блюдах;
- качество master → crop pipeline;
- фактическую стоимость на рецепт;
- решение: Top 50 vs 150 vs отложить.

---

## Pilot batch (10)

| recipe_id | title | meal_type | category | status | estimated_calls |
|-----------|-------|-----------|----------|--------|-----------------|
| 1 | Куриные котлеты с картофельным пюре в духовке | dinner | main | planned | 2 |
| 2 | Мясные "розы", фаршированные гречневой крупой | breakfast | breakfast | planned | 2 |
| 3 | Рыба «Красное и белое» | dinner | main | planned | 2 |
| 4 | Куриный суп с домашней лапшой | lunch | soup | planned | 2 |
| 5 | Чисто английский завтрак из овсянки | breakfast | breakfast | planned | 2 |
| 6 | Мацовая запеканка с грибами | dinner | main | planned | 2 |
| 7 | Спагетти с курицей в сливочном соусе | dinner | main | planned | 2 |
| 8 | Салат "Баклажанчик" | dinner | salad | planned | 2 |
| 9 | Салат "Винегретная фантазия" | dinner | salad | planned | 2 |
| 10 | Гречка с грибами портабелла или шампиньонами | dinner | main | planned | 2 |

Полные поля (`master_prompt`, `recommended_vessel`, `camera_angle`, `ingredients`) — в JSON.

---

## Статусы pilot

| Статус | Значение |
|--------|----------|
| `planned` | prompt готов, генерация не начата |
| `generated_draft` | есть draft master |
| `approved` | качество принято |
| `rejected` | не подходит стилю |
| `needs_retry` | повтор с уточнением prompt |
| `final_ready` | master + crops + URL в БД |

---

## Рекомендуемый режим генерации (pilot)

| Рецепт | Режим |
|--------|-------|
| Hero Top 10 | 1× draft_low + 1× final_high |
| Остальной pilot | 1× draft_low + 1× final_medium |

`estimated_calls = 2` на рецепт в batch JSON.

---

## Workflow после генерации

```bash
# 1. Сохранить master локально
# 2. Crops
python backend/scripts/process_recipe_images.py --master path/to/master.png --recipe-id 1

# 3. URL в БД (после import рецептов)
python backend/scripts/apply_recipe_images.py --recipe-id 1 --base-url https://cdn.planam.ru/recipes/1 --dry-run
python backend/scripts/apply_recipe_images.py --recipe-id 1 --base-url https://cdn.planam.ru/recipes/1 --commit
```

---

## Поля для заполнения после pilot

| Поле | Когда |
|------|-------|
| `actual_cost` | после каждой генерации |
| `actual_tokens` | из API usage |
| `quality_score` | ручная оценка 1–5 |
| `decision` | approved / rejected / needs_retry |

---

## Что не делать

- Не генерировать 150 изображений до завершения pilot.
- Не коммитить тяжёлые `.webp` в git (`public/recipe-images/**` в `.gitignore`).
