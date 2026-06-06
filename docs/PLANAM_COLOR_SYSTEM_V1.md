# PLANAM COLOR SYSTEM V1

Единая палитра PlanAm V1 для `NEXT_PUBLIC_PLANAM_UI_2026=true`.

Источник токенов: `apps/web/app/globals.css` + `apps/web/tailwind.config.ts`.

## Принципы

- Больше белого и воздуха на canvas
- Насыщенный зелёный акцент (еда, свежесть, здоровье)
- Высокий контраст текста
- Карточки легче: белый surface, тонкая border, минимум тени

## Semantic tokens (CSS variables)

| Token | Light | Dark | Role |
|-------|-------|------|------|
| `--pa-bg-canvas` | `#FFFFFF` | `#121412` | Фон приложения |
| `--pa-bg-surface` | `#FFFFFF` | `#1A1D1A` | Карточки |
| `--pa-bg-elevated` | `#F6FAF6` | `#242824` | Вторичные блоки |
| `--pa-text-primary` | `#1A1F1C` | `#F4FAF4` | Заголовки, основной текст |
| `--pa-text-secondary` | `#5C665C` | `#A8B4A8` | Подписи |
| `--pa-brand-primary` | `#2F9E44` | `#4ADE80` | CTA, акцент |
| `--pa-brand-secondary` | `#248A38` | `#86EFAC` | Hover / success |
| `--pa-accent` | `#E07B39` | `#FB923C` | Тёплый акцент |
| `--pa-border` | `#E2E8E0` | `#2F352F` | Разделители |

## Tailwind usage

- Фон: `bg-pa-canvas`, `bg-pa-surface`, `bg-pa-elevated`
- Текст: `text-pa-foreground`, `text-pa-muted`
- Бренд: `bg-pa-brand`, `text-pa-brand`, `bg-sage-500`
- Границы: `border-pa-border`

## Запрещено

- Случайные оттенки `#5E8B57`, `#FBF7EF`, `#ECE4D6` в новых V1-экранах
- Смешение legacy `cream-*` и `pa-*` на одном экране без миграции

## Shopping category slugs

Категории покупок — отдельный канонический список в `apps/web/lib/shopping/categories-v1.ts`. Slug `продукты` запрещён; fallback — `другое`.
