# PLANAM V1 — Documentation Freeze Report

**Дата freeze:** 2026-06-03  
**Статус:** документация V1 **зафиксирована**  
**Следующий этап:** PLANAM V1 IMPLEMENTATION MASTER — Sprint 1  
**Код:** не изменялся

---

# 1. Какие документы изменены (финальный проход)

| Документ | Версия | Изменения в freeze |
|----------|--------|-------------------|
| [PLANAM_V1_FINAL_VISION.md](./PLANAM_V1_FINAL_VISION.md) | 1.1 freeze | Hero + визуальный объект: default еда, исключения; статус freeze |
| [PLANAM_V1_RELEASE_BLUEPRINT.md](./PLANAM_V1_RELEASE_BLUEPRINT.md) | 1.2 freeze | Эволюция продукта; динамический Hero §6; фото §13 → Image Strategy |
| [PLANAM_V1_PRODUCT_MASTER.md](./PLANAM_V1_PRODUCT_MASTER.md) | 1.3 freeze | Эволюция; динамический Hero в топ-решениях; индекс + freeze |
| [PLANAM_V1_HOME_STATES.md](./PLANAM_V1_HOME_STATES.md) | 1.2 freeze | Убраны «блюдо дня» / фикс. ужин; приоритет Hero; визуал |
| [PLANAM_V1_SHOPPING_MODEL_UPDATE.md](./PLANAM_V1_SHOPPING_MODEL_UPDATE.md) | 1.1 freeze | Статус freeze; снято «HOME_STATES не обновлён» |

## Созданы

| Документ | Назначение |
|----------|------------|
| [PLANAM_V1_IMAGE_STRATEGY.md](./PLANAM_V1_IMAGE_STRATEGY.md) | Фото, Hero, fallback, темы |
| **Этот отчёт** | Фиксация freeze |

---

# 2. Исправленные противоречия

| Было | Стало | Где |
|------|-------|-----|
| Hero = всегда фото еды / ужин | Динамический Hero; фото только при «следующий приём» | Final Vision, Blueprint, Home States, Product Master |
| «Блюдо дня» на ПланАм | «Ближайший приём пищи» | Home States |
| «Завтрашний ужин» в Hero | «Следующий приём / preview завтра» | Home States |
| Приоритет: покупки > hero блюда (неявно) | Явная цепочка Final Vision | Home States footer |
| Покупки = список из меню | Единый семейный список (14 категорий) | Уже в Shopping Update; подтверждено в freeze |
| 13 категорий (в TO_V2) | 14 категорий — канон V1 | Отмечено: синхронизировать TO_V2 при Sprint 1 ТЗ |

**Не входили в freeze-проход** (могут содержать примеры «ужин» как время суток, не Hero): AI Journey, Growth Model, Life Scenarios, Family Model §2. Синхронизация — по мере Sprint 1, без изменения freeze-документов.

---

# 3. Решения, зафиксированные окончательно

## Продукт

1. PlanAm снимает нагрузку решений о питании семьи — продаёт **готовое решение**.
2. 4 вопроса: готовить · купить · дома · здоровье — фильтр первого уровня.
3. **Эволюция:** питание — ядро; покупки/остатки/здоровье/семья — ежедневный центр бытовых решений.
4. **3-секундный тест** — критерий успеха V1.

## Навигация

5. Bottom nav: Сегодня · Покупки · **ПланАм** · Здоровье · Профиль.
6. ПланАм `/` — центр, не дашборд.

## Hero

7. Динамический: следующий полезный шаг.
8. **Не привязан к ужину.**
9. Приоритет: нет меню → критичные покупки → инсайт здоровья → следующий приём.
10. Визуал: **еда по умолчанию**; исключения — иллюстрация/иконка действия.

## AI

11. AI в фоне; не вкладка; не обязательный чат.
12. Free: меню, покупки, замена, остатки, семья.
13. PRO: внутри Здоровья (AI Nutritionist).

## Покупки

14. **Единый семейный список** (меню + ручные + быт + дети + питомцы).
15. **14 категорий** утверждены; **«Продукты»** запрещена.
16. AI: тип покупки (recipe / home / child / pet) + категория.
17. P0: ручное «+ Добавить».

## Семья и рост

18. Семья — главное преимущество; общее меню, покупки, остатки.
19. Вирусность через семью, не геймификацию.

## Визуал и изображения

20. Еда — главный визуальный объект по умолчанию.
21. Image Strategy: размеры Hero, fallback, темы, когда не показывать фото.

## Запреты

22. Не CRM, не админка, не каталог-вкладка, не калькулятор, не AI-чат-продукт.

---

# 4. Обязательные принципы для разработки

Любая реализация **обязана** соответствовать (в порядке приоритета):

| # | Принцип | Источник |
|---|---------|----------|
| 1 | Final Vision побеждает при конфликте | FINAL_VISION |
| 2 | 3-секундный тест на ПланАм | FINAL_VISION |
| 3 | Динамический Hero | FINAL_VISION, HOME_STATES |
| 4 | 5 tabs, ПланАм в центре | FINAL_VISION, BLUEPRINT |
| 5 | AI — результат, не чат-вкладка | FINAL_VISION, AI_JOURNEY |
| 6 | Единый семейный список покупок | SHOPPING_UPDATE, FINAL_VISION |
| 7 | 14 категорий, не «Продукты» | FINAL_VISION, BACKLOG P0-SHOP-01 |
| 8 | Фото еды по Image Strategy | IMAGE_STRATEGY |
| 9 | Fit viewport ПланАм / Сегодня / Здоровье | BLUEPRINT |
| 10 | Legacy не в user path | RELEASE_SCREENS, BACKLOG P0-NAV-03 |

---

# 5. Иерархия документов (freeze)

```text
1. PLANAM_V1_FINAL_VISION.md          ← START HERE
2. PLANAM_V1_RELEASE_BLUEPRINT.md
3. PLANAM_V1_PRODUCT_MASTER.md        ← индекс
4. PLANAM_V1_HOME_STATES.md
5. PLANAM_V1_SHOPPING_MODEL_UPDATE.md
6. PLANAM_V1_IMAGE_STRATEGY.md
7. PLANAM_V1_PRODUCT_BACKLOG.md       ← Sprint 1 scope (P0)
8. Остальные V1_* (family, growth, screens, AI journey, V2…)
9. PLANAM_CURRENT_STATE_*             ← as-is код, справочно
```

---

# 6. Готовность к Sprint 1

| Критерий | Статус |
|----------|--------|
| Высший приоритет (Final Vision) | ✅ Зафиксирован |
| Навигация и экраны | ✅ Blueprint + Release Screens |
| Hero и состояния | ✅ Final Vision + Home States |
| Покупки и категории | ✅ Shopping Update + Final Vision |
| Изображения | ✅ Image Strategy |
| Backlog P0 (35 задач) | ✅ Product Backlog |
| As-is аудит | ✅ Current State Master |
| Противоречия в freeze-наборе | ✅ Устранены |

## Вердикт

**Документация готова к разработке Sprint 1.**

Следующий документ: **PLANAM V1 IMPLEMENTATION MASTER — SPRINT 1** (ТЗ на реализацию по P0 backlog).

## Out of scope freeze (не блокирует Sprint 1)

- Синхронизация вторичных docs (AI Journey, Growth, Family §2, TO_V2 «13 категорий»).
- Реализация в коде.
- Коммиты / push.

---

# 7. Правило изменений после freeze

Изменения в freeze-документах V1 — только через **явное продуктовое согласование** с обновлением версии документа и записью в новом freeze-отчёте.

---

*PLANAM V1 Documentation Freeze — complete.*
