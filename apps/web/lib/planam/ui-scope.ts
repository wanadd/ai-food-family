/**
 * PLANAM 2026 theme scope — applied on `html` when the 2026 shell is active.
 * @see docs/PLANAM_DESIGN_SYSTEM_2026.md §1.3–1.4
 */

export const PLANAM_UI_2026_ATTR = "data-planam-ui";
export const PLANAM_UI_2026_VALUE = "2026";

export function isPlanamUi2026ScopeEnabled(): boolean {
  return process.env.NEXT_PUBLIC_PLANAM_UI_2026 === "true";
}

export function applyPlanamUi2026Scope(root: HTMLElement): void {
  root.setAttribute(PLANAM_UI_2026_ATTR, PLANAM_UI_2026_VALUE);
}

export function clearPlanamUi2026Scope(root: HTMLElement): void {
  if (root.getAttribute(PLANAM_UI_2026_ATTR) === PLANAM_UI_2026_VALUE) {
    root.removeAttribute(PLANAM_UI_2026_ATTR);
  }
}
