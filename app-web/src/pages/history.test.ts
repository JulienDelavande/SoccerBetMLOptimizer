import { beforeAll, describe, expect, it } from "vitest";
import { setLang } from "../i18n";
beforeAll(() => setLang("fr"));
import type { MyBet } from "../api";
import { myBetsTable, myResult, sortMyBets } from "./history";

const mb = (o: Partial<MyBet>): MyBet => ({
  match_id: "m1", side: "home", recommended_price: 2.1, placed_price: null, stake: 25, status: "won", settled_gain: 27.5,
  created_at: "2026-11-01T10:00:00", league: "Ligue 1", home_team: "Lens", away_team: "PSG", commence_time: "2026-11-02T20:00:00", ...o,
});
const text = (html: string) => html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");

describe("my history", () => {
  it("formats results: signed gains with tone, void as Annulé, placed as pending", () => {
    expect(myResult(mb({}))).toEqual({ text: "+27,50 €", tone: "up" });
    expect(myResult(mb({ status: "lost", settled_gain: -25 }))).toEqual({ text: "−25,00 €", tone: "down" });
    expect(myResult(mb({ status: "void", settled_gain: null })).text).toBe("Annulé");
    expect(myResult(mb({ status: "placed", settled_gain: null })).text).toBe("en attente");
  });

  it("sorts by kick-off, newest first, undated last", () => {
    const out = sortMyBets([mb({ match_id: "a", commence_time: "2026-11-01T10:00:00" }), mb({ match_id: "b", commence_time: null }),
      mb({ match_id: "c", commence_time: "2026-11-09T10:00:00" })]);
    expect(out.map((b) => b.match_id)).toEqual(["c", "a", "b"]);
  });

  it("prints odds with two decimals and dashes for missing teams", () => {
    const t = text(myBetsTable([mb({ placed_price: 2.1333333 }), mb({ match_id: "x", home_team: null, away_team: null, commence_time: null, stake: null, recommended_price: null, status: "void", settled_gain: null })]));
    expect(t).toMatch(/2\.13/);
    expect(t).not.toMatch(/2\.1333/);
    expect(t).toMatch(/– – –/);
    expect(t).not.toMatch(/null|undefined/);
  });
});
