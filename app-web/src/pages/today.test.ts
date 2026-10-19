import { describe, expect, it } from "vitest";
import type { Bet } from "../types";
import { daySummary } from "./today";

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
