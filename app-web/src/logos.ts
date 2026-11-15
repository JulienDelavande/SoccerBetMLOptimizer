import { esc } from "./format";

// Logos live on the CDN as /logos/{teams,leagues,bookies}/<name>; nginx resolves the extension.
const slug = (name: string) => encodeURIComponent(name.replace(/ /g, "_"));
const PREFIX = /^(FC|AC|AS|RC|SC|SS|US|CF|1\. ?FC|RB|VfB|VfL|TSG|SV)\s+/i;
const SKIP = new Set(["de", "del", "la", "le", "les", "du", "des", "di", "da", "do", "of", "the", "y", "and"]);
/** Monogram for a missing logo: first letters of up to two words that start with a letter
 *  (so "1. FC Heidenheim 1846" -> "H", "Brighton & Hove Albion" -> "BH", "Estudiantes de La Plata" -> "EP"). */
export const initials = (name: string) => {
  const words = name.replace(PREFIX, "").split(/[\s\-/.]+/).filter((w) => /^\p{L}/u.test(w) && !SKIP.has(w.toLowerCase()));
  const out = words.slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  return out || name.trim().slice(0, 2).toUpperCase();
};

/** <img> replaced by a monogram block when the logo is missing (see installLogoFallback).
 *  Logos always sit next to the visible name, so they are decorative (alt=""). */
const img = (src: string, name: string, cls: string, fallback: string) =>
  `<img class="${cls}" src="${src}" alt="" data-name="${esc(name)}" data-fallback="${esc(fallback)}" loading="lazy" onerror="__noLogo(this)">`;

export function installLogoFallback() {
  (window as unknown as { __noLogo: (el: HTMLImageElement) => void }).__noLogo = (el) => {
    const span = document.createElement("span");
    span.className = `${el.className} mono-logo`;
    span.textContent = el.dataset.fallback ?? "";
    span.setAttribute("aria-hidden", "true");
    if (el.dataset.name) span.title = el.dataset.name;
    el.replaceWith(span);
  };
}

export const teamLogo = (name: string, cls = "crest") => img(`/logos/teams/${slug(name)}`, name, cls, initials(name));
export const leagueLogo = (key: string | null, name: string, cls = "lg-logo") =>
  key ? img(`/logos/leagues/${key}`, name, cls, initials(name)) : "";

/** Profile picture that falls back to the user's initials when the image fails. */
export const avatar = (url: string | null, name: string, cls: string) =>
  url ? img(esc(url), name, cls, initials(name || "?")) : `<span class="${cls} mono-logo" aria-hidden="true">${esc(initials(name || "?"))}</span>`;

const BOOK_LOGO: Record<string, string> = { betfair_ex_eu: "betfair", betfair_ex_uk: "betfair", betfair_sb_uk: "betfair",
  unibet_eu: "unibet", unibet_fr: "unibet", unibet_uk: "unibet", unibet_nl: "unibet", unibet_se: "unibet", unibet_it: "unibet",
  tipico_de: "tipico", livescorebet_eu: "livescorebet", ladbrokes_uk: "ladbrokes", parionssport_fr: "parionssport",
  betclic_fr: "betclic", leovegas_se: "leovegas" };
export const bookLogo = (key: string, title: string, cls = "bk-logo") =>
  img(`/logos/bookies/${BOOK_LOGO[key] ?? key}`, title, cls, title.slice(0, 2).toUpperCase());
