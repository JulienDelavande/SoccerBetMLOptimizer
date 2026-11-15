// Waitlist for the future paid offer (V1: no payment). Same card on Today (after the day's bets)
// and on the account page. Neutral copy only: no promise of winnings, no ROI (Code conso L121-4 15°).
import { ApiError, joinWaitlist } from "./api";
import type { UserProfile, WaitlistPayload } from "./api";
import { ageConfirmed, setAgeConfirmed } from "./age";
import { esc } from "./format";
import { getLang, t } from "./i18n";
import { icon } from "./icons";

export const WAITLIST_KEY = "waitlist_joined";
export const MESSAGE_MAX = 1000;
// Same shape check as the backend: one @, a dot in the domain, no spaces.
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export const PLANS = [["monthly", "Mensuel"], ["yearly", "Annuel"], ["unsure", "Je ne sais pas"]] as const;
export const BUDGETS = [["lt10", "< 10 €"], ["10_20", "10-20 €"], ["20_30", "20-30 €"], ["30plus", "30 € et +"]] as const;

export interface WaitlistValues {
  email: string; plan: string; budget: string; message: string; consent: boolean; adult: boolean; website: string;
}
export type WaitlistField = "email" | "plan" | "budget" | "message" | "consent" | "adult";
/** What this device remembers after joining (to show the success state and prefill an update). */
export interface Joined { email: string; plan: string; budget: string }

/** Field -> French error key (translated at render). Empty object = valid. */
export function validateWaitlist(v: WaitlistValues): Partial<Record<WaitlistField, string>> {
  const e: Partial<Record<WaitlistField, string>> = {};
  const email = v.email.trim();
  if (!email || email.length > 320 || !EMAIL_RE.test(email)) e.email = "Indique une adresse email valide.";
  if (!PLANS.some(([k]) => k === v.plan)) e.plan = "Choisis une formule.";
  if (!BUDGETS.some(([k]) => k === v.budget)) e.budget = "Choisis un budget.";
  if (v.message.trim().length > MESSAGE_MAX) e.message = "1000 caractères maximum.";
  if (!v.consent) e.consent = "Coche cette case pour être prévenu du lancement.";
  if (!v.adult) e.adult = "Réservé aux personnes de 18 ans et plus.";
  return e;
}

/** Request body for POST /api/waitlist (call only once validateWaitlist is empty). */
export function waitlistPayload(v: WaitlistValues, lang = getLang()): WaitlistPayload {
  const message = v.message.trim();
  return {
    email: v.email.trim().toLowerCase(),
    plan: v.plan as WaitlistPayload["plan"],
    budget: v.budget as WaitlistPayload["budget"],
    message: message || null,
    lang,
    consent: true,
    adult: true,
    website: v.website,
  };
}

export function joined(): Joined | null {
  if (typeof localStorage === "undefined") return null;
  try {
    const j = JSON.parse(localStorage.getItem(WAITLIST_KEY) ?? "null");
    return j && typeof j.email === "string" ? j : null;
  } catch { return null; }
}
const remember = (j: Joined) => { try { localStorage.setItem(WAITLIST_KEY, JSON.stringify(j)); } catch { /* private mode */ } };

const radios = (name: string, opts: readonly (readonly [string, string])[], checked?: string) =>
  opts.map(([v, l]) => `<label class="wl-opt"><input type="radio" name="${name}" value="${v}"${v === checked ? " checked" : ""} /><span>${t(l)}</span></label>`).join("");

const errSlot = (f: WaitlistField) => `<p class="wl-err" id="wl-${f}-err" hidden></p>`;

