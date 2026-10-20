import { getMyBets, removeBet } from "../api";
import { esc, eur, fmtDate } from "../format";
import type { MyBet } from "../api";
import type { SiteData } from "../types";
import { betsTable, bindRows, savedBankroll } from "./shared";
import { currentUser } from "../session";
import { getView } from "../view";
import { t } from "../i18n";

const PAGE = 60;

export function renderHistory(app: HTMLElement, data: SiteData) {
  if (currentUser() && getView() === "me") { renderMyHistory(app); return; }
  const settled = data.bets.filter((b) => ["won", "lost", "void"].includes(b.status)).sort((a, b) => b.kickoff.localeCompare(a.kickoff));
  const leagues = [...new Set(settled.map((b) => b.league))].sort();
  app.innerHTML = `
    <section class="sec"><div class="sec-head"><h2>${t("Historique")}</h2><span class="k">${t("{n} paris · mise pour {b} € · gain en % de la bankroll du jour", { n: settled.length, b: savedBankroll() })}</span></div>
      <div class="filters">
        <div class="seg" id="st">${["Tous", "Gagnés", "Perdus"].map((l, i) => `<button data-v="${["", "won", "lost"][i]}" class="${i ? "" : "on"}">${t(l)}</button>`).join("")}</div>
        <select id="lg"><option value="">${t("Tous les championnats")}</option>${leagues.map((l) => `<option>${esc(l)}</option>`).join("")}</select>
      </div></section>
    <div id="rows"></div>`;
  let status = "", league = "", shown = PAGE;
  const draw = () => {
    const rows = settled.filter((b) => (!status || b.status === status) && (!league || b.league === league));
    const box = app.querySelector<HTMLElement>("#rows")!;
    box.innerHTML = (rows.length ? betsTable(rows.slice(0, shown), savedBankroll(), { date: "full" }) : `<div class="empty">${t("Aucun pari.")}</div>`) +
      (rows.length > shown ? `<button class="more" id="more">${t("Voir plus ({n})", { n: rows.length - shown })}</button>` : "");
    bindRows(box);
    box.querySelector("#more")?.addEventListener("click", () => { shown += PAGE; draw(); });
  };
  app.querySelectorAll<HTMLButtonElement>("#st button").forEach((b) => b.addEventListener("click", () => {
    app.querySelectorAll("#st button").forEach((x) => x.classList.remove("on"));
    b.classList.add("on"); status = b.dataset.v!; shown = PAGE; draw();
  }));
  app.querySelector<HTMLSelectElement>("#lg")!.addEventListener("change", (e) => { league = (e.target as HTMLSelectElement).value; shown = PAGE; draw(); });
  draw();
}


/** "Me" view: the user's confirmed bets. */
function renderMyHistory(app: HTMLElement) {
  app.innerHTML = `<section class="sec"><div class="sec-head"><h2>${t("Mon historique")}</h2></div></section><div id="rows"><div class="empty">${t("Chargement…")}</div></div>`;
  const draw = () => getMyBets().then(({ bets }) => {
    const box = app.querySelector<HTMLElement>("#rows")!;
    if (bets.length === 0) { box.innerHTML = `<div class="empty">${t("Aucun pari confirmé. Depuis les paris du jour, indique ceux que tu as joués.")}</div>`; return; }
    box.innerHTML = `<table class="tbl"><thead><tr><th>${t("Date")}</th><th>${t("Match")}</th><th>${t("Pari")}</th><th class="r">${t("Cote")}</th><th class="r">${t("Mise")}</th><th class="r">${t("Résultat")}</th><th></th></tr></thead><tbody>
      ${bets.map((b: MyBet) => `<tr><td class="mono">${b.commence_time ? fmtDate(b.commence_time) : "–"}</td>
        <td class="match">${esc(b.home_team ?? "")} – ${esc(b.away_team ?? "")}</td>
        <td>${label(b)}</td><td class="r mono">${b.placed_price ?? b.recommended_price ?? "–"}</td>
        <td class="r mono">${b.stake != null ? eur(b.stake) : "–"}</td>
        <td class="r">${b.status === "placed" ? t("en attente") : b.settled_gain != null ? (b.settled_gain >= 0 ? "+" : "−") + eur(Math.abs(b.settled_gain)) : t("À venir")}</td>
        <td class="r"><button class="go" data-del="${esc(b.match_id)}|${esc(b.side)}">✕</button></td></tr>`).join("")}
    </tbody></table>`;
    box.querySelectorAll<HTMLButtonElement>("[data-del]").forEach((btn) => btn.addEventListener("click", async () => {
      const [mid, side] = btn.dataset.del!.split("|");
      await removeBet(mid, side); draw();
    }));
  }).catch(() => { app.querySelector("#rows")!.innerHTML = `<div class="empty">${t("Erreur de chargement.")}</div>`; });
  draw();
}

const label = (b: MyBet) =>
  b.side === "draw" ? t("Match nul") : t("Victoire {team}", { team: b.side === "home" ? (b.home_team ?? "") : (b.away_team ?? "") });
