import { oddsChart } from "../charts";
import { betLabel, bookName, esc, eur, fmtDate, fmtDay, fmtStamp, fmtTime, odds, pct, stakeFor } from "../format";
import { bookLogo, leagueLogo, teamLogo } from "../logos";
import type { MatchDetail, Side } from "../types";
import { savedBankroll } from "./shared";

const SIDE_HEAD: Record<Side, string> = { home: "1", draw: "N", away: "2" };
const RESULT = { W: "V", D: "N", L: "D" } as const;

/** Slide-over panel with the detail of one recommended bet (route #/match/<id>).
 * `onUserClose` runs when the visitor closes it; the returned function closes it silently. */
export function openMatch(id: string, onUserClose: () => void): () => void {
  const root = document.createElement("div");
  root.className = "drawer-wrap";
  root.innerHTML = `<div class="drawer-bg"></div><aside class="drawer" role="dialog" aria-modal="true"><button class="close" aria-label="Fermer">✕ FERMER</button><div class="drawer-body"><div class="empty">Chargement…</div></div></aside>`;
  document.body.append(root);
  document.body.classList.add("noscroll");
  const remove = () => { root.remove(); document.body.classList.remove("noscroll"); document.removeEventListener("keydown", onKey); };
  const userClose = () => { remove(); onUserClose(); };
  const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") userClose(); };
  document.addEventListener("keydown", onKey);
  root.querySelector(".drawer-bg")!.addEventListener("click", userClose);
  root.querySelector(".close")!.addEventListener("click", userClose);
  const body = root.querySelector<HTMLElement>(".drawer-body")!;
  fetch(`/api/site/match/${encodeURIComponent(id)}`)
    .then((res) => { if (!res.ok) throw new Error(res.status === 404 ? "pari inconnu" : `API ${res.status}`); return res.json(); })
    .then((m: MatchDetail) => { body.innerHTML = render(m); })
    .catch((e: Error) => { body.innerHTML = `<div class="empty">Impossible de charger ce match (${esc(e.message)}).</div>`; });
  return remove;
}

function render(m: MatchDetail) {
  const b = m.bet, bankroll = savedBankroll(), stake = stakeFor(b.stake, bankroll);
  const label = betLabel({ side: b.side, home: m.home, away: m.away });
  const status = m.status === "won" ? `<span class="res res-won">Gagné · ${pct(b.gain, 2)}</span>`
    : m.status === "lost" ? `<span class="res res-lost">Perdu · ${pct(b.gain, 2)}</span>`
    : m.status === "void" ? `<span class="res res-void">Annulé</span>`
    : m.status === "pending" ? `<span class="res res-live">EN COURS</span>` : "";
  return `
    <header class="mh">
      <div class="k">${leagueLogo(m.league_key, m.league)} ${esc(m.league)} · ${fmtDay(m.kickoff)} · ${fmtTime(m.kickoff)}${m.venue ? ` · ${esc(m.venue)}` : ""}</div>
      <div class="mh-teams">
        <div class="mh-team">${teamLogo(m.home, "crest-xl")}<b>${esc(m.home)}</b></div>
        <div class="mh-score">${m.score ? esc(m.score) : "VS"}${m.xg ? `<small>xG ${m.xg[0].toFixed(1)} – ${m.xg[1].toFixed(1)}</small>` : ""}</div>
        <div class="mh-team">${teamLogo(m.away, "crest-xl")}<b>${esc(m.away)}</b></div>
      </div>
    </header>
    <section class="mbet">
      <div><div class="k">Pari</div><div class="v">${esc(label)}</div></div>
      <div><div class="k">Cote ${esc(bookName(b.book))}</div><div class="v mono">${odds(b.price)}</div></div>
      <div><div class="k">Juste prix</div><div class="v mono">${odds(b.fair_price)}</div></div>
      <div><div class="k">Avantage</div><div class="v mono up">${pct(b.edge)}</div></div>
      <div><div class="k">Mise (${eur(bankroll).replace(",00", "")})</div><div class="v"><span class="stake">${eur(stake)}</span></div></div>
      <div><div class="k">CLV</div><div class="v mono ${b.clv !== null && b.clv >= 0 ? "up" : "down"}">${b.clv === null ? "–" : pct(b.clv)}</div></div>
    </section>
    <div class="mstamp">${status}<span class="k">Cote relevée le ${fmtStamp(m.odds_at)}</span>
      ${m.status === "upcoming" && b.link ? `<a class="go big-go" href="${esc(b.link)}" target="_blank" rel="noopener nofollow">Parier chez ${esc(bookName(b.book))} ↗</a>` : ""}</div>
    <section class="mpanel"><h3>Cote Pinnacle · ${esc(label)}</h3>
      <p class="k">Notre cote contre la cote Pinnacle jusqu'au coup d'envoi. Si Pinnacle finit sous notre cote, on a acheté plus cher que le marché : c'est le CLV.</p>
      ${oddsChart(m.pinnacle[b.side], b.price, m.kickoff)}</section>
    <section class="mpanel"><h3>Cotes au moment du pari</h3>${booksTable(m)}</section>
    <section class="mpanel form2"><div><h3>Forme · ${esc(m.home)}</h3>${form(m.form.home)}</div><div><h3>Forme · ${esc(m.away)}</h3>${form(m.form.away)}</div></section>
    <section class="mpanel"><h3>Confrontations</h3>${m.h2h.length ? `<table class="tbl mini">${m.h2h.map((h) =>
      `<tr><td class="mono">${fmtDate(h.date)}</td><td>${esc(h.home)}</td><td class="r mono strong">${esc(h.score)}</td><td>${esc(h.away)}</td></tr>`).join("")}</table>` : `<div class="empty">Aucune confrontation récente.</div>`}</section>
    ${m.referee ? `<p class="fine">Arbitre : ${esc(m.referee)} · données FBref, cotes The Odds API</p>` : `<p class="fine">Données FBref, cotes The Odds API</p>`}`;
}