/** The form. `user` (signed in) fixes the email to the account's; `prev` prefills an update. */
export function waitlistForm(user: Pick<UserProfile, "email"> | null, prev: Joined | null = null, adult = false): string {
  const email = user?.email ?? prev?.email ?? "";
  const locked = !!user?.email;
  return `<form class="wl-form" novalidate>
    <div class="wl-field wl-wide">
      <label class="k" for="wl-email">${t("Email")}</label>
      <input class="wl-input" id="wl-email" name="email" type="email" inputmode="email" autocomplete="email" spellcheck="false"
        required maxlength="320" value="${esc(email)}"${locked ? ` readonly aria-describedby="wl-email-note wl-email-err"` : ` aria-describedby="wl-email-err"`} />
      ${locked ? `<p class="wl-note" id="wl-email-note">${t("L'adresse de ton compte.")} <button type="button" class="wl-link" id="wl-email-edit">${t("Utiliser une autre adresse")}</button></p>` : ""}
      ${errSlot("email")}
    </div>
    <fieldset class="wl-field wl-wide" aria-describedby="wl-plan-err">
      <legend class="k">${t("Formule souhaitée")}</legend>
      <div class="wl-opts">${radios("plan", PLANS, prev?.plan)}</div>
      ${errSlot("plan")}
    </fieldset>
    <fieldset class="wl-field wl-wide" aria-describedby="wl-budget-err">
      <legend class="k">${t("Budget mensuel")}</legend>
      <div class="wl-opts wl-opts-budget">${radios("budget", BUDGETS, prev?.budget)}</div>
      ${errSlot("budget")}
    </fieldset>
    <div class="wl-field wl-wide">
      <label class="k" for="wl-message">${t("Ce que tu en attends")} <small>${t("(facultatif)")}</small></label>
      <textarea class="wl-input" id="wl-message" name="message" rows="3" maxlength="${MESSAGE_MAX}" aria-describedby="wl-count wl-message-err"></textarea>
      <p class="wl-note wl-count num" id="wl-count" aria-live="off">0 / ${MESSAGE_MAX}</p>
      ${errSlot("message")}
    </div>
    <div class="wl-hp" aria-hidden="true"><label>${t("Ne pas remplir")}<input type="text" name="website" tabindex="-1" autocomplete="off" /></label></div>
    <div class="wl-checks wl-wide">
      <label class="age-check wl-check"><input type="checkbox" name="consent" required aria-describedby="wl-consent-err" /><span>${t("J'accepte d'être contacté par email au sujet du lancement d'OptiBet Pro")} (<a href="/confidentialite.html#liste-attente" target="_blank" rel="noopener">${t("confidentialité")}</a>)</span></label>
      ${errSlot("consent")}
      <label class="age-check wl-check"><input type="checkbox" name="adult" required${adult ? " checked" : ""} aria-describedby="wl-adult-err" /><span>${t("Je certifie avoir 18 ans ou plus")}</span></label>
      ${errSlot("adult")}
    </div>
    <div class="wl-actions wl-wide">
      <button type="submit" class="btn-cta wl-submit">${t("Rejoindre la liste d'attente")}</button>
      <p class="wl-status" role="status" aria-live="polite"></p>
    </div>
  </form>`;
}

export function waitlistDone(j: Joined | null): string {
  return `<div class="wl-done">
    <span class="wl-done-ic" aria-hidden="true">${icon("check")}</span>
    <div>
      <p class="wl-done-t" id="wl-done-t" tabindex="-1">${t("C'est noté, tu seras prévenu.")}</p>
      ${j?.email ? `<p class="wl-note">${t("Inscrit avec {email}.", { email: `<b>${esc(j.email)}</b>` })}</p>` : ""}
    </div>
    <button type="button" class="go" id="wl-update">${t("Modifier mes réponses")}</button>
  </div>`;
}

/** The whole card; `mountWaitlist` makes it live. */
export function waitlistCard(): string {
  return `<section class="card waitlist" id="waitlist" aria-labelledby="wl-title" data-reveal>
    <div class="wl-pitch">
      <span class="wl-badge">${icon("lock")}<span>${t("OptiBet Pro, bientôt")}</span></span>
      <h2 id="wl-title" tabindex="-1">${t("Une formule payante se prépare")}</h2>
      <p>${t("Laisse ton email pour être prévenu du lancement et dis-nous ce que tu en attends. Gratuit, sans engagement, désinscription en un clic.")}</p>
    </div>
    <div class="wl-body" id="wl-body"></div>
    <p class="sr-only" id="wl-live" role="status" aria-live="polite"></p>
  </section>`;
}

function values(form: HTMLFormElement): WaitlistValues {
  const f = new FormData(form);
  const s = (k: string) => String(f.get(k) ?? "");
  return { email: s("email"), plan: s("plan"), budget: s("budget"), message: s("message"),
           consent: f.get("consent") !== null, adult: f.get("adult") !== null, website: s("website") };
}

const FIELDS: WaitlistField[] = ["email", "plan", "budget", "message", "consent", "adult"];

