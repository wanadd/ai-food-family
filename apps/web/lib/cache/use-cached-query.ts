import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchOrCache,
  getCached,
  setCached,
} from "@/lib/cache/session-cache";

type UseCachedQueryResult<T> = {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<T | null>;
};

/**
 * Read-through hook for the session cache.
 *
 * - If the cache has data for ``key``, ``data`` is returned synchronously
 *   on the very first render and ``loading`` is ``false``. This is the
 *   key win for "instant" repeat tab visits.
 * - If the cache is cold, ``fetcher`` is called once, the result is
 *   stored, and any concurrent callers with the same key share the
 *   in-flight promise.
 * - When ``key`` changes (e.g. mode switches personal → family) the
 *   hook tries the cache for the new key first, then fetches if needed.
 * - ``refresh()`` bypasses the cache and re-fetches.
 * - Pass ``null`` as ``key`` to disable (e.g. when initData not ready).
 *
 * Caller is responsible for invalidating related cache keys after
 * mutations via the ``invalidate`` helper from session-cache.
 */
export function useCachedQuery<T>(
  key: string | null,
  fetcher: () => Promise<T>,
): UseCachedQueryResult<T> {
  const initial = key ? getCached<T>(key) : null;
  const [data, setData] = useState<T | null>(initial);
  const [loading, setLoading] = useState<boolean>(Boolean(key) && initial == null);
  const [error, setError] = useState<Error | null>(null);

  // We intentionally do not include ``fetcher`` in the effect deps so
  // that callers can pass an inline arrow without re-firing the fetch
  // on every render. The latest fetcher is captured via ref.
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    if (!key) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    const cached = getCached<T>(key);
    if (cached != null) {
      setData(cached);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchOrCache<T>(key, () => fetcherRef.current())
      .then((result) => {
        if (cancelled) return;
        setData(result);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err : new Error("Не удалось загрузить"));
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [key]);

  const refresh = useCallback(async (): Promise<T | null> => {
    if (!key) return null;
    setLoading(true);
    setError(null);
    try {
      const fresh = await fetcherRef.current();
      setCached(key, fresh);
      setData(fresh);
      return fresh;
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Не удалось обновить"));
      return null;
    } finally {
      setLoading(false);
    }
  }, [key]);

  return { data, loading, error, refresh };
}
