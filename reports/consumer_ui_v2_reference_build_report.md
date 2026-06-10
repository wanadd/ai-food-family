# PLANAM — Consumer UI V2 по визуальному референсу: отчёт сборки

Дата: 2026-06-10
Ветка работы: `rebuild/consumer-ui-reference-v2`

## 1–2. База до работы

```text
git branch --show-current → feat/ui-reference-redesign-planam-2026
git rev-parse --short HEAD → b853c9e

git log --oneline -5:
b853c9e feat(ui): align planam 2026 screens with visual reference
17e833c fix(ui): canonicalize 2026 deep links and remove orphan components
60731d6 fix(ui): address visual qa home and leftovers routes fix issues
d5fc187 docs(ui): add full visual qa walkthrough audit
938cd4e docs(ui): add p0 home leftovers routes fix report
```

База — вершина цепочки работ (cleanup → reference redesign). Это последняя
рабочая ветка после предыдущих PR этой серии; явный задеплоенный tag в репо
не размечен, поэтому взята актуальная вершина серии (зафиксировано здесь).

## 3. Reference Breakdown (до кода)

| Экран | Элементы референса, которые переносим |
|---|---|
| Home | Greeting + дата, hero meal c фото и CTA «Готовить», 3 статус-карточки (Купить/Запасы/Меню %), один AI-совет |
| Menu | Заголовок «Меню», date chips недели, компактные meal rows (thumb, имя, мин·ккал) с «+» quick actions |
| Recipe | Hero фото, метрики, чистые ингредиенты, «Начать готовить», шаги нумерованными карточками |
| Shopping | Фильтры [Купить][Все][Куплено], категории по порядку, количество справа, full-row checkbox toggle |
| Pantry | «Запасы», поиск, filter chips, строки «название · срок/кол-во», CTA «Добавить продукт» |
| Wellness | Metrics-first progress bars, AI tip, «Рекомендации для вас», мягкий chat CTA внизу |
| AI Loading | Staged-процесс с этапами, прогресс-полосками и тарелкой-fallback |
| Profile/Subscription | Hub-список и soft paywall (уже близки после прошлого PR — точечно, без пересборки) |

## 4. Новый V2 consumer layer

```text
apps/web/components/planam-v2/
  ui/V2Primitives.tsx        V2Card, V2Button, V2SectionHeader, V2PageHeader,
                             V2ProgressBar, V2Chip, V2ListRow, V2EmptyState,
                             V2AiTip, V2BottomSheet (поверх DS 2026)
  ai/AiProcessLoadingV2.tsx  staged AI loading, variants: menu|shopping|pantry|wellness
  home/HomeV2.tsx            Home «что сделать сейчас»
  menu/MenuTodayV2.tsx       экран «Меню» + quick-actions bottom sheet
  menu/GenerateMenuV2.tsx    «Соберём меню»: дни/цель/запасы/семья → AI loading → «Меню готово»
  shopping/ShoppingV2.tsx    чеклист покупок с taxonomy guard
  home-domain/PantryV2.tsx   «Запасы»: поиск, фильтры, sheet действий
  home-domain/LeftoversV2.tsx «Из того, что есть дома» + «После готовки»
  wellness/WellnessV2.tsx    metrics-first дашборд здоровья
```

Плюс P0-слой: `apps/web/lib/planam/productTaxonomy.ts` + тесты
(см. `reports/product_taxonomy_ui_guard_report.md`).

## 5. Canonical routes → V2

| Route | Было | Стало |
|---|---|---|
| `/` | Home2026 | **HomeV2** |
| `/plan/today` | PlanToday2026 | **MenuTodayV2** |
| `/plan/generate` | PlanGenerate2026 | **GenerateMenuV2** |
| `/shopping` | Shopping2026 | **ShoppingV2** |
| `/home/pantry` | Pantry2026 | **PantryV2** |
| `/home/leftovers` | Leftovers2026 | **LeftoversV2** |
| `/shopping/leftovers` (legacy alias) | Leftovers2026 | **LeftoversV2** |
| `/wellness` | WellnessHome2026 | **WellnessV2** |

Старые компоненты физически не удалены — лежат на месте, просто больше
не подключены к canonical routes.

## 6. Home

