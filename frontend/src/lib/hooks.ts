/**
 * Custom React hooks for data fetching (CONV-51).
 *
 * Simple SWR-like pattern using useEffect + useState.
 * Keeps the dashboard dependency-free (no SWR/React Query).
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface UseQueryResult<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  refetch: () => void;
}

const cache = new Map<string, { data: unknown; ts: number }>();
const CACHE_TTL = 30_000; // 30s
const MAX_CACHE_SIZE = 100;

function pruneCache() {
  if (cache.size <= MAX_CACHE_SIZE) return;
  const entries = [...cache.entries()].sort((a, b) => a[1].ts - b[1].ts);
  const toRemove = entries.slice(0, entries.length - MAX_CACHE_SIZE);
  for (const [key] of toRemove) cache.delete(key);
}

export function useQuery<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = [],
  cacheKey?: string
): UseQueryResult<T> {
  const [data, setData] = useState<T | null>(() => {
    if (cacheKey) {
      const cached = cache.get(cacheKey);
      if (cached && Date.now() - cached.ts < CACHE_TTL) return cached.data as T;
    }
    return null;
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(data === null);
  const [tick, setTick] = useState(0);
  const fetcherRef = useRef(fetcher);

  // Always keep the latest fetcher reference
  useEffect(() => {
    fetcherRef.current = fetcher;
  });

  const refetch = useCallback(() => setTick((t) => t + 1), []);

  const depsKey = JSON.stringify(deps);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetcherRef.current()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
          if (cacheKey) {
            cache.set(cacheKey, { data: result, ts: Date.now() });
            pruneCache();
          }
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Unknown error");
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick, depsKey, cacheKey]);

  return { data, error, loading, refetch };
}
