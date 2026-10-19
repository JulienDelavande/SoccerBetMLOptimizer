import { esc } from "./format";

// Logos live on the CDN as /logos/{teams,leagues,bookies}/<name>; nginx resolves the extension.
const slug = (name: string) => encodeURIComponent(name.replace(/ /g, "_"));
const initials = (name: string) =>
  name.replace(/^(FC|AC|AS|RC|SC|SS|US|CF|1\. ?FC|RB|VfB|VfL|TSG|SV)\s+/i, "").split(/[\s-]+/).filter(Boolean)
    .slice(0, 2).map((w) => w[0]).join("").toUpperCase();

/** <img> replaced by a monogram block when the logo is missing (see installLogoFallback). */
const img = (src: string, alt: string, cls: string, fallback: string) =>
  `<img class="${cls}" src="${src}" alt="${esc(alt)}" data-fallback="${esc(fallback)}" loading="lazy" onerror="__noLogo(this)">`;

export function installLogoFallback() {
  (window as unknown as { __noLogo: (el: HTMLImageElement) => void }).__noLogo = (el) => {
    const span = document.createElement("span");
    span.className = `${el.className} mono-logo`;
    span.textContent = el.dataset.fallback ?? "";
    span.title = el.alt;
    el.replaceWith(span);
  };
}

export const teamLogo = (name: string, cls = "crest") => img(`/logos/teams/${slug(name)}`, name, cls, initials(name));
export const leagueLogo = (key: string | null, name: string, cls = "lg-logo") =>
  key ? img(`/logos/leagues/${key}`, name, cls, name.slice(0, 2).toUpperCase()) : "";

const BOOK_LOGO: Record<string, string> = { betfair_ex_eu: "betfair", betfair_ex_uk: "betfair", betfair_sb_uk: "betfair",
  unibet_eu: "unibet", unibet_fr: "unibet", unibet_uk: "unibet", unibet_nl: "unibet", unibet_se: "unibet", unibet_it: "unibet",
  tipico_de: "tipico", livescorebet_eu: "livescorebet", ladbrokes_uk: "ladbrokes", parionssport_fr: "parionssport",
  betclic_fr: "betclic", leovegas_se: "leovegas" };
export const bookLogo = (key: string, title: string, cls = "bk-logo") =>
  img(`/logos/bookies/${BOOK_LOGO[key] ?? key}`, title, cls, title.slice(0, 2).toUpperCase());
