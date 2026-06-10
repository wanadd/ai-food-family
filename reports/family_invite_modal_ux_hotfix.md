# Family Invite Modal UX Hotfix

**Date:** 2026-06-10  
**Scope:** Frontend only — `InviteSheet` + `FamilyDashboard`  
**Backend:** не менялся

---

## Проблема

После починки bot/invite flow приглашение работало функционально, но UX ломался:

1. Пользователь нажимал **«Отправить ссылку-приглашение»**
2. Ссылка создавалась на backend
3. Модалка **сразу закрывалась** (`onSuccess` → `setShowInviteSheet(false)`)
4. Share-кнопка **«Отправить приглашение в Telegram»** не успевала отобразиться
5. На dashboard показывалось **«Приглашение отправлено»** до реальной отправки
6. При повторном открытии модалки внутренний `lastInvite` сохранялся → share-кнопка появлялась только со **второго раза**

---

## Root cause

```tsx
// FamilyDashboard.tsx (до fix)
onSuccess={(invite) => {
  setLastInvite(invite);
  setShowInviteSheet(false); // ← закрывало sheet до share UI
}}
```

```tsx
// InviteSheet.tsx (до fix)
setLastInvite(invite);
onSuccess(invite); // ← вызывался сразу после create, не после share
```

Два конфликтующих state: внутренний `lastInvite` в sheet и `lastInvite` в dashboard, плюс преждевременное закрытие.

---

## Решение

### 1. Явные шаги flow (`InviteSheet.tsx`)

| Step | UI |
|------|-----|
| `menu` | Выбор: номер / ссылка |
| `phone` | Ввод номера |
| `loading` | «Готовим приглашение…» |
| `share` | Ссылка + **«Отправить приглашение в Telegram»** |
| `sent` | Success + «Готово» |

### 2. `onSuccess` только после реального завершения

- **Link invite:** `onSuccess` вызывается при нажатии «Отправить приглашение в Telegram» (после `window.open(share_url)`)
- **Phone invite + bot notified:** `onSuccess` сразу после API (человек уже получил push в боте)
- **Phone invite без bot:** переход на step `share`, как у link invite

### 3. Модалка не закрывается сама

- Убран `setShowInviteSheet(false)` из `onSuccess` в `FamilyDashboard`
- Закрытие только по «Закрыть» / «Готово» (на step `sent`)
- Во время `loading` кнопка «Закрыть» disabled

### 4. Reset state при открытии

```tsx
useEffect(() => {
  if (open) {
    setStep("menu");
    setPhone("");
    setError(null);
    setLastInvite(null);
  }
}, [open]);
```

Повторное открытие — чистый flow, без «призрака» прошлого invite.

### 5. Success banner на dashboard

Показывается **только после `onSuccess`** (т.е. после share или bot-notify):

- Bot-notified: «Приглашение отправлено — ожидаем ответ в Telegram»
- Link share: «Ссылка отправлена — ожидаем, когда человек примет приглашение»

### 6. Dark/light

Добавлены `dark:` классы для overlay, surface, текста, error, share block.

---

## Изменённые файлы

| File | Change |
|------|--------|
| `apps/web/components/family/InviteSheet.tsx` | Step machine, loading, share-first flow |
| `apps/web/components/family/FamilyDashboard.tsx` | Не закрывать sheet в onSuccess; уточнён banner text |

---

## Сценарии QA

| Сценарий | Ожидание |
|----------|----------|
| Link invite, первый клик | Loading → share CTA без закрытия модалки |
| Share в Telegram | Открывается share URL → step `sent` → «Готово» |
| Phone + bot notify | Loading → step `sent` с текстом про бот |
| Phone без bot | Loading → share CTA |
| Повторное открытие | Чистое меню (menu step) |
| AddPerson → Invite Telegram | AddPerson закрывается, Invite открывается с menu |
| Dark theme | Читаемый текст и границы |

---

## Backend

Не изменялся. Используются существующие:

- `POST /families/{id}/invites/link`
- `POST /families/{id}/invite-by-phone`

---

## Test result

- `npx vitest run` — без изменений в тестах invite (компонент не покрыт unit-тестами)
- Manual QA в Telegram Mini App — рекомендуется

---

## Критерий готовности

- [x] Share-кнопка появляется после первого действия (без второго клика)
- [x] Модалка не закрывается при создании invite
- [x] Success state только после share / bot notify
- [x] Backend не тронут
- [x] Predictable step flow
