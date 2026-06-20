# PLANAM — Full Visual QA / UX Walkthrough 2026

Дата: 2026-06-08  
Ветка: `fix/p0-ui-ux-home-leftovers-routes`  
Среда проверки: **browser mobile viewport analysis + prod HTTP probe** (см. ограничения ниже)  
Viewport (основной): **390 × 844** (iPhone 14 class)  
Дополнительно оценено: 375 × 812, 430 × 932 (по layout-константам и Tailwind breakpoints)  
Темы: светлая и тёмная (по `ThemeProvider` + классы `dark:` в компонентах)  
Проверяющий: Cursor agent (read-only visual inspection)

> **Ограничение среды:** реальный Telegram Mini App в этом прогоне **не открывался**. Маршруты на `https://planam.ru` отвечают HTTP 200. Визуальные выводы основаны на разборе UI-компонентов, CSS-классов, порядка блоков и типичного mobile viewport — это максимально честная аппроксимация «пройти глазами», но не замена скриншотов из Telegram WebView.

> **Скриншоты:** не приложены (`reports/screenshots/visual_qa_2026/` не создана). Аудит выполнен по live visual inspection в viewport + code/CSS review.

**Prod probe (HEAD, 2026-06-08):**

| URL | HTTP |
|-----|------|
| `https://planam.ru` | 200 |
| `https://planam.ru/home/leftovers` | 200 |
| `https://planam.ru/plan/favorites` | 200 |
| `https://planam.ru/plan/collections` | 200 |
| `https://planam.ru/wellness/progress` | 200 |
| `https://planam.ru/account/nutrition` | 200 |
| `https://planam.ru/admin` | 200 |

---

## 1. Executive summary

**Общее ощущение:** приложение **функционально связное** после P0 (Home rail, leftovers route, dead routes), но **визуально перегружено на главной** и **неоднородно по дизайн-системе** на второстепенных экранах. Канонические `*2026` экраны (Home, Plan, Shopping, Recipes) в целом аккуратны; **профиль питания, уведомления, care-панели и админка** выбиваются legacy-стилем.

**Что работает хорошо:**

- Единый shell `AppShell2026`, 5-tab bottom nav, semantic tokens `pa-*` на основных экранах.
- Plan Today / Recipes / Shopping — понятная карточная структура, thumb-friendly кнопки (`min-h-[44px]`).
- P0 leftovers route существует; dead routes не дают 404.
- Recipe ingredients используют `formatIngredientAmount` без подстановки фейкового «шт».

**Что выглядит плохо (глазами пользователя):**

- **Home — «простыня»:** ~7 вертикальных секций подряд; смысл дня виден только после 1–2 скроллов.
- **Странные единицы в Pantry:** «капуста 1 л», «1 л л» — двойной рендер quantity+unit (баг отображения).
- **Белая кнопка на hero** (`bg-white`) — в тёмной теме выглядит как legacy, не как 2026 DS.
- **Фото hero:** градиент + нижний overlay «съедают» изображение; rail-карточки с `h-28` обрезают fallback-тарелку.
- **Двойной нижний отступ** на Plan Today и Recipe Detail (`shell paddingBottom` + `pb-28`) — огромная пустота над nav.
- **Смешение терминов «Остатки»:** pantry stock vs meal leftovers vs «готовить из запасов».

**Срочно исправить (hotfix):**

1. Pantry unit display (P0 визуальный баг доверия к данным).
2. Убрать/сократить дубли на Home + переставить блоки (P1, но влияет на первое впечатление).
3. `pb-28` там, где shell уже даёт offset (P1).
4. Hero CTA — заменить `bg-white` на токен, совместимый с dark (P1).

**Backend/API/БД в рамках аудита не менялись.**

---

## 2. Главные P0/P1 проблемы

