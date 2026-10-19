import "./style.css";
import { renderHistory } from "./pages/history";
import { renderMethod } from "./pages/method";
import { renderPerformance } from "./pages/performance";
import { renderToday } from "./pages/today";
import type { SiteData } from "./types";
import { utc } from "./format";

const app = document.querySelector<HTMLElement>("#app")!;
const routes: Record<string, (app: HTMLElement, data: SiteData) => void> = {
  "/": renderToday, "/performance": renderPerformance, "/historique": renderHistory, "/methode": renderMethod,
};

const themeBtn = document.querySelector<HTMLButtonElement>("#theme")!;
const paintTheme = () => { themeBtn.textContent = document.documentElement.dataset.theme === "dark" ? "☀ JOUR" : "☾ NUIT"; };
themeBtn.addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("theme", next);
  paintTheme();
});
paintTheme();

async function load(): Promise<SiteData> {
  const res = await fetch("/api/site");
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

function route(data: SiteData) {
  const path = location.hash.replace(/^#/, "") || "/";
  const render = routes[path] ?? renderToday;
  document.querySelectorAll<HTMLAnchorElement>(".menu a").forEach((a) => a.classList.toggle("on", a.dataset.route === (routes[path] ? path : "/")));
  render(app, data);
  window.scrollTo(0, 0);
}

load().then((data) => {
  const at = utc(data.generated_at);
  document.querySelector("#stamp")!.textContent =
    `● LIVE · ${at.toLocaleDateString("fr-FR", { weekday: "short", day: "2-digit", month: "2-digit" }).toUpperCase()} · MAJ ${at.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}`;
  window.addEventListener("hashchange", () => route(data));
  route(data);
}).catch((e) => {
  document.querySelector("#stamp")!.textContent = "● HORS LIGNE";
  app.innerHTML = `<div class="empty pad">Impossible de charger les données (${String(e.message)}). Réessayez dans un instant.</div>`;
});
