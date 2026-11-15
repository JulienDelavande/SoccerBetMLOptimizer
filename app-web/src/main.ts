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
import { dayKey, esc, todayKey, utc } from "./format";
import { avatar } from "./logos";
import { NAV, routeTitle } from "./routes";
import { icon } from "./icons";
import { initMotion, reducedMotion, withTransition } from "./motion";

const app = document.querySelector<HTMLElement>("#app")!;
const routes: Record<string, (app: HTMLElement, data: SiteData) => void> = {
  "/": renderToday, "/performance": renderPerformance, "/historique": renderHistory, "/methode": renderMethod,
};
installLogoFallback();
initMotion(app);
// iOS only fires :active styles when a touch listener exists somewhere on the page.
document.addEventListener("touchstart", () => {}, { passive: true });
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

const THEME_COLOR = { light: "#EDE4CF", dark: "#16271A" } as const;

function paintTheme() {
  const dark = document.documentElement.dataset.theme === "dark";
  const btn = document.querySelector<HTMLButtonElement>("#theme")!;
  btn.innerHTML = icon(dark ? "sun" : "moon");
  btn.setAttribute("aria-label", t(dark ? "Passer en thème clair" : "Passer en thème sombre"));
  // The browser chrome follows the chosen theme, not the OS one.
  document.querySelectorAll<HTMLMetaElement>('meta[name="theme-color"]').forEach((m) => { m.content = THEME_COLOR[dark ? "dark" : "light"]; });
}

/** The Bot/Me switch: shown only when signed in; reflects the current view. */
function paintViewSwitch() {
  const sw = document.querySelector<HTMLElement>("#viewsw")!;
  sw.hidden = !currentUser();
  document.querySelector(".top")!.classList.toggle("signed-in", !!currentUser());
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
  const first = (u?.name ?? "").trim().split(/\s+/)[0] || t("Compte");
  a.innerHTML = u ? `${avatar(u.avatar_url, u.name ?? u.email ?? "", "nav-avatar")}<span class="nav-name">${esc(first)}</span>` : t("Compte");
  if (u) a.title = u.name ?? u.email ?? ""; else a.removeAttribute("title");
}

/** Header CTA: on the day view only, and only when today has bets: a shortcut down to them. */
function paintCta(onToday: boolean) {
  const cta = document.querySelector<HTMLButtonElement>("#cta")!;
  const today = todayKey();
  const u = currentUser(), books = u && getView() === "me" ? u.books : [];
  const n = siteData ? siteData.bets.filter((b) => dayKey(b.odds_at) === today && (books.length === 0 || books.includes(b.book))).length : 0;
  cta.hidden = !onToday || n === 0;
  cta.innerHTML = `${t("Paris du jour")}<b aria-hidden="true">${n}</b><span class="sr-only"> ${t(n > 1 ? "({n} paris)" : "({n} pari)", { n })}</span>`;
}

/** Mobile nav row: keep the active item visible and fade only the edges that hide more items. */
function syncMenuScroll(scrollActive = false) {
  const menu = document.querySelector<HTMLElement>(".menu")!;
  if (scrollActive) {
    const a = menu.querySelector<HTMLElement>("a.on");
    if (a && menu.scrollWidth > menu.clientWidth) {
      const l = a.offsetLeft - menu.offsetLeft, r = l + a.offsetWidth;
      if (l < menu.scrollLeft || r > menu.scrollLeft + menu.clientWidth)
        menu.scrollTo({ left: Math.max(0, l - 24), behavior: reducedMotion() ? "auto" : "smooth" });
    }
  }
  menu.classList.toggle("fade-l", menu.scrollLeft > 2);
  menu.classList.toggle("fade-r", menu.scrollLeft + menu.clientWidth < menu.scrollWidth - 2);
}
document.querySelector(".menu")!.addEventListener("scroll", () => syncMenuScroll(), { passive: true });
window.addEventListener("resize", () => syncMenuScroll(), { passive: true });

