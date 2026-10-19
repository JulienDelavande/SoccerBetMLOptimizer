import { esc } from "../format";
import type { SiteData } from "../types";
import { betsTable, bindRows, savedBankroll } from "./shared";

const PAGE = 60;

export function renderHistory(app: HTMLElement, data: SiteData) {
  const settled = data.bets.filter((b) => ["won", "lost", "void"].includes(b.status)).sort((a, b) => b.kickoff.localeCompare(a.kickoff));
  const leagues = [...new Set(settled.map((b) => b.league))].sort();
  app.innerHTML = `
    <section class="sec"><div class="sec-head"><h2>Historique</h2><span class="k">${settled.length} paris · mise pour ${savedBankroll()} € · gain en % de la bankroll du jour</span></div>
      <div class="filters">
        <div class="seg" id="st">${["Tous", "Gagnés", "Perdus"].map((l, i) => `<button data-v="${["", "won", "lost"][i]}" class="${i ? "" : "on"}">${l}</button>`).join("")}</div>
        <select id="lg"><option value="">Tous les championnats</option>${leagues.map((l) => `<option>${esc(l)}</option>`).join("")}</select>
      </div></section>
    <div id="rows"></div>`;
  let status = "", league = "", shown = PAGE;
  const draw = () => {
    const rows = settled.filter((b) => (!status || b.status === status) && (!league || b.league === league));
    const box = app.querySelector<HTMLElement>("#rows")!;
    box.innerHTML = (rows.length ? betsTable(rows.slice(0, shown), savedBankroll(), { date: "full" }) : `<div class="empty">Aucun pari.</div>`) +
      (rows.length > shown ? `<button class="more" id="more">Voir plus (${rows.length - shown})</button>` : "");
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
