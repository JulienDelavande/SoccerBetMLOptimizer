import { deleteAccount, telegramLink, updateSettings } from "../api";
import type { UserProfile } from "../api";
import { esc } from "../format";
import { currentUser, logout, renderGoogleButton, setUser } from "../session";
import { BOOKS_ALL } from "./books";
import { t } from "../i18n";
import { icon } from "../icons";
import { avatar } from "../logos";
import { pageHead } from "./shared";
import { ageConfirmed, setAgeConfirmed } from "../age";
import { mountWaitlist, waitlistCard } from "../waitlist";

const RISK = [
  ["prudent", "Prudent", "quart de Kelly · mises prudentes"],
  ["balanced", "Équilibré", "demi-Kelly · méthode publiée"],
  ["aggressive", "Agressif", "Kelly plein · plus volatil"],
] as const;

export { AGE_KEY, ageConfirmed } from "../age";

export function renderAccount(app: HTMLElement) {
  const user = currentUser();
  app.innerHTML = user ? "" : loggedOut();
  if (!user) {
    const gbtn = app.querySelector<HTMLElement>("#gbtn")!;
    const box = app.querySelector<HTMLInputElement>("#age")!;
    // Until the box is ticked the Google button is inert: not clickable, not focusable, announced as unavailable.
    const lock = (ok: boolean) => { gbtn.inert = !ok; gbtn.classList.toggle("locked", !ok); gbtn.setAttribute("aria-disabled", String(!ok)); };
    box.checked = ageConfirmed();
    lock(box.checked);
    box.addEventListener("change", () => {
      setAgeConfirmed(box.checked);
      lock(box.checked);
    });
    renderGoogleButton(gbtn, (u) => { setUser(u); renderAccount(app); });
    mountWaitlist(app.querySelector<HTMLElement>("#waitlist")!, null);
    return;
  }
  renderSettings(app, user);
}

function loggedOut() {
  return `${pageHead(t("Mon compte"))}
    <section class="acct-hero card" data-reveal>
      <div class="acct-pitch">
        <p class="lead">${t("Un espace perso gratuit pour suivre la méthode à ta façon.")}</p>
        <ul class="perks">
          <li><b>${t("Tes bookmakers")}</b><span>${t("ne vois que les paris jouables chez toi.")}</span></li>
          <li><b>${t("Ton risque")}</b><span>${t("prudent, équilibré ou agressif.")}</span></li>
          <li><b>${t("Ta bankroll")}</b><span>${t("mises calculées pour ton montant, suivi de tes résultats réels.")}</span></li>
          <li><b>${t("Alertes Telegram")}</b><span>${t("la sélection du jour, une fois publiée.")}</span></li>
        </ul>
        <div class="signin">
          <label class="age-check"><input type="checkbox" id="age" name="age" required /><span>${t("Je certifie avoir 18 ans ou plus")}</span></label>
          <div id="gbtn" class="gbtn"></div>
        </div>
      </div>
    </section>
    ${waitlistCard()}`;
}