- Greeting + дата → Hero (P0–P4 priority logic, существующий `resolvePlanAmHeroState`) → 3 статус-карточки grid (Купить / Запасы / Меню %) → один AI tip (`nutritionist_advice`, fallback «Соберите меню…», клик → /wellness).
- Нет TodayDishRail, нет дублей quick actions, нет большой AI chat card. 4 блока, не простыня.

## 7. Menu (`/plan/today`)

- Заголовок «Меню» + сабтайтл, date chips всегда видимы при multi-day плане (зелёный активный).
- Компактные meal rows: thumb 56px, тип приёма, имя, «мин · ккал», статус.
- Клик по карточке: рецепт при `recipe_id`, иначе meal outcome sheet (без падения).
- Кнопка «+» открывает bottom sheet: Открыть рецепт / Заменить блюдо / Добавить в покупки / Удалить из меню (только доступные действия).
- Loading — staged `AiProcessLoadingV2` («PLANAM загружает меню»), не spinner.
- Empty: «Меню пока не собрано» → CTA «Собрать меню».
- «Свой вариант» в sheet не добавлен: у `POST /menus/generate` нет поля свободного текста (см. Phase 2).

## 8. Shopping

- Header «Список покупок · N товаров к покупке», прогресс-бар.
- Фильтры **[Купить] [Все] [Куплено]** + chip «Из меню» (sync).
- Категории нормализованы (canonical V1 + `detectProductCategory`), порядок фикс, неизвестное → «Прочее/Другое».
- Item row: checkbox-кружок, имя (normalize + зачёркивание при checked), количество справа через guarded `formatProductQuantity`. Вся строка кликабельна.
- Manual add: bottom sheet (название/количество/единица/категория) через существующий `POST /shopping-lists/items`; категория автоподбирается по имени.
- Nested scroll отсутствует — один page scroll.

## 9. Pantry / Leftovers

Pantry:
- «Запасы · N продуктов дома», поиск, фильтры [Все] [Скоро заканчивается] [Много] [Просрочено].
- Строки «название · срок/количество» (taxonomy guard), клик → bottom sheet: Количество/Срок/Категория + «Найти рецепт», «Удалить». Edit-формы нет в sheet (есть add API; полноценный edit — Phase 2).
- CTA «Добавить продукт» (bottom sheet, `POST /pantry/items`) и «Из того, что есть дома».

Leftovers:
- «Из того, что есть дома · Подберём блюда из ваших запасов», chip-сводка по запасам.
- «PLANAM может приготовить» — карточки рецептов из pantry (have/total ингредиентов).
- Ниже отдельная секция «После готовки» (Скоро испортится / Что осталось) — не смешана с подбором.
- Loading — `AiProcessLoadingV2` variant `pantry`; empty — «Пока не из чего подбирать» → CTA «Открыть запасы».

## 10. Wellness

Реально перестроен порядок: Header («Здоровье · Ваш баланс на сегодня») →
карточка метрик с progress bars (Калории, Белки, Жиры, Углеводы, Вода — из
`ProgressOverview.targets/daily_actual` и `WaterToday`; Активность строкой) →
быстрый трекер воды → AI tip → «Рекомендации для вас» (горизонтальные карточки
блюд из меню на сегодня с переходом в рецепт) → CTA «Спросить AI-нутрициолога»
(в самом низу, чат не первый блок). Empty: «Заполните питание» → профиль.

## 11. Product taxonomy / categories

См. `reports/product_taxonomy_ui_guard_report.md`. Кратко:
`normalizeProductName` / `detectProductCategory` / `formatProductQuantity` /
`isSuspiciousUnit`; «капуста 1 л» → «капуста», «1 л л» → «1 л»,
`undefined г` → пусто; применено в Shopping/Pantry/Recipe ingredients/Leftovers;
21 unit-тест.

## 12. AI loading states

`AiProcessLoadingV2` (props: active, variant, title, subtitle, steps) с
вариантами **menu / shopping / pantry / wellness**, прогресс-полосы по этапам и
тарелка-fallback. Используется: `/plan/generate` (генерация), `/plan/today`
(загрузка меню), `/home/leftovers` (подбор из запасов), `/shopping` (первая
загрузка). Генерация не выглядит зависшей: 4 этапа с подписями.

## 13. Что осталось legacy

