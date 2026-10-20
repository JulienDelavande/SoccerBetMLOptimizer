import { attachEquityHover, equityChart } from "../charts";
import { dayKey, eur, eur0, fmtDayKey, fmtStamp, odds, pct, sliceEquity, splitAmount, stakeFor, todayKey } from "../format";
import type { Bet, SiteData } from "../types";
import { BANKROLL_KEY, betsTable, bindRows, kpiStrip, riskStake, savedBankroll } from "./shared";
import { currentUser } from "../session";
import { getView } from "../view";
import { locale, t } from "../i18n";

const RANGES: [string, number | null][] = [["1M", 31], ["3M", 92], ["1Y", 366], ["ALL", null]];
const RANGE_LABEL: Record<string, string> = { "1Y": "1A", "ALL": "TOUT" };  // FR labels via i18n

/** Home: track record on top, then the bets recommended on one day (default: the latest). */
export function renderToday(app: HTMLElement, data: SiteData, day?: string) {
  const k = data.kpis;
  const user = currentUser();
  const mine = !!user && getView() === "me";
  const days = [...new Set(data.bets.map((b) => dayKey(b.odds_at)))].sort();
  const selected = day && /^\d{4}-\d{2}-\d{2}$/.test(day) ? day : days[days.length - 1] ?? todayKey();
  const [int, dec] = splitAmount(k?.bankroll ?? data.start_bankroll);
  app.innerHTML = `
    <section class="hero">
      <div class="hero-l">
        <div>
          <div class="k">${t("Bankroll · départ {v} · {since}", { v: eur0(data.start_bankroll), since: k ? new Date(k.since).toLocaleDateString(locale(), { month: "long", year: "numeric" }) : "" })}</div>
          <div class="big num">${int}<span>${dec}</span></div>
          ${k ? `<div class="delta num ${k.return < 0 ? "neg" : ""}">${k.return >= 0 ? "▲" : "▼"} ${pct(k.return)}</div>` : ""}
        </div>
        <p class="note">${k ? t("{n} paris réglés. ", { n: k.bets }) : ""}${t("On compare chaque cote à celle de Pinnacle, le bookmaker le plus précis du marché, et on ne joue que quand un bookmaker est en retard sur lui.")}</p>
      </div>
      <div class="hero-chart">
        <div class="tabs">${RANGES.map(([l], i) => `<button data-range="${i}" class="${i === 3 ? "on" : ""}">${t(RANGE_LABEL[l] ?? l)}</button>`).join("")}</div>
        <div id="eq"></div>
      </div>
    </section>
    ${k ? kpiStrip([
      [t("CLV moyen"), k.clv === null ? "–" : pct(k.clv), t("vs clôture Pinnacle"), k.clv !== null && k.clv >= 0 ? "up" : "down"],
      [t("Paris"), `${k.bets}`, t("{n} % gagnants", { n: Math.round(k.win_rate * 100) }), ""],
      [t("ROI / pari"), pct(k.roi), t("cote moy. {v}", { v: odds(k.avg_price) }), k.roi >= 0 ? "" : "down"],
      [t("Drawdown max"), pct(k.max_drawdown), new Date(k.max_drawdown_day).toLocaleDateString(locale(), { month: "long", year: "numeric" }), "down"],
    ]) : ""}
    <section class="sec" id="day">
      <div class="sec-head">
        <h2>${t("Paris du jour")}</h2>
        <label class="bankroll">${t("Ma bankroll")} <input id="bk" type="number" min="1" step="10" inputmode="decimal" /> €</label>
      </div>
      <div class="daynav">
        <button id="prev" aria-label="${t('Jour précédent')}">←</button>
        <label class="daypick"><span id="dayname"></span><input id="daydate" type="date" /></label>
        <button id="next" aria-label="${t('Jour suivant')}">→</button>
        <span class="k" id="dayinfo"></span>
      </div>
      <div id="daysum"></div>
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
  input.value = String(mine && user ? user.bankroll : savedBankroll());
  let current = selected;
  // Changing day only redraws the day section and rewrites the URL in place: no re-render, no scroll.
  const show = (d: string | undefined) => {
    if (!d) return;
    current = d;
    history.replaceState(null, "", `#/jour/${d}`);
    drawDay();
  };
  app.querySelector("#prev")!.addEventListener("click", () => show(days.filter((d) => d < current).pop()));
  app.querySelector("#next")!.addEventListener("click", () => show(days.find((d) => d > current)));
  const picker = app.querySelector<HTMLInputElement>("#daydate")!;
  picker.min = days[0] ?? ""; picker.max = todayKey();
  picker.addEventListener("change", () => show(picker.value || undefined));
  input.addEventListener("input", () => drawDay());

  function drawDay() {
    const bankroll = Math.max(0, Number(input.value) || 0);
    localStorage.setItem(BANKROLL_KEY, String(bankroll));
    app.querySelector<HTMLButtonElement>("#prev")!.disabled = !days.some((d) => d < current);
    app.querySelector<HTMLButtonElement>("#next")!.disabled = !days.some((d) => d > current);
    picker.value = current;
    app.querySelector("#dayname")!.textContent = fmtDayKey(current);
    let bets = data.bets.filter((b) => dayKey(b.odds_at) === current).sort((a, b) => a.kickoff.localeCompare(b.kickoff));
    if (mine && user) {
      const books = user.books;
      bets = bets.filter((b) => books.length === 0 || books.includes(b.book))
                 .map((b) => ({ ...b, stake: riskStake(b.stake, user.risk_preset) }));
    }
    app.querySelector("#dayinfo")!.innerHTML = dayInfo(bets);
    app.querySelector("#daysum")!.innerHTML = bets.length ? daySummary(bets, bankroll) : "";
    const box = app.querySelector<HTMLElement>("#bets")!;
    box.innerHTML = bets.length === 0
      ? `<div class="empty">${mine ? t("Aucun pari chez tes bookmakers ce jour-là.") : t("Aucun pari de valeur recommandé ce jour-là. Analyse quotidienne à 14 h 05 (heure de Paris).")}</div>`
      : betsTable(bets, bankroll, { date: "day" });
    bindRows(box);
  }
  drawDay();

  // Coming back from a match page: restore where the visitor was; a shared day link lands on the bets.
  const saved = sessionStorage.getItem(`scroll:${location.hash || "#/"}`);
  if (saved !== null) { window.scrollTo(0, Number(saved)); sessionStorage.removeItem(`scroll:${location.hash || "#/"}`); }
  else if (day) app.querySelector("#day")!.scrollIntoView();
  else window.scrollTo(0, 0);
}

