# PLANAM Recipe Gold V3 — Generation Contract

**Status:** Stage E foundation (schema + validator only)  
**Schema version:** `recipe_gold_v3`  
**No recipe generation on Stage E**

---

## 1. What is a Gold V3 recipe?

Gold V3 — оригинальный production-ready рецепт PLANAM:

- русское пользовательское название и описание;
- структурированные ингредиенты и шаги;
- `nutrition_per_serving` как единственный nutrition contract;
- restriction/allergen/diet metadata;
- shopping-safe ingredient rows;
- image prompt metadata без генерации фото на Stage E.

Теги библиотеки (будущий импорт Stage R): `recipe_gold_v3`, `status:gold`.

---

## 2. Povarenok signals ≠ recipes

`exports/povarenok_culinary_signals_v3_100.jsonl` содержит **сигналы**, не рецепты.

Generator Stage F может использовать только:

- `dish_family`, `meal_type_hints`, `category_hints`;
- `main_product_groups`, `cooking_methods`, `equipment_hints`;
- `restriction_hints`, `allergen_hints`, `nutrition_style_hints`;
- `generation_prompt_hints`;
- `source_signal_ids` (trace only).

---

## 3. Запрещено

| Запрет | Причина |
|--------|---------|
| original Povarenok title | originality / legal |
| original steps / description | direct copy risk |
| `source_url` в user-facing output | source leakage |
| узнаваемая структура блюда 1:1 | similarity risk |
| английские префиксы `High protein:` и т.п. | UX quality |
| technical categories `eggs`, `casserole`, `sport` | user-facing quality |
| `bowl` в русском title без исключения | V2 regression |

---

## 4. Stage F generator flow

1. Выбрать signal с `avoid_for_planam=false` и `family_fit=high|medium`.
2. Создать **новый** title, description, steps, proportions.
3. Заполнить `source_signal_ids`.
4. Установить `originality.* = true`, `source_similarity_risk=low|medium`.
5. Прогнать `validate_recipe_gold_v3`.
6. Только при `ok=true` и `score>=85` — кандидат в import dry-run (Stage R).

---

## 5. JSON schema (summary)

См. `apps/api/app/recipes/recipe_gold_v3_schema.py` и пример в `exports/recipe_gold_v3_validation_samples.jsonl`.

Ключевые поля:

- `schema_version`: `recipe_gold_v3`
- `status`: `gold`
- `source_type`: `generated_original` | `manual_original`
- `nutrition_per_serving`: `{kcal, protein_g, fat_g, carbs_g, ...}`
- `restriction_keys`: canonical keys из Stage B catalog
- `ingredients[]`: `{name, amount, unit, display_amount, category, shopping_name}`
- `steps[]`: `{step_number, text}` (min 4 steps, min 25 chars each)

---

## 6. Required fields

`schema_version`, `status`, `source_type`, `originality`, `title`, `description`, `meal_type`, `category`, `servings`, `prep_time_min`, `cook_time_min`, `total_time_min`, `difficulty`, `ingredients`, `steps`, `nutrition_per_serving`, `restriction_keys`, `allergen_keys`, `diet_tags`, `image_prompt_data`.

---

## 7. Nutrition contract

**V3 writes/reads:** `nutrition_per_serving.kcal|protein_g|fat_g|carbs_g` (+ optional fiber/salt/sugar).

**Legacy DB fields** (`calories_per_serving`, `nutrition_kcal_per_serving`, …) — mapper concern **Stage N**, не Stage E.

Validator checks:

- `kcal > 0`;
- macros non-negative;
- kcal vs macros within ~35%;
- servings 1–8.

---

## 8. Restriction contract

- `restriction_keys` must exist in `restrictions_catalog`.
- No contradictions: `no_pork` + pork ingredient, `vegetarian` + meat, etc.
- Stage B `restriction_safety` used as additional gate.

---

## 9. Shopping contract

Each ingredient requires:

- `display_amount` (user-friendly);
- `shopping_name`;
- `category` (Russian canonical groups);
- `amount` + `unit` usable for aggregation.

`shopping.aggregation_safe=true` recommended.

---

## 10. Image prompt data contract

```json
{
  "dish_visual_summary": "краткое описание внешнего вида",
  "serving_style": "единый сервиз PLANAM",
  "avoid_visuals": ["текст", "логотипы", "руки", "грязный фон"]
}
```

No photo generation on Stage E/F dry-run without explicit approval.

---

## 11. Validation gates

| Gate | Module |
|------|--------|
| Schema values | `recipe_gold_v3_validation.py` |
| Originality | same + blocked titles/fragments |
| Nutrition | same |
| Restrictions | same + `restriction_safety` |
| Shopping | same |
| Quality score | 0–100, warnings subtract |

CLI: `backend/scripts/validate_recipe_gold_v3.py`

---

## 12. Production-ready definition

A recipe is production-ready when:

- `validate_recipe_gold_v3().ok == True`
- `score >= 85`
- no errors
- `originality.source_similarity_risk != high`
- `ingredients >= 4`, `steps >= 4`
- `nutrition_per_serving` complete

---

## 13. Stage mapping

| Stage | Responsibility |
|-------|----------------|
| E (this) | schema + validator + contract |
| F | generate 10 originals dry-run |
| R | import dry-run / apply |
| N | KBJU UI mapper fix |