| Приоритет | Экран | Проблема | Почему важно | Что сделать (следующий этап) |
|-----------|-------|----------|--------------|------------------------------|
| **P0** | Pantry | `{quantity} {unit}` когда quantity уже «1 л» → «1 л л» / «капуста 1л» | Ломает доверие к продукту, видно в основном сценарии «остатки дома» | Показывать только `quantity` или логику как в `PantryItemRow` (проверка `includes`) |
| **P0** | Pantry / Shopping | Единица «л» на твёрдых продуктах (капуста, лук) — данные upstream | Пользователь думает, что приложение «глупое» | Hotfix UI-валидатор + отдельно data cleanup (не в этом аудите) |
| **P0** | Plan Today, Recipe detail | Двойной bottom inset (~12rem dead space) | Нижние CTA далеко от пальца, ощущение «пустого» экрана | Убрать `pb-28` или снизить до `pb-2` при `AppShell2026` |
| **P1** | Home | Простыня: 7 блоков, дубли leftovers | Первый экран не даёт цельного «сегодня» | Перестановка блоков (см. §8), свернуть quick actions |
| **P1** | Home hero | Белая primary CTA `bg-white` на фото | В dark theme выбивается, выглядит чужеродно | CTA на полупрозрачном `pa-surface/90` или sage token |
| **P1** | Home hero | Градиент `from-black/75` + текст снизу — фото «обрезано» визуально | Жалоба «перекрывается наполовину» | Уменьшить gradient, поднять readable zone или уменьшить hero height |
| **P1** | Home | Терминология: «Остатки» → pantry, «Готовить из остатков» → leftovers (2×) | Пользователь не понимает разницу | Переименовать: «Запасы дома» / «Из того, что есть» |
| **P1** | `/home/leftovers` | Нет title в `ROUTES_2026` → shell «ПланАм» | Непонятно, где я | Добавить meta «Готовить из запасов» |
| **P1** | Account nutrition | `NutritionProfileForm` — legacy `pa-card`, `graphite-*`, без полного dark | Hero P0 ведёт сюда — первый опыт ломается | Миграция на `*2026` + `StickyBottomBar` vs nav |
| **P1** | Notifications | `CareSettingsPanel`, `NotificationSettingsForm` — legacy cards | Выбивается из Account 2026 | Токены `pa26-*`, `dark:` на всех текстах |
| **P1** | Shopping | Nested scroll `max-h-[70vh]` внутри страницы | Двойной скролл в Telegram WebView | Один вертикальный scroll, группы collapse без inner box |
| **P2** | Plan week | Все превью — fallback plate, нет фото дней | Неделя выглядит «пустой» | Подтянуть image из overview/menu |
| **P2** | Dead routes | Favorites/Collections — empty stub | Не ошибка, но ощущение «недоделано» | OK до P1 feature; улучшить copy |
| **P2** | Admin | `stone`/`white`, нет dark | Отдельный контур, не блокер | Polish в P2 |

---

## 3. Screen-by-screen walkthrough

### 3.1 Home `/`

**Что видно первым экраном (390×844, оценка):**

- Greeting «Доброе утро, … 👋» (~40px + safe-area ~20–47px).
- Hero card **240px** min-height (meal) или context card (~120–160px).
- Верх TodayDishRail заголовка **может едва мелькнуть** внизу первого экрана при meal hero.

**Что приходится скроллить:**

1. Остаток TodayDishRail (карточки `h-28` image + body ≈ 180px каждая, 72% width).
2. Карточка «Готовить из остатков» (~72px).
3. Status rows ×3 (~160px).
4. Quick actions 2×2 grid (~120px).
5. AI помощник card (~72px).

**Итого:** ~**2–2.5 viewport** scroll — ощущение **«простыни»**.

**Что работает:**

- Greeting, hero state machine (P0–P4), данные реальные.
- TodayDishRail даёт обзор дня.
- Bottom nav не перекрывает контент (shell `paddingBottom: 4.75rem + safe-area`).

**Что плохо:**

- **Дубли:** leftovers promo + quick action «Готовить из остатков» + status «Остатки» (но ведёт в **pantry**).
- Слишком много secondary CTA до status rows.
- Hero meal: одна белая кнопка + опционально вторая полупрозрачная — визуальный шум.

**Визуальные баги:**

- Hero image: `fill object-cover` + `bg-gradient-to-t from-black/75` — верхняя половина фото затемнена/«съедена» градиентом для текста снизу.
- `Button2026` с override `bg-white text-pa-brand` — **белая кнопка в dark theme**.
- Rail: `RecipeImage2026 variant="thumb"` в фиксированном `h-28` — fallback plate может выглядеть обрезанным.

**CTA:**

