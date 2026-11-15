import { prefetchMatch } from "../matchCache";
import { attachEquityHover, equityChart } from "../charts";
import { dayKey, eur, eur0, fmtDate, fmtDayKey, fmtStamp, int as count, pct, sliceEquity, stakeFor, todayKey, usefulRanges } from "../format";
import type { Bet, SiteData } from "../types";
import { BANKROLL_KEY, bankrollNote, betTickets, bindMarquee, bindRows, kpiStrip, marquee, paintPlaced, recordFacts, recordNotice, riskStake, savedBankroll } from "./shared";
import { icon } from "../icons";
import { markSettled } from "../motion";
import { getMyBets, updateSettings } from "../api";
import { currentUser, setUser } from "../session";
import { getView } from "../view";
import { t } from "../i18n";
import { heroBall, mountHeroBall, type Callout } from "../ball/hero";
import { mountWaitlist, waitlistCard } from "../waitlist";

const RANGES: [string, number | null][] = [["1M", 31], ["3M", 92], ["1Y", 366], ["ALL", null]];
const RANGE_LABEL: Record<string, string> = { "1Y": "1A", "ALL": "TOUT" };  // FR labels via i18n

/** Home: the published track record on top (CLV and bet count first, the fictitious bankroll second,
 *  a visible notice), then the bets published on one day (default: the latest). */
