/**
 * Lightweight in-memory session cache.
 *
 * Lives in module scope, so it lasts as long as the JS module is alive
 * (i.e. the whole Telegram Mini App session). No persistence to
 * localStorage — initData and Ama balance can rotate between sessions,
 * and we don't want stale snapshots leaking across them.
 *
 * Keys are conventionally namespaced as ``<resource>:<mode|scope>``
 * (e.g. ``menu-overview:family``, ``shopping-list:personal``). Use the
 * ``cacheKey`` helper for stable spellings so invalidation patterns
 * stay accurate.
 *
 * Usage from a hook:
 *
 *   const { data, loading } = useCachedQuery(cacheKey.menuOverview(mode),
 *     () => fetchMenuOverview(initData, mode));
 *
 * Usage from a mutation:
 *
 *   await replaceDish(...);
 *   invalidate("menu-overview");
 *   invalidate("selected-menu");
 *
 * The cache deliberately does NOT track per-user keys because data is
 * scoped per session — a different Telegram user would land in a fresh
 * JS context. If you need per-user safety call ``clearAll`` on auth
 * change.
 */

type CacheEntry<T> = {
  data: T | null;
  inFlight: Promise<T> | null;
};

const store = new Map<string, CacheEntry<unknown>>();

export function getCached<T>(key: string): T | null {
  const entry = store.get(key) as CacheEntry<T> | undefined;
  return entry?.data ?? null;
}

export function setCached<T>(key: string, value: T): void {
  store.set(key, { data: value, inFlight: null });
}

/**
 * Read-through cache: returns cached data if present, otherwise calls
 * ``fetcher`` once (deduped while in-flight) and stores the result.
 */
export async function fetchOrCache<T>(
  key: string,
  fetcher: () => Promise<T>,
): Promise<T> {
  const existing = store.get(key) as CacheEntry<T> | undefined;
  if (existing?.data != null) return existing.data;
  if (existing?.inFlight) return existing.inFlight;
  const promise = (async () => {
    try {
      const data = await fetcher();
      store.set(key, { data, inFlight: null });
      return data;
    } catch (err) {
      store.delete(key);
      throw err;
    }
  })();
  store.set(key, { data: existing?.data ?? null, inFlight: promise });
  return promise;
}

/**
 * Invalidate one or more entries by exact key or by namespace prefix.
 *
 * - ``invalidate("menu-overview")`` drops all entries whose key is
 *   exactly ``menu-overview`` or starts with ``menu-overview:``.
 * - ``invalidate(/^menu-/)`` drops everything matching the regexp.
 */
export function invalidate(pattern: string | RegExp): void {
  const keys = Array.from(store.keys());
  if (typeof pattern === "string") {
    for (const key of keys) {
      if (key === pattern || key.startsWith(`${pattern}:`)) {
        store.delete(key);
      }
    }
    return;
  }
  for (const key of keys) {
    if (pattern.test(key)) store.delete(key);
  }
}

export function clearAll(): void {
  store.clear();
}

/** Stable cache-key spellings shared between readers and invalidators. */
export const cacheKey = {
  selectedMenu: (mode: string) => `selected-menu:${mode}`,
  menuOverview: (mode: string) => `menu-overview:${mode}`,
  shoppingList: (mode: string) => `shopping-list:${mode}`,
  pantry: (mode: string) => `pantry:${mode}`,
  nutritionProfile: () => `nutrition-profile`,
  progressOverview: (mode: string) => `progress-overview:${mode}`,
  careSettings: (mode: string) => `care-settings:${mode}`,
  notificationSettings: () => `notification-settings`,
} as const;
