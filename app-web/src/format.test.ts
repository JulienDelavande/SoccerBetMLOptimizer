import { beforeAll, describe, expect, it } from "vitest";
import { setLang } from "./i18n";
beforeAll(() => setLang("fr"));
import { betLabel, drawdown, isoUtc, pct, sliceEquity, splitAmount, stakeFor } from "./format";

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

import { dayKey } from "./format";
describe("dayKey", () => {
  it("uses Paris time for the recommendation day", () => {
    expect(dayKey("2026-10-19T21:30:00")).toBe("2026-10-19"); // 23:30 in Paris
    expect(dayKey("2026-10-19T22:30:00")).toBe("2026-10-20"); // 00:30 in Paris
  });
});

import { bookName } from "./format";
describe("bookName", () => {
  it("keeps curated names and prettifies raw keys", () => {
    expect(bookName("onexbet")).toBe("1xBet");
    expect(bookName("unibet_se")).toBe("Unibet (SE)");
    expect(bookName("marathonbet")).toBe("Marathonbet");
  });

  it("uses the brands' own spelling, with the region kept", () => {
    expect(bookName("mybookieag")).toBe("MyBookie");
    expect(bookName("betonlineag")).toBe("BetOnline");
    expect(bookName("gtbets")).toBe("GTbets");
    expect(bookName("leovegas")).toBe("LeoVegas");
    expect(bookName("leovegas_se")).toBe("LeoVegas (SE)");
    expect(bookName("paddypower")).toBe("Paddy Power");
    expect(bookName("betvictor")).toBe("BetVictor");
    expect(bookName("skybet")).toBe("Sky Bet");
    expect(bookName("nordicbet")).toBe("Nordic Bet");
    expect(bookName("livescorebet_eu")).toBe("LiveScore Bet (EU)");
    expect(bookName("betfair_ex_uk")).toBe("Betfair (UK)");
  });
});

import { axisNum, int, prevDayKey } from "./format";
describe("numbers and days", () => {
  it("groups counts and compacts large axis values", () => {
    expect(int(12873).replace(/\s/g, " ")).toBe("12 873");
    expect(axisNum(1650)).toBe("1650".replace(/^(\d)(\d{3})$/, "$1\u202f$2"));
    expect(axisNum(1234567)).toMatch(/^1,2\s?M/);
  });

  it("steps back one calendar day, across months and DST", () => {
    expect(prevDayKey("2026-11-02")).toBe("2026-11-01");
    expect(prevDayKey("2026-03-01")).toBe("2026-02-28");
    expect(prevDayKey("2026-03-30")).toBe("2026-03-29");
  });
});

describe("isoUtc", () => {
  // Safari rejects "2024-09-23Z" (Chrome accepts it): every naive backend value must become strict ISO 8601.
  it("turns date-only keys into midnight UTC", () => expect(isoUtc("2024-09-23")).toBe("2024-09-23T00:00:00Z"));
  it("marks naive timestamps as UTC", () => expect(isoUtc("2026-11-15T14:49:21")).toBe("2026-11-15T14:49:21Z"));
  it("accepts a space separator", () => expect(isoUtc("2026-11-15 14:49:21")).toBe("2026-11-15T14:49:21Z"));
  it("keeps explicit zones", () => {
    expect(isoUtc("2026-11-15T14:49:21Z")).toBe("2026-11-15T14:49:21Z");
    expect(isoUtc("2026-11-15T14:49:21+01:00")).toBe("2026-11-15T14:49:21+01:00");
  });
});
