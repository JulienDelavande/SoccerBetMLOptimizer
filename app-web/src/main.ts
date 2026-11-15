import "./style.css";
import { renderHistory } from "./pages/history";
import { renderMethod } from "./pages/method";
import { renderPerformance } from "./pages/performance";
import { renderToday } from "./pages/today";
import { renderMatch } from "./pages/match";
import { renderAccount } from "./pages/account";
import { installLogoFallback } from "./logos";
import { currentUser, initSession } from "./session";
import { getLang, setLang, t } from "./i18n";
import { getView, setView } from "./view";
import type { SiteData } from "./types";
import { dayKey, esc, utc } from "./format";
import { icon } from "./icons";
import { initMotion, reducedMotion, withTransition } from "./motion";

const app = document.querySelector<HTMLElement>("#app")!;
const routes: Record<string, (app: HTMLElement, data: SiteData) => void> = {
  "/": renderToday, "/performance": renderPerformance, "/historique": renderHistory, "/methode": renderMethod,
};
const NAV: Record<string, string> = {
  "/": "Aujourd'hui", "/performance": "Performance", "/historique": "Historique", "/methode": "Méthode", "/compte": "Compte",
};
installLogoFallback();
initMotion(app);
let navigated = false;
let siteData: SiteData | null = null;

/** Translate the static chrome (nav labels, footer, lang button) for the current language. */
function paintChrome() {
  document.querySelectorAll<HTMLAnchorElement>(".menu a[data-route]").forEach((a) => {
    const label = NAV[a.dataset.route!];
    if (label) a.textContent = t(label);
  });
  document.querySelector("#foot-legal")!.textContent =
    t("OptiBet · paris de valeur, pas de conseil financier. Jouer comporte des risques.");
  document.querySelector("#foot-age")!.textContent = t("18+ · Joueurs Info Service 09 74 75 13 13");
  document.querySelector(".skip")!.textContent = t("Aller au contenu");
  document.querySelector(".menu")!.setAttribute("aria-label", t("Navigation"));
  const lang = document.querySelector<HTMLButtonElement>("#lang")!;
  lang.textContent = getLang() === "fr" ? "EN" : "FR";
  lang.setAttribute("aria-label", getLang() === "fr" ? "Switch to English" : "Passer en français");
  document.querySelector("#viewsw")!.setAttribute("aria-label", t("Vue"));
  paintTheme();
  paintAccountLink();
  paintViewSwitch();
}

function paintTheme() {
  const dark = document.documentElement.dataset.theme === "dark";
  const btn = document.querySelector<HTMLButtonElement>("#theme")!;
  btn.innerHTML = icon(dark ? "sun" : "moon");
  btn.setAttribute("aria-label", t(dark ? "Passer en thème clair" : "Passer en thème sombre"));
}

/** The Bot/Me switch: shown only when signed in; reflects the current view. */
function paintViewSwitch() {
  const sw = document.querySelector<HTMLElement>("#viewsw")!;
  sw.hidden = !currentUser();
  sw.querySelectorAll<HTMLButtonElement>("button[data-view]").forEach((b) => {
    b.textContent = t(b.dataset.view === "bot" ? "Bot" : "Moi");
    const on = b.dataset.view === getView();
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", String(on));
  });
}

function paintStamp() {
  if (!siteData) return;
  const at = utc(siteData.generated_at);
  document.querySelector("#stamp")!.classList.add("is-live");
  document.querySelector("#stamp-t")!.textContent =
    `${t("LIVE")} · ${at.toLocaleDateString(getLang() === "fr" ? "fr-FR" : "en-GB", { weekday: "short", day: "2-digit", month: "2-digit" })} · ${t("MAJ")} ${at.toLocaleTimeString(getLang() === "fr" ? "fr-FR" : "en-GB", { hour: "2-digit", minute: "2-digit" })}`;
}

/** Reflect the signed-in state in the nav (avatar/name on the account link). */
function paintAccountLink() {
  const a = document.querySelector<HTMLAnchorElement>('.menu a[data-route="/compte"]');
  if (!a) return;
  const u = currentUser();
  a.innerHTML = u
    ? `${u.avatar_url ? `<img src="${esc(u.avatar_url)}" class="nav-avatar" alt="">` : ""}${esc((u.name ?? t("Compte")).split(" ")[0])}`
    : t("Compte");
}

/** Header CTA: on the day view only, a shortcut down to the day's bets. */
function paintCta(onToday: boolean) {
  const cta = document.querySelector<HTMLButtonElement>("#cta")!;
  const latest = siteData ? [...siteData.bets].map((b) => dayKey(b.odds_at)).sort().pop() : undefined;
  const n = siteData && latest ? siteData.bets.filter((b) => dayKey(b.odds_at) === latest).length : 0;
  cta.hidden = !onToday || n === 0;
  cta.innerHTML = `${t("Paris du jour")}<b>${n}</b>`;
}

async function load(): Promise<SiteData> {
  const res = await fetch("/api/site");
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

function route() {
  const data = siteData!;
  const path = location.hash.replace(/^#/, "") || "/";
  const match = path.match(/^\/match\/([\w-]+)$/);
  const day = path.match(/^\/jour\/(\d{4}-\d{2}-\d{2})$/);
  const key = match || day ? "/" : routes[path] || path === "/compte" ? path : "/";
  document.querySelectorAll<HTMLAnchorElement>(".menu a").forEach((a) => {
    const on = a.dataset.route === key;
    a.classList.toggle("on", on);
    if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  paintCta(key === "/" && !match);
  if (match) {
    renderMatch(app, match[1], () => { if (navigated) history.back(); else location.hash = (document.querySelector<HTMLAnchorElement>("#back")!.getAttribute("href") ?? "#/"); });
    return;
  }
  if (path === "/compte") { renderAccount(app); window.scrollTo(0, 0); return; }
  if (day || key === "/") renderToday(app, data, day?.[1]);
  else { routes[key](app, data); window.scrollTo(0, 0); }
}

document.querySelector("#lang")!.addEventListener("click", () => {
  setLang(getLang() === "fr" ? "en" : "fr");
  document.documentElement.lang = getLang();
  paintChrome(); paintStamp(); withTransition(route);
});

document.querySelector("#theme")!.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  const apply = () => { document.documentElement.dataset.theme = next; paintTheme(); };
  localStorage.setItem("theme", next);
  const d = document as Document & { startViewTransition?: (cb: () => void) => unknown };
  // Ease the light/dark swap (no brightness jump) where view transitions exist.
  if (d.startViewTransition && !reducedMotion()) d.startViewTransition(apply); else apply();
});

document.querySelector("#cta")!.addEventListener("click", () => {
  document.querySelector("#day")?.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "start" });
});

document.querySelector("#viewsw")!.addEventListener("click", (e) => {
  const v = (e.target as HTMLElement).closest<HTMLButtonElement>("button[data-view]")?.dataset.view;
  if (v === "bot" || v === "me") { setView(v); paintViewSwitch(); withTransition(route); }
});

Promise.all([load(), initSession()]).then(([data]) => {
  siteData = data;
  document.documentElement.lang = getLang();
  paintChrome(); paintStamp();
  window.addEventListener("hashchange", () => { navigated = true; paintAccountLink(); withTransition(route); });
  withTransition(route);
}).catch((e) => {
  paintChrome();
  document.querySelector("#stamp-t")!.textContent = t("HORS LIGNE");
  app.innerHTML = `<div class="empty pad">${t("Impossible de charger les données ({e}). Réessayez dans un instant.", { e: esc(String(e.message)) })}</div>`;
});
