import { attachEquityHover, equityChart } from "../charts";
import { dayKey, eur, eur0, fmtDate, fmtDayKey, fmtStamp, int as count, odds, pct, sliceEquity, splitAmount, stakeFor, todayKey } from "../format";
import type { Bet, SiteData } from "../types";
import { BANKROLL_KEY, betTickets, bindMarquee, bindRows, kpiStrip, marquee, paintPlaced, riskStake, savedBankroll } from "./shared";
import { icon } from "../icons";
import { markSettled } from "../motion";
import { getMyBets, updateSettings } from "../api";
import { currentUser, setUser } from "../session";
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
  const books = new Set(data.bets.map((b) => b.book)).size;
  const latest = days[days.length - 1];
  const today = todayKey();
  const nLatest = latest ? data.bets.filter((b) => dayKey(b.odds_at) === latest).length : 0;
  const since = k ? new Date(k.since).toLocaleDateString(locale(), { month: "long", year: "numeric" }) : "";
  app.innerHTML = `
    <h1 class="sr-only">${t("Paris de valeur du jour")}</h1>
    <section class="hero">
      <div class="hero-l" data-reveal>
        <svg class="rings" viewBox="0 0 400 400" aria-hidden="true"><circle cx="200" cy="200" r="198"/><circle cx="200" cy="200" r="140"/><circle cx="200" cy="200" r="82"/><line x1="200" y1="0" x2="200" y2="400"/></svg>
        <div class="hero-label"><span class="eyebrow">${t("Bankroll")}</span><span>${since ? t("départ {v} · {since}", { v: eur0(data.start_bankroll), since }) : t("départ {v}", { v: eur0(data.start_bankroll) })}</span></div>
        <div class="big num"><span data-count>${int}</span><span class="big-dec">${dec}</span></div>
        ${k ? `<div class="delta num ${k.return < 0 ? "neg" : ""}">${icon(k.return >= 0 ? "arrow-up" : "arrow-down")}<b>${pct(k.return)}</b><span>${t("depuis le départ")}</span></div>` : ""}
        <p class="lede">${k ? t("{n} paris réglés. ", { n: count(k.bets) }) : ""}${t("On compare chaque cote à celle de Pinnacle, le bookmaker le plus précis du marché, et on ne joue que quand un bookmaker est en retard sur lui.")}</p>
      </div>
      <div class="hero-chart card" data-reveal>
        <div class="card-h"><h2>${t("Courbe de bankroll")}</h2>
          <div class="seg seg-sm tabs" role="group" aria-label="${t("Période")}">${RANGES.map(([l], i) => `<button data-range="${i}" class="${i === 3 ? "on" : ""}" aria-pressed="${i === 3}">${t(RANGE_LABEL[l] ?? l)}</button>`).join("")}</div></div>
        <div id="eq"></div>
      </div>
    </section>
    ${k ? `<section class="bento" data-reveal>
      <div class="statcard">
        <svg class="arc" viewBox="0 0 200 120" aria-hidden="true"><path d="M10 120a90 90 0 0 1 180 0"/><path d="M50 120a50 50 0 0 1 100 0"/></svg>
        <div class="statcard-v num"${k.clv === null ? "" : " data-count"}>${k.clv === null ? "–" : pct(k.clv)}</div>
        <div class="statcard-l">${t("CLV moyen")}<span>${t("vs clôture Pinnacle")}</span></div>
      </div>
      ${kpiStrip([
        [t("Paris"), count(k.bets), t("{n} % gagnants", { n: Math.round(k.win_rate * 100) }), ""],
        [t("ROI / pari"), pct(k.roi), t("cote moy. {v}", { v: odds(k.avg_price) }), k.roi >= 0 ? "up" : "down"],
        [t("Drawdown max"), pct(k.max_drawdown), new Date(k.max_drawdown_day).toLocaleDateString(locale(), { month: "long", year: "numeric" }), "down"],
      ], "board", false)}
    </section>` : ""}
    ${marquee([
      ...(!latest ? [] : latest === today
        ? [t(nLatest > 1 ? "{n} paris de valeur ce jour" : "{n} pari de valeur ce jour", { n: nLatest })]
        : [t(nLatest > 1 ? "Dernière sélection · {d} · {n} paris" : "Dernière sélection · {d} · {n} pari", { d: fmtDate(`${latest}T12:00:00`), n: nLatest })]),
      ...(k ? [
        `${t("CLV moyen")} ${k.clv === null ? "–" : pct(k.clv)}`,
        `${t("ROI / pari")} ${pct(k.roi)}`,
        t("{n} paris réglés", { n: count(k.bets) }),
      ] : []),
      ...(books ? [t("{n} bookmakers comparés à Pinnacle", { n: books })] : []),
      t("Analyse quotidienne 14 h 05"),
      `${t("MAJ")} ${fmtStamp(data.generated_at)}`,
    ])}
    <section class="sec" id="day">
      <div class="sec-head">
        <h2 id="dayhead">${t("Paris du jour")}</h2>
        <label class="bankroll"><span>${t("Ma bankroll")}</span><span class="field-pill"><input id="bk" name="bankroll" type="number" min="1" step="10" inputmode="decimal" autocomplete="off" /><i>€</i></span></label>
      </div>
      <div class="daynav">
        <button class="round" id="prev" aria-label="${t('Jour précédent')}">${icon("arrow-left")}</button>
        <label class="daypick">${icon("calendar")}<span id="dayname"></span><input id="daydate" name="day" type="date" autocomplete="off" aria-label="${t("Choisir un jour")}" /></label>
        <button class="round" id="next" aria-label="${t('Jour suivant')}">${icon("arrow-right")}</button>
        <span class="dayinfo" id="dayinfo"></span>
      </div>
      <div id="daysum"></div>
      <div id="bets"></div>
    </section>`;

  const eqBox = app.querySelector<HTMLElement>("#eq")!;
  const drawEq = (i: number) => {
    const eq = sliceEquity(data.equity, RANGES[i][1]);
    eqBox.innerHTML = equityChart(eq, i === 3 ? data.start_bankroll : eq[0]?.bankroll ?? data.start_bankroll, { draw: true });
    attachEquityHover(eqBox, eq);
  };
  app.querySelectorAll<HTMLButtonElement>(".tabs button").forEach((b) => b.addEventListener("click", () => {
    app.querySelectorAll(".tabs button").forEach((x) => { x.classList.remove("on"); x.setAttribute("aria-pressed", "false"); });
    b.classList.add("on"); b.setAttribute("aria-pressed", "true");
    drawEq(Number(b.dataset.range));
  }));
  drawEq(3);

  bindMarquee(app);
  const input = app.querySelector<HTMLInputElement>("#bk")!;
  input.value = String(mine && user ? user.bankroll : savedBankroll());
  let current = selected;
  // Me view: which of the day's bets the user said they played (filled once /me/bets answers).
  const placed = mine ? new Set<string>() : undefined;
  if (placed) getMyBets().then(({ bets }) => {
    bets.forEach((b) => placed.add(`${b.match_id}|${b.side}`));
    paintPlaced(app.querySelector<HTMLElement>("#bets")!, placed);
  }).catch(() => { /* toggles stay usable; they just start unticked */ });
  // Changing day only redraws the day section and rewrites the URL in place: no re-render, no scroll,
  // and no replayed entrance (content swaps in place).
  const show = (d: string | undefined) => {
    if (!d) return;
    current = d;
    markSettled();
    history.replaceState(null, "", `#/jour/${d}`);
    drawDay();
  };
  app.querySelector("#prev")!.addEventListener("click", () => show(days.filter((d) => d < current).pop()));
  app.querySelector("#next")!.addEventListener("click", () => show(days.find((d) => d > current)));
  const picker = app.querySelector<HTMLInputElement>("#daydate")!;
  picker.min = days[0] ?? ""; picker.max = todayKey();
  picker.addEventListener("change", () => show(picker.value || undefined));
  // Me view: the bankroll is an account setting (saved, debounced); Bot view: a local preference.
  let saveTimer = 0;
  input.addEventListener("input", () => {
    drawDay();
    const bankroll = Math.max(0, Number(input.value) || 0);
    if (!mine) { localStorage.setItem(BANKROLL_KEY, String(bankroll)); return; }
    clearTimeout(saveTimer);
    if (bankroll > 0) saveTimer = window.setTimeout(() => { updateSettings({ bankroll }).then(setUser).catch(() => {}); }, 800);
  });

  function drawDay() {
    const bankroll = Math.max(0, Number(input.value) || 0);
    app.querySelector<HTMLButtonElement>("#prev")!.disabled = !days.some((d) => d < current);
    app.querySelector<HTMLButtonElement>("#next")!.disabled = !days.some((d) => d > current);
    picker.value = current;
    app.querySelector("#dayname")!.textContent = fmtDayKey(current);
    app.querySelector("#dayhead")!.textContent = t(current === latest && latest !== today ? "Dernière sélection" : "Paris du jour");
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
      : betTickets(bets, bankroll, placed);
    bindRows(box, placed);
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
    ? `<span class="pub">${icon("check")}${t("Publié le {t}, avant les coups d'envoi", { t: fmtStamp(first.odds_at) })}</span>`
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
  const cell = (k: string, v: string, s: string, tone = "") => `<div class="kpi"><div class="k">${k}</div><div class="v num ${tone}" data-count>${v}</div><div class="s">${s}</div></div>`;
  return `<section class="daysum" data-reveal>
    ${cell(t("À engager"), eur(stake), t(bets.length > 1 ? "{n} paris · {p} de la bankroll" : "{n} pari · {p} de la bankroll", { n: bets.length, p: pct(stake / (bankroll || 1)).replace("+", "") }))}
    ${cell(t("Gain espéré"), `${expected >= 0 ? "+" : "−"}${eur(Math.abs(expected))}`, t("moyenne sur le long terme"), "up")}
    ${cell(t("Si tout passe"), `+${eur(allWin)}`, t("tous les paris gagnants"))}
    ${settled.length
      ? cell(t("Résultat"), `${result >= 0 ? "+" : "−"}${eur(Math.abs(result))}`, t("{n}/{m} matchs joués · {w}", { n: settled.length, m: bets.length, w: won(settled) }), result >= 0 ? "up" : "down")
      : cell(t("Résultat"), "–", t("aucun match joué"))}
  </section>`;
}