/** Bind the card rendered by waitlistCard(): success state if already joined, else the form. */
export function mountWaitlist(card: HTMLElement, user: Pick<UserProfile, "email"> | null): void {
  const body = card.querySelector<HTMLElement>("#wl-body")!;
  const showDone = (focus: boolean) => {
    body.innerHTML = waitlistDone(joined());
    body.querySelector("#wl-update")!.addEventListener("click", () => showForm(joined(), true));
    if (focus) {
      body.querySelector<HTMLElement>("#wl-done-t")!.focus();
      card.querySelector("#wl-live")!.textContent = t("C'est noté, tu seras prévenu.");
    }
  };
  const showForm = (prev: Joined | null, focus: boolean) => {
    body.innerHTML = waitlistForm(user, prev, ageConfirmed());
    bindForm(body.querySelector<HTMLFormElement>("form")!, () => showDone(true));
    if (focus) body.querySelector<HTMLInputElement>(user?.email ? "input[name=plan]" : "#wl-email")!.focus();
  };
  if (joined()) showDone(false); else showForm(null, false);
}

function bindForm(form: HTMLFormElement, onDone: () => void) {
  const status = form.querySelector<HTMLElement>(".wl-status")!;
  const submit = form.querySelector<HTMLButtonElement>(".wl-submit")!;
  const msg = form.querySelector<HTMLTextAreaElement>("#wl-message")!;
  const count = form.querySelector<HTMLElement>("#wl-count")!;
  msg.addEventListener("input", () => { count.textContent = `${msg.value.length} / ${MESSAGE_MAX}`; });
  form.querySelector("#wl-email-edit")?.addEventListener("click", (e) => {
    const input = form.querySelector<HTMLInputElement>("#wl-email")!;
    input.readOnly = false; input.setAttribute("aria-describedby", "wl-email-err");
    (e.currentTarget as HTMLElement).closest(".wl-note")!.remove();
    input.select(); input.focus();
  });
  form.querySelector<HTMLInputElement>("input[name=adult]")!.addEventListener("change", (e) => setAgeConfirmed((e.target as HTMLInputElement).checked));

  const paintField = (f: WaitlistField, msgKey: string | undefined) => {
    const slot = form.querySelector<HTMLElement>(`#wl-${f}-err`)!;
    slot.hidden = !msgKey; slot.textContent = msgKey ? t(msgKey) : "";
    form.querySelectorAll<HTMLElement>(`[name=${f}]`).forEach((el) => {
      if (msgKey) el.setAttribute("aria-invalid", "true"); else el.removeAttribute("aria-invalid");
    });
    slot.closest(".wl-field")?.classList.toggle("has-err", !!msgKey);
  };
  const paint = (errors: Partial<Record<WaitlistField, string>>) => FIELDS.forEach((f) => paintField(f, errors[f]));
  // A flagged field loses its error as soon as it is fixed, while it is being edited (input, not
  // blur: a blur-time reflow would move the control the pointer is pressing). Errors are only
  // added on submit.
  const recheck = (e: Event) => {
    const f = (e.target as HTMLInputElement).name as WaitlistField;
    if (!FIELDS.includes(f) || !form.querySelector(`[name=${f}][aria-invalid]`)) return;
    if (!validateWaitlist(values(form))[f]) paintField(f, undefined);
  };
  form.addEventListener("input", recheck);
  form.addEventListener("change", recheck);

  let busy = false;
  // aria-disabled (not disabled) while sending, so keyboard focus stays on the button.
  const setBusy = (on: boolean, label: string) => {
    busy = on; submit.textContent = label; submit.classList.toggle("is-loading", on);
    if (on) { submit.setAttribute("aria-disabled", "true"); submit.setAttribute("aria-busy", "true"); }
    else { submit.removeAttribute("aria-disabled"); submit.removeAttribute("aria-busy"); }
  };
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (busy) return;
    const v = values(form);
    const errors = validateWaitlist(v);
    paint(errors);
    const first = FIELDS.find((f) => errors[f]);
    if (first) {
      status.className = "wl-status down";
      status.textContent = t("Vérifie les champs signalés.");
      form.querySelector<HTMLElement>(`[name=${first}]`)?.focus();
      return;
    }
    const label = submit.textContent ?? "";
    setBusy(true, t("Envoi…"));
    status.className = "wl-status"; status.textContent = "";
    try {
      const p = waitlistPayload(v);
      await joinWaitlist(p);
      remember({ email: p.email, plan: p.plan, budget: p.budget });
      onDone();
    } catch (err) {
      status.className = "wl-status down";
      status.textContent = err instanceof ApiError && err.status === 429
        ? t("Trop de tentatives. Réessaie dans une heure.")
        : err instanceof ApiError && err.status === 422
          ? t("Vérifie les champs signalés.")
          : t("Envoi impossible pour l'instant. Réessaie dans un instant.");
      setBusy(false, label);
    }
  });
}
