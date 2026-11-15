import { beforeAll, describe, expect, it } from "vitest";
import { setLang } from "../i18n";
beforeAll(() => setLang("fr"));
import type { SiteData } from "../types";
import { bankrollNote, recordFacts, recordNotice } from "./shared";
import { groupTable, monthlyGrid, timeTicks } from "../charts";
import { periodLabel, usefulRanges } from "../format";

const text = (html: string) => html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").replace(/[  ]/g, " ");
const kpis = { bets: 80 } as SiteData["kpis"];
const data = { live_since: "2026-10-19T00:00:00", generated_at: "2026-11-15T12:00:00", kpis };

describe("track record facts", () => {
  it("states the start date, the honest length and the settled count", () => {
    expect(recordFacts(data)).toEqual({ since: "19 octobre 2026", period: "4 semaines", settled: 80 });
  });

  it("labels short, medium and long periods", () => {
    expect(periodLabel("2026-10-19T00:00:00", "2026-10-19T20:00:00")).toBe("1 jour");
    expect(periodLabel("2026-10-19T00:00:00", "2026-10-29T00:00:00")).toBe("10 jours");
    expect(periodLabel("2026-10-19T00:00:00", "2026-11-15T12:00:00")).toBe("4 semaines");
    expect(periodLabel("2026-10-19T00:00:00", "2027-04-19T00:00:00")).toBe("6 mois");
  });
});

describe("recordNotice", () => {
  const notice = () => text(recordNotice(data));
  it("says past results, short sample and high variance with the real numbers", () => {
    const t = notice();
    expect(t).toMatch(/Résultats passés : aucune garantie pour la suite/);
    expect(t).toMatch(/depuis le 19 octobre 2026 : 4 semaines, 80 paris réglés/);
    expect(t).toMatch(/échantillon court et la variance est élevée/);
  });
  it("frames the site as information, with responsible-gambling lines", () => {
    const t = notice();
    expect(t).toMatch(/pas un conseil de pari adapté à votre situation/);
    expect(t).toMatch(/Ne misez que ce que vous pouvez vous permettre de perdre/);
    expect(t).toMatch(/moins de 18 ans/);
    expect(t).toMatch(/Joueurs Info Service : 09 74 75 13 13 \(appel non surtaxé\)/);
    expect(recordNotice(data)).toContain('href="tel:+33974751313"');
  });
  it("explains the fictitious bankroll", () => {
    expect(text(bankrollNote(10000))).toMatch(/10 000 € fictifs au départ.*demi-Kelly.*Les résultats réels diffèrent/);
  });
});

describe("short history charts", () => {
  const eq = (days: string[]) => days.map((day, i) => ({ day, bankroll: 10000 + i * 100 }));
  const RANGES: [string, number | null][] = [["1M", 31], ["3M", 92], ["1Y", 366], ["ALL", null]];

  it("hides range tabs that would show the whole curve anyway", () => {
    expect(usefulRanges(RANGES, eq(["2026-10-18", "2026-11-15"])).map(([l]) => l)).toEqual(["ALL"]);
    expect(usefulRanges(RANGES, eq(["2026-10-18", "2027-01-05"])).map(([l]) => l)).toEqual(["1M", "ALL"]);
    expect(usefulRanges(RANGES, eq(["2024-09-23", "2026-11-15"])).map(([l]) => l)).toEqual(["1M", "3M", "1Y", "ALL"]);
    expect(usefulRanges(RANGES, [])).toEqual([["ALL", null]]);
  });

  it("uses weekly ticks for a few weeks of data and months beyond", () => {
    const d = (s: string) => Date.parse(`${s}T00:00:00Z`);
    const weekly = timeTicks(d("2026-10-18"), d("2026-11-15"), 680);
    expect(weekly.map((k) => new Date(k.t).toISOString().slice(0, 10))).toEqual(["2026-10-19", "2026-10-26", "2026-11-02", "2026-11-09"]);
    expect(weekly[0].label).toBe("19 oct.");
    const monthly = timeTicks(d("2026-01-10"), d("2026-11-15"), 680);
    expect(monthly.length).toBeGreaterThanOrEqual(4);
    expect(new Date(monthly[0].t).getUTCDate()).toBe(1);
  });

  it("shows a few months as tiles, marking the partial first month and the month in progress", () => {
    const t = text(monthlyGrid([{ month: "2026-10", return: 0.071 }, { month: "2026-11", return: 0.207 }],
      { since: "2026-10-19", now: "2026-11-15T12:00:00" }));
    expect(t).toMatch(/octobre 2026 depuis le 19 oct\. \+7,1 %/);
    expect(t).toMatch(/novembre 2026 en cours \+20,7 %/);
    expect(t).not.toMatch(/Année/);
  });

  it("keeps the year grid for a long history", () => {
    const months = Array.from({ length: 8 }, (_, i) => ({ month: `2026-0${i + 1}`, return: 0.01 }));
    expect(monthlyGrid(months)).toContain("mg-row");
  });

  it("counts the per-league result on the fictitious base", () => {
    const t = text(groupTable([{ name: "LaLiga", bets: 3, win_rate: 0.5, roi: 0.1, clv: 0.02, profit: 1234.4 }], "Championnat", 10000));
    expect(t).toMatch(/Résultat sur 10 000 € fictifs/);
    expect(t).toMatch(/\+1 234 €/);
  });
});

// Public copy must read as information, never as a promise to win (Code de la consommation
// L121-4 15° and L121-2). Scan every source string, French and English.
describe("copy compliance", () => {
  const sources = import.meta.glob(["../**/*.ts", "!../**/*.test.ts"], { query: "?raw", import: "default", eager: true }) as Record<string, string>;
  const all = Object.values(sources).join("\n");
  const banned = [
    /gagner\b/i, /\bgagnez\b/i, /battre les bookmakers/i, /beat the bookmakers/i, /gains? assurés?/i, /\brentab/i, /\bprofitable\b/i,
    /garantis\b/i, /guaranteed (profit|return|gain)/i, /\bon achète moins cher\b/i, /we buy below/i, /gains? à long terme/i,
    /long-run profit/i, /gain espéré/i, /expected gain/i, /historique.{0,20}rejoué/i, /replayed (bets|history)/i, /history before/i,
    /de gagnants/i, /% of winners/i,
  ];
  for (const re of banned) it(`never says ${re}`, () => expect(all).not.toMatch(re));
});
