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
import { esc, utc } from "./format";

const app = document.querySelector<HTMLElement>("#app")!;
const routes: Record<string, (app: HTMLElement, data: SiteData) => void> = {
  "/": renderToday, "/performance": renderPerformance, "/historique": renderHistory, "/methode": renderMethod,
};
const NAV: Record<string, string> = {
  "/": "Aujourd'hui", "/performance": "Performance", "/historique": "Historique", "/methode": "Méthode", "/compte": "Compte",
};
installLogoFallback();
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
  document.querySelector("#lang")!.textContent = getLang() === "fr" ? "EN" : "FR";
  paintAccountLink();
  paintViewSwitch();
}

/** The Bot/Me switch: shown only when signed in; reflects the current view. */
function paintViewSwitch() {
  const sw = document.querySelector<HTMLElement>("#viewsw")!;
  sw.hidden = !currentUser();
  sw.querySelectorAll<HTMLButtonElement>("button[data-view]").forEach((b) => {
    b.textContent = t(b.dataset.view === "bot" ? "Bot" : "Moi");
    b.classList.toggle("on", b.dataset.view === getView());
  });
}

function paintStamp() {
  if (!siteData) return;
  const at = utc(siteData.generated_at);
  document.querySelector("#stamp")!.textContent =
    `● ${t("LIVE")} · ${at.toLocaleDateString(undefined, { weekday: "short", day: "2-digit", month: "2-digit" }).toUpperCase()} · ${t("MAJ")} ${at.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}`;
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
  document.querySelectorAll<HTMLAnchorElement>(".menu a").forEach((a) => a.classList.toggle("on", a.dataset.route === key));
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
  paintChrome(); paintStamp(); route();
});

document.querySelector("#viewsw")!.addEventListener("click", (e) => {
  const v = (e.target as HTMLElement).closest<HTMLButtonElement>("button[data-view]")?.dataset.view;
  if (v === "bot" || v === "me") { setView(v); paintViewSwitch(); route(); }
});

Promise.all([load(), initSession()]).then(([data]) => {
  siteData = data;
  document.documentElement.lang = getLang();
  paintChrome(); paintStamp();
  window.addEventListener("hashchange", () => { navigated = true; paintAccountLink(); route(); });
  route();
}).catch((e) => {
  document.querySelector("#stamp")!.textContent = `● ${t("HORS LIGNE")}`;
  app.innerHTML = `<div class="empty pad">${t("Impossible de charger les données ({e}). Réessayez dans un instant.", { e: String(e.message) })}</div>`;
});
