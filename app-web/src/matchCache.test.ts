import { afterEach, describe, expect, it, vi } from "vitest";
import { clearMatchCache, loadMatch, matchIdFromHref, prefetchMatch } from "./matchCache";

const ok = (body: unknown) => Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));

describe("match detail cache", () => {
  afterEach(() => { clearMatchCache(); vi.unstubAllGlobals(); });

  it("fetches a match once, even when prefetched then opened", async () => {
    const f = vi.fn(() => ok({ home: "A" }));
    vi.stubGlobal("fetch", f);
    prefetchMatch("m1");
    const m = await loadMatch("m1");
    expect(m).toEqual({ home: "A" });
    expect(f).toHaveBeenCalledTimes(1);
  });

  it("drops failed requests so the next open retries", async () => {
    const f = vi.fn().mockResolvedValueOnce(new Response("", { status: 500 })).mockImplementation(() => ok({ home: "B" }));
    vi.stubGlobal("fetch", f);
    await expect(loadMatch("m2")).rejects.toThrow("API 500");
    await expect(loadMatch("m2")).resolves.toEqual({ home: "B" });
    expect(f).toHaveBeenCalledTimes(2);
  });

  it("refetches after five minutes", async () => {
    const f = vi.fn(() => ok({ home: "C" }));
    vi.stubGlobal("fetch", f);
    await loadMatch("m3", 0);
    await loadMatch("m3", 60_000);
    await loadMatch("m3", 6 * 60_000);
    expect(f).toHaveBeenCalledTimes(2);
  });

  it("reads the match id from a ticket href", () => {
    expect(matchIdFromHref("#/match/abc123")).toBe("abc123");
    expect(matchIdFromHref("#/performance")).toBeNull();
  });
});
