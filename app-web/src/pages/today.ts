import { attachEquityHover, equityChart } from "../charts";
import { dayKey, eur, fmtDayKey, fmtStamp, odds, pct, sliceEquity, splitAmount, stakeFor, todayKey } from "../format";
import type { Bet, SiteData } from "../types";
import { BANKROLL_KEY, betsTable, bindRows, kpiStrip, savedBankroll } from "./shared";

const RANGES: [string, number | null][] = [["1M", 31], ["3M", 92], ["1A", 366], ["TOUT", null]];

/** Home: track record on top, then the bets recommended on one day (default: the latest). */
export function renderToday(app: HTMLElement, data: SiteData, day?: string) {
  const k = data.kpis;
  const days = [...new Set(data.bets.map((b) => dayKey(b.odds_at)))].sort();
  const current = day && /^\d{4}-\d{2}-\d{2}$/.test(day) ? day : days[days.length - 1] ?? todayKey();
  const [int, dec] = splitAmount(k?.bankroll ?? data.start_bankroll);
  app.innerHTML = `
    <section class="hero">
      <div class="hero-l">
        <div>
          <div class="k">Bankroll · départ ${eur(data.start_bankroll).replace(",00", "")} · ${k ? new Date(k.since).toLocaleDateString("fr-FR", { month: "long", year: "numeric" }) : ""}</div>
          <div class="big num">${int}<span>${dec}</span></div>
          ${k ? `<div class="delta num ${k.return < 0 ? "neg" : ""}">${k.return >= 0 ? "▲" : "▼"} ${pct(k.return)}</div>` : ""}
        </div>
        <p class="note">${k ? `${k.bets} paris réglés. ` : ""}On compare chaque cote à celle de Pinnacle, le bookmaker le plus précis du marché, et on ne joue que quand un bookmaker est en retard sur lui.</p>
      </div>
      <div class="hero-chart">
        <div class="tabs">${RANGES.map(([l], i) => `<button data-range="${i}" class="${i === 3 ? "on" : ""}">${l}</button>`).join("")}</div>
        <div id="eq"></div>
      </div>
    </section>
    ${k ? kpiStrip([
      ["CLV moyen", k.clv === null ? "–" : pct(k.clv), "vs clôture Pinnacle", k.clv !== null && k.clv >= 0 ? "up" : "down"],
      ["Paris", `${k.bets}`, `${Math.round(k.win_rate * 100)} % gagnants`, ""],
      ["ROI / pari", pct(k.roi), `cote moy. ${odds(k.avg_price)}`, k.roi >= 0 ? "" : "down"],
      ["Drawdown max", pct(k.max_drawdown), new Date(k.max_drawdown_day).toLocaleDateString("fr-FR", { month: "long", year: "numeric" }), "down"],
    ]) : ""}
    <section class="sec" id="day">
      <div class="sec-head">
        <h2>Paris du jour</h2>
        <label class="bankroll">Ma bankroll <input id="bk" type="number" min="1" step="10" inputmode="decimal" /> €</label>
      </div>
      <div class="daynav">
        <button id="prev" aria-label="Jour précédent">←</button>
        <label class="daypick"><span id="dayname"></span><input id="daydate" type="date" /></label>
        <button id="next" aria-label="Jour suivant">→</button>
        <span class="k" id="dayinfo"></span>
      </div>
      <div id="bets"></div>
    </section>`;

  const eqBox = app.querySelector<HTMLElement>("#eq")!;
  const drawEq = (i: number) => {
    const eq = sliceEquity(data.equity, RANGES[i][1]);
    eqBox.innerHTML = equityChart(eq, i === 3 ? data.start_bankroll : eq[0]?.bankroll ?? data.start_bankroll);
    attachEquityHover(eqBox, eq);
  };
  app.querySelectorAll<HTMLButtonElement>(".tabs button").forEach((b) => b.addEventListener("click", () => {
    app.querySelectorAll(".tabs button").forEach((x) => x.classList.remove("on"));
    b.classList.add("on");
    drawEq(Number(b.dataset.range));
  }));
  drawEq(3);

  const input = app.querySelector<HTMLInputElement>("#bk")!;
  input.value = String(savedBankroll());
  const prev = days.filter((d) => d < current).pop(), next = days.find((d) => d > current);
  const go = (d?: string) => { if (d) location.hash = `#/jour/${d}`; };
  app.querySelector<HTMLButtonElement>("#prev")!.disabled = !prev;
  app.querySelector<HTMLButtonElement>("#next")!.disabled = !next;
  app.querySelector("#prev")!.addEventListener("click", () => go(prev));
  app.querySelector("#next")!.addEventListener("click", () => go(next));
  const picker = app.querySelector<HTMLInputElement>("#daydate")!;
  picker.value = current; picker.min = days[0] ?? ""; picker.max = todayKey();
  picker.addEventListener("change", () => go(picker.value));
  app.querySelector("#dayname")!.textContent = fmtDayKey(current);

  const bets = data.bets.filter((b) => dayKey(b.odds_at) === current).sort((a, b) => a.kickoff.localeCompare(b.kickoff));
  app.querySelector("#dayinfo")!.innerHTML = dayInfo(bets);
  const drawBets = () => {
    const bankroll = Math.max(0, Number(input.value) || 0);
    localStorage.setItem(BANKROLL_KEY, String(bankroll));
    const box = app.querySelector<HTMLElement>("#bets")!;
    box.innerHTML = bets.length === 0
      ? `<div class="empty">Aucun pari de valeur recommandé ce jour-là. Analyse quotidienne à 14 h 05 (heure de Paris).</div>`
      : betsTable(bets, bankroll, { date: "day" }) + total(bets, bankroll);
    bindRows(box);
  };
  input.addEventListener("input", drawBets);
  drawBets();
  if (day) app.querySelector("#day")!.scrollIntoView();
}

function dayInfo(bets: Bet[]) {
  if (bets.length === 0) return "";
  const first = bets.reduce((a, b) => (a.odds_at < b.odds_at ? a : b));
  return first.published
    ? `<span class="pub">✓ Publié le ${fmtStamp(first.odds_at)}, avant les coups d'envoi</span>`
    : `Cotes relevées le ${fmtStamp(first.odds_at)}`;
}

const total = (bets: Bet[], bankroll: number) => {
  const sum = bets.reduce((s, b) => s + stakeFor(b.stake, bankroll), 0);
  return `<div class="total"><span>${bets.length} pari${bets.length > 1 ? "s" : ""} · total engagé</span><b>${eur(sum)} · ${pct(sum / (bankroll || 1)).replace("+", "")}</b></div>`;
};
