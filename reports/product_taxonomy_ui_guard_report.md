# PLANAM — Product Taxonomy UI Guard (frontend-level)

Дата: 2026-06-10
Ветка: `rebuild/consumer-ui-reference-v2` (база: `feat/ui-reference-redesign-planam-2026`, `b853c9e`)

## Зачем

Продукты и категории могли отображаться вперемешку, а единицы — «дико»
(`капуста 1 л`, `1 л л`, `undefined г`). Это frontend-защитный слой:
данные на сервере не меняются, меняется только то, что видит пользователь.
Пересборка рецептурной базы — отдельная задача (вне этого PR).

## Что сделано

### Новый модуль `apps/web/lib/planam/productTaxonomy.ts`

| Функция | Что делает |
|---|---|
| `normalizeProductName(name)` | trim, схлопывание пробелов, первая буква заглавная |
| `detectProductCategory(name, currentCategory?)` | canonical slug категории: уважает каноничную backend-категорию, переопределяет legacy/`продукты`/мусорные слаги по имени продукта (через `normalizeCategorySlug` + `suggestCategorySlug`) |
| `isSuspiciousUnit(name, unit)` | true для «твёрдый продукт + л/мл» (капуста 1 л, курица 2 л, сыр 300 мл); жидкие продукты (молоко, сок, масло, бульон) — не флагуются |
| `formatProductQuantity(input)` | надстройка над базовым `formatProductQuantity`: invalid-токены (`null/undefined/NaN`) → пусто, дубли единиц (`1 л` + `л`) → `1 л`, подозрительные сочетания → пустая строка (показываем только название) |

Фейковых конверсий нет: если разумного количества нет — показываем продукт без количества
(«капуста» лучше, чем «капуста 1 л»).

### Категории

Используется существующий canonical-набор `SHOPPING_CATEGORIES_V1`
(овощи и зелень, фрукты и ягоды, мясо и птица, рыба и морепродукты, молочные,
яйца, хлеб и выпечка, крупы и макароны, бакалея, специи и соусы, напитки,
быт, детские, питомцы, другое). Неизвестная категория всегда → «Другое»,
запрещённый слаг «продукты» переопределяется по имени.

Исправлен приоритет правил в `category-suggest.ts`: «Бульон куриный» теперь
классифицируется как бакалея (раньше — мясо_птица, т.к. матчился /курин/).

## Где применён guard

| Поверхность | Файл | Что именно |
|---|---|---|
| Shopping | `components/planam-v2/shopping/ShoppingV2.tsx` | имя через `normalizeProductName`, количество через guarded `formatProductQuantity`, категория через `groupShoppingItems` → `normalizeCategorySlug`; manual add автоподбирает категорию по имени |
| Pantry | `components/planam-v2/home-domain/PantryV2.tsx` | то же + категория в bottom sheet через `detectProductCategory` |
| Recipe ingredients | `lib/recipes/ingredient-amount.ts` | fallback-количество идёт через guarded `formatProductQuantity` (amount от backend по-прежнему trusted) |
| Menu-generated shopping list | тот же ShoppingV2 (sync «Из меню» рендерится через guarded rows) |
| Leftovers recipes | `components/planam-v2/home-domain/LeftoversV2.tsx` (списки рецептов из pantry; количеств у них нет, имена безопасны) |

## Тесты

`apps/web/lib/planam/productTaxonomy.test.ts` — 21 кейс, все проходят:

```text
капуста 1 л   → ""        (только название)
курица 2 л    → ""
сыр + мл      → suspicious
молоко 1 л    → "1 л"
1 л + л       → "1 л"     (без дубля)
рис 500 г     → "500 г"
undefined г   → ""
null шт       → ""
капуста       → овощи_зелень
курица        → мясо_птица
молоко/творог → молочные
рис/киноа     → крупы_макароны
"продукты"    → переопределяется по имени
неизвестное   → другое
```

Для запуска тестов добавлен `apps/web/vitest.config.ts` (alias `@` → корень
приложения); до этого тесты с alias-импортами не могли резолвиться.

## Ограничения / Phase 2

- Guard работает на отображении; сами данные (упстрим) не чинились.
- Подозрительные сочетания не логируются на сервер — только скрываются в UI.
- Полная чистка рецептурной базы и единиц — отдельная backend-задача.
