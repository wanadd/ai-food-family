# Frontend Architecture V2

Next.js PLANAM AppShell with server/client boundaries and versioned API client. Navigation: Главная, Меню, Покупки, Профиль; Здоровье is a separate access point. Shopping and Pantry are distinct views but share household context. Personal mode works without family setup. Planning uses one client-neutral UI contract with explicit `PERSON` and `HOUSEHOLD` scope; it never creates or requires an implicit household for personal mode.

Planning reads and commands carry the canonical Plan owner scope. Person scope is authorized against the resolved CorePerson; household scope is authorized against the resolved Household membership/capability. The UI preserves explicit empty, unknown, blocked, stale-conflict and revision states without deciding authorization or safety.

AppShell consumes a `PlatformAdapter` capability snapshot for auth bootstrap, viewport, safe area, fullscreen, back, theme, deep links, share, camera/file upload and notifications. Business UI components do not import Telegram SDK or inspect client type. Mobile layout uses dynamic viewport and safe-area insets, keyboard-aware bottom navigation, bottom sheets and modal/back semantics; no core flow relies on fixed plain `100vh`. Telegram is the first adapter; browser fallback is usable; MAX/native adapters are designed but not implemented.

Screens consume contracts, never tables or hidden safety assumptions. Loading, empty, unknown, blocked, error and manual-override states are explicit. UI cannot decide authorization or safety. Existing brand/UX documents remain visual authority; current components are donor knowledge, not target architecture. Mobile Telegram constraints and desktop Telegram surfaces are both tested.