- `/plan` (PlanWeek2026), `/plan/recipes` (RecipeCatalog2026), `/plan/recipes/[id]` (RecipeDetail2026) — уже приведены к референсу прошлым PR, в V2-слой не переносились.
- `/account`, `/account/subscription` — AccountHub2026/SubscriptionHub2026 (близки к референсу, не переносились).
- `/account/nutrition` (NutritionProfileForm), `/account/notifications` (NotificationsView/CareSettingsPanel), `/account/family`, `/account/settings` — **legacy, требуют V2 migration (Phase 2), не выдаются за готовое**.
- `/wellness/chat` — текущий WellnessChat2026.
- Старые компоненты (Home2026, PlanToday2026, Shopping2026, Pantry2026, Leftovers2026, WellnessHome2026, PlanGenerate2026) — на месте, отключены от canonical routes, физически не удалены.

## 14. Что не трогали

Backend, API, БД, Telegram auth, admin, Docker/Nginx, payment stub,
Telegram bot, care.py, notification_scheduler.py, recipe import pipeline,
legacy redirects, legacy pages, нижний bar (5 вкладок, тот же порядок;
«Сегодня» → «Меню» выполнено в предыдущем PR этой серии и сохранено),
рецепты не удалялись, DB reset не выполнялся, CDN/image pipeline не добавлялся,
новый `/menu` route не создавался.

## 15. Build / тесты

```text
apps/web: npm run build → ✓ Compiled successfully (все routes собраны)
npx vitest run → 4 files, 37 tests passed
```

Попутно починены 2 теста, которые не могли запускаться из-за отсутствия
alias-конфига vitest: добавлен `apps/web/vitest.config.ts`; обновлено
ожидание hero CTA («Готовить»); исправлен приоритет правила категорий
(«Бульон куриный» → бакалея).

## 16. Screenshots

**Скриншоты не сделаны, визуальная проверка не подтверждена.**
Среда сборки без Telegram WebView/браузера с initData; экраны зависят от
авторизации Mini App. Папка `reports/screenshots/consumer_v2_reference/`
не наполнена. Требуется ручная проверка на viewport 390×844 (light/dark).

## 17. Phase 2

- V2 migration: `/account/nutrition`, `/account/notifications`, `/account/family`, `/account/settings`.
- «Свой вариант» (свободный текст) в генерации меню — требует поля в API `POST /menus/generate`.
- Edit-форма продукта в Pantry sheet (PATCH `/pantry/items/{id}` уже есть — нужен UI).
- Перенос `/plan`, `/plan/recipes`, recipe detail в planam-v2 слой.
- Серверная чистка единиц/категорий (upstream данных), логирование suspicious units.
- Скриншоты и визуальный QA-прогон light/dark.

## Reference Compliance

| Screen | Reference target | PLANAM result | Still missing |
|---|---|---|---|
| Home | greeting, hero meal, 3 статуса, AI tip | HomeV2: те же 4 блока, hero P0–P4 | фото hero зависит от данных рецепта |
| Menu | «Меню», date chips, meal rows + «+» | MenuTodayV2: chips, rows, quick-actions sheet | «Свой вариант» (нет API) |
| Recipe | hero, метрики, ингредиенты, «Начать готовить», шаги | RecipeDetail2026 (прошлый PR) + guarded ingredients | перенос в V2-слой |
| Shopping | фильтры, категории, checklist | ShoppingV2: [Купить][Все][Куплено], guard, manual add | свайпы/undo |
| Pantry | поиск, фильтры, сроки, CTA | PantryV2: всё перечисленное + sheet | edit-форма в sheet |
| Leftovers | подбор из запасов | LeftoversV2 + секция «После готовки» | фото в карточках подбора |
| Wellness | metrics-first, bars, tip, рекомендации | WellnessV2: точный reference-порядок | шаги/активность как метрика-бар (нет источника шагов) |
| AI Loading | этапы, не «зависло» | AiProcessLoadingV2, 4 варианта | прогресс, привязанный к реальным фазам backend |
| Profile | hub-список | AccountHub2026 (как было) | V2-перенос, sub-экраны legacy |
| Subscription | soft paywall | SubscriptionHub2026 (как было) | V2-перенос |

## Scope confirmation

**Backend/API/БД/auth/admin/payment/Docker/Telegram bot/recipe DB reset не менялись.**
Рецепты не удалялись. Legacy redirects и legacy pages не снимались.
Старые компоненты физически не удалены. Bottom nav: 5 вкладок, порядок прежний,
«Сегодня» → «Меню» (сделано ранее в этой серии и сохранено).
