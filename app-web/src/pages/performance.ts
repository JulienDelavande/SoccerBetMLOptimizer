import { EQ_WIDE, attachEquityHover, clvChart, drawdownChart, equityChart, groupTable, monthlyGrid } from "../charts";
import { getMyBets } from "../api";
import { eur, int, odds, pct, prevDayKey } from "../format";
import type { MyStats } from "../api";
import type { EquityPoint } from "../types";
import type { SiteData } from "../types";
import { card, kpiStrip, pageHead } from "./shared";
import { currentUser } from "../session";
import { getView } from "../view";
import { locale, t } from "../i18n";

export function renderPerformance(app: HTMLElement, data: SiteData) {
  const user = currentUser();
  if (user && getView() === "me") { renderMyPerformance(app, user.bankroll); return; }
  const k = data.kpis;
  if (!k) { app.innerHTML = `<div class="empty pad">${t("Pas encore de pari réglé.")}</div>`; return; }
  app.innerHTML = `
    ${pageHead(t("Performance"), t("Depuis le {d} · mises en demi-Kelly", { d: new Date(k.since).toLocaleDateString(locale()) }))}
    ${kpiStrip([
      [t("Bankroll"), eur(k.bankroll), `${t("départ")} ${eur(data.start_bankroll)}`, ""],
      [t("Rendement"), pct(k.return), t("cumulé"), k.return >= 0 ? "up" : "down"],
      [t("CLV moyen"), k.clv === null ? "–" : pct(k.clv), t("{n} % des paris mesurés", { n: Math.round(k.clv_coverage * 100) }), k.clv !== null && k.clv >= 0 ? "up" : "down"],
      [t("Drawdown max"), pct(k.max_drawdown), new Date(k.max_drawdown_day).toLocaleDateString(locale()), "down"],
    ])}
    ${kpiStrip([
      [t("Paris"), int(k.bets), t("{n} % gagnants", { n: Math.round(k.win_rate * 100) }), ""],
      [t("ROI / pari"), pct(k.roi), t("mise fixe"), k.roi >= 0 ? "" : "down"],
      [t("Cote moyenne"), odds(k.avg_price), t("avantage moyen {v}", { v: pct(k.avg_edge) }), "", false],
      [t("Mise moyenne"), pct(k.avg_stake).replace("+", ""), t("de la bankroll"), ""],
    ], "light")}
    ${card(t("Bankroll"), "", `<div id="eq"></div>`)}
    ${card(t("Drawdown"), t("Écart au plus haut historique"), drawdownChart(data.equity))}
    ${card(t("Rendement mensuel"), "", monthlyGrid(data.monthly))}
    ${card(t("Closing line value"), t("Chaque point = un pari · ligne = moyenne glissante 30 paris"),
      `${clvChart(data.clv_series)}<p class="note">${t("Le CLV compare notre cote à la cote de clôture de Pinnacle. Positif en moyenne = on achète moins cher que le juste prix : c'est l'indicateur qui prédit les gains à long terme, bien avant le résultat des matchs.")}</p>`)}
    ${card(t("Par championnat"), "", groupTable(data.by_league, t("Championnat")), "flush")}
    ${card(t("Par cote"), "", groupTable(data.by_odds, t("Cote")), "flush")}`;
  const eq = app.querySelector<HTMLElement>("#eq")!;
  eq.innerHTML = equityChart(data.equity, data.start_bankroll, { draw: true, box: EQ_WIDE });
  attachEquityHover(eq, data.equity);
}

/** "Me" view: the signed-in user's own realised performance, from their confirmed bets. */
function renderMyPerformance(app: HTMLElement, bankroll: number) {
  app.innerHTML = `${pageHead(t("Ma performance"))}
    <div id="myperf"><div class="empty pad">${t("Chargement…")}</div></div>`;
  getMyBets().then(({ stats: s }) => {
    const box = app.querySelector<HTMLElement>("#myperf")!;
    if (s.settled === 0) { box.innerHTML = `<div class="empty pad">${t("Confirme tes paris pour suivre ta bankroll réelle.")}</div>`; return; }
    const eq = myEquity(bankroll, s.equity);
    box.innerHTML = kpiStrip([
      [t("Gain net"), `${s.bankroll_delta >= 0 ? "+" : "−"}${eur(Math.abs(s.bankroll_delta))}`, "", s.bankroll_delta >= 0 ? "up" : "down"],
      [t("ROI / pari"), s.roi === null ? "–" : pct(s.roi), t("mise fixe"), s.roi !== null && s.roi >= 0 ? "up" : "down"],
      [t("Réussite"), s.win_rate === null ? "–" : `${Math.round(s.win_rate * 100)} %`, "", ""],
      [t("Paris réglés"), int(s.settled), "", ""],
    ]) + card(t("Bankroll"), "", `<div id="myeq"></div>`);
    const el = app.querySelector<HTMLElement>("#myeq")!;
    el.innerHTML = equityChart(eq, bankroll, { draw: true, box: EQ_WIDE });
    attachEquityHover(el, eq);
  }).catch(() => { app.querySelector("#myperf")!.innerHTML = `<div class="empty pad">${t("Erreur de chargement.")}</div>`; });
}

/** The user's equity curve: their bankroll the day before the first settled bet, then bankroll + delta. */
export function myEquity(bankroll: number, equity: MyStats["equity"]): EquityPoint[] {
  const pts = equity.map((p) => ({ day: p.t.slice(0, 10), bankroll: bankroll + p.delta }));
  return pts.length ? [{ day: prevDayKey(pts[0].day), bankroll }, ...pts] : [];
}
