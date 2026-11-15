import { beforeAll, describe, expect, it } from "vitest";
import { setLang } from "../i18n";
beforeAll(() => setLang("fr"));
import { myEquity, roiNote } from "./performance";

describe("roiNote", () => {
  it("flags the per-bet ROI as not meaningful under 500 settled bets", () => {
    expect(roiNote(80).replace(/\s/g, " ")).toBe("non significatif (n = 80)");
    expect(roiNote(499)).toMatch(/^non significatif/);
  });

  it("drops the flag once the sample is large enough", () => {
    expect(roiNote(500)).toBe("mise fixe");
  });
});

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
