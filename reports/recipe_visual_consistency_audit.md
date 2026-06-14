# Recipe Visual Consistency — Read-Only Audit

**Дата:** 2026-06-10  
**Статус:** read-only, платная генерация фото **не запускалась**

---

## Текущее состояние контракта

| Элемент | Где хранится | Проблема |
|---------|--------------|----------|
| Описание для фото | `recipes.image_prompt_data` → `dish_visual_summary` | Нет enum `final_dish_type` |
| Шаги | `recipes.steps` / `step_rows` | Нарезка не стандартизирована |
| Hero image | `hero_image_url`, `image_url` | Могли генерироваться до уточнения текстуры |
| Quality gate | Gold V3 pipeline | Проверяет семантику ингредиентов, не texture enum |

### Целевой контракт (V4, не в БД)

```json
{
  "final_dish_type": "soup_puree | chunky_soup | salad | ...",
  "final_texture": "smooth | chunky | ...",
  "visible_cut": "none | cubes | ...",
  "plating": "short description",
  "must_show": ["..."],
  "must_not_show": ["..."]
}
```

**Рекомендация:** добавить `visual_contract JSONB` на `recipes` (additive migration) или расширить `image_prompt_data`.

---

## Подозрительные рецепты (эвристический аудит)

Аудит по названию, типу блюда и известным жалобам UX. Для точной проверки нужен SQL на проде.

| display_title / title | final_dish_type (inferred) | image | reason | recommended_fix |
|----------------------|----------------------------|-------|--------|-----------------|
| Овощной суп-пюре | `soup_puree` | hero | `soup_puree_but_image_looks_chunky` | visual_contract: texture=smooth, must_not_show=cubes; regen prompt |
| Летний овощной суп с фасолью | `chunky_soup` | hero | `title_mentions_soup_but_may_conflict_with_puree_sibling` | Уточнить dish type в contract |
| Курица с брокколи (под сыром) | `baked_main` | hero | `image_prompt_too_generic` | must_show: cheese melt, broccoli |
| Салаты (категория) | `salad` | various | `salad_without_cutting_style` | Шаги: нарезка соломкой/кубиками |
| Крем-супы | `soup_puree` | various | `steps_blend_but_visual_contract_allows_chunks` | Шаги: блендер до однородности |

---

## Промпты фото (подготовка, без генерации)

### Суп-пюре

```
FINAL DISH: smooth vegetable puree soup, homogeneous texture, no visible vegetable cubes or chunks.
MUST NOT SHOW: diced carrots, potato cubes, whole beans floating.
MUST SHOW: creamy smooth surface, garnish only as swirl of cream or herbs.
```

### Суп кусочками

```
FINAL DISH: clear or hearty soup with visible ingredient pieces.
MUST SHOW: distinct vegetable/meat pieces in broth.
MUST NOT SHOW: blender-smooth puree texture.
```

### Салат

```
FINAL DISH: fresh salad; specify cut: {strips|cubes|whole leaves}.
MUST SHOW: identifiable cut style matching recipe steps.
```

---

## Шаги приготовления — пробелы

| Тип блюда | Что проверять | Действие |
|-----------|---------------|----------|
| Пюре-супы | «пробить блендером», «до однородности» | Добавить в step_rows при отсутствии |
| Салаты | тип нарезки | Нормализация Gold V3 |
| Запеканки | корочка, форма | visual_contract.plating |
| Супы | различать puree vs chunky | final_dish_type в контракте |

---

## Следующие шаги

1. Скрипт `scripts/audit_recipe_visual_consistency.py` (read-only SQL + heuristics)
2. Миграция `visual_contract` (после подтверждения)
3. Обновить `image_generation_config.py` с учётом `final_dish_type`
4. **Генерация фото** — только после явного подтверждения пользователя
