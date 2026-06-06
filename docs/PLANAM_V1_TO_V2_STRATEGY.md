# PLANAM V1 → V2 Strategy

**Версия:** 1.0  
**Дата:** 2026-06-03  
**Путь продукта:** Меню → Покупки → Остатки → Доставка

---

# 1. Продуктовая эволюция

```text
V1: Меню + Покупки + Остатки + Здоровье (семья)
         ↓
V1.5: Умные остатки, события, PRO AI глубже
         ↓
V2: Доставка продуктов из того же списка покупок
```

---

# 2. Этап 1 — Меню (V1, сейчас)

| Что закладываем | Зачем для V2 |
|-----------------|--------------|
| `recipe_id` + `ingredients[]` с quantity/unit | Маппинг на SKU магазина |
| `servings` per slot | Масштабирование заказа |
| Family scope | Один заказ на семью |
| Канон категорий покупок | Соответствие aisle/SKU категориям ритейлера |

**Архитектурное правило:** ингредиент — не строка, а **структурированная сущность** (name, amount, unit, category_slug).

---

# 3. Этап 2 — Покупки (V1)

| Что закладываем | Зачем для V2 |
|-----------------|--------------|
| Shopping list item: `name`, `category`, `checked`, `source` (menu/manual) | Источник для cart API |
| Sync menu → shopping | Не дублировать логику при доставке |
| 13 канонических категорий | Adapter layer: `category_slug → retailer_aisle` |
| Family list scope | Один checkout на family_id |

**Не делаем в V1:** привязка к конкретному магазину. Делаем **абстрактный список**, готовый к adapter.

---

# 4. Этап 3 — Остатки (V1 / V1.5)

| Что закладываем | Зачем для V2 |
|-----------------|--------------|
| Pantry item: product, qty, expiry | «Не заказывай то, что есть дома» |
| Outcome sheet → pantry update | Замкнутый цикл |
| Leftovers tracking | Меньше перезаказа |

**V2 сценарий:** перед доставкой система вычитает pantry → «докупить только 4 из 11».

---

# 5. Этап 4 — Доставка (V2)

| Компонент | Описание |
|-----------|----------|
| **Retailer Adapter** | Интерфейс: `resolveSku(ingredient) → sku`, `createCart(items) → order_id` |
| **Fulfillment Service** | Отдельный модуль, не в UI monolith |
| **UI** | Кнопка на экране Покупки: «Заказать доставку» (рядом с чеклистом) |
| **Payment** | Существующий billing + retailer payment или redirect |

---

# 6. Как текущая архитектура готовит без переписывания

## Backend

| Слой | Сейчас | Не трогать при V2 |
|------|--------|-------------------|
| `menus`, `recipes`, `ingredients` | Генерация, slots | Добавить adapter read, не менять schema core |
| `shopping_lists` | Family/personal scope | Расширить `item_metadata` (sku_ref optional) |
| `pantry` | Остатки | Использовать как pre-filter для cart |
| `families` | Scope | Тот же scope для order |
| AI services | Generate/replace | Не смешивать с fulfillment |

**Паттерн:** новый bounded context `fulfillment/` с adapter interface; UI вызывает через API `POST /shopping/delivery-quote`.

## Frontend

| Слой | Сейчас | V2 |
|------|--------|-----|
| `/home/shopping` | Чеклист | + CTA доставки (feature flag) |
| ПланАм статус 🛒 | Счётчик | + «или заказать» (V2) |
| Категории | 13 slug | Те же slug → retailer mapping |

**Паттерн:** не новая вкладка — расширение Покупок.

## Data model extension (V2-ready fields, optional in V1)

```text
shopping_list_item:
  + external_sku_id (nullable)
  + retailer_id (nullable)
  + price_estimate (nullable)

ingredient:
  + canonical_name (для matching)
  + category_slug (уже есть через mapping)
```

Добавление nullable полей в V1.5 — без breaking changes.

---

# 7. Что НЕ делать в V1 (чтобы не переписывать)

| Избегать | Почему |
|----------|--------|
| Hardcode retailer API в menu generation | Adapter отдельно |
| Отдельное «приложение доставки» | Один продукт, одна навигация |
| Shopping list без category_slug | Невозможен aisle mapping |
| Personal-only shopping в family mode | Сломает семейный checkout |
| AI генерирует «названия из головы» без recipe_id | Нет SKU match |

---

# 8. Roadmap по кварталам (ориентир)

| Фаза | Фокус |
|------|-------|
| V1 launch | Меню · Покупки · Остатки · Семья · AI в фоне |
| V1.5 | События, pantry AI, PRO depth, retailer pilot 1 город |
| V2 | Delivery CTA, 1–2 ритейлера, pantry-aware cart |

---

# 9. Критерий готовности к V2

- [ ] 80%+ shopping items имеют `category_slug` из канона
- [ ] Menu → shopping sync без ручных правок
- [ ] Family list стабилен при 2+ active adults
- [ ] Pantry coverage > 50% активных пользователей
- [ ] Retention D30 достаточен для monetization доставки

---

*Стратегия дополняет Blueprint. Продукт V1 не ждёт доставку — но не закрывает путь к ней.*
