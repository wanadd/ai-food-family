# PLANAM V1 — Sprint 1 Design Review

**Дата:** 2026-06-03  
**Тип:** итоговая оценка pre-implementation design validation  
**Spec:** [PLANAM_V1_SPRINT1_DESIGN_SPEC.md](./PLANAM_V1_SPRINT1_DESIGN_SPEC.md)  
**Код:** не изменялся

---

# Итоговая оценка

| Критерий | Оценка | Комментарий |
|----------|--------|-------------|
| Соответствие Final Vision | **9/10** | Динамический Hero и 5 tabs описаны; нужно убрать header на `/` |
| 3-секундный тест (дизайн) | **Проходит** | При условии 3 статусов always visible + compact SE |
| Telegram UX | **8/10** | 5 tabs влезают; риск двойного header |
| Fit viewport (ПланАм) | **8/10** | Требует compact hero 128px на SE |
| Готовность к коду | **Да** | После 3 согласований ниже |

**Общий вердикт:** дизайн Sprint 1 **готов к реализации** с низким риском крупной переделки, если зафиксировать mitigation из spec до начала кода.

---

# Сильные стороны

1. **Динамический Hero** — один layout, шесть понятных variants; не привязан к ужину.
2. **Три статуса** — страховка 3-секундного теста: даже non-meal Hero не ломает ответы на 4 вопроса.
3. **ПланАм в центре nav** — продуктовая логика Final Vision визуально очевидна.
4. **Еда по умолчанию, исключения явные** — согласовано с Image Strategy.
5. **Не копируем референс** — свой паттерн «решение + статусы», сильнее каталога-референса.
6. **Семейный список покупок** отражён в shopping-hero copy («еда и быт — один список»).
7. **Существующие токены 2026** (cream/sage, 4.75rem nav) — spec не требует новой DS.

---

# Слабые стороны

1. **As-is код: 4 tabs, нет ПланАм в nav** — gap между spec и реализацией (ожидаемо Sprint 1).
2. **ShellHeader + greeting** — дублирование на `/` съедает ~52px на SE.
3. **Secondary CTAs + Ask** — на маленьком viewport могут потребовать микро-скролл.
4. **Порог shopping-hero** — не зафиксирован в Final Vision числом; нужно product OK.
5. **Нет Figma** — только текстовые wireframes; QA на устройстве обязателен в Sprint 1.

---

# Что менять до кода

| Приоритет | Изменение | Статус |
|-----------|-----------|--------|
| **P0** | Скрыть `ShellHeader2026` на `/`; greeting только в body | Требует согласования → **рекомендуется утвердить** |
| **P0** | Добавить 5-ю вкладку ПланАм в центр `NAV_TABS_2026` | В backlog P0-NAV-01 |
| **P0** | Убрать 🏠 link из header когда ПланАм = tab | В backlog P0-NAV-02 |
| **P1** | Hero compact mode: photo max 128px если `height < 700` | В spec §3.2 |
| **P1** | Зафиксировать shopping-hero triggers (§2.4 spec) | Product OK |
| **P2** | Скрывать secondary links на compact | Можно в Sprint 1 polish |

---

# Что утверждено окончательно

| # | Решение |
|---|---------|
| 1 | Bottom nav: **Сегодня · Покупки · ПланАм · Здоровье · Профиль** |
| 2 | ПланАм — **центральная** вкладка, 44px круг, sage accent |
| 3 | Hero — **динамический**, приоритет Final Vision |
| 4 | Визуал Hero: **еда по умолчанию**; исключения — иллюстрация/иконка |
| 5 | ПланАм layout: greeting → hero → CTA → **3 статуса** → ask |
| 6 | Above fold: минимум greeting + hero + CTA + **3 статуса** |
| 7 | 3-секундный тест — **обязательный** критерий приёмки Sprint 1 |
| 8 | Не CRM, не dashboard, не AI-chat-tab |
| 9 | Image fallback **same size** — без layout shift |
| 10 | 5 tabs на iPhone SE **без truncate** при 10px labels |

---

# 3-секундный тест — summary

**Проходит** во всех 6 Hero states при наличии трёх статусных строк.

Единственный сценарий провала: header + tall hero + отсутствие статусов → **исключён** spec (статусы обязательны, header скрыт на `/`).

---

# Telegram UX — summary

- **5 вкладок** на 320–375px — **да**, с compact padding.
- **Safe areas** — обязательны top (greeting) и bottom (nav).
- **Скрыть:** дублирующий header на `/`, back на tab roots.
- **Риск:** TG header + App header — mitigation P0.

---

# Риски — top 5 для Sprint 1

1. Hero не помещается без скролла на SE  
2. Конфликт логики Hero states  
3. Миграция 4 → 5 tabs + active state `/`  
4. Bottom nav перекрывает контент  
5. Фото / placeholder layout shift  

Полный список: 20 пунктов в [DESIGN_SPEC §7](./PLANAM_V1_SPRINT1_DESIGN_SPEC.md).

---

# Следующий шаг

После согласования этого review:

```text
PLANAM V1 IMPLEMENTATION MASTER — SPRINT 1
```

**Checklist перед кодом:**

- [ ] Product OK: скрыть header на `/`
- [ ] Product OK: shopping-hero thresholds
- [ ] Product OK: compact hero на SE
- [ ] Design spec approved
- [ ] P0 backlog aligned (NAV-01, NAV-02, HOME-*)

---

# Документы validation pass

| Документ | Согласован с spec |
|----------|-------------------|
| FINAL_VISION | ✅ |
| RELEASE_BLUEPRINT | ✅ |
| HOME_STATES | ✅ |
| IMAGE_STRATEGY | ✅ |
| PRODUCT_MASTER | ✅ |

---

*Design Review complete. Pre-implementation validation passed conditionally.*
