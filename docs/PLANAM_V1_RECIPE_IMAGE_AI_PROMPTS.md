# PLANAM V1 Recipe Image AI Prompts

**Дата:** 2026-06-03  
**Style profile:** `planam_v1_home_kitchen`  
**Код:** `backend/scripts/recipe_image_utils.py`, `build_recipe_image_prompts.py`

---

## Prompt Builder Inputs

| Поле | Источник |
|------|----------|
| `title` | каталог / pilot batch |
| `meal_type` | enrichment |
| `category` | enrichment |
| `ingredients` | top 6–8 имён |
| `short_visual_description` | heuristic (`short_visual_description()`) |
| `recommended_vessel` | `VESSEL_MAPPINGS` |
| `camera_angle` | `VESSEL_MAPPINGS` |
| `style_profile` | `planam_v1_home_kitchen` |

---

## MASTER PROMPT TEMPLATE

```text
Create one photorealistic master food image for the PlanAm family meal-planning app.

Dish: {title}
Meal type: {meal_type}
Main ingredients: {ingredients}
Visual description: {short_visual_description}

PlanAm visual system:
- The dish should look like it was cooked at home in a real kitchen.
- The image must feel real, warm, appetizing, and believable.
- The food should not look overly perfect or artificial.
- It should be carefully and beautifully served, but still homemade.
- The dish must belong to the same visual world as other PlanAm recipe images.

Tableware:
- Use tableware from one consistent modern home ceramic dinnerware set.
- Light neutral ceramic: warm white, milk white, or very light beige.
- No bright patterns.
- No random different plates.
- Choose the appropriate item from the same set:
  {recommended_vessel}

Background:
- Consistent bright home kitchen background.
- Light kitchen countertop, light wood, or light stone surface.
- Minimal uncluttered background.
- Same family-home kitchen feeling across all recipe images.

Lighting:
- Soft natural daylight from a kitchen window.
- Gentle shadows.
- Fresh, clean, warm tone.
- Not dramatic studio lighting.

Composition:
- {camera_angle}
- The dish is the clear main subject.
- Ingredients and texture should be visible.
- Composition should be premium but real.
- Slight natural imperfection is welcome.
- The image should make the user want to cook this dish.

Restrictions:
- no text
- no watermark
- no logo
- no collage
- no packaging
- no people
- no hands
- no excessive garnish
- no fine-dining restaurant presentation
- no plastic stock-photo look
- no messy table
```

---

## Генерация prompts

```bash
# Pilot 10 из Top 50 Hero
python backend/scripts/build_recipe_image_prompts.py --pilot 10

# Кастомный вывод
python backend/scripts/build_recipe_image_prompts.py --pilot 10 --output data/planam_v1_image_pilot_batch.json
```

Выход: `data/planam_v1_image_pilot_batch.json` с полем `master_prompt` на каждый рецепт.

---

## Правило одного master

После AI-генерации:

1. Сохранить `master.png` / `master.webp`
2. Запустить `process_recipe_images.py` — **не** запрашивать отдельные hero/card/thumb у модели

---

## Python API

```python
from recipe_image_utils import build_master_prompt, build_pilot_row

prompt = build_master_prompt(recipe_dict)
row = build_pilot_row(recipe_dict, recipe_id=1)
```
