import { attachEquityHover, clvChart, drawdownChart, equityChart, groupTable, monthlyGrid } from "../charts";
import { eur, odds, pct } from "../format";
import type { SiteData } from "../types";
import { kpiStrip } from "./shared";
import { locale, t } from "../i18n";

export function renderPerformance(app: HTMLElement, data: SiteData) {
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
