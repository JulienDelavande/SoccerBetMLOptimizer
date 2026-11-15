import { betLabel, bookName, esc, eur, eur0, fmtDate, fmtDay, fmtLongDate, fmtTime, int, odds, pct, periodLabel, stakeFor } from "../format";
import { leagueLogo, teamLogo } from "../logos";
import type { Bet, SiteData } from "../types";
import { confirmBet, removeBet } from "../api";
import { currentUser } from "../session";
import { t } from "../i18n";
import { icon } from "../icons";

/** One KPI: [label, value, sub, tone, countUp?]. tone is "up" | "down" | "". Count-up is on by default;
 *  turn it off for odds and other values that must never tick (brief: never count odds). */
export type Kpi = [string, string, string, string, boolean?];

const kpiCell = ([l, v, s, tone, count = true]: Kpi) =>
  `<div class="kpi"><div class="k">${l}</div><div class="v num ${tone}"${count ? " data-count" : ""}>${v}</div>${s ? `<div class="s">${s}</div>` : ""}</div>`;

/** Scoreboard row of KPI tiles. `variant` "board" = hunter green tiles, "light" = raised cream tiles. */
export const kpiStrip = (items: Kpi[], variant: "board" | "light" = "board", reveal = true) =>
  `<section class="kpis kpis-${variant}"${reveal ? " data-reveal" : ""}>${items.map(kpiCell).join("")}</section>`;

export const BANKROLL_KEY = "bankroll";
export const savedBankroll = () => Math.max(0, Number(localStorage.getItem(BANKROLL_KEY) ?? "1000") || 0);

// The bot stakes at half Kelly; a user's preset rescales that (capped at 5% per bet).
const KELLY_BY_RISK: Record<string, number> = { prudent: 0.25, balanced: 0.5, aggressive: 1.0 };
export const riskStake = (fraction: number, risk: string) =>
  Math.min(fraction * ((KELLY_BY_RISK[risk] ?? 0.5) / 0.5), 0.05);

// Fallback for the offline Method page (no payload): the date bets started being published live.
export const LIVE_SINCE = "2026-10-19T00:00:00";
export const JIS_PHONE = "09 74 75 13 13";

/** Facts every view of the track record repeats: start date, honest length, settled count. */
export function recordFacts(data: Pick<SiteData, "live_since" | "generated_at" | "kpis">) {
  const since = data.live_since || LIVE_SINCE;
  return { since: fmtLongDate(since), period: periodLabel(since, data.generated_at), settled: data.kpis?.bets ?? 0 };
}

/** Visible notice next to the track record (not fine print): past results, short sample, information
 *  only, responsible gambling. Required framing for a French audience (Code de la consommation L121-2/4). */
export function recordNotice(data: Pick<SiteData, "live_since" | "generated_at" | "kpis">) {
  const f = recordFacts(data);
  return `<aside class="notice" data-reveal aria-labelledby="notice-h">
    <span class="notice-ic">${icon("alert")}</span>
    <div class="notice-b">
      <h2 id="notice-h">${t("Résultats passés : aucune garantie pour la suite")}</h2>
      <p>${t("Historique publié en direct depuis le {d} : {p}, {n} paris réglés. C'est un échantillon court et la variance est élevée : sur une période aussi courte, le rendement dépend surtout du hasard et peut s'inverser.", { d: f.since, p: f.period, n: int(f.settled) })}</p>
      <p>${t("Information uniquement, pas un conseil de pari adapté à votre situation. Ne misez que ce que vous pouvez vous permettre de perdre. Interdit aux moins de 18 ans.")}
        ${t("Joueurs Info Service :")} <a href="tel:+33974751313" class="nowrap">${JIS_PHONE}</a> ${t("(appel non surtaxé).")}</p>
    </div>
  </aside>`;
}