async function load(): Promise<SiteData> {
  const res = await fetch("/api/site");
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

function route() {
  const data = siteData;
  const path = location.hash.replace(/^#/, "") || "/";
  const match = path.match(/^\/match\/([\w-]+)$/);
  const day = path.match(/^\/jour\/(\d{4}-\d{2}-\d{2})$/);
  const key = match || day ? "/" : routes[path] || path === "/compte" ? path : "/";
  document.querySelectorAll<HTMLAnchorElement>(".menu a").forEach((a) => {
    const on = a.dataset.route === key;
    a.classList.toggle("on", on);
    if (on) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  syncMenuScroll(true);
  document.title = routeTitle(path);
  paintCta(key === "/" && !match);
  if (!data) { renderOffline(key); return; }
  if (match) {
    renderMatch(app, match[1], () => { if (navigated) history.back(); else location.hash = (document.querySelector<HTMLAnchorElement>("#back")!.getAttribute("href") ?? "#/"); });
    return;
  }
  if (path === "/compte") { renderAccount(app); window.scrollTo(0, 0); return; }
  if (day || key === "/") renderToday(app, data, day?.[1]);
  else { routes[key](app, data); window.scrollTo(0, 0); }
}

/** No data: account and method still work (they do not need it); other routes offer a retry. */
function renderOffline(key: string) {
  if (key === "/compte") { renderAccount(app); return; }
  if (key === "/methode") { renderMethod(app, { kpis: null } as SiteData); return; }
  app.innerHTML = `<div class="empty pad offline"><p>${t("Impossible de charger les données. Vérifie ta connexion puis réessaie.")}</p>
    <button class="go" id="retry" type="button">${t("Réessayer")}</button></div>`;
  app.querySelector("#retry")!.addEventListener("click", () => location.reload());
}

document.querySelector("#lang")!.addEventListener("click", () => {
  setLang(getLang() === "fr" ? "en" : "fr");
  document.documentElement.lang = getLang();
  paintChrome(); paintStamp(); if (!siteData) paintOfflineStamp();
  withTransition(route, false);   // same page, new words: no replayed entrance
});

document.querySelector("#theme")!.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  const apply = () => { document.documentElement.dataset.theme = next; paintTheme(); };
  localStorage.setItem("theme", next);
  const d = document as Document & { startViewTransition?: (cb: () => void) => { finished: Promise<unknown> } };
  // Ease the light/dark swap (plain cross-fade, no route rise) where view transitions exist.
  if (!d.startViewTransition || reducedMotion()) { apply(); return; }
  const root = document.documentElement;
  root.classList.add("vt-theme");
  d.startViewTransition(apply).finished.finally(() => root.classList.remove("vt-theme"));
});

document.querySelector("#cta")!.addEventListener("click", () => {
  document.querySelector("#day")?.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "start" });
});

document.querySelector("#viewsw")!.addEventListener("click", (e) => {
  const v = (e.target as HTMLElement).closest<HTMLButtonElement>("button[data-view]")?.dataset.view;
  if (v === "bot" || v === "me") { setView(v); paintViewSwitch(); withTransition(route); }
});

function paintOfflineStamp() {
  document.querySelector("#stamp")!.classList.add("is-offline");
  document.querySelector("#stamp-t")!.textContent = t("HORS LIGNE");
}

const onHash = () => {
  navigated = true; paintAccountLink();
  // Move focus to the new page for keyboard and screen-reader users (no scroll jump).
  withTransition(() => { route(); app.focus({ preventScroll: true }); });
};

const session = initSession();
Promise.all([load(), session]).then(([data]) => {
  siteData = data;
  document.documentElement.lang = getLang();
  paintChrome(); paintStamp();
  window.addEventListener("hashchange", onHash);
  withTransition(route);
}).catch(async () => {
  await session;
  document.documentElement.lang = getLang();
  paintChrome(); paintOfflineStamp();
  window.addEventListener("hashchange", onHash);
  route();
});