export function renderToday(app: HTMLElement, data: SiteData, day?: string) {
  const k = data.kpis;
  const user = currentUser();
  const mine = !!user && getView() === "me";
  const days = [...new Set(data.bets.map((b) => dayKey(b.odds_at)))].sort();
  const selected = day && /^\d{4}-\d{2}-\d{2}$/.test(day) ? day : days[days.length - 1] ?? todayKey();
  const facts = recordFacts(data);
  const ranges = usefulRanges(RANGES, data.equity);
  const all = ranges.length - 1;
  const books = new Set(data.bets.map((b) => b.book)).size;
  const latest = days[days.length - 1];
  const today = todayKey();
  const nLatest = latest ? data.bets.filter((b) => dayKey(b.odds_at) === latest).length : 0;
  app.innerHTML = `
    <h1 class="sr-only">${t("Paris de valeur du jour")}</h1>
    <section class="hero">
      <div class="hero-l" data-reveal>
        <div class="hero-label"><span class="eyebrow">${t("CLV moyen")}</span><span>${t("historique publié depuis le {d} · {p}", { d: facts.since, p: facts.period })}</span></div>
        <div class="big num">${k && k.clv !== null ? `<span data-count>${pct(k.clv).replace(/\s?%$/, "")}</span><span class="big-dec">%</span>` : "<span>–</span>"}</div>
        <p class="big-note">${t("écart de cote moyen, pas un gain")}</p>
        <div class="delta num"><b>${count(facts.settled)}</b><span>${t(facts.settled > 1 ? "paris réglés" : "pari réglé")} · ${t("{n} publiés", { n: count(data.bets.length) })}</span></div>
        <p class="lede">${t("Écart moyen entre la cote publiée et la cote de clôture de Pinnacle, la référence de marché. Chaque jour, les cotes de plus de vingt bookmakers sont comparées à un prix estimé à partir de Pinnacle ; on signale les cotes au-dessus de ce prix estimé.")}</p>
      </div>
      ${heroBall(ballCallouts(data, books))}
      <div class="hero-chart card" data-reveal>
        <div class="card-h"><h2>${t("Bankroll fictive")}<small>${t("départ {v}", { v: eur0(data.start_bankroll) })}</small></h2>
          ${ranges.length > 1 ? `<div class="seg seg-sm tabs" role="group" aria-label="${t("Période")}">${ranges.map(([l], i) => `<button data-range="${i}" class="${i === all ? "on" : ""}" aria-pressed="${i === all}">${t(RANGE_LABEL[l] ?? l)}</button>`).join("")}</div>` : ""}</div>
        <div id="eq"></div>
        <p class="note chart-note">${bankrollNote(data.start_bankroll)}</p>
      </div>
    </section>
    ${k ? `<section class="bento" data-reveal>
      <div class="statcard">
        <svg class="arc" viewBox="0 0 200 120" aria-hidden="true"><path d="M10 120a90 90 0 0 1 180 0"/><path d="M50 120a50 50 0 0 1 100 0"/></svg>
        <div class="statcard-v num" data-count>${count(k.bets)}</div>
        <div class="statcard-l">${t(k.bets > 1 ? "paris réglés" : "pari réglé")}<span>${t("{w} gagnés · {l} perdus", { w: count(wins(k)), l: count(k.bets - wins(k)) })}</span></div>
      </div>
      ${kpiStrip([
        [t("Rendement fictif"), pct(k.return), t("bankroll fictive {v}", { v: eur0(k.bankroll) }), ""],
        [t("Drawdown max"), pct(k.max_drawdown), t("pire recul depuis un sommet"), "down"],
        [t("Période"), facts.period, t("échantillon court"), "txt", false],
      ], "board", false)}
    </section>
    ${recordNotice(data)}` : ""}
    ${marquee([
      ...(!latest ? [] : latest === today
        ? [t(nLatest > 1 ? "{n} paris de valeur ce jour" : "{n} pari de valeur ce jour", { n: nLatest })]
        : [t(nLatest > 1 ? "Dernière sélection · {d} · {n} paris" : "Dernière sélection · {d} · {n} pari", { d: fmtDate(`${latest}T12:00:00`), n: nLatest })]),
      ...(k ? [
        `${t("Écart de cote moyen")} ${k.clv === null ? "–" : pct(k.clv)}`,
        t("{n} paris réglés", { n: count(k.bets) }),
      ] : []),
      t("Publié en direct depuis le {d}", { d: facts.since }),
      ...(books ? [t(books > 1 ? "{n} bookmakers avec un pari publié" : "{n} bookmaker avec un pari publié", { n: books })] : []),
      t("Analyse quotidienne 14 h 05"),
      `${t("MAJ")} ${fmtStamp(data.generated_at)}`,
    ])}
    <section class="sec" id="day">
      <div class="sec-head">
        <h2 id="dayhead">${t("Sélection du jour")}</h2>
        <label class="bankroll"><span>${t("Ma bankroll")}<small>${t("pour calculer mes mises")}</small></span><span class="field-pill"><input id="bk" name="bankroll" type="number" min="1" step="10" inputmode="decimal" autocomplete="off" /><i>€</i></span></label>
      </div>
      <div class="daynav">
        <button class="round" id="prev" aria-label="${t('Jour précédent')}">${icon("arrow-left")}</button>
        <label class="daypick">${icon("calendar")}<span id="dayname"></span><input id="daydate" name="day" type="date" autocomplete="off" aria-label="${t("Choisir un jour")}" /></label>
        <button class="round" id="next" aria-label="${t('Jour suivant')}">${icon("arrow-right")}</button>
        <span class="dayinfo" id="dayinfo"></span>
      </div>
      <div id="daysum"></div>
      <div id="bets"></div>
    </section>
    ${waitlistCard()}`;

  const eqBox = app.querySelector<HTMLElement>("#eq")!;
  const drawEq = (i: number) => {
    const eq = sliceEquity(data.equity, ranges[i][1]);
    eqBox.innerHTML = equityChart(eq, i === all ? data.start_bankroll : eq[0]?.bankroll ?? data.start_bankroll, { draw: true });
    attachEquityHover(eqBox, eq);
  };
  app.querySelectorAll<HTMLButtonElement>(".tabs button").forEach((b) => b.addEventListener("click", () => {
    app.querySelectorAll(".tabs button").forEach((x) => { x.classList.remove("on"); x.setAttribute("aria-pressed", "false"); });
    b.classList.add("on"); b.setAttribute("aria-pressed", "true");
    drawEq(Number(b.dataset.range));
  }));
  drawEq(all);
  mountHeroBall(app.querySelector<HTMLElement>(".ball-stage")!);

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
    app.querySelector("#dayhead")!.textContent = t(current === latest && latest !== today ? "Dernière sélection" : "Sélection du jour");
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
      ? `<div class="empty">${mine ? t("Aucun pari chez tes bookmakers ce jour-là.") : t("Aucune cote signalée ce jour-là. Analyse quotidienne à 14 h 05 (heure de Paris).")}</div>`
      : betTickets(bets, bankroll, placed);
    bindRows(box, placed);
    // A day has a handful of bets: warm their match pages once the browser is idle, so a tap opens instantly.
    const ids = bets.slice(0, 6).map((b) => b.id);
    const idle = (cb: () => void) => ("requestIdleCallback" in window ? requestIdleCallback(cb, { timeout: 3000 }) : setTimeout(cb, 1500));
    if (ids.length) idle(() => ids.forEach(prefetchMatch));
  }
  drawDay();
  mountWaitlist(app.querySelector<HTMLElement>("#waitlist")!, user);

  // Coming back from a match page: restore where the visitor was; a shared day link lands on the bets.
  const saved = sessionStorage.getItem(`scroll:${location.hash || "#/"}`);
  if (saved !== null) { window.scrollTo(0, Number(saved)); sessionStorage.removeItem(`scroll:${location.hash || "#/"}`); }
  else if (day) app.querySelector("#day")!.scrollIntoView();
  else window.scrollTo(0, 0);
}