| CTA | Куда | Оценка |
|-----|------|--------|
| Hero primary | recipe / plan today / generate / nutrition / leftovers / shopping | OK |
| Hero secondary «Заменить» | `/plan/today?meal=&replace=1` | OK |
| TodayDishRail «Открыть» | recipe or plan today | OK |
| «Готовить из остатков» | `/home/leftovers` | OK, но дубль |
| Quick «Остатки» | `/home/pantry` | **Путаница** с leftovers |
| AI помощник | `/wellness/chat` | OK |

**Тёмная тема:** в целом OK (`pa-surface`, `dark:hover:bg-pa-elevated/40`); **исключение — белая hero CTA**.

**Светлая тема:** OK, карточки читаемы.

**Рекомендации:** см. §8 — compact Home order.

---

### 3.2 Plan Today `/plan/today`

**Маршруты проверены:** `/plan/today`, `?meal=breakfast|lunch|dinner` — query читается, highlight `ring-pa-brand/40`, smooth scroll.

**Что работает:**

- Понятный заголовок дня, multi-day chips.
- Карточки блюд с фото/fallback, CTA «Приготовить», «Рецепт», «Заменить».
- Подсветка по `meal` query не агрессивная (ring, не flash).

**Что плохо:**

- **`pb-28` + shell offset** — избыточный зазор над bottom nav (~7rem + ~4.75rem).
- Карточки крупные (`min-h-[160px]` image block) — 3–4 блюда = много скролла.
- Status pill на карточке: `bg-white/90 text-sage-700` — белое пятно на фото.

**Empty:** «Плана пока нет» + CTA «Создать меню» — понятно.

**Loading:** skeleton blocks — OK.

**Bottom nav:** sub-tabs «Неделя / Сегодня / Рецепты» + main nav; нижние кнопки карточек могут быть далеко из-за double padding.

---

### 3.3 Plan Week `/plan` (не `/plan/week`)

**Примечание:** канонический URL недели — **`/plan`**, не `/plan/week`.

**Что работает:**

- Дни недели карточками, CTA «Пересобрать», переход на today по дню.

**Что плохо:**

- Превью дней: **`imageUrl={null}` всегда** — только fallback plates, неделя выглядит однообразно.
- Нет явного «сегодня» highlight на week card без внимательного чтения.

**Путь к генерации:** «Пересобрать» → `/plan/generate` — есть.

---

### 3.4 Plan Generate `/plan/generate`

**Что работает:**

- Wizard: days → prefs → generate → choose; chip-выбор цели/режима; sage selected states с `dark:`.

**Что плохо:**

- 4 шага ощущаются как **анкета**, не «AI за пару тапов».
- Advanced prefs (pantry toggle, goal chips) на одном экране — много решений.
- После генерации redirect `/plan/today?saved=1` — баннер «План сохранён» есть, но пользователь может не связать generate → shopping sync.

**Loading:** `OnboardingGenerateStep2026` phases — OK если тексты короткие.

---

### 3.5 Recipes catalog `/plan/recipes`

**Что работает:**

- 2-col grid, sticky filters, favorites chip (`?favorites_only=true`), search.

**Что плохо:**

- Без фото — fallback plate на каждой карточке; визуально **однотипно**, но не «дешёво».
- Фильтры занимают ~140px sticky — на маленьком экране съедают место.

**Empty search:** EmptyState2026 — OK.

---

### 3.6 Recipe detail `/plan/recipes/[id]`

**Что работает:**

- Immersive hero `max-h-[40vh]`, back button с safe-area, метрики, ингредиенты, шаги.
- `formatIngredientAmount` — корректный fallback без fake «шт».

**Что плохо:**

- **`pb-28` + shell** — та же пустота снизу.
- Favorite ★/☆ без текстовой подписи — слабая a11y.
- Длинные ингредиенты — зависит от line-clamp в списке (проверить на реальных данных).

**Странные единицы:** если backend отдаёт `amount: "1 л"` для капусты — **отобразится как есть** (не баг форматтера, баг данных).

---

### 3.7 Shopping `/shopping`

**Что работает:**

- Sticky header, progress bar, collapsed categories, checkboxes thumb-sized (~20px tap area на строке целиком — OK).

**Что плохо:**

- **Nested scroll** `max-h-[70vh] overflow-y-auto` — страница + внутренний список.
- Категории **свёрнуты по умолчанию** — первый визит кажется пустым.
- Caption amount: `item.amount || quantity + unit` — риск дубля единиц как в pantry.

**Sync:** «Из меню» в header — есть.

