// Match detail requests, shared between prefetch (hover / touch / idle on Today) and the match page,
// so opening a ticket usually finds its data already loaded. Failed requests are dropped to allow a retry.
import type { MatchDetail } from "./types";

const TTL_MS = 5 * 60_000;  // same freshness as the backend cache
const cache = new Map<string, { p: Promise<MatchDetail>; at: number }>();

export function loadMatch(id: string, now = Date.now()): Promise<MatchDetail> {
  const hit = cache.get(id);
  let p = hit && now - hit.at < TTL_MS ? hit.p : undefined;
  if (!p) {
    p = fetch(`/api/site/match/${encodeURIComponent(id)}`)
      .then((res) => { if (!res.ok) throw new Error(`API ${res.status}`); return res.json() as Promise<MatchDetail>; });
    p.catch(() => cache.delete(id));
    cache.set(id, { p, at: now });
  }
  return p;
}

/** Warm the cache without surfacing errors (the match page will retry and report). */
export const prefetchMatch = (id: string) => { loadMatch(id).catch(() => {}); };

export const matchIdFromHref = (href: string | null) => href?.match(/#\/match\/([\w-]+)$/)?.[1] ?? null;

export const clearMatchCache = () => cache.clear();
