import { beforeAll, describe, expect, it } from "vitest";
import { setLang } from "../i18n";
beforeAll(() => setLang("fr"));
import type { Bet, SiteData } from "../types";
import { ballCallouts, daySummary } from "./today";

const bet = (o: Partial<Bet>): Bet => ({
  id: "x", kickoff: "2026-10-20T19:00:00", odds_at: "2026-10-19T10:05:00", published: true, league_key: null, link: null,
  probs: { home: 0.5, draw: 0.3, away: 0.2 }, home: "A", away: "B", league: "L", side: "home", price: 2, fair_price: 1.9,
  edge: 0.05, stake: 0.02, book: "onexbet", status: "upcoming", score: null, gain: 0, clv: null, ...o,
});
const text = (html: string) => html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");

describe("daySummary", () => {
  it("sums stakes, expected and maximum gain for the bankroll", () => {
    const t = text(daySummary([bet({}), bet({ price: 3, stake: 0.01 })], 1000));
    expect(t).toMatch(/À engager 30,00 €/);
    expect(t).toMatch(/Gain espéré \+1,50 €/); // 20*0.05 + 10*0.05
    expect(t).toMatch(/Si tout passe \+40,00 €/); // 20*1 + 10*2
    expect(t).toMatch(/aucun match joué/);
  });

  it("reports the settled result", () => {
    const t = text(daySummary([bet({ status: "won", gain: 0.02 }), bet({ status: "lost", gain: -0.02 }), bet({})], 500));
    expect(t).toMatch(/Résultat \+0,00 € 2\/3 matchs joués · 1 gagné/);
  });
});

describe("ballCallouts", () => {
  const kpis = { bankroll: 2000, return: 1, bets: 400, win_rate: 0.5, roi: 0.1, avg_price: 2.4, avg_stake: 0.02, avg_edge: 0.036, clv: 0.03, clv_coverage: 1, max_drawdown: -0.1, max_drawdown_day: "2026-10-30", since: "2024-09-24" };
  const site = (k: object | null) => ({ kpis: k, bets: [], equity: [], start_bankroll: 1000 } as unknown as SiteData);

  it("pins live CLV, edge and bookmaker count, CLV first and books last (the two kept on phones)", () => {
    const cs = ballCallouts(site(kpis), 28);
    expect(cs.map((c) => c.value)).toEqual(["+3,0 %", "+3,6 %", "28"]);
    expect(cs[0].label).toBe("CLV moyen");
    expect(cs[2]).toMatchObject({ label: "bookmakers comparés", valueFirst: true });
  });

  it("drops what the payload lacks", () => {
    expect(ballCallouts(site({ ...kpis, clv: null }), 1).map((c) => c.label)).toEqual(["Écart vs juste prix Pinnacle", "bookmaker comparé"]);
    expect(ballCallouts(site(null), 0)).toEqual([]);
  });
});