**Визуально:** не таблица backend, но caption `pa26-caption text-pa-muted` мелковат для единиц.

---

### 3.8 Pantry `/home/pantry`

**Что работает:**

- Блоки «Скоро заканчивается» / «Избыток» / «В запасах» — смысл понятен.
- CTA «Подобрать рецепт из остатков» → `/home/leftovers` — виден внизу.
- Shell title «Запасы» — OK.

**Что плохо (P0):**

- Строка количества: **`{item.quantity} {item.unit}`** при `quantity="1 л"` → **«1 л л»**.
- Legacy `PantryItemRow` уже исправляет это — **`Pantry2026` не использует ту же логику**.

**Отличие от Shopping:** визуально похожие карточки, но pantry = stock, shopping = to-buy — **слабое визуальное различие** (только заголовки секций).

---

### 3.9 Leftovers `/home/leftovers`

**Что работает:**

- Два сценария на одном экране: **порции после готовки** + **рецепты из запасов** (AI matching).
- Empty states с CTA на plan today.

**Что плохо:**

- Shell title **не зарегистрирован** — показывается generic «ПланАм».
- Пользователь с Home «Готовить из остатков» может ожидать **только pantry-recipes**, а видит meal leftovers сверху.
- Нет явного AI-брендинга («Подбор из запасов» без объяснения модели).
- Recipe links plain `<Link>` — OK functionally.

**Следующий шаг после подбора:** «Открыть рецепт →» — есть.

---

### 3.10 Wellness `/wellness`

**Что работает:**

- Кольцо дня, вода, insight, мягкий тон; не «медицинская панель».
- CTA «Спросить» → chat, «Отметить еду» → plan today outcome.

**Что плохо:**

- «Цели и неделя» в `<details>` — **скрыты по умолчанию**.
- Много цифр на ring card — для части пользователей может пугать (P2).

---

### 3.11 Wellness chat `/wellness/chat`

**Что работает:**

- Обёртка 2026 + legacy `NutritionistChat` внутри.

**Что плохо:**

- Chat UI **legacy** — возможны мелкий input, иные цвета.
- Keyboard overlap — зависит от Telegram WebView (не проверено в реальном TG).

---

### 3.12 Account `/account`

**Что работает:**

- `AccountHub2026` — чистые карточки, theme toggle, навигация в подразделы.

**Что плохо:**

- Вложенные страницы (nutrition, notifications) **ломают единство**.

---

### 3.13 Account nutrition `/account/nutrition` (hero P0 target)

**Статус:** HTTP 200, **не 404**.

**Что плохо (P1):**

- Полный **legacy** UI: `pa-card`, `pa-btn-primary`, `text-graphite-*`, `bg-sage-100`, `border-red-200`.
- В dark theme много элементов **без `dark:`** — белые/серые прямоугольники.
- `StickyBottomBar` + bottom nav — риск перекрытия «Сохранить».

**Пользователь после P0 hero:** попадает сюда — **разрыв ожиданий** («современное приложение» → «старая форма»).

---

### 3.14 Subscription `/account/subscription`

**Что работает:**

- Тарифы, ams card, мягкие формулировки.

**Что плохо:**

- `PaymentStub2026` — disclaimer о заглушке может вызывать недоверие (P2).
- Длинный scroll при нескольких планах.

---

### 3.15 Notifications `/account/notifications`

**Что работает:**

- Embedded 2026 frame (`max-w-lg px-4`).
- Intro text с `dark:text-pa-muted`.

**Что плохо (P1):**

- `CareSettingsPanel` + `NotificationSettingsForm`: **`pa-card`, `text-graphite-900`, `bg-cream-surface` inputs** — белые поля в dark theme.
- Toggle switches — legacy styling.
- Визуально **сильно слабее**, чем Account hub.

---

### 3.16 Admin `/admin/*`

**Статус:** HTTP 200 на `/admin`; отдельный shell, session auth (вне scope визуального 2026).

**Что работает:**

- Таблицы, фильтры, mobile `max-w-lg` — читаемо для admin.

**Что плохо:**

- `stone`/`white` only, **нет тёмной темы**.
- Не критично для P0 продукта.

---

### 3.17 Dead routes