/** What the fictitious bankroll is (shown under every track-record bankroll curve). */
export const bankrollNote = (start: number) =>
  t("Simulation : {v} fictifs au départ, en suivant les mises publiées (demi-Kelly) aux cotes publiées. Les résultats réels diffèrent : limites de mise, cotes qui bougent, paris indisponibles.", { v: eur0(start) });

/** Page title block: big heading and an optional one-line context. */
export const pageHead = (title: string, sub = "", extra = "") =>
  `<header class="phead" data-reveal><h1>${title}</h1>${sub ? `<p class="phead-sub">${sub}</p>` : ""}${extra}</header>`;

/** Rounded content card with a title row; "flush" lets tables run edge to edge. */
export const card = (title: string, sub: string, body: string, variant = "") =>
  `<section class="card ${variant}" data-reveal><div class="card-h"><h2>${title}</h2>${sub ? `<p class="card-sub">${sub}</p>` : ""}</div>${body}</section>`;

/** Stadium LED board: hunter-green band of live facts separated by tomato dots. Pauses on hover and
 *  focus; the pause button is the touch (and WCAG 2.2.2) way to stop it. */
export function marquee(facts: string[]) {
  if (facts.length === 0) return "";
  const run = facts.map((f) => `<span class="mq-item">${esc(f)}</span><i class="mq-dot" aria-hidden="true"></i>`).join("");
  return `<section class="marquee" aria-label="${t("En direct")}" tabindex="0">
    <div class="mq-track"><div class="mq-run">${run}</div><div class="mq-run" aria-hidden="true">${run}</div></div>
    <button class="mq-pause" type="button" aria-pressed="false" aria-label="${t("Mettre le bandeau en pause")}">${icon("pause", "ic ic-pause")}${icon("play", "ic ic-play")}</button></section>`;
}

/** Wire the marquee pause toggle (call after rendering a page that has one). */
export function bindMarquee(root: HTMLElement) {
  root.querySelectorAll<HTMLButtonElement>(".mq-pause").forEach((btn) => btn.addEventListener("click", () => {
    const paused = btn.closest(".marquee")!.classList.toggle("paused");
    btn.setAttribute("aria-pressed", String(paused));
  }));
}

/** Match cell; with an id the teams become the row's link (stretched over the whole row). */
export const matchCell = (b: Pick<Bet, "home" | "away" | "league" | "league_key"> & { id?: string }, extra = "") => {
  const teams = `<span class="team">${teamLogo(b.home)}${esc(b.home)}</span><i aria-hidden="true">–</i><span class="team">${teamLogo(b.away)}${esc(b.away)}</span>`;
  return `<td class="match">${b.id ? `<a class="teams row-link" href="#/match/${esc(b.id)}">${teams}</a>` : `<div class="teams">${teams}</div>`}
    <small>${leagueLogo(b.league_key, b.league)}${esc(b.league)}</small>${extra}</td>`;
};

/** Result: bet link before kickoff, live tag, or settled score and gain (sign always shown). */
export const resultCell = (b: Bet) => {
  if (b.status === "upcoming")
    return b.link
      ? `<a class="go" href="${esc(b.link)}" target="_blank" rel="noopener nofollow" data-stop>${esc(bookName(b.book))}${icon("arrow-up-right")}</a>`
      : `<span class="res res-up">${t("À venir")}</span>`;
  if (b.status === "pending") return `<span class="res res-live"><i class="live-dot" aria-hidden="true"></i>${t("EN COURS")}</span>`;
  if (b.status === "void") return `<span class="res res-void">${t("Annulé")}</span>`;
  return `<span class="res res-${b.status}">${b.score ? `<span class="res-score">${esc(b.score)}</span>` : ""}${pct(b.gain, 2)}</span>`;
};