function renderSettings(app: HTMLElement, user: UserProfile) {
  const riskNote = (v: string) => t(RISK.find(([k]) => k === v)?.[2] ?? RISK[1][2]);
  app.innerHTML = `
    ${pageHead(t("Mon compte"), t("Règle ton espace, puis bascule en « Moi » (en haut) pour voir les paris et tes stats à ta façon."),
      `<div class="acct-id">${avatar(user.avatar_url, user.name ?? user.email ?? "", "avatar")}<span>${esc(user.name ?? user.email ?? "")}</span><button class="go" id="logout">${t("Déconnexion")}</button></div>`)}
    <section class="card" data-reveal><div class="card-h"><h2>${t("Réglages")}</h2></div>
      <div class="settings">
        <label class="field"><span class="k">${t("Ma bankroll")}</span><span class="field-pill"><input id="bk" name="bankroll" type="number" min="1" step="10" inputmode="decimal" autocomplete="off" value="${user.bankroll}"><i>€</i></span></label>
        <div class="field"><span class="k" id="risk-l">${t("Niveau de risque")}</span><div class="seg" id="risk" role="group" aria-labelledby="risk-l" aria-describedby="risk-d">${RISK.map(([v, l]) =>
          `<button data-v="${v}" class="${user.risk_preset === v ? "on" : ""}" aria-pressed="${user.risk_preset === v}">${t(l)}</button>`).join("")}</div>
          <small class="field-note" id="risk-d">${riskNote(user.risk_preset)}</small></div>
        <div class="field full"><span class="k" id="books-l">${t("Mes bookmakers")} <small>${t("(aucun = tous)")}</small></span><div class="book-chips" id="books" role="group" aria-labelledby="books-l">${BOOKS_ALL.map((b) =>
          `<button data-b="${b.key}" class="${user.books.includes(b.key) ? "on" : ""}" aria-pressed="${user.books.includes(b.key)}">${esc(b.label)}</button>`).join("")}</div></div>
      </div>
      <p class="note down" id="save-err" role="alert" hidden></p>
    </section>
    <section class="card" data-reveal><div class="card-h"><h2>${t("Alertes Telegram")}</h2></div>
      <div class="tg" id="tg"></div></section>
    ${waitlistCard()}
    <section class="card danger-zone" data-reveal><div class="card-h"><h2>${t("Compte")}</h2></div>
      <p class="note">${t("Supprimer ton compte efface définitivement tes réglages et tes paris.")}</p>
      <button class="go danger" id="delacct">${t("Supprimer mon compte")}</button>
      <p class="note down" id="del-err" role="alert" hidden></p></section>`;

  const err = app.querySelector<HTMLElement>("#save-err")!;
  /** Optimistic save: apply `paint(next)` now, persist, and on failure repaint `prev` and say so. */
  const save = async <T,>(patch: Parameters<typeof updateSettings>[0], paint: (v: T) => void, next: T, prev: T) => {
    paint(next);
    err.hidden = true;
    try { setUser(await updateSettings(patch)); }
    catch { paint(prev); err.textContent = t("Réglage non enregistré. Réessaie dans un instant."); err.hidden = false; }
  };

  app.querySelector("#logout")!.addEventListener("click", async () => { await logout(); renderAccount(app); });
  const bk = app.querySelector<HTMLInputElement>("#bk")!;
  bk.addEventListener("change", () => {
    const prev = currentUser()?.bankroll ?? user.bankroll, next = Number(bk.value) || 0;
    if (next <= 0) { bk.value = String(prev); return; }
    save({ bankroll: next }, (v: number) => { bk.value = String(v); }, next, prev);
  });
  const paintRisk = (v: string) => {
    app.querySelectorAll<HTMLButtonElement>("#risk button").forEach((x) => { const on = x.dataset.v === v; x.classList.toggle("on", on); x.setAttribute("aria-pressed", String(on)); });
    app.querySelector("#risk-d")!.textContent = riskNote(v);
  };
  app.querySelectorAll<HTMLButtonElement>("#risk button").forEach((b) => b.addEventListener("click", () => {
    const prev = currentUser()?.risk_preset ?? user.risk_preset, next = b.dataset.v as UserProfile["risk_preset"];
    if (next !== prev) save({ risk_preset: next }, paintRisk, next, prev);
  }));
  const paintBooks = (keys: string[]) => app.querySelectorAll<HTMLButtonElement>("#books button").forEach((x) => {
    const on = keys.includes(x.dataset.b!); x.classList.toggle("on", on); x.setAttribute("aria-pressed", String(on));
  });
  app.querySelectorAll<HTMLButtonElement>("#books button").forEach((b) => b.addEventListener("click", () => {
    const prev = [...app.querySelectorAll<HTMLButtonElement>("#books button.on")].map((x) => x.dataset.b!);
    const next = prev.includes(b.dataset.b!) ? prev.filter((k) => k !== b.dataset.b) : [...prev, b.dataset.b!];
    save({ books: next }, paintBooks, next, prev);
  }));
  app.querySelector("#delacct")!.addEventListener("click", async () => {
    if (!confirm(t("Supprimer définitivement ton compte et toutes tes données ?"))) return;
    try { await deleteAccount(); setUser(null); renderAccount(app); }
    catch { const de = app.querySelector<HTMLElement>("#del-err")!; de.textContent = t("Suppression impossible pour l'instant. Réessaie dans un instant."); de.hidden = false; }
  });
  renderTelegram(app.querySelector<HTMLElement>("#tg")!, user);
  mountWaitlist(app.querySelector<HTMLElement>("#waitlist")!, user);
}

function renderTelegram(el: HTMLElement, user: UserProfile) {
  if (user.telegram_linked) { el.innerHTML = `<p class="pub">${icon("check")}${t("Telegram relié. Tu reçois les paris du jour.")}</p>`; return; }
  el.innerHTML = `<p class="note">${t("Relie Telegram pour recevoir la sélection du jour une fois publiée.")}</p><button class="go" id="tglink">${t("Relier Telegram")}</button><div id="tgcode"></div>`;
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
