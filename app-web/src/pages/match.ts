import { multiLineChart, oddsChart } from "../charts";
import { betLabel, bookName, dayKey, esc, eur, eur0, fmtDate, fmtDay, fmtDayKey, fmtStamp, fmtTime, odds, pct, stakeFor } from "../format";
import { bookLogo, leagueLogo, teamLogo } from "../logos";
import type { MatchDetail, Side } from "../types";
import { probBar, savedBankroll } from "./shared";
import { t } from "../i18n";

const SIDES: Side[] = ["home", "draw", "away"];
const SIDE_HEAD: Record<Side, string> = { home: "1", draw: "N", away: "2" };
const RESULT = { W: "W", D: "D", L: "L" } as const;  // form chips: language-neutral W/D/L

/** Full page for one recommended bet (route #/match/<id>). */
export function renderMatch(app: HTMLElement, id: string, back: () => void) {
  app.innerHTML = `<div class="empty pad">${t("Chargement…")}</div>`;
  window.scrollTo(0, 0);
  fetch(`/api/site/match/${encodeURIComponent(id)}`)
    .then((res) => { if (!res.ok) throw new Error(`API ${res.status}`); return res.json(); })
    .then((m: MatchDetail) => {
      app.innerHTML = render(m);
      app.querySelector("#back")!.addEventListener("click", (e) => { e.preventDefault(); back(); });
    })
    .catch((e: Error) => { app.innerHTML = `<div class="empty pad">${t("Impossible de charger ce match ({e}).", { e: esc(e.message) })} <a href="#/">${t("Retour")}</a></div>`; });
}

function render(m: MatchDetail) {
  const b = m.bet, bankroll = savedBankroll(), day = dayKey(m.odds_at);
  const label = betLabel({ side: b.side, home: m.home, away: m.away });
  const status = m.status === "won" ? `<span class="res res-won">${t("Gagné · {p} de bankroll", { p: pct(b.gain, 2) })}</span>`
    : m.status === "lost" ? `<span class="res res-lost">${t("Perdu · {p} de bankroll", { p: pct(b.gain, 2) })}</span>`
    : m.status === "void" ? `<span class="res res-void">${t("Annulé")}</span>`
    : m.status === "pending" ? `<span class="res res-live">${t("EN COURS")}</span>` : `<span class="res res-up">${t("À venir")}</span>`;
  return `
    <nav class="crumbs"><a id="back" href="#/jour/${day}">← ${t("Paris du {d}", { d: esc(fmtDayKey(day)) })}</a></nav>
    <section class="mhero">
      <div class="k mh-meta">${leagueLogo(m.league_key, m.league)}${esc(m.league)} · ${fmtDay(m.kickoff)} · ${fmtTime(m.kickoff)}${m.venue ? ` · ${esc(m.venue)}` : ""}</div>
      <div class="mh-teams">
        <div class="mh-team">${teamLogo(m.home, "crest-xl")}<b>${esc(m.home)}</b></div>
        <div class="mh-score">${m.score ? esc(m.score) : "VS"}${m.xg ? `<small>xG ${m.xg[0].toFixed(1)} – ${m.xg[1].toFixed(1)}</small>` : ""}</div>
        <div class="mh-team">${teamLogo(m.away, "crest-xl")}<b>${esc(m.away)}</b></div>
      </div>
      <div class="mh-probs">
        <div class="k">${t("Probabilités au moment du pari (juste prix Pinnacle)")}</div>${probBar(m.probs, b.side, true)}
        ${m.closing_probs ? `<div class="k">${t("À la clôture")}</div>${probBar(m.closing_probs, b.side, true)}` : ""}
      </div>
    </section>
    <section class="kpis kpis-6">
      ${kpi(t("Pari"), esc(label), "", "")}
      ${kpi(t("Cote") + " " + esc(bookName(b.book)), odds(b.price), t("juste prix {v}", { v: odds(b.fair_price) }), "")}
      ${kpi(t("Avantage"), pct(b.edge), t("vs juste prix"), "up")}
      ${kpi(t("Mise · {b}", { b: eur0(bankroll) }), eur(stakeFor(b.stake, bankroll)), t("{p} de la bankroll", { p: pct(b.stake).replace("+", "") }), "")}
      ${kpi(t("CLV"), b.clv === null ? "–" : pct(b.clv), t("vs clôture Pinnacle"), b.clv !== null && b.clv >= 0 ? "up" : "down")}
      ${kpi(t("Résultat"), status, "", "")}
    </section>
    <div class="mstamp"><span class="k">${t("Cotes relevées le {t}", { t: fmtStamp(m.odds_at) })}</span>
      ${m.status === "upcoming" && b.link ? `<a class="go big-go" href="${esc(b.link)}" target="_blank" rel="noopener nofollow">${t("Parier chez {book} ↗", { book: esc(bookName(b.book)) })}</a>` : ""}</div>
    <section class="mgrid2">
      <div class="panel-c"><div class="panel-h"><h3>${t("Cote Pinnacle · {label}", { label: esc(label) })}</h3></div>
        <p class="k pad-x">${t("Pinnacle jusqu'au coup d'envoi contre notre cote. Clôture sous notre cote = on a acheté moins cher que le marché (CLV).")}</p>
        ${oddsChart(m.pinnacle[b.side], b.price, m.kickoff)}</div>
      <div class="panel-c"><div class="panel-h"><h3>${t("Elo · 2 saisons")}</h3></div>
        <p class="k pad-x">${t("Force des équipes (Elo maison, tous championnats FBref), avant chaque match.")}</p>
        ${m.elo ? multiLineChart([
          { label: short(m.home), cls: "s-home", points: m.elo.home },
          { label: short(m.away), cls: "s-away", points: m.elo.away },
        ]) : `<div class="empty">${t("Elo indisponible.")}</div>`}</div>
    </section>
    ${m.xg_form.home.length || m.xg_form.away.length ? `<section class="panel"><div class="panel-h"><h3>${t("xG glissant · 8 matchs")}</h3><span class="k">${t("trait plein = xG pour · pointillé = xG contre")}</span></div>
      ${multiLineChart([
        { label: `${short(m.home)} +`, cls: "s-home", points: m.xg_form.home.map((p) => ({ d: p.d, v: p.for })) },
        { label: `${short(m.home)} −`, cls: "s-home", dashed: true, points: m.xg_form.home.map((p) => ({ d: p.d, v: p.against })) },
        { label: `${short(m.away)} +`, cls: "s-away", points: m.xg_form.away.map((p) => ({ d: p.d, v: p.for })) },
        { label: `${short(m.away)} −`, cls: "s-away", dashed: true, points: m.xg_form.away.map((p) => ({ d: p.d, v: p.against })) },
      ], 2, { w: 1100, h: 240, top: 14, right: 130, bottom: 26, left: 46 })}</section>` : ""}
    <section class="mgrid2">
      <div class="panel-c"><div class="panel-h"><h3>${t("Forme")}</h3></div>
        <div class="form2 pad-x">${form(m.home, m.form.home)}${form(m.away, m.form.away)}</div></div>
      <div class="panel-c"><div class="panel-h"><h3>${t("Confrontations")}</h3></div>
        ${m.h2h.length ? `<table class="tbl mini">${m.h2h.map((h) =>
          `<tr><td class="mono">${fmtDate(h.date)}</td><td>${esc(h.home)}</td><td class="r mono strong">${esc(h.score)}</td><td>${esc(h.away)}</td></tr>`).join("")}</table>` : `<div class="empty">${t("Aucune confrontation récente.")}</div>`}</div>
    </section>
    <section class="panel"><div class="panel-h"><h3>${t("Cotes au moment du pari")}</h3><span class="k">${t("{n} bookmakers · meilleure cote en gras · notre ligne surlignée", { n: m.books.length })}</span></div>${booksTable(m)}</section>
    <p class="fine">${m.referee ? t("Arbitre : {ref} · Données FBref, cotes The Odds API", { ref: esc(m.referee) }) : t("Données FBref, cotes The Odds API")}</p>`;
}

