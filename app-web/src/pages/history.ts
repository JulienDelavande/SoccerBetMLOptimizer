import { getMyBets, removeBet } from "../api";
import { esc, eur, fmtDate, odds } from "../format";
import type { MyBet } from "../api";
import type { SiteData } from "../types";
import { betsTable, bindRows, pageHead, savedBankroll } from "./shared";
import { icon } from "../icons";
import { currentUser } from "../session";
import { getView } from "../view";
import { t } from "../i18n";

const PAGE = 60;

export function renderHistory(app: HTMLElement, data: SiteData) {
  if (currentUser() && getView() === "me") { renderMyHistory(app); return; }
  const settled = data.bets.filter((b) => ["won", "lost", "void"].includes(b.status)).sort((a, b) => b.kickoff.localeCompare(a.kickoff));
  const leagues = [...new Set(settled.map((b) => b.league))].sort();
  app.innerHTML = `
    ${pageHead(t("Historique"), t("{n} paris · mise pour {b} € · gain en % de la bankroll du jour", { n: settled.length, b: savedBankroll() }),
      `<div class="filters">
        <div class="seg" id="st" role="group" aria-label="${t("Résultat")}">${["Tous", "Gagnés", "Perdus"].map((l, i) => `<button data-v="${["", "won", "lost"][i]}" class="${i ? "" : "on"}" aria-pressed="${!i}">${t(l)}</button>`).join("")}</div>
        <label class="select"><span class="sr-only">${t("Championnat")}</span><select id="lg"><option value="">${t("Tous les championnats")}</option>${leagues.map((l) => `<option>${esc(l)}</option>`).join("")}</select></label>
      </div>`)}
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
    app.querySelectorAll("#st button").forEach((x) => { x.classList.remove("on"); x.setAttribute("aria-pressed", "false"); });
    b.classList.add("on"); b.setAttribute("aria-pressed", "true"); status = b.dataset.v!; shown = PAGE; draw();
  }));
  app.querySelector<HTMLSelectElement>("#lg")!.addEventListener("change", (e) => { league = (e.target as HTMLSelectElement).value; shown = PAGE; draw(); });
  draw();
}


/** "Me" view: the user's confirmed bets. */
function renderMyHistory(app: HTMLElement) {
  app.innerHTML = `${pageHead(t("Mon historique"))}<div id="rows"><div class="empty">${t("Chargement…")}</div></div>`;
  const box = app.querySelector<HTMLElement>("#rows")!;
  const draw = () => getMyBets().then(({ bets }) => {
    if (bets.length === 0) { box.innerHTML = `<div class="empty">${t("Aucun pari confirmé. Depuis les paris du jour, indique ceux que tu as joués.")}</div>`; return; }
    box.innerHTML = myBetsTable(bets);
    box.querySelectorAll<HTMLButtonElement>("[data-del]").forEach((btn) => btn.addEventListener("click", async () => {
      const [mid, side] = btn.dataset.del!.split("|");
      btn.disabled = true;
      try { await removeBet(mid, side); await draw(); }
      catch {
        btn.disabled = false;
        box.querySelector("#delerr")?.remove();
        box.insertAdjacentHTML("afterbegin", `<p class="note down" id="delerr" role="alert">${t("Impossible de retirer ce pari. Réessaie dans un instant.")}</p>`);
      }
    }));
  }).catch(() => { box.innerHTML = `<div class="empty">${t("Erreur de chargement.")}</div>`; });
  draw();
}

const dash = "–";
/** Newest kick-off first; bets without a date go last. */
export const sortMyBets = (bets: MyBet[]) =>
  [...bets].sort((a, b) => (b.commence_time ?? "").localeCompare(a.commence_time ?? ""));

/** Result cell text and tone for one confirmed bet. */
export function myResult(b: MyBet): { text: string; tone: string } {
  if (b.status === "void") return { text: t("Annulé"), tone: "" };
  if (b.status === "placed") return { text: t("en attente"), tone: "" };
  if (b.settled_gain == null) return { text: t("À venir"), tone: "" };
  return { text: `${b.settled_gain >= 0 ? "+" : "−"}${eur(Math.abs(b.settled_gain))}`, tone: b.settled_gain >= 0 ? "up" : "down" };
}

const myPrice = (b: MyBet) => { const p = b.placed_price ?? b.recommended_price; return p == null ? dash : odds(p); };

export function myBetsTable(bets: MyBet[]) {
  const rows = sortMyBets(bets).map((b) => {
    const res = myResult(b), stake = b.stake != null ? eur(b.stake) : dash;
    return `<tr><td class="mono when">${b.commence_time ? fmtDate(b.commence_time) : dash}</td>
      <td class="match">${esc(b.home_team ?? dash)} – ${esc(b.away_team ?? dash)}
        <span class="pick-s">${esc(label(b))} · ${myPrice(b)} · ${stake}</span></td>
      <td class="hide-xs">${esc(label(b))}</td><td class="r mono hide-xs">${myPrice(b)}</td>
      <td class="r mono hide-xs">${stake}</td>
      <td class="r mono ${res.tone}">${res.text}</td>
      <td class="r"><button class="ibtn ibtn-sm" aria-label="${t("Retirer ce pari")}" data-del="${esc(b.match_id)}|${esc(b.side)}">${icon("x")}</button></td></tr>`;
  }).join("");
  return `<div class="tbl-card"><table class="tbl"><thead><tr><th>${t("Date")}</th><th>${t("Match")}</th><th class="hide-xs">${t("Pari")}</th><th class="r hide-xs">${t("Cote")}</th><th class="r hide-xs">${t("Mise")}</th><th class="r">${t("Résultat")}</th><th><span class="sr-only">${t("Retirer ce pari")}</span></th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

const label = (b: MyBet) =>
  b.side === "draw" ? t("Match nul") : t("Victoire {team}", { team: (b.side === "home" ? b.home_team : b.away_team) ?? dash });
