# PLANAM Recipe Image Master Prompt (Gold V3 / Stage IMG)

**Status:** active for Gold V3 batch 256–265  
**Style version:** `planam_gold_v3_master`  
**Pipeline:** 1 master image → `hero.webp` / `card_800.webp` / `thumb_400.webp`

---

## Master style (all recipes)

Every PlanAm recipe photo must share one visual language:

| Rule | Detail |
|------|--------|
| Tableware | One consistent modern home ceramic set — warm white / milk white / light beige |
| Background | Bright home kitchen — light countertop, light wood, or light stone |
| Lighting | Soft natural daylight from a window; gentle shadows; warm clean tone |
| Composition | Dish is the clear subject; appetizing home presentation; clean layout |
| Mood | Modern homemade food — real, warm, believable, not restaurant gloss |
| Angles | 3/4 or slight top angle per dish type (see vessel mapping) |

### Must NOT appear

- text, watermark, logo
- packaging, branded boxes
- people, hands
- messy clutter, random objects
- plastic stock-photo look
- fine-dining theatrical plating
- excessive garnish or chaos

---

## Master prompt template

Code constant: `MASTER_PHOTO_PROMPT` in `apps/api/app/recipes/recipe_gold_v3_image_pipeline.py`.

```text
Create one photorealistic master food image for the PlanAm family meal-planning app.

Dish: {title}
Meal type: {meal_type}
Main ingredients: {ingredients}
Visual description: {short_visual_description}

PlanAm visual system (Gold V3):
- Modern homemade food on one consistent light ceramic dinnerware set.
- Beautiful bright home kitchen background with minimal clutter.
- Appetizing presentation with clean composition and good camera angle.
- Warm, fresh, natural daylight — not studio drama.
- Same visual language across all PlanAm recipe images.

Tableware:
- Light neutral ceramic from one modern home set (warm white / milk white / light beige).
- No patterns, no random different plates.
- Use: {recommended_vessel}

Background:
- Consistent bright home kitchen countertop or light wood/stone surface.
- Minimal, uncluttered, family-home feeling.

Composition:
- {camera_angle}
- The dish is the clear main subject; textures and ingredients visible.
- Slight natural imperfection is welcome.

Restrictions:
- no text, watermark, logo, collage
- no packaging
- no people, no hands
- no excessive garnish or random objects
- no fine-dining restaurant look
- no plastic stock-photo look
```

---

## Negative prompt (reference for QA)

```text
text, watermark, logo, packaging, hands, people, clutter, messy table,
plastic look, stock photo, restaurant fine dining, dramatic studio lighting,
random plates, bright patterns, branded items, collage
```

---

## Dish-specific additions (examples)

| Dish | Vessel | Angle | Visual note |
|------|--------|-------|-------------|
| Котлеты с овощами | flat dinner plate | 3/4 | golden patties with visible vegetable side |
| Крупа с овощами | medium bowl | slight top (~25°) | creamy grain texture with colorful vegetables |
| Куриный суп с овощами | deep bowl | 3/4 | clear broth, steam, rustic family portion |
| Куриные грудки с фруктами и овощами | flat plate | 3/4 | protein + fruit/veg colors on one plate |
| Запеканка с курицей и овощами | flat plate | 3/4 | baked portion, golden top |
| Суп с фаршированной свининой | deep bowl | 3/4 | hearty soup, visible meat/veg |
| Овощной суп-пюре | deep bowl | 3/4 | smooth puree, vibrant vegetable color |
| Салат с морепродуктами | shallow bowl | top / 3/4 | fresh seafood salad, clean colors |
| Салат с курицей и фруктами | shallow bowl | top / 3/4 | bright salad, chicken and fruit visible |
| Овощной суп с бобовыми | deep bowl | 3/4 | legume vegetable soup, homestyle |

Implementation: `infer_dish_type()` + `VESSEL_MAPPINGS` in `recipe_gold_v3_image_pipeline.py`.

---

## File layout (production)

```text
public/recipe-images/{recipe_id}/master.png
public/recipe-images/{recipe_id}/master.webp
public/recipe-images/{recipe_id}/hero.webp      → hero_image_url
public/recipe-images/{recipe_id}/card_800.webp  → image_url
public/recipe-images/{recipe_id}/thumb_400.webp → thumbnail_url
```

Public URL: `https://planam.ru/recipe-images/{id}/hero.webp`

---

## Cost reference

| Model | Size | Quality | Est. USD / image |
|-------|------|---------|------------------|
| gpt-image-1 | 1536×1024 | medium | ~$0.063 |

10 images ≈ **$0.63** (estimate before apply; refine from actual usage report).
