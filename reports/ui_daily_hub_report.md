# PLANAM UI Daily Hub Report

## 1. Цель
Привести главный экран (`/`, компонент `Home2026`) к утверждённой daily-hub
логике с реальными данными и честными fallback-состояниями: приветствие →
карточка блюда дня → блоки Купить / Остатки / Здоровье → кнопки Открыть меню /
Список покупок → вторичный вход в AI-помощник. Без фейковых цифр и mock-данных.

## 2. Что было не так
Базовая структура daily hub уже существовала, но было два расхождения со
спецификацией и одна заглушка:

1. **AI-помощник был фейковой заглушкой.** Кнопка «Спросить PlanAm» открывала
   bottom-sheet с текстом «Скоро здесь появится помощник PlanAm» — не вела в
   реальный AI/нутрициолог (нарушение §7.8 и запрета на «вид, что данные есть»).
2. **Блок «Остатки» показывал не то.** Он брал `meal_leftovers_count` и вёл на
   `/shopping/leftovers` (остатки приготовленных блюд), тогда как спец §7.4/§10
   требует pantry (`family_pantry_items`, «47 продуктов») с переходом на экран
   запасов.
3. **Fallback приветствия без имени** возвращал «Добро пожаловать 👋» вместо
   приветствия по времени суток + 👋 (спец §7.1/§11).

## 3. Изменённые файлы
Backend (аддитивно, без новых таблиц/эндпоинтов):
- `apps/api/app/schemas/menu_overview.py` — новое поле `pantry_items_count: int = 0`.
- `apps/api/app/services/menu_overview.py` — заполнение `pantry_items_count=len(pantry_items)` (список уже загружался для why-reasons/оценки, новых запросов нет).

Frontend:
- `apps/web/lib/menu/overview-types.ts` — тип `pantry_items_count?: number`.
- `apps/web/lib/home/planam-hero-2026.ts` — новый `pantryStatusLabel(overview)`; fallback приветствия без имени → приветствие по времени + 👋.
- `apps/web/components/home-2026/PlanAmStatusRows2026.tsx` — «Остатки» → `pantryStatusLabel` + переход на `/home/pantry`.
- `apps/web/components/home-2026/Home2026.tsx` — AI-помощник теперь ведёт в реальный `/wellness/chat` с честным описанием; удалена заглушка bottom-sheet и неиспользуемое состояние/импорт.

## 4. Новая структура главной
- **Приветствие** — `Доброе утро/день/вечер[, Имя] 👋`.
- **Главная карточка блюда** — `PlanAmHero2026` (фото или placeholder, название, время/ккал если есть, CTA «Приготовить»); empty state «Составим меню?» → «Создать меню».
- **Купить** — реальное число некупленных товаров → `/shopping`.
- **Остатки** — реальное число продуктов в запасах → `/home/pantry`.
- **Здоровье** — статус нутрициолога → `/wellness`.
- **Открыть меню** — `/plan/today`.
- **Список покупок** — `/shopping`.
- **AI-помощник** — вторичный вход → `/wellness/chat`.

## 5. Карта данных

| Блок | Что показывает | Источник данных | Hook/API/Route | Fallback |
|---|---|---|---|---|
| Приветствие | имя пользователя по времени суток | Telegram user context (`user.first_name`) | `useTelegram()` → `formatPlanAmGreeting` | «Доброе утро/день/вечер 👋» без имени |
| Главное блюдо | актуальный приём пищи (по времени, dinner→lunch→breakfast→snack), название, фото, время, ккал | `family_menu_selections.menu_data` → `today_meals` + `selected_menu.meals` | `GET /menus/overview` → `fetchMenuOverview` → `resolvePlanAmHeroState`/`pickNextMealByTime` | нет меню → «Составим меню?» / «Создать меню»; нет фото → `MealFallbackPlate2026`; нет времени/ккал → скрыто |
| Купить | число некупленных товаров | `family_shopping_lists.items` (unchecked) | `GET /menus/overview` → `shopping_unchecked_count` → `shoppingStatusLabel` | 0 → «Всё куплено» |
| Остатки | число продуктов в запасах | `family_pantry_items` (active by scope) | `GET /menus/overview` → `pantry_items_count` → `pantryStatusLabel`; route `/home/pantry` | 0/нет → «Пока пусто» |
| Здоровье | статус рекомендаций нутрициолога | nutritionist advice (на основе профиля/меню) | `GET /menus/overview` → `nutritionist_advice` → `wellnessStatusLabel`; route `/wellness` | нет данных → «—» / «В норме» |
| AI-помощник | вход в существующий AI-чат | существующий route | `/wellness/chat` (`WellnessChat2026`) | — (entry point, данные не нужны) |

## 6. Что подключено к реальным данным
- Приветствие — `user.first_name` из Telegram-контекста.
- Главное блюдо, Купить, Остатки, Здоровье — все из `GET /menus/overview`
  (scope-aware: `mode` передаётся через `X-App-Mode`, см. `apiGet`).
- AI-помощник ведёт в реальный существующий `/wellness/chat`.

## 7. Где используется fallback
- Главное блюдо: при отсутствии меню — empty state «Составим меню?»; при
  отсутствии фото — `MealFallbackPlate2026`; время/ккал скрываются, если поля пусты.
- Купить/Остатки: при 0 — «Всё куплено» / «Пока пусто».
- Здоровье: при отсутствии данных — нейтральное «В норме»/«—».
- Здоровье-блок пока показывает текстовый статус нутрициолога, а не числовой
  прогресс «X / Y ккал». Числовой дневной прогресс калорий доступен через
  отдельный агрегатор (`/menus/today/nutrition`), но не входит в `/menus/overview`.
  Подтягивание его на главную — отдельная задача (см. §10 ниже).

## 8. Навигация
Нижняя навигация (`BottomNavigation2026`) не менялась — она уже thumb-friendly и
ведёт только на активные 2026-маршруты (Сегодня · Покупки · ПланАм · Здоровье ·
Профиль). Изменён только переход блока «Остатки» на главной: с
`/shopping/leftovers` на `/home/pantry` (запасы), что соответствует §7.4/§10.
Экран остатков блюд (`/shopping/leftovers`) по-прежнему доступен из раздела
покупок — рабочая функция не удалена.

## 9. Проверки
- `npm run build`: **успешно** (все маршруты скомпилированы, включая `/`, `/home/pantry`, `/wellness/chat`).
- `npm run lint`: **успешно** (только pre-existing warnings про `<img>` в `AccountHub2026`/`ProfileDashboard`, не связаны с правками).
- backend `py_compile` + `pytest -k "overview or menu"`: **42 passed**.
- ручная проверка переходов: выполнять в dev UI (Telegram Mini App) —
  Открыть меню → `/plan/today`; Список покупок → `/shopping`; Остатки →
  `/home/pantry`; Здоровье → `/wellness`; AI-помощник → `/wellness/chat`.

## 10. Что осталось
- Блок «Здоровье» на главной показывает текстовый статус, а не «X / Y ккал».
  Для числового дневного прогресса нужен отдельный fetch
  `GET /menus/today/nutrition` (уже существует) или добавление сводки в
  `/menus/overview`. Сейчас используется честный текстовый статус нутрициолога —
  фейковых цифр нет. Требуется отдельная frontend-задача, если нужен числовой
  прогресс на главной.
- Функция `leftoversStatusLabel` оставлена в `planam-hero-2026.ts` (не удалена,
  может пригодиться для UI остатков блюд), сейчас на главной не используется.
