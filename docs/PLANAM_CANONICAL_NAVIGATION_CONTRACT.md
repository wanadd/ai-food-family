# PLANAM Canonical Navigation Contract

Sprint: 1.8B-0

## Root Bottom-Nav Screens

- `/` — ПланАм / главная.
- `/plan/today` — меню на сегодня.
- `/home/shopping` — покупки.
- `/wellness` — здоровье.

Root screens must not show an in-app BackButton. Telegram BackButton should be
hidden on root screens.

## Canonical Nested Screens

- `/plan/recipes` — каталог рецептов.
- `/plan/recipes/[id]` — детальная карточка рецепта.
- `/home/pantry` — запасы.
- `/home/leftovers` — готовить из запасов / leftovers foundation.
- `/account` — аккаунт.
- `/account/family` — семья.
- `/account/notifications` — уведомления.
- `/account/settings` — настройки.
- `/account/settings/documents` — документы.
- `/account/settings/support` — поддержка.
- `/account/settings/about` — о приложении.
- `/events` — future scaffold placeholder: "Раздел скоро появится".

Nested screens should show an in-app BackButton in a consistent location.
Telegram BackButton should be visible on nested screens.

## Back Behavior

- Recipe opened from menu returns to the same menu day/context when possible.
- Recipe opened from catalog returns to catalog filters/search/scroll when possible.
- Recipe opened from home returns to home.
- Account/settings/documents/support/family/notifications return to the previous
  settings/home source when available.
- If no safe previous context exists, fallback is `/`.

## Compatibility Redirects

- `/shopping` redirects to `/home/shopping`.
- `/recipes` redirects to `/plan/recipes`.
- `/recipes/[id]` redirects to `/plan/recipes/[id]`.
- `/menu/current` redirects to `/plan/today`.
- `/menu/recipes` redirects to `/plan/recipes`.
- `/menu/generate` redirects to `/plan/generate`.
- `/menu/event` redirects to `/events`.
- `/health` redirects to `/wellness`.
- `/health/chat` redirects to `/wellness/chat`.
- `/nutritionist` redirects to `/wellness/chat`.
- `/profile` redirects to `/account`.
- `/settings` redirects to `/account/settings`.

Redirect routes are compatibility surfaces. New code must link to canonical
routes, not redirect aliases.

## Future-Feature Protection

Legacy cleanup must not remove planned PLANAM feature scaffolding. Before
deleting a route, component, service, or script, classify it as one of:

- `KEEP_ACTIVE`
- `KEEP_REDIRECT`
- `KEEP_PROTECTED`
- `KEEP_FUTURE_SCAFFOLD`
- `DELETE_LEGACY`
- `REFACTOR_LATER`
- `REVIEW_MANUALLY`

`KEEP_FUTURE_SCAFFOLD` means the feature is not fully active in UI yet, but the
code represents planned product functionality. It may be hidden from navigation
or replaced with a clean placeholder, but must not be deleted without explicit
approval.

Protected future scaffolds include Events, Health/AI nutritionist/Pro,
Cooking mode, Pantry/leftovers/cook-from-stock, Family, profile nutrition
restrictions, Shopping/OCR/voice hooks, Telegram bot/relay/webhook,
payments/subscriptions/Pro, Recipe Factory/Gold V3 pipeline, and Admin.

If classification is uncertain, use `REVIEW_MANUALLY` and do not delete.