/** Live facts pinned to the hero ball, worded as measurements (first and last are the ones kept on
 *  phones, where the CLV is already the big number). */
export function ballCallouts(data: SiteData, books: number): Callout[] {
  const k = data.kpis;
  const out: Callout[] = [];
  if (k) out.push({ label: t(k.bets > 1 ? "paris réglés" : "pari réglé"), value: count(k.bets), valueFirst: true, tone: "accent" });
  if (k && k.clv !== null) out.push({ label: t("CLV moyen"), value: pct(k.clv) });
  if (books) out.push({ label: t(books > 1 ? "bookmakers retenus" : "bookmaker retenu"), value: count(books), valueFirst: true });
  return out;
}

const wins = (k: NonNullable<SiteData["kpis"]>) => Math.round(k.win_rate * k.bets);

function dayInfo(bets: Bet[]) {
  if (bets.length === 0) return "";
  const first = bets.reduce((a, b) => (a.odds_at < b.odds_at ? a : b));
  return `<span class="pub">${icon("check")}${t("Publié le {t}, avant les coups d'envoi", { t: fmtStamp(first.odds_at) })}</span>`;
}

const won = (bets: Bet[]) => { const n = bets.filter((b) => b.status === "won").length; return t(n > 1 ? "{n} gagnés" : "{n} gagné", { n }); };

/** What the day's bets commit for the visitor's own bankroll and the most they can lose; once matches
 *  are played, the actual result. Never a gain projection (no expected value, no all-win amount). */
export function daySummary(bets: Bet[], bankroll: number) {
  const stake = bets.reduce((t, b) => t + stakeFor(b.stake, bankroll), 0);
  const settled = bets.filter((b) => b.status === "won" || b.status === "lost");
  const result = settled.reduce((t, b) => t + b.gain * bankroll, 0);
  const cell = (k: string, v: string, s: string, tone = "") => `<div class="kpi"><div class="k">${k}</div><div class="v num ${tone}" data-count>${v}</div><div class="s">${s}</div></div>`;
  return `<section class="daysum" data-reveal>
    ${cell(t("À engager"), eur(stake), t(bets.length > 1 ? "{n} paris · {p} de la bankroll" : "{n} pari · {p} de la bankroll", { n: bets.length, p: pct(stake / (bankroll || 1)).replace("+", "") }))}
    ${cell(t("Perte maximale"), `−${eur(stake)}`, t("si tous les paris sont perdus"), "down")}
    ${settled.length
      ? cell(t("Résultat"), `${result >= 0 ? "+" : "−"}${eur(Math.abs(result))}`, t("{n}/{m} matchs joués · {w}", { n: settled.length, m: bets.length, w: won(settled) }), result >= 0 ? "up" : "down")
      : cell(t("Résultat"), "–", t("aucun match joué"))}
  </section>`;
}
