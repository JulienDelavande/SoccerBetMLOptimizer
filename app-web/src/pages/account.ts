import { deleteAccount, telegramLink, updateSettings } from "../api";
import type { UserProfile } from "../api";
import { esc } from "../format";
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
    renderGoogleButton(app.querySelector<HTMLElement>("#gbtn")!, (u) => { setUser(u); renderAccount(app); });
    return;
  }
  renderSettings(app, user);
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

function renderSettings(app: HTMLElement, user: UserProfile) {
  app.innerHTML = `
    <section class="sec"><div class="sec-head">
      <h2>${t("Mon compte")}</h2>
      <div class="acct-id">${user.avatar_url ? `<img src="${esc(user.avatar_url)}" alt="" class="avatar">` : ""}<span>${esc(user.name ?? user.email ?? "")}</span><button class="go" id="logout">${t("Déconnexion")}</button></div>
    </div></section>
    <p class="note pad-x">${t("Règle ton espace, puis bascule en « Moi » (en haut) pour voir les paris et tes stats à ta façon.")}</p>
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
