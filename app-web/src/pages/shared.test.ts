import { beforeAll, describe, expect, it } from "vitest";
import { setLang } from "../i18n";
beforeAll(() => setLang("fr"));
import type { Bet } from "../types";
import { betTickets, kpiStrip, marquee } from "./shared";
import { equityChart } from "../charts";

const bet = (o: Partial<Bet>): Bet => ({
  id: "abc123", kickoff: "2026-11-22T14:00:00", odds_at: "2026-11-15T11:05:00", published: true, league_key: "soccer_italy_serie_a",
  link: "https://example.test/bet", probs: { home: 0.35, draw: 0.28, away: 0.37 }, home: "Sassuolo", away: "Genoa", league: "Serie A",
  side: "away", price: 2.85, fair_price: 2.74, edge: 0.041, stake: 0.0111, book: "unibet_se", status: "upcoming", score: null, gain: 0, clv: null, ...o,
});
const text = (html: string) => html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");

describe("betTickets", () => {
  it("renders a ticket linking to the match with price, stake and edge", () => {
    const html = betTickets([bet({})], 1000);
    expect(html).toContain('href="#/match/abc123"');
    const t = text(html);
    expect(t).toMatch(/Victoire Genoa/);
    expect(t).toMatch(/2\.85/);
    expect(t).toMatch(/juste prix 2\.74/);
    expect(t).toMatch(/11,10 €/);
    expect(t).toMatch(/\+4,1 %/);
    expect(t).toMatch(/Unibet \(SE\)/);           // raw book key is prettified
    expect(html).not.toContain("placed-btn");      // signed out: no "j'ai joué"
  });

  it("shows the settled score and signed gain", () => {
    const t = text(betTickets([bet({ status: "lost", score: "2-0", gain: -0.0085 })], 1000));
    expect(t).toMatch(/2-0/);
    expect(t).toMatch(/−0,85 %/);
  });
});

describe("kpiStrip", () => {
  it("counts up by default but never for opted-out values (odds)", () => {
    const html = kpiStrip([["Paris", "421", "", ""], ["Cote moyenne", "2.48", "", "", false]]);
    expect(html.match(/data-count/g)).toHaveLength(1);
  });
});

describe("marquee", () => {
  it("duplicates the run for the loop and hides the copy from assistive tech", () => {
    const html = marquee(["A", "B"]);
    expect(html.match(/class="mq-run"/g)).toHaveLength(2);
    expect(html).toContain('class="mq-run" aria-hidden="true"');
    expect(marquee([])).toBe("");
  });
});

describe("equityChart callouts", () => {
  it("pins the record high and the worst trough", () => {
    const eq = [1000, 1100, 1300, 1050, 980, 1010, 1200, 1250, 1240, 1260, 1270, 1280].map((b, i) =>
      ({ day: `2026-01-${String(i + 1).padStart(2, "0")}`, bankroll: b }));
    const t = text(equityChart(eq, 1000));
    expect(t).toMatch(/Record 1\s300 €/);
    expect(t).toMatch(/Pire creux −24,6 %/);
  });

  it("skips the trough callout when the drawdown is negligible", () => {
    const eq = [1000, 1010, 1020, 1030].map((b, i) => ({ day: `2026-01-0${i + 1}`, bankroll: b }));
    expect(equityChart(eq, 1000)).not.toContain("Pire creux");
  });
});
