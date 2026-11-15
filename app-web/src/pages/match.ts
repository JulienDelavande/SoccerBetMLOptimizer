import { multiLineChart, oddsChart } from "../charts";
import { betLabel, bookName, dayKey, esc, eur, eur0, fmtDate, fmtDay, fmtDayKey, fmtStamp, fmtTime, odds, pct, stakeFor } from "../format";
import { bookLogo, leagueLogo, teamLogo } from "../logos";
import type { MatchDetail, Side } from "../types";
import { card, probBar, savedBankroll } from "./shared";
import { icon } from "../icons";
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
      document.title = `${m.home} - ${m.away} · OptiBet`;
      app.querySelector("#back")!.addEventListener("click", (e) => { e.preventDefault(); back(); });
    })
    .catch((e: Error) => { app.innerHTML = `<div class="empty pad">${t("Impossible de charger ce match ({e}).", { e: esc(e.message) })} <a class="go" href="#/">${t("Retour")}</a></div>`; });
}

function render(m: MatchDetail) {
  const b = m.bet, bankroll = savedBankroll(), day = dayKey(m.odds_at);
  const label = betLabel({ side: b.side, home: m.home, away: m.away });
  const gain = t("{p} de la bankroll", { p: pct(b.gain, 2) });
  const [result, resultSub, resultTone] = m.status === "won" ? [t("Gagné"), gain, "up"]
    : m.status === "lost" ? [t("Perdu"), gain, "down"]
    : m.status === "void" ? [t("Annulé"), t("mise remboursée"), ""]
    : m.status === "pending" ? [`<span class="v-live"><i class="live-dot" aria-hidden="true"></i>${t("En cours")}</span>`, t("match en cours"), ""]
    : [t("À venir"), `${fmtDay(m.kickoff)} · ${fmtTime(m.kickoff)}`, ""];
  return `
    <h1 class="sr-only">${t("{home} contre {away}", { home: esc(m.home), away: esc(m.away) })}</h1>
    <nav class="crumbs"><a id="back" class="back" href="#/jour/${day}">${icon("arrow-left")}<span>${t("Paris du {d}", { d: esc(fmtDayKey(day)) })}</span></a></nav>
    <section class="mhero" data-reveal>
      <svg class="pitch" viewBox="0 0 600 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><line x1="300" y1="0" x2="300" y2="300"/><circle cx="300" cy="150" r="96"/><circle cx="300" cy="150" r="150"/><circle class="spot" cx="300" cy="150" r="3.5"/></svg>
      <div class="mh-meta">${leagueLogo(m.league_key, m.league)}<span>${esc(m.league)}</span><i></i><span>${fmtDay(m.kickoff)} · ${fmtTime(m.kickoff)}</span>${m.venue ? `<i></i><span>${esc(m.venue)}</span>` : ""}</div>
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
    <section class="kpis kpis-board kpis-6" data-reveal>
      ${kpi(t("Pari"), esc(label), "", "")}
      ${kpi(t("Cote") + " " + esc(bookName(b.book)), odds(b.price), t("juste prix {v}", { v: odds(b.fair_price) }), "")}
      ${kpi(t("Avantage"), pct(b.edge), t("vs juste prix"), "up")}
      ${kpi(t("Mise · {b}", { b: eur0(bankroll) }), eur(stakeFor(b.stake, bankroll)), t("{p} de la bankroll", { p: pct(b.stake).replace("+", "") }), "")}
      ${kpi(t("CLV"), b.clv === null ? "–" : pct(b.clv), t("vs clôture Pinnacle"), b.clv !== null && b.clv >= 0 ? "up" : "down")}
      ${kpi(t("Résultat"), result, resultSub, resultTone)}
    </section>
    <div class="mstamp"><span class="note">${t("Publié le {t}", { t: fmtStamp(m.odds_at) })}</span>
      ${m.status === "upcoming" && b.link ? `<a class="btn-cta" href="${esc(b.link)}" target="_blank" rel="noopener nofollow">${t("Parier chez {book}", { book: esc(bookName(b.book)) })}${icon("arrow-up-right")}</a>` : ""}</div>
    <div class="grid2">
      ${card(t("Cote Pinnacle · {label}", { label: esc(label) }), t("Pinnacle jusqu'au coup d'envoi, face à la cote publiée. Clôture sous la cote publiée = CLV positif."),
        oddsChart(m.pinnacle[b.side], b.price, m.kickoff))}
      ${card(t("Elo · 2 saisons"), t("Force des équipes (Elo maison, tous championnats FBref), avant chaque match."),
        m.elo ? multiLineChart([
          { label: short(m.home), cls: "s-home", points: m.elo.home },
          { label: short(m.away), cls: "s-away", points: m.elo.away },
        ], 0, undefined, t("Elo")) : `<div class="empty">${t("Elo indisponible.")}</div>`)}
    </div>
    ${m.xg_form.home.length || m.xg_form.away.length ? card(t("xG glissant · 8 matchs"), t("trait plein = xG pour · pointillé = xG contre"),
      multiLineChart([
        { label: `${short(m.home)} +`, cls: "s-home", points: m.xg_form.home.map((p) => ({ d: p.d, v: p.for })) },
        { label: `${short(m.home)} −`, cls: "s-home", dashed: true, points: m.xg_form.home.map((p) => ({ d: p.d, v: p.against })) },
        { label: `${short(m.away)} +`, cls: "s-away", points: m.xg_form.away.map((p) => ({ d: p.d, v: p.for })) },
        { label: `${short(m.away)} −`, cls: "s-away", dashed: true, points: m.xg_form.away.map((p) => ({ d: p.d, v: p.against })) },
      ], 2, { w: 1100, h: 240, top: 14, right: 130, bottom: 26, left: 46 }, t("xG glissant"))) : ""}
    <div class="grid2">
      ${card(t("Forme"), "", `<div class="form2">${form(m.home, m.form.home)}${form(m.away, m.form.away)}</div>`)}
      ${card(t("Confrontations"), "", m.h2h.length ? `<table class="tbl mini">${m.h2h.map((h) =>
          `<tr><td class="mono">${fmtDate(h.date)}</td><td>${esc(h.home)}</td><td class="r mono strong">${esc(h.score)}</td><td>${esc(h.away)}</td></tr>`).join("")}</table>` : `<div class="empty">${t("Aucune confrontation récente.")}</div>`)}
    </div>
    ${card(t("Cotes au moment du pari"), t("{n} bookmakers · meilleure cote en gras · notre ligne surlignée", { n: m.books.length }), `<div class="tbl-scroll" tabindex="0" role="region" aria-label="${t("Cotes au moment du pari")}">${booksTable(m)}</div>`, "flush")}
    <p class="fine">${m.referee ? t("Arbitre : {ref} · Données FBref, cotes The Odds API", { ref: esc(m.referee) }) : t("Données FBref, cotes The Odds API")}</p>`;
}

const kpi = (l: string, v: string, s: string, tone: string) =>
  `<div class="kpi"><div class="k">${l}</div><div class="v num ${tone}">${v}</div>${s ? `<div class="s">${s}</div>` : ""}</div>`;
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
