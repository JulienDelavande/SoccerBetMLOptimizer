import { deleteAccount, getMyBets, removeBet, telegramLink, updateSettings } from "../api";
import type { MyBet, MyStats, UserProfile } from "../api";
import { esc, eur, fmtDate, pct } from "../format";
import { currentUser, logout, renderGoogleButton, setUser } from "../session";
import { BOOKS_ALL } from "./books";
import { t } from "../i18n";

const RISK = [
  ["prudent", "Prudent", "quart de Kelly · mises prudentes"],
  ["balanced", "Équilibré", "demi-Kelly · recommandé"],
  ["aggressive", "Agressif", "Kelly plein · plus volatil"],
] as const;

export function renderAccount(app: HTMLElement) {
  const user = currentUser();
  app.innerHTML = user ? "" : loggedOut();
  if (!user) {
    const slot = app.querySelector<HTMLElement>("#gbtn")!;
    renderGoogleButton(slot, (u) => { setUser(u); renderAccount(app); });
    return;
  }
  renderDashboard(app, user);
}

function loggedOut() {
  return `<section class="sec"><div class="sec-head"><h2>${t("Mon compte")}</h2></div></section>
    <section class="acct-hero">
      <div class="acct-pitch">
        <p class="lead">${t("Un espace perso gratuit pour suivre la méthode à ta façon.")}</p>
        <ul class="perks">
          <li><b>${t("Tes bookmakers")}</b> — ${t("ne vois que les paris jouables chez toi.")}</li>
          <li><b>${t("Ton risque")}</b> — ${t("prudent, équilibré ou agressif.")}</li>
          <li><b>${t("Ta bankroll")}</b> — ${t("mises calculées pour ton montant, suivi de tes gains réels.")}</li>
          <li><b>${t("Alertes Telegram")}</b> — ${t("les paris du jour, dès qu'ils sortent.")}</li>
        </ul>
        <div id="gbtn" class="gbtn"></div>
      </div>
    </section>`;
}

function renderDashboard(app: HTMLElement, user: UserProfile) {
  app.innerHTML = `
    <section class="sec"><div class="sec-head">
      <h2>${t("Mon compte")}</h2>
      <div class="acct-id">${user.avatar_url ? `<img src="${esc(user.avatar_url)}" alt="" class="avatar">` : ""}<span>${esc(user.name ?? user.email ?? "")}</span><button class="go" id="logout">${t("Déconnexion")}</button></div>
    </div></section>
    <section class="panel"><div class="panel-h"><h3>${t("Réglages")}</h3></div>
      <div class="settings">
        <label class="field"><span class="k">${t("Ma bankroll")}</span><input id="bk" type="number" min="1" step="10" value="${user.bankroll}"> €</label>
        <div class="field"><span class="k">${t("Niveau de risque")}</span><div class="seg" id="risk">${RISK.map(([v, l, d]) =>
          `<button data-v="${v}" class="${user.risk_preset === v ? "on" : ""}" title="${t(d)}">${t(l)}</button>`).join("")}</div></div>
        <div class="field full"><span class="k">${t("Mes bookmakers")} <small>${t("(aucun = tous)")}</small></span><div class="books" id="books">${BOOKS_ALL.map((b) =>
          `<button data-b="${b.key}" class="${user.books.includes(b.key) ? "on" : ""}">${esc(b.label)}</button>`).join("")}</div></div>
      </div>
    </section>
    <section class="panel"><div class="panel-h"><h3>${t("Alertes Telegram")}</h3></div>
      <div class="tg pad-x" id="tg"></div></section>
    <section class="panel"><div class="panel-h"><h3>${t("Mes stats")}</h3></div><div id="mystats" class="pad-x"><div class="empty">${t("Chargement…")}</div></div></section>
    <section class="panel"><div class="panel-h"><h3>${t("Mes paris")}</h3></div><div id="mybets"><div class="empty">${t("Chargement…")}</div></div></section>
    <section class="panel warn"><div class="panel-h"><h3>${t("Compte")}</h3></div>
      <p class="pad-x">${t("Supprimer ton compte efface définitivement tes réglages et tes paris.")}</p>
      <button class="go danger" id="delacct" style="margin:0 22px 18px">${t("Supprimer mon compte")}</button></section>`;

  app.querySelector("#logout")!.addEventListener("click", async () => { await logout(); renderAccount(app); });
  const bk = app.querySelector<HTMLInputElement>("#bk")!;
  bk.addEventListener("change", () => updateSettings({ bankroll: Number(bk.value) || 0 }).then(setUser));
  app.querySelectorAll<HTMLButtonElement>("#risk button").forEach((b) => b.addEventListener("click", async () => {
    app.querySelectorAll("#risk button").forEach((x) => x.classList.remove("on"));
    b.classList.add("on");
    setUser(await updateSettings({ risk_preset: b.dataset.v as UserProfile["risk_preset"] }));
  }));
  app.querySelectorAll<HTMLButtonElement>("#books button").forEach((b) => b.addEventListener("click", async () => {
    b.classList.toggle("on");
    const books = [...app.querySelectorAll<HTMLButtonElement>("#books button.on")].map((x) => x.dataset.b!);
    setUser(await updateSettings({ books }));
  }));
  app.querySelector("#delacct")!.addEventListener("click", async () => {
    if (confirm(t("Supprimer définitivement ton compte et toutes tes données ?"))) { await deleteAccount(); setUser(null); renderAccount(app); }
  });

  renderTelegram(app.querySelector<HTMLElement>("#tg")!, user);
  loadBets(app, user);
}

