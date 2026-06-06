# PLANAM V1 Recipe Image Style System

**Дата:** 2026-06-03  
**Статус:** freeze для V1 pilot  
**Основа:** [PLANAM_V1_IMAGE_STRATEGY.md](./PLANAM_V1_IMAGE_STRATEGY.md), [PLANAM_RECIPE_MEDIA_ARCHITECTURE.md](./PLANAM_RECIPE_MEDIA_ARCHITECTURE.md)

---

## Главный принцип

```text
1 рецепт → 1 master image → автоматические версии (hero / card / thumb)
```

**Запрещено:** отдельно генерировать hero, card и thumbnail.  
**Разрешено:** один master + crop/resize в `process_recipe_images.py`.

---

## Визуальный мир PlanAm

Все изображения должны ощущаться как:

```text
реально приготовлено дома
на одной светлой современной кухне
в посуде из одного сервиза
```

### Стиль

| Да | Нет |
|----|-----|
| реалистичные, домашние | ресторанный глянец |
| аппетитные, тёплые | пластиковый stock |
| чистые, естественные | идеальная симметрия |
| немного «живые» | неестественные цвета |
| понятные семье | хаотичный фон, декор |

---

## Единый сервиз

| Параметр | Значение |
|----------|----------|
| Материал | светлая керамика |
| Тон | молочно-белый / тёплый белый / светло-бежевый |
| Форма | минималистичная современная |
| Узоры | **нет** |
| Случайные тарелки | **нет** |

Разные типы блюд — разные предметы **из одного набора**:

| Тип блюда | Посуда |
|-----------|--------|
| супы, каши, рагу | глубокая миска |
| вторые блюда | плоская тарелка |
| салаты | неглубокая миска / тарелка |
| завтраки | небольшая тарелка / миска |
| напитки | стакан / кружка той же семьи |

---

## Фон и свет

| Элемент | Правило |
|---------|---------|
| Фон | светлая домашняя кухня, столешница / светлое дерево / светлый камень |
| Clutter | минимум, без хаоса |
| Свет | мягкий дневной из окна |
| Тени | лёгкие, не студийные |
| Тон | свежий, тёплый, чистый |

---

## Block F — Vessel Mapping

| dish_type | meal_type | category | recommended_vessel | camera_angle |
|-----------|-----------|----------|-------------------|--------------|
| soup | lunch | soup | deep ceramic bowl | 3/4 angle |
| porridge | breakfast | breakfast | medium ceramic bowl | slight top angle (~25°) |
| pasta | dinner | main | flat dinner plate | 3/4 angle |
| chicken_with_side | dinner | main | flat dinner plate | 3/4 angle, protein + side |
| salad | lunch | salad | shallow bowl or flat plate | top / 3/4 angle |
| casserole | dinner | main | plate with portion from baking dish | 3/4 angle |
| breakfast | breakfast | quick | small plate / bowl | slight top angle |
| side | dinner | side | small side plate | 3/4 angle |
| default | dinner | main | flat dinner plate | 3/4 angle |

Реализация: `backend/scripts/recipe_image_utils.py` → `VESSEL_MAPPINGS`, `infer_dish_type()`.

---

## Block H — One Master Image Rule

### Генерация

На каждый рецепт — **одно** master image (рекомендуемый размер **1536×1024**, landscape 3:2).

### Производные

```text
master.webp
  ↓ process_recipe_images.py
hero.webp        1200×675 (16:9)
card_800.webp    800×800
thumb_400.webp   400×400
```

### Плохой crop

Если master **не кропается** в hero без потери блюда:

- **не** генерировать отдельное hero-фото автоматически;
- пометить рецепт `needs_manual_review` в pilot manifest.

---

## Image Storage Plan (Block K)

### CDN (целевая)

```text
https://cdn.planam.ru/recipes/{recipe_id}/master.webp
https://cdn.planam.ru/recipes/{recipe_id}/hero.webp
https://cdn.planam.ru/recipes/{recipe_id}/card_800.webp
https://cdn.planam.ru/recipes/{recipe_id}/thumb_400.webp
```

### Локально (до CDN)

```text
public/recipe-images/{recipe_id}/master.webp
public/recipe-images/{recipe_id}/hero.webp
public/recipe-images/{recipe_id}/card_800.webp
public/recipe-images/{recipe_id}/thumb_400.webp
```

### Поля в БД

| Поле | Версия |
|------|--------|
| `hero_image_url` | hero.webp |
| `image_url` | card_800.webp |
| `thumbnail_url` | thumb_400.webp |

Выбор в UI/API: `hero_image_url ?? image_url ?? thumbnail_url ?? fallback`

---

## Связанные скрипты

| Скрипт | Роль |
|--------|------|
| `build_recipe_image_prompts.py` | master prompt на рецепт |
| `process_recipe_images.py` | crop master → variants |
| `apply_recipe_images.py` | запись URL в БД |