function booksTable(m: MatchDetail) {
  if (m.books.length === 0) return `<div class="empty">Pas de cotes enregistrées.</div>`;
  const best = Object.fromEntries((["home", "draw", "away"] as Side[]).map((s) => [s, Math.max(...m.books.map((b) => b[s]))]));
  const fair = (s: Side) => (s === m.bet.side ? m.bet.fair_price : null);
  return `<table class="tbl mini books"><thead><tr><th>Bookmaker</th>${(["home", "draw", "away"] as Side[]).map((s) =>
      `<th class="r ${s === m.bet.side ? "sel" : ""}">${SIDE_HEAD[s]}</th>`).join("")}<th class="r">Marge</th></tr></thead><tbody>
    ${m.books.map((b) => `<tr class="${b.ours ? "ours" : ""}"><td class="bk">${bookLogo(b.key, b.title)}${esc(b.title)}</td>
      ${(["home", "draw", "away"] as Side[]).map((s) => `<td class="r mono ${b[s] === best[s] ? "best" : ""} ${s === m.bet.side ? "sel" : ""}">${odds(b[s])}</td>`).join("")}
      <td class="r mono">${pct(b.margin).replace("+", "")}</td></tr>`).join("")}
    </tbody></table><p class="k pad-t">Meilleure cote de chaque issue en gras · juste prix ${esc(SIDE_HEAD[m.bet.side])} = ${odds(fair(m.bet.side)!)}</p>`;
}

const form = (games: MatchDetail["form"]["home"]) => games.length === 0 ? `<div class="empty">–</div>` :
  `<div class="chips">${[...games].reverse().map((g) => `<span class="chip chip-${g.result}" title="${fmtDate(g.date)} ${g.venue === "H" ? "vs" : "@"} ${esc(g.opponent)} ${g.score}">${RESULT[g.result]}</span>`).join("")}</div>
   <table class="tbl mini">${games.map((g) => `<tr><td class="mono">${fmtDate(g.date)}</td><td>${g.venue === "H" ? "vs" : "@"} ${esc(g.opponent)}</td><td class="r mono">${esc(g.score)}</td></tr>`).join("")}</table>`;
