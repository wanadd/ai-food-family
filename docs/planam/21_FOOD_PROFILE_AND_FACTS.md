# Food Profile And Facts Contract

## Ownership

Core owns person identity. Food owns FoodProfile and food-domain facts. FoodProfile includes dietary policy, allergies, intolerances, celiac facts, pregnancy/process-state facts, PKU/phenylalanine facts, medical-food context where appropriate, nutrition target inputs/outputs, evidence references, and safety decisions.

FoodProfile is not CorePerson. CorePerson plus FoodProfile is the accepted model, not a giant global PersonProfile.

## Knowledge and safety semantics

Food facts are typed, person-scoped, provenance-bearing, and time-aware where applicable. `UNKNOWN`, `MISSING`, `NOT_PROVIDED`, `KNOWN_NONE`, `KNOWN_PRESENT`, `DECLINED`, and `NOT_APPLICABLE` are distinct where the domain needs that distinction. Missing nutrient is not zero. Missing allergen is not absence. `UNKNOWN` is not `SAFE`.

Safety evaluation happens per person before household aggregation. Hard safety is never averaged across household members. Free text alone must not drive deterministic medical BLOCK decisions. AI output cannot close an evidence gap.

## Target food ontology

The target food ontology separates generic food, packaged product, product instance, ingredient, recipe, recipe version, planned menu item, cooked event, consumed event, pantry item, shopping item, OCR-extracted receipt fact, and evidence source. Product facts, cooking facts, and consumption facts are not profile facts.

Pregnancy food safety depends on actual product/process/cooking state and temporal context. Celiac disease is not the same as gluten-free preference. Allergy is not intolerance.

## Evidence and nutrition

The Evidence Engine remains the deterministic food authority layer. Food identity, unit normalization, nutrient facts, allergen/celiac facts, pregnancy process-state, PKU/phenylalanine facts, source authority, and provenance remain additive contracts.

NutritionTarget is derived, versioned, and provenanced separately from user-entered goals. Recipe-derived nutrition retains source recipe, recipe version, process state, serving basis, and uncertainty.

## Recipe, planning, shopping, pantry, cooking, and consumption

The target recipe architecture uses Recipe and RecipeVersion. Gold V3 is the clean canonical recipe library target. The legacy 174 recipes are transition data, not the target canonical library, and deletion is not authorized by this checkpoint.

Planning/menu, shopping, pantry/product, receipt/OCR, cooking, and consumption are separate domain areas. Planned is not cooked. Cooked is not consumed. OCR output is evidence/proposal input until normalized, validated, and accepted by the owning domain.

The Gold V3 generator, validator, recipe generation contracts, image pipeline, `MASTER_STYLE`, prompts/contracts, and reusable valid infrastructure survive as accepted previous work.
