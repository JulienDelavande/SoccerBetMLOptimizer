import { betLabel, bookName, esc, eur, fmtDate, fmtDay, fmtTime, odds, pct, stakeFor } from "../format";
import { leagueLogo, teamLogo } from "../logos";
import type { Bet } from "../types";

/** Row of big KPI cells: [label, value, sub, tone]. */
export const kpiStrip = (items: [string, string, string, string][]) =>
  `<section class="kpis">${items.map(([l, v, s, tone]) =>
    `<div class="kpi"><div class="k">${l}</div><div class="v num ${tone}">${v}</div><div class="s">${s}</div></div>`).join("")}</section>`;

export const BANKROLL_KEY = "bankroll";
export const savedBankroll = () => Math.max(0, Number(localStorage.getItem(BANKROLL_KEY) ?? "1000") || 0);

export const matchCell = (b: Pick<Bet, "home" | "away" | "league" | "league_key">, extra = "") =>
  `<td class="match"><div class="teams"><span class="team">${teamLogo(b.home)}${esc(b.home)}</span><i>–</i><span class="team">${teamLogo(b.away)}${esc(b.away)}</span></div>
    <small>${leagueLogo(b.league_key, b.league)}${esc(b.league)}</small>${extra}</td>`;

/** Result cell: bet link before kickoff, live tag, or settled gain. */
export const resultCell = (b: Bet) => {
  if (b.status === "upcoming")
    return b.link ? `<a class="go" href="${esc(b.link)}" target="_blank" rel="noopener nofollow" data-stop>${esc(bookName(b.book))} ↗</a>` : `<span class="res res-up">À venir</span>`;
  if (b.status === "pending") return `<span class="res res-live">EN COURS</span>`;
  if (b.status === "void") return `<span class="res res-void">Annulé</span>`;
  return `<span class="res res-${b.status}">${b.score ?? ""} · ${pct(b.gain, 2)}</span>`;
};

/** Bets table shared by the day view and the history; rows open the match detail. */
export function betsTable(bets: Bet[], bankroll: number, opts: { date: "day" | "full" }) {
  const when = (k: string) => `${opts.date === "full" ? fmtDate(k) : fmtDay(k)}<small>${fmtTime(k)}</small>`;
  const rows = bets.map((b) => `<tr class="click ${b.status === "pending" ? "live" : ""}" data-id="${esc(b.id)}">
      <td class="mono">${when(b.kickoff)}</td>
      ${matchCell(b, `<span class="pick-s">${esc(betLabel(b))} · ${odds(b.price)}</span><span class="pick-s">${resultCell(b)}</span>`)}
      <td class="hide-xs">${esc(betLabel(b))}${probBar(b.probs, b.side)}</td>
      <td class="r mono hide-xs">${odds(b.price)}</td>
      <td class="r mono hide-s">${odds(b.fair_price)}</td>
      <td class="r mono edge hide-xs">${pct(b.edge)}</td>
      <td class="r"><span class="stake">${eur(stakeFor(b.stake, bankroll))}</span></td>
      <td class="r hide-xs">${resultCell(b)}</td></tr>`).join("");
  return `<table class="tbl bets"><thead><tr><th>Coup d'envoi</th><th>Match</th><th class="hide-xs">Pari · probabilités 1 / N / 2</th><th class="r hide-xs">Cote</th><th class="r hide-s">Juste prix</th><th class="r hide-xs">Avantage</th><th class="r">Mise</th><th class="r hide-xs">Résultat</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

/** Opens the match detail when a bet row is clicked (links inside the row keep working). */
export function bindRows(root: HTMLElement) {
  root.querySelectorAll<HTMLTableRowElement>("tr.click").forEach((tr) => tr.addEventListener("click", (e) => {
    if ((e.target as HTMLElement).closest("[data-stop]")) return;
    location.hash = `#/match/${tr.dataset.id}`;
  }));
}

const SIDE_SHORT = { home: "1", draw: "N", away: "2" } as const;
/** 1 / N / 2 probability bar (Pinnacle fair line); the outcome we bet on is highlighted. */
export const probBar = (probs: Bet["probs"], side: Bet["side"], big = false) =>
  `<div class="pbar ${big ? "pbar-big" : ""}">${(["home", "draw", "away"] as const).map((s) =>
    `<span class="pb ${s === side ? "pb-on" : ""}" style="flex:${Math.max(probs[s], 0.04)}" title="${SIDE_SHORT[s]} ${Math.round(probs[s] * 100)} %">
      <b>${big ? `${SIDE_SHORT[s]} · ` : ""}${Math.round(probs[s] * 100)}%</b></span>`).join("")}</div>`;
