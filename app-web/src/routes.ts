import { t } from "./i18n";

/** Nav label (French key) per top-level route. */
export const NAV: Record<string, string> = {
  "/": "Aujourd'hui", "/performance": "Performance", "/historique": "Historique", "/methode": "Méthode", "/compte": "Compte",
};

/** Document title for a route path (the hash without "#"). Match pages refine it once the match is loaded. */
export function routeTitle(path: string): string {
  if (/^\/match\//.test(path)) return `${t("Match")} · OptiBet`;
  const key = /^\/jour\//.test(path) ? "/" : path;
  return `${t(NAV[key] ?? NAV["/"])} · OptiBet`;
}
