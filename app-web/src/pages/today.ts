import { attachEquityHover, equityChart } from "../charts";
import { betLabel, bookName, esc, eur, fmtDay, fmtTime, odds, pct, sliceEquity, splitAmount, stakeFor } from "../format";
import type { Bet, SiteData } from "../types";
import { kpiStrip } from "./shared";

const RANGES: [string, number | null][] = [["1M", 31], ["3M", 92], ["1A", 366], ["TOUT", null]];
const BANKROLL_KEY = "bankroll";

export function renderToday(app: HTMLElement, data: SiteData) {
  const k = data.kpis;
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
    <section class="sec">
      <div class="sec-head">
        <h2>Paris à jouer</h2>
        <label class="bankroll">Ma bankroll <input id="bk" type="number" min="1" step="10" inputmode="decimal" /> €</label>
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
  input.value = localStorage.getItem(BANKROLL_KEY) ?? "1000";
  const drawBets = () => {
    const bankroll = Math.max(0, Number(input.value) || 0);
    localStorage.setItem(BANKROLL_KEY, String(bankroll));
    app.querySelector("#bets")!.innerHTML = betsTable(data.today, bankroll);
  };
  input.addEventListener("input", drawBets);
  drawBets();
}

function betsTable(bets: Bet[], bankroll: number) {
  if (bets.length === 0)
    return `<div class="empty">Aucun pari de valeur pour l'instant. Nouvelle analyse chaque jour à 14 h 05 (heure de Paris).</div>`;
  const total = bets.reduce((s, b) => s + stakeFor(b.stake, bankroll), 0);
  let lastDay = "";
  const rows = bets.map((b) => {
    const d = fmtDay(b.kickoff), head = d !== lastDay ? `<tr class="day"><td colspan="8">${d}</td></tr>` : "";
    lastDay = d;
    return `${head}<tr class="${b.status === "pending" ? "live" : ""}">
      <td class="mono">${b.status === "pending" ? "EN COURS" : fmtTime(b.kickoff)}</td>
      <td class="match">${esc(b.home)} – ${esc(b.away)}<small>${esc(b.league)}</small><span class="pick-s">${esc(betLabel(b))}</span></td>
      <td class="hide-xs">${esc(betLabel(b))}</td>
      <td class="mono hide-s">${esc(bookName(b.book)).toUpperCase()}</td>
      <td class="r mono">${odds(b.price)}</td>
      <td class="r mono hide-s">${odds(b.fair_price)}</td>
      <td class="r mono edge hide-xs">${pct(b.edge)}</td>
      <td class="r"><span class="stake">${eur(stakeFor(b.stake, bankroll))}</span></td></tr>`;
  }).join("");
  return `<table class="tbl bets"><thead><tr><th>Heure</th><th>Match</th><th class="hide-xs">Pari</th><th class="hide-s">Book</th><th class="r">Cote</th><th class="r hide-s">Juste prix</th><th class="r hide-xs">Avantage</th><th class="r">Mise</th></tr></thead>
    <tbody>${rows}</tbody></table>
    <div class="total"><span>${bets.length} pari${bets.length > 1 ? "s" : ""} · total engagé</span><b>${eur(total)} · ${pct(total / (bankroll || 1)).replace("+", "")}</b></div>`;
}
