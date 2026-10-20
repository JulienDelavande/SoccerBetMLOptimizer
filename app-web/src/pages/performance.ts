import { attachEquityHover, clvChart, drawdownChart, equityChart, groupTable, monthlyGrid } from "../charts";
import { getMyBets } from "../api";
import { eur, odds, pct } from "../format";
import type { SiteData } from "../types";
import { kpiStrip } from "./shared";
import { currentUser } from "../session";
import { getView } from "../view";
import { locale, t } from "../i18n";

export function renderPerformance(app: HTMLElement, data: SiteData) {
  const user = currentUser();
  if (user && getView() === "me") { renderMyPerformance(app, user.bankroll); return; }
  const k = data.kpis;
  if (!k) { app.innerHTML = `<div class="empty pad">${t("Pas encore de pari réglé.")}</div>`; return; }
  app.innerHTML = `
    <section class="sec"><div class="sec-head"><h2>${t("Performance")}</h2><span class="k">${t("Depuis le {d} · mises en demi-Kelly", { d: new Date(k.since).toLocaleDateString(locale()) })}</span></div></section>
    ${kpiStrip([
      [t("Bankroll"), eur(k.bankroll), `${t("départ")} ${eur(data.start_bankroll)}`, ""],
      [t("Rendement"), pct(k.return), t("cumulé"), k.return >= 0 ? "up" : "down"],
      [t("CLV moyen"), k.clv === null ? "–" : pct(k.clv), t("{n} % des paris mesurés", { n: Math.round(k.clv_coverage * 100) }), k.clv !== null && k.clv >= 0 ? "up" : "down"],
      [t("Drawdown max"), pct(k.max_drawdown), new Date(k.max_drawdown_day).toLocaleDateString(locale()), "down"],
    ])}
    ${kpiStrip([
      [t("Paris"), `${k.bets}`, t("{n} % gagnants", { n: Math.round(k.win_rate * 100) }), ""],
      [t("ROI / pari"), pct(k.roi), t("mise fixe"), k.roi >= 0 ? "" : "down"],
      [t("Cote moyenne"), odds(k.avg_price), t("avantage moyen {v}", { v: pct(k.avg_edge) }), ""],
      [t("Mise moyenne"), pct(k.avg_stake).replace("+", ""), t("de la bankroll"), ""],
    ])}
    <section class="panel"><div class="panel-h"><h3>${t("Bankroll")}</h3></div><div id="eq"></div></section>
    <section class="panel"><div class="panel-h"><h3>${t("Drawdown")}</h3><span class="k">${t("Écart au plus haut historique")}</span></div>${drawdownChart(data.equity)}</section>
    <section class="panel"><div class="panel-h"><h3>${t("Rendement mensuel")}</h3></div>${monthlyGrid(data.monthly)}</section>
    <section class="panel"><div class="panel-h"><h3>${t("Closing line value")}</h3><span class="k">${t("Chaque point = un pari · ligne = moyenne glissante 30 paris")}</span></div>
      ${clvChart(data.clv_series)}
      <p class="note pad-x">${t("Le CLV compare notre cote à la cote de clôture de Pinnacle. Positif en moyenne = on achète moins cher que le juste prix : c'est l'indicateur qui prédit les gains à long terme, bien avant le résultat des matchs.")}</p></section>
    <section class="panel"><div class="panel-h"><h3>${t("Par championnat")}</h3></div>${groupTable(data.by_league, t("Championnat"))}</section>
    <section class="panel"><div class="panel-h"><h3>${t("Par cote")}</h3></div>${groupTable(data.by_odds, t("Cote"))}</section>`;
  const eq = app.querySelector<HTMLElement>("#eq")!;
  eq.innerHTML = equityChart(data.equity, data.start_bankroll);
  attachEquityHover(eq, data.equity);
}

/** "Me" view: the signed-in user's own realised performance, from their confirmed bets. */
function renderMyPerformance(app: HTMLElement, bankroll: number) {
  app.innerHTML = `<section class="sec"><div class="sec-head"><h2>${t("Ma performance")}</h2></div></section>
    <div id="myperf"><div class="empty pad">${t("Chargement…")}</div></div>`;
  getMyBets().then(({ stats: s }) => {
    const box = app.querySelector<HTMLElement>("#myperf")!;
    if (s.settled === 0) { box.innerHTML = `<div class="empty pad">${t("Confirme tes paris pour suivre ta bankroll réelle.")}</div>`; return; }
    const eq = [{ day: "", bankroll }, ...s.equity.map((p) => ({ day: p.t.slice(0, 10), bankroll: bankroll + p.delta }))];
    box.innerHTML = kpiStrip([
      [t("Gain net"), `${s.bankroll_delta >= 0 ? "+" : "−"}${eur(Math.abs(s.bankroll_delta))}`, "", s.bankroll_delta >= 0 ? "up" : "down"],
      [t("ROI / pari"), s.roi === null ? "–" : pct(s.roi), t("mise fixe"), s.roi !== null && s.roi >= 0 ? "up" : "down"],
      [t("Réussite"), s.win_rate === null ? "–" : `${Math.round(s.win_rate * 100)} %`, "", ""],
      [t("Paris réglés"), `${s.settled}`, "", ""],
    ]) + `<section class="panel"><div class="panel-h"><h3>${t("Bankroll")}</h3></div><div id="myeq"></div></section>`;
    const el = app.querySelector<HTMLElement>("#myeq")!;
    el.innerHTML = equityChart(eq, bankroll);
    attachEquityHover(el, eq);
  }).catch(() => { app.querySelector("#myperf")!.innerHTML = `<div class="empty pad">${t("Erreur de chargement.")}</div>`; });
}
