import { describe, expect, it } from "vitest";
import { myEquity } from "./performance";

describe("myEquity", () => {
  it("seeds the curve the day before the first settled bet", () => {
    const eq = myEquity(2500, [{ t: "2026-11-02T20:00:00", delta: 30 }, { t: "2026-11-05T20:00:00", delta: -25 }]);
    expect(eq).toEqual([
      { day: "2026-11-01", bankroll: 2500 },
      { day: "2026-11-02", bankroll: 2530 },
      { day: "2026-11-05", bankroll: 2475 },
    ]);
    expect(eq.every((p) => Number.isFinite(new Date(p.day).getTime()))).toBe(true);
  });

  it("is empty without settled bets", () => {
    expect(myEquity(1000, [])).toEqual([]);
  });
});