function renderTelegram(el: HTMLElement, user: UserProfile) {
  if (user.telegram_linked) { el.innerHTML = `<p class="pub">${t("✓ Telegram relié. Tu reçois les paris du jour.")}</p>`; return; }
  el.innerHTML = `<p class="note">${t("Relie Telegram pour recevoir les paris du jour dès leur sortie.")}</p><button class="go" id="tglink">${t("Relier Telegram")}</button><div id="tgcode"></div>`;
  el.querySelector("#tglink")!.addEventListener("click", async () => {
    try {
      const { code, bot } = await telegramLink();
      const link = bot ? `https://t.me/${bot}?start=${code}` : "";
      el.querySelector("#tgcode")!.innerHTML = link
        ? `<p class="note">${t("Ouvre le bot et valide : ")}<a class="go" href="${esc(link)}" target="_blank" rel="noopener">${t("Ouvrir @{bot}", { bot: esc(bot) })}</a></p>`
        : `<p class="note">${t("Envoie {cmd} au bot Telegram.", { cmd: `<code>/start ${esc(code)}</code>` })}</p>`;
    } catch { el.querySelector("#tgcode")!.innerHTML = `<p class="note down">${t("Indisponible pour l'instant.")}</p>`; }
  });
}

async function loadBets(app: HTMLElement, user: UserProfile) {
  let data: { bets: MyBet[]; stats: MyStats };
  try { data = await getMyBets(); } catch { app.querySelector("#mybets")!.innerHTML = `<div class="empty">${t("Erreur de chargement.")}</div>`; return; }
  const s = data.stats;
  app.querySelector("#mystats")!.innerHTML = s.settled === 0
    ? `<div class="empty">${t("Confirme tes paris pour suivre ta bankroll réelle.")}</div>`
    : `<div class="mystat-row">
        <div><div class="k">${t("Gain net")}</div><div class="v num ${s.bankroll_delta >= 0 ? "up" : "down"}">${s.bankroll_delta >= 0 ? "+" : "−"}${eur(Math.abs(s.bankroll_delta))}</div></div>
        <div><div class="k">ROI</div><div class="v num">${s.roi === null ? "–" : pct(s.roi)}</div></div>
        <div><div class="k">${t("Réussite")}</div><div class="v num">${s.win_rate === null ? "–" : Math.round(s.win_rate * 100) + " %"}</div></div>
        <div><div class="k">${t("Paris réglés")}</div><div class="v num">${s.settled}</div></div>
      </div>`;
  const box = app.querySelector<HTMLElement>("#mybets")!;
  if (data.bets.length === 0) { box.innerHTML = `<div class="empty">${t("Aucun pari confirmé. Depuis les paris du jour, indique ceux que tu as joués.")}</div>`; return; }
  box.innerHTML = `<table class="tbl"><thead><tr><th>${t("Date")}</th><th>${t("Match")}</th><th>${t("Pari")}</th><th class="r">${t("Cote")}</th><th class="r">${t("Mise")}</th><th class="r">${t("Résultat")}</th><th></th></tr></thead><tbody>
    ${data.bets.map((b) => `<tr><td class="mono">${b.commence_time ? fmtDate(b.commence_time) : "–"}</td>
      <td class="match">${esc(b.home_team ?? "")} – ${esc(b.away_team ?? "")}</td>
      <td>${t(b.side === "home" ? "Victoire {team}" : b.side === "away" ? "Victoire {team}" : "Match nul", { team: b.side === "home" ? (b.home_team ?? "") : (b.away_team ?? "") })}</td><td class="r mono">${b.placed_price ?? b.recommended_price ?? "–"}</td>
      <td class="r mono">${b.stake != null ? eur(b.stake) : "–"}</td>
      <td class="r">${b.status === "placed" ? t("en attente") : b.settled_gain != null ? (b.settled_gain >= 0 ? "+" : "−") + eur(Math.abs(b.settled_gain)) : b.status}</td>
      <td class="r"><button class="go" data-del="${esc(b.match_id)}|${esc(b.side)}">✕</button></td></tr>`).join("")}
  </tbody></table>`;
  box.querySelectorAll<HTMLButtonElement>("[data-del]").forEach((btn) => btn.addEventListener("click", async () => {
    const [mid, side] = btn.dataset.del!.split("|");
    await removeBet(mid, side); loadBets(app, user);
  }));
}