/** Bets table (history): rows open the match detail. */
export function betsTable(bets: Bet[], bankroll: number, opts: { date: "day" | "full"; placed?: Set<string> }) {
  const when = (k: string) => `${opts.date === "full" ? fmtDate(k) : fmtDay(k)}<small>${fmtTime(k)}</small>`;
  const rows = bets.map((b) => `<tr class="click ${b.status === "pending" ? "live" : ""}" data-id="${esc(b.id)}">
      <td class="mono when">${when(b.kickoff)}</td>
      ${matchCell(b, `<span class="pick-s">${esc(betLabel(b))} · ${odds(b.price)}</span><span class="pick-s">${resultCell(b)}</span>`)}
      <td class="hide-xs">${esc(betLabel(b))}${probBar(b.probs, b.side)}</td>
      <td class="r mono hide-xs">${odds(b.price)}</td>
      <td class="r mono hide-s">${odds(b.fair_price)}</td>
      <td class="r mono edge hide-xs">${pct(b.edge)}</td>
      <td class="r"><span class="stake">${eur(stakeFor(b.stake, bankroll))}</span>${placedBtn(b, bankroll, opts.placed)}</td>
      <td class="r hide-xs">${resultCell(b)}</td></tr>`).join("");
  return `<div class="tbl-card" data-reveal><table class="tbl bets"><thead><tr><th>${t("Coup d'envoi")}</th><th>${t("Match")}</th><th class="hide-xs">${t("Pari · probabilités 1 / N / 2")}</th><th class="r hide-xs">${t("Cote")}</th><th class="r hide-s">${t("Juste prix")}</th><th class="r hide-xs">${t("Avantage")}</th><th class="r">${t("Mise")}</th><th class="r hide-xs">${t("Résultat")}</th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

/** Day view: each bet as a match ticket (main part + perforated stub with the price).
 *  `placed` (Me view only) holds "match_id|side" of the bets the user said they played. */
export function betTickets(bets: Bet[], bankroll: number, placed?: Set<string>) {
  return `<ol class="tickets">${bets.map((b) => {
    const stake = eur(stakeFor(b.stake, bankroll));
    return `<li class="tk-w" data-reveal><article class="ticket st-${b.status}">
      <div class="tk-main">
        <div class="tk-top">
          <span class="tk-league">${leagueLogo(b.league_key, b.league)}<span title="${esc(b.league)}">${esc(b.league)}</span></span>
          <span class="tk-seat"><small>${t("Coup d'envoi")}</small><b>${fmtDay(b.kickoff)} · ${fmtTime(b.kickoff)}</b></span>
        </div>
        <h3 class="tk-teams"><a class="tk-link" href="#/match/${esc(b.id)}">
          <span class="team">${teamLogo(b.home, "crest crest-md")}<span>${esc(b.home)}</span></span>
          <span class="team">${teamLogo(b.away, "crest crest-md")}<span>${esc(b.away)}</span></span></a></h3>
        <div class="tk-pick"><span class="pick"><i aria-hidden="true"></i>${esc(betLabel(b))}</span>${probBar(b.probs, b.side)}</div>
      </div>
      <div class="tk-stub">
        <div class="tk-odds"><small title="${esc(bookName(b.book))}">${t("Cote")} · ${esc(bookName(b.book))}</small><b class="mono">${odds(b.price)}</b><span>${t("juste prix {v}", { v: odds(b.fair_price) })}</span></div>
        <dl class="tk-meta">
          <div><dt>${t("Mise")}</dt><dd class="mono">${stake}</dd></div>
          <div><dt>${t("Avantage")}</dt><dd class="mono edge-chip">${pct(b.edge)}</dd></div>
        </dl>
        <div class="tk-act">${resultCell(b)}${placedBtn(b, bankroll, placed)}</div>
      </div>
    </article></li>`;
  }).join("")}</ol>`;
}

/** "J'ai joué" toggle: Me view only (placed set given), for bets not yet settled. */
const placedBtn = (b: Bet, bankroll: number, placed?: Set<string>) => {
  if (!placed || !currentUser() || (b.status !== "upcoming" && b.status !== "pending")) return "";
  const on = placed.has(`${b.id}|${b.side}`);
  return `<button class="placed-btn${on ? " on" : ""}" aria-pressed="${on}" data-stop data-placed="${esc(b.id)}|${b.side}|${b.price}|${stakeFor(b.stake, bankroll)}">${placedLabel(on)}</button>`;
};
const placedLabel = (on: boolean) => (on ? `${icon("check")}${t("joué")}` : t("j'ai joué"));

/** Reflect a fresh "played" set on already-rendered toggles (no re-render, no motion). */
export function paintPlaced(root: HTMLElement, placed: Set<string>) {
  root.querySelectorAll<HTMLButtonElement>("[data-placed]").forEach((btn) => {
    const [id, side] = btn.dataset.placed!.split("|");
    const on = placed.has(`${id}|${side}`);
    btn.classList.toggle("on", on);
    btn.setAttribute("aria-pressed", String(on));
    btn.innerHTML = placedLabel(on);
  });
}

const rememberScroll = () => sessionStorage.setItem(`scroll:${location.hash || "#/"}`, String(window.scrollY));

/** Opens the match detail from a row or ticket (links inside keep working) and wires "j'ai joué". */
export function bindRows(root: HTMLElement, placed?: Set<string>) {
  root.querySelectorAll<HTMLTableRowElement>("tr.click").forEach((tr) => tr.addEventListener("click", (e) => {
    // The row link (stretched over the row) navigates by itself; this catches clicks it does not cover.
    if ((e.target as HTMLElement).closest("[data-stop], a")) return;
    rememberScroll();
    location.hash = `#/match/${tr.dataset.id}`;
  }));
  root.querySelectorAll<HTMLAnchorElement>(".tk-link, .row-link").forEach((a) => a.addEventListener("click", rememberScroll));
  root.querySelectorAll<HTMLButtonElement>("[data-placed]").forEach((btn) => btn.addEventListener("click", async (e) => {
    e.stopPropagation();
    const [match_id, side, price, stake] = btn.dataset.placed!.split("|");
    const key = `${match_id}|${side}`;
    const paint = (on: boolean) => {
      btn.classList.toggle("on", on);
      btn.setAttribute("aria-pressed", String(on));
      btn.innerHTML = placedLabel(on);
      if (on) placed?.add(key); else placed?.delete(key);
    };
    const done = !btn.classList.contains("on");
    paint(done);
    try {
      if (done) await confirmBet({ match_id, side, recommended_price: Number(price), stake: Number(stake) });
      else await removeBet(match_id, side);
    } catch { paint(!done); }
  }));
}

const SIDE_SHORT = { home: "1", draw: "N", away: "2" } as const;
/** Spoken summary of a probability bar, e.g. "1 35 %, N 28 %, 2 37 % · pari : 2". */
export const probLabel = (probs: Bet["probs"], side: Bet["side"]) =>
  `${(["home", "draw", "away"] as const).map((s) => `${t(SIDE_SHORT[s])} ${Math.round(probs[s] * 100)} %`).join(", ")} · ${t("pari : {s}", { s: t(SIDE_SHORT[side]) })}`;
/** 1 / N / 2 probability bar (Pinnacle fair line); the outcome we bet on is filled and ticked. */
export const probBar = (probs: Bet["probs"], side: Bet["side"], big = false) =>
  `<div class="pbar ${big ? "pbar-big" : ""}" role="img" aria-label="${esc(probLabel(probs, side))}">${(["home", "draw", "away"] as const).map((s) =>
    `<span class="pb ${s === side ? "pb-on" : ""}" style="flex:${Math.max(probs[s], 0.04)}" aria-hidden="true">
      <b>${s === side ? "✓ " : ""}${big ? `${t(SIDE_SHORT[s])} · ` : ""}${Math.round(probs[s] * 100)}%</b></span>`).join("")}</div>`;