function dayInfo(bets: Bet[]) {
  if (bets.length === 0) return "";
  const first = bets.reduce((a, b) => (a.odds_at < b.odds_at ? a : b));
  return first.published
    ? `<span class="pub">${t("✓ Publié le {t}, avant les coups d'envoi", { t: fmtStamp(first.odds_at) })}</span>`
    : t("Cotes relevées le {t}", { t: fmtStamp(first.odds_at) });
}

const won = (bets: Bet[]) => { const n = bets.filter((b) => b.status === "won").length; return t(n > 1 ? "{n} gagnés" : "{n} gagné", { n }); };

/** What the day's bets commit and return for the visitor's bankroll. */
export function daySummary(bets: Bet[], bankroll: number) {
  const stake = bets.reduce((t, b) => t + stakeFor(b.stake, bankroll), 0);
  const expected = bets.reduce((t, b) => t + stakeFor(b.stake, bankroll) * b.edge, 0);
  const allWin = bets.reduce((t, b) => t + stakeFor(b.stake, bankroll) * (b.price - 1), 0);
  const settled = bets.filter((b) => b.status === "won" || b.status === "lost");
  const result = settled.reduce((t, b) => t + b.gain * bankroll, 0);
  const cell = (k: string, v: string, s: string, tone = "") => `<div class="kpi"><div class="k">${k}</div><div class="v num ${tone}">${v}</div><div class="s">${s}</div></div>`;
  return `<section class="kpis daysum">
    ${cell(t("À engager"), eur(stake), t(bets.length > 1 ? "{n} paris · {p} de la bankroll" : "{n} pari · {p} de la bankroll", { n: bets.length, p: pct(stake / (bankroll || 1)).replace("+", "") }))}
    ${cell(t("Gain espéré"), `${expected >= 0 ? "+" : "−"}${eur(Math.abs(expected))}`, t("moyenne sur le long terme"), "up")}
    ${cell(t("Si tout passe"), `+${eur(allWin)}`, t("tous les paris gagnants"))}
    ${settled.length
      ? cell(t("Résultat"), `${result >= 0 ? "+" : "−"}${eur(Math.abs(result))}`, t("{n}/{m} matchs joués · {w}", { n: settled.length, m: bets.length, w: won(settled) }), result >= 0 ? "up" : "down")
      : cell(t("Résultat"), "–", t("aucun match joué"))}
  </section>`;
}
