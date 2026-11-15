import { beforeAll, describe, expect, it } from "vitest";
import { setLang } from "../i18n";
beforeAll(() => setLang("fr"));
import type { Bet, SiteData } from "../types";
import { ballCallouts, daySummary } from "./today";

const bet = (o: Partial<Bet>): Bet => ({
  id: "x", kickoff: "2026-10-20T19:00:00", odds_at: "2026-10-19T10:05:00", league_key: null, link: null,
  probs: { home: 0.5, draw: 0.3, away: 0.2 }, home: "A", away: "B", league: "L", side: "home", price: 2, fair_price: 1.9,
  edge: 0.05, stake: 0.02, book: "onexbet", status: "upcoming", score: null, gain: 0, clv: null, ...o,
});
const text = (html: string) => html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");

describe("daySummary", () => {
  it("sums the stakes and the maximum loss for the visitor's bankroll", () => {
    const t = text(daySummary([bet({}), bet({ price: 3, stake: 0.01 })], 1000));
    expect(t).toMatch(/À engager 30,00 € 2 paris · 3,0 % de la bankroll/);
    expect(t).toMatch(/Perte maximale −30,00 € si tous les paris sont perdus/);
    expect(t).toMatch(/Résultat – aucun match joué/);
  });

  it("never projects a gain: no theoretical edge, no all-win amount", () => {
    const t = text(daySummary([bet({}), bet({ price: 3, stake: 0.01 })], 1000));
    expect(t).not.toMatch(/Écart théorique|Fourchette|tout gagné|Gain espéré|Si tout passe|long terme/);
    expect(t).not.toMatch(/\+1,50 €|\+40,00 €/); // 20*0.05 + 10*0.05 edge, 20*1 + 10*2 all-win
    expect(t).not.toMatch(/\+/);
  });

  it("reports the settled result", () => {
    const t = text(daySummary([bet({ status: "won", gain: 0.02 }), bet({ status: "lost", gain: -0.02 }), bet({})], 500));
    expect(t).toMatch(/Résultat \+0,00 € 2\/3 matchs joués · 1 gagné/);
  });
});

describe("ballCallouts", () => {
  const kpis = { bankroll: 12900, return: 0.29, bets: 80, win_rate: 0.5875, roi: 0.27, avg_price: 2.4, avg_stake: 0.02, avg_edge: 0.036, clv: 0.024, clv_coverage: 1, max_drawdown: -0.034, max_drawdown_day: "2026-10-30", since: "2026-10-19" };
  const site = (k: object | null) => ({ kpis: k, bets: [], equity: [], start_bankroll: 10000 } as unknown as SiteData);

  it("pins neutral measurements: settled bets, CLV and bookmaker count (first and last kept on phones)", () => {
    const cs = ballCallouts(site(kpis), 28);
    expect(cs.map((c) => c.value)).toEqual(["80", "+2,4 %", "28"]);
    expect(cs.map((c) => c.label)).toEqual(["paris réglés", "CLV moyen", "bookmakers retenus"]);
    expect(cs[0]).toMatchObject({ valueFirst: true, tone: "accent" });
    expect(cs[2]).toMatchObject({ valueFirst: true });
  });

  it("never pins the return or the bankroll", () => {
    const values = ballCallouts(site(kpis), 28).map((c) => c.value);
    expect(values).not.toContain("+29,0 %");
    expect(values.join(" ")).not.toMatch(/€/);
  });

  it("drops what the payload lacks", () => {
    expect(ballCallouts(site({ ...kpis, clv: null, bets: 1 }), 1).map((c) => c.label)).toEqual(["pari réglé", "bookmaker retenu"]);
    expect(ballCallouts(site(null), 0)).toEqual([]);
  });
});