const kpi = (l: string, v: string, s: string, tone: string) =>
  `<div class="kpi"><div class="k">${l}</div><div class="v num ${tone}">${v}</div><div class="s">${s}</div></div>`;
const short = (team: string) => (team.length > 12 ? team.split(" ")[0] : team);

function booksTable(m: MatchDetail) {
  if (m.books.length === 0) return `<div class="empty">${t("Pas de cotes enregistrées.")}</div>`;
  const best = Object.fromEntries(SIDES.map((s) => [s, Math.max(...m.books.map((b) => b[s]))]));
  return `<table class="tbl books"><thead><tr><th>${t("Bookmaker")}</th>${SIDES.map((s) =>
      `<th class="r ${s === m.bet.side ? "sel" : ""}">${SIDE_HEAD[s]}</th>`).join("")}<th class="r">${t("Marge")}</th></tr></thead><tbody>
    ${m.books.map((b) => `<tr class="${b.ours ? "ours" : ""}"><td><span class="bk">${bookLogo(b.key, b.title)}${esc(b.title)}</span></td>
      ${SIDES.map((s) => `<td class="r mono ${b[s] === best[s] ? "best" : ""} ${s === m.bet.side ? "sel" : ""}">${odds(b[s])}</td>`).join("")}
      <td class="r mono">${pct(b.margin).replace("+", "")}</td></tr>`).join("")}
    </tbody></table>`;
}

const form = (team: string, games: MatchDetail["form"]["home"]) => `<div><div class="form-h">${teamLogo(team)}<b>${esc(team)}</b></div>${games.length === 0 ? `<div class="empty">–</div>` :
  `<div class="chips">${[...games].reverse().map((g) => `<span class="chip chip-${g.result}" title="${fmtDate(g.date)} ${g.venue === "H" ? "vs" : "@"} ${esc(g.opponent)} ${g.score}">${RESULT[g.result]}</span>`).join("")}</div>
   <table class="tbl mini">${games.map((g) => `<tr><td class="mono">${fmtDate(g.date)}</td><td>${g.venue === "H" ? "vs" : "@"} ${esc(g.opponent)}</td><td class="r mono">${esc(g.score)}</td></tr>`).join("")}</table>`}</div>`;