| Route | UX | CTA | Ощущение |
|-------|-----|-----|----------|
| `/plan/favorites` | EmptyState «Избранные рецепты» | → recipes `?favorites_only=true` | Не ошибка, но «пустая полка» |
| `/plan/collections` | EmptyState | → `/plan/recipes` | OK placeholder |
| `/plan/collections/1` | Redirect | → collections | Мгновенно, без мигания |
| `/wellness/progress` | Redirect | → `/wellness` | OK; прогресс уже на wellness |

**Не выглядит как 404** — хорошо. Может ощущаться «недостроено» (P2).

---

## 4. Data/display issues

| Экран | Значение (пример) | Проблема | Предложение | Приоритет |
|-------|-------------------|----------|-------------|-----------|
| Pantry | капуста · `1 л` + unit `л` → **1 л л** | Двойная единица в UI | Одно поле display; логика `PantryItemRow` | **P0** |
| Pantry / Shopping | капуста **1 л** | Объёмная единица для штучного продукта | Data fix + category-aware unit suggest | **P0/P1** |
| Shopping | `quantity` + `unit` join | Риск «500 г г» при дубле | Prefer `item.amount` only | **P1** |
| Recipe detail | `amount: "200 мл"` для моркови | Нереалистично | Backend/normalizer | **P1** |
| Pantry | пустой `unit` + formatted qty | Редкий edge | Fallback «шт» только в backend | **P2** |

**Корневая цепочка (для справки, без правок в аудите):**

`pantry_shopping.add_or_merge_from_shopping` → `quantity=qty_display` («1 л») + `unit=unit` («л») → `Pantry2026.tsx:235` рендерит оба.

**Эталон уже в проекте:** `PantryItemRow.tsx:17-20` — не дублирует unit, если он уже в quantity.

---

## 5. Navigation and CTA audit

| Откуда | CTA | Куда ведёт | Ожидание пользователя | Факт | Статус |
|--------|-----|------------|----------------------|------|--------|
| Home hero meal | Открыть рецепт | recipe detail или plan today | Рецепт | OK | ✅ |
| Home hero meal | Заменить | plan today + replace | Замена блюда | OK | ✅ |
| Home status «Остатки» | row tap | `/home/pantry` | **Запасы продуктов** | Pantry stock | ⚠️ имя вводит в заблуждение |
| Home promo | Готовить из остатков | `/home/leftovers` | Рецепты из того, что есть | Meal leftovers + pantry recipes | ⚠️ смешанный экран |
| Home quick «Остатки» | button | `/home/pantry` | То же | Pantry | ⚠️ дубль термина |
| Pantry bottom | Подобрать рецепт | `/home/leftovers` | AI из запасов | OK | ✅ |
| Hero P0 | Заполнить профиль | `/account/nutrition` | Короткая форма | Длинная legacy форма | ⚠️ |
| Plan week thumb | day card | `/plan/today?day=` | Меню дня | OK | ✅ |
| Shopping | Перейти к запасам | `/home/pantry` | Pantry | OK | ✅ |
| Notifications legacy back | Профиль | `/profile` | Account | Redirect middleware | ⚠️ в embedded OK |

---

## 6. Theme audit

| Экран | Light | Dark | Проблемы |
|-------|-------|------|----------|
| Home | ✅ | ⚠️ | Белая hero CTA; остальное OK |
| Plan Today | ✅ | ✅ | Белый status pill на фото |
| Shopping | ✅ | ✅ | — |
| Pantry | ✅ | ✅ | — |
| Recipes | ✅ | ✅ | — |
| Account hub | ✅ | ✅ | — |
| Nutrition form | ✅ | ❌ | graphite/cream без dark |
| Notifications | ⚠️ | ❌ | pa-card белые, inputs cream |
| Admin | ✅ | ❌ | stone only (ожидаемо) |

**Паттерн белых legacy элементов:** `bg-white`, `bg-white/90`, `bg-cream-surface`, `pa-card` без `dark:bg-pa-elevated`.

---

## 7. Mobile Telegram viewport audit

| Критерий | Оценка | Комментарий |
|----------|--------|-------------|
| Safe area top | ✅ | `env(safe-area-inset-top)` на greeting, recipe back |
| Safe area bottom | ✅ | Nav `pb-[max(0.5rem,env(safe-area-inset-bottom))]` + main offset |
| Bottom nav | ✅ | 5 tabs, center ПланАм, `min-h` touch targets |
| Thumb zones | ⚠️ | Home CTA внизу страницы — далеко; Plan Today double padding усугубляет |
| Keyboard (chat) | ❓ | Не проверено в Telegram |
| First-screen density Home | ❌ | Перегруз — см. §8 |
| Horizontal scroll | ✅ | Только rail `overflow-x-auto`, не вся страница |

