import { attachEquityHover, clvChart, drawdownChart, equityChart, groupTable, monthlyGrid } from "../charts";
import { eur, odds, pct } from "../format";
import type { SiteData } from "../types";
import { kpiStrip } from "./shared";

export function renderPerformance(app: HTMLElement, data: SiteData) {
  const k = data.kpis;
  if (!k) { app.innerHTML = `<div class="empty pad">Pas encore de pari réglé.</div>`; return; }
  app.innerHTML = `
    <section class="sec"><div class="sec-head"><h2>Performance</h2><span class="k">Depuis le ${new Date(k.since).toLocaleDateString("fr-FR")} · mises en demi-Kelly</span></div></section>
    ${kpiStrip([
      ["Bankroll", eur(k.bankroll), `départ ${eur(data.start_bankroll)}`, ""],
      ["Rendement", pct(k.return), "cumulé", k.return >= 0 ? "up" : "down"],
      ["CLV moyen", k.clv === null ? "–" : pct(k.clv), `${Math.round(k.clv_coverage * 100)} % des paris mesurés`, k.clv !== null && k.clv >= 0 ? "up" : "down"],
      ["Drawdown max", pct(k.max_drawdown), new Date(k.max_drawdown_day).toLocaleDateString("fr-FR"), "down"],
    ])}
    ${kpiStrip([
      ["Paris", `${k.bets}`, `${Math.round(k.win_rate * 100)} % gagnants`, ""],
      ["ROI / pari", pct(k.roi), "mise fixe", k.roi >= 0 ? "" : "down"],
      ["Cote moyenne", odds(k.avg_price), `avantage moyen ${pct(k.avg_edge)}`, ""],
      ["Mise moyenne", pct(k.avg_stake).replace("+", ""), "de la bankroll", ""],
    ])}
    <section class="panel"><div class="panel-h"><h3>Bankroll</h3></div><div id="eq"></div></section>
    <section class="panel"><div class="panel-h"><h3>Drawdown</h3><span class="k">Écart au plus haut historique</span></div>${drawdownChart(data.equity)}</section>
    <section class="panel"><div class="panel-h"><h3>Rendement mensuel</h3></div>${monthlyGrid(data.monthly)}</section>
    <section class="panel"><div class="panel-h"><h3>Closing line value</h3><span class="k">Chaque point = un pari · ligne = moyenne glissante 30 paris</span></div>
      ${clvChart(data.clv_series)}
      <p class="note pad-x">Le CLV compare notre cote à la cote de clôture de Pinnacle. Positif en moyenne = on achète moins cher que le juste prix : c'est l'indicateur qui prédit les gains à long terme, bien avant le résultat des matchs.</p></section>
    <section class="panel"><div class="panel-h"><h3>Par championnat</h3></div>${groupTable(data.by_league, "Championnat")}</section>
    <section class="panel"><div class="panel-h"><h3>Par cote</h3></div>${groupTable(data.by_odds, "Cote")}</section>`;
  const eq = app.querySelector<HTMLElement>("#eq")!;
  eq.innerHTML = equityChart(data.equity, data.start_bankroll);
  attachEquityHover(eq, data.equity);
}
