import "./style.css";
import { renderHistory } from "./pages/history";
import { renderMethod } from "./pages/method";
import { renderPerformance } from "./pages/performance";
import { renderToday } from "./pages/today";
import { renderMatch } from "./pages/match";
import { installLogoFallback } from "./logos";
import type { SiteData } from "./types";
import { utc } from "./format";

const app = document.querySelector<HTMLElement>("#app")!;
const routes: Record<string, (app: HTMLElement, data: SiteData) => void> = {
  "/": renderToday, "/performance": renderPerformance, "/historique": renderHistory, "/methode": renderMethod,
};
installLogoFallback();
// Whether the visitor navigated inside the site (a deep-linked match page goes "back" to its day).
let navigated = false;

async function load(): Promise<SiteData> {
  const res = await fetch("/api/site");
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

function route(data: SiteData) {
  const path = location.hash.replace(/^#/, "") || "/";
  const match = path.match(/^\/match\/([\w-]+)$/);
  const day = path.match(/^\/jour\/(\d{4}-\d{2}-\d{2})$/);
  const key = match || day ? "/" : routes[path] ? path : "/";
  document.querySelectorAll<HTMLAnchorElement>(".menu a").forEach((a) => a.classList.toggle("on", a.dataset.route === key));
  if (match) {
    renderMatch(app, match[1], () => { if (navigated) history.back(); else location.hash = (document.querySelector<HTMLAnchorElement>("#back")!.getAttribute("href") ?? "#/"); });
    return;
  }
  if (day) renderToday(app, data, day[1]);
  else { routes[key](app, data); window.scrollTo(0, 0); }
}

load().then((data) => {
  const at = utc(data.generated_at);
  document.querySelector("#stamp")!.textContent =
    `● LIVE · ${at.toLocaleDateString("fr-FR", { weekday: "short", day: "2-digit", month: "2-digit" }).toUpperCase()} · MAJ ${at.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}`;
  window.addEventListener("hashchange", () => { navigated = true; route(data); });
  route(data);
}).catch((e) => {
  document.querySelector("#stamp")!.textContent = "● HORS LIGNE";
  app.innerHTML = `<div class="empty pad">Impossible de charger les données (${String(e.message)}). Réessayez dans un instant.</div>`;
});
