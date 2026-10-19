import { describe, expect, it } from "vitest";
import { betLabel, drawdown, pct, sliceEquity, splitAmount, stakeFor } from "./format";

describe("format", () => {
  it("formats signed percentages with a real minus sign", () => {
    expect(pct(0.03).replace(/\s/g, " ")).toBe("+3,0 %");
    expect(pct(-0.112).replace(/\s/g, " ")).toBe("−11,2 %");
    expect(pct(0)).toMatch(/^0,0/);
    expect(pct(-0.0001)).toMatch(/^0,0/); // no "−0,0 %"
  });

  it("splits a bankroll for the hero number", () => {
    const [i, d] = splitAmount(1647.2);
    expect(i.replace(/\s/g, "")).toBe("1647");
    expect(d).toBe(",20€");
  });

  it("rounds stakes to 10 cents of the chosen bankroll", () => {
    expect(stakeFor(0.0116, 1000)).toBe(11.6);
    expect(stakeFor(0.0116, 250)).toBe(2.9);
    expect(stakeFor(0, 1000)).toBe(0);
  });

  it("labels bets", () => {
    expect(betLabel({ side: "home", home: "Lens", away: "PSG" })).toBe("Victoire Lens");
    expect(betLabel({ side: "away", home: "Lens", away: "PSG" })).toBe("Victoire PSG");
    expect(betLabel({ side: "draw", home: "Lens", away: "PSG" })).toBe("Match nul");
  });

  it("slices the equity curve by trailing days", () => {
    const eq = [{ day: "2026-01-01", bankroll: 1000 }, { day: "2026-03-01", bankroll: 1100 }, { day: "2026-03-20", bankroll: 1050 }];
    expect(sliceEquity(eq, 30).map((p) => p.day)).toEqual(["2026-03-01", "2026-03-20"]);
    expect(sliceEquity(eq, null)).toHaveLength(3);
    expect(sliceEquity([], 30)).toEqual([]);
  });

  it("computes the drawdown from the running peak", () => {
    const dd = drawdown([{ day: "a", bankroll: 1000 }, { day: "b", bankroll: 1200 }, { day: "c", bankroll: 900 }]);
    expect(dd.map((d) => d.dd)).toEqual([0, 0, -0.25]);
  });
});