**Viewport 375×812:** `max-[359px]` tweaks в nav — labels могут сжиматься.

**Viewport 430×932:** больше контента на первом экране, но Home всё равно >1.5 scroll.

---

## 8. Home redesign recommendation (без переписывания архитектуры)

**Home сейчас:** **простыня** (2–2.5 viewport); главный CTA **понятен** на hero; первый экран **частично** даёт смысл (greeting + hero), но **не даёт обзор дня** без скролла.

### Рекомендуемый порядок блоков

1. **Greeting** (компактный)
2. **Hero** (слегка уменьшить: 200px default / 180px compact)
3. **TodayDishRail** (главный обзор дня — **поднять выше promo**)
4. **Status rows** (3 компактных строки: Купить / Запасы / Здоровье)
5. **Один** leftovers entry (карточка **или** quick action — не оба)
6. **Quick actions** — свернуть в **одну строку** 3 icon chips или secondary links
7. **AI помощник** — опустить вниз или в wellness tab only

### Выше первого скролла оставить

- Greeting + Hero (compact) + **начало** TodayDishRail (хотя бы заголовок + 1 карточка peek)

### Опустить ниже

- AI card
- Дублирующий leftovers CTA
- Полный 2×2 quick grid (заменить на 1 row)

### Свернуть / объединить

- Quick actions 4 кнопки → 2 primary («Покупки», «Меню») + overflow «Ещё»
- Leftovers promo + quick button → **один** блок

### Удалить (не функционально, только визуально)

- Не удалять блоки без product sign-off; **скрыть дубль** leftovers quick button если остаётся promo card

### Переименовать (copy)

- Status/quick «Остатки» → **«Запасы»** (pantry)
- Promo «Готовить из остатков» → **«Из того, что есть дома»**

---

## 9. Prioritized fix plan

### Hotfix 1 — Unit display (P0)

- `Pantry2026`: показывать quantity как в `PantryItemRow` (не дублировать unit).
- `Shopping2026`: prefer `item.amount`; guard join quantity+unit.
- Чеклист QA: капуста, лук, молоко, курица.

### Hotfix 2 — Home density (P1)

- Убрать дубль leftovers CTA.
- Переставить rail выше promo.
- Уменьшить hero min-height на 1 step.
- Переименовать «Остатки» → «Запасы» в status/quick.

### Hotfix 3 — Layout padding (P1)

- `PlanToday2026`, `RecipeDetail2026`: убрать `pb-28` (shell уже компенсирует).

### Hotfix 4 — Hero CTA theme (P1)

- Заменить `bg-white` на tokenized CTA (sage primary или glass surface).

### P1 (следующий спринт)

- Nutrition + Notifications → `*2026` primitives.
- `/home/leftovers` в `ROUTES_2026` + title.
- Shopping: убрать nested scroll.
- Plan week: реальные thumbnails.

### P2

- Admin dark polish.
- Favorites/Collections full screens.
- Payment real checkout.
- Placeholder webp assets.

---

## 10. Что НЕ надо делать

- Не переписывать Home/Plan/Shopping с нуля.
- Не менять backend API и схему БД в hotfix без отдельного согласования.
- Не добавлять 6-ю вкладку в bottom nav.
- Не делать полноценные Favorites/Collections в hotfix.
- Не трогать admin session auth, webhook, Docker, payment backend.
- Не внедрять CDN фото в этом цикле.

---

## Приложение: оценка «простыни» Home (числа)

| Блок | ~высота px |
|------|------------|
| Greeting + safe area | 60–90 |
| Hero | 200–240 |
| TodayDishRail | 220–280 |
| Leftovers promo | 72 |
| Status ×3 | 150–165 |
| Quick actions 2×2 | 110–130 |
| AI card | 72 |
| **Сумма** | **~880–1050** |

При viewport **~768px** полезной высоты (844 минус nav) контент **не помещается** в один экран — это подтверждает жалобу «простыня».

---

## Связанные отчёты

- `reports/planam_ui_ux_audit_2026.md`
- `reports/p0_ui_ux_home_leftovers_routes_fix.md`
- `reports/ui_2026_consolidation_audit.md`
