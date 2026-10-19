import { betLabel, esc, fmtDate, odds, pct } from "../format";
import type { Bet, SiteData } from "../types";

const PAGE = 60;
const RESULT = { won: "Gagné", lost: "Perdu", void: "Annulé" } as Record<string, string>;

export function renderHistory(app: HTMLElement, data: SiteData) {
  const leagues = [...new Set(data.history.map((b) => b.league))].sort();
  app.innerHTML = `
    <section class="sec"><div class="sec-head"><h2>Historique</h2><span class="k">${data.history.length} paris · gain en % de la bankroll du jour</span></div>
      <div class="filters">
        <div class="seg" id="st">${["Tous", "Gagnés", "Perdus"].map((l, i) => `<button data-v="${["", "won", "lost"][i]}" class="${i ? "" : "on"}">${l}</button>`).join("")}</div>
        <select id="lg"><option value="">Tous les championnats</option>${leagues.map((l) => `<option>${esc(l)}</option>`).join("")}</select>
      </div></section>
    <div id="rows"></div>`;
  let status = "", league = "", shown = PAGE;
  const draw = () => {
    const rows = data.history.filter((b) => (!status || b.status === status) && (!league || b.league === league));
    app.querySelector("#rows")!.innerHTML = table(rows.slice(0, shown)) +
      (rows.length > shown ? `<button class="more" id="more">Voir plus (${rows.length - shown})</button>` : "");
    app.querySelector("#more")?.addEventListener("click", () => { shown += PAGE; draw(); });
  };
  app.querySelectorAll<HTMLButtonElement>("#st button").forEach((b) => b.addEventListener("click", () => {
    app.querySelectorAll("#st button").forEach((x) => x.classList.remove("on"));
    b.classList.add("on"); status = b.dataset.v!; shown = PAGE; draw();
  }));
  app.querySelector<HTMLSelectElement>("#lg")!.addEventListener("change", (e) => { league = (e.target as HTMLSelectElement).value; shown = PAGE; draw(); });
  draw();
}

function table(bets: Bet[]) {
  if (bets.length === 0) return `<div class="empty">Aucun pari.</div>`;
  return `<table class="tbl hist"><thead><tr><th>Date</th><th>Match</th><th class="hide-xs">Pari</th><th class="r">Cote</th><th class="r hide-s">Mise</th><th class="r hide-xs">Score</th><th class="r">Résultat</th><th class="r hide-s">CLV</th></tr></thead><tbody>
    ${bets.map((b) => `<tr>
      <td class="mono">${fmtDate(b.kickoff)}</td>
      <td class="match">${esc(b.home)} – ${esc(b.away)}<small>${esc(b.league)}</small><span class="pick-s">${esc(betLabel(b))} · ${b.score ?? "–"}</span></td>
      <td class="hide-xs">${esc(betLabel(b))}</td>
      <td class="r mono">${odds(b.price)}</td>
      <td class="r mono hide-s">${pct(b.stake).replace("+", "")}</td>
      <td class="r mono hide-xs">${b.score ?? "–"}</td>
      <td class="r"><span class="res res-${b.status}">${b.status === "void" ? RESULT.void : pct(b.gain, 2)}</span></td>
      <td class="r mono hide-s ${b.clv !== null && b.clv >= 0 ? "up" : "down"}">${b.clv === null ? "–" : pct(b.clv)}</td></tr>`).join("")}
  </tbody></table>`;
}
