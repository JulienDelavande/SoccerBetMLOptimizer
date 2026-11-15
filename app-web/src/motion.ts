// Motion layer: reveal-on-enter, KPI count-up, chart draw-in and route view transitions.
// Pages only mark elements (data-reveal, data-count, svg.draw); this module does the rest.
// Everything degrades to the final, static state under prefers-reduced-motion.
import { locale } from "./i18n";

const STAGGER_MS = 50;
const STAGGER_CAP = 6;          // items 6+ share the last delay, so long lists never crawl in
const COUNT_MS = 900;
/** Elements rendered later than this after a route change (re-renders while typing, day switches)
 *  appear instantly: motion is for arriving on a page, not for every keystroke. */
const SETTLE_MS = 1500;

const rm = typeof matchMedia === "function" ? matchMedia("(prefers-reduced-motion: reduce)") : null;
export const reducedMotion = () => !!rm?.matches;

let routeAt = 0;
const observedAt = new WeakMap<Element, number>();
let revealIO: IntersectionObserver | null = null;
let countIO: IntersectionObserver | null = null;

/** Call when a page (re)starts, so its first render gets the entrance choreography. */
export const markRoute = () => { routeAt = performance.now(); };
const isLate = (el: Element) => (observedAt.get(el) ?? 0) - routeAt > SETTLE_MS;

/** Watch `root` for new content and wire motion onto it. Call once at startup. */
export function initMotion(root: HTMLElement) {
  const sync = () => document.documentElement.classList.toggle("motion", !reducedMotion());
  sync();
  rm?.addEventListener("change", sync);
  revealIO = new IntersectionObserver(onReveal, { rootMargin: "0px 0px -6% 0px", threshold: 0.01 });
  countIO = new IntersectionObserver(onCount, { threshold: 0.5 });
  let queued = false;
  new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => { queued = false; enhance(root); });
  }).observe(root, { childList: true, subtree: true });
}

function enhance(root: HTMLElement) {
  const now = performance.now();
  root.querySelectorAll("[data-reveal]:not([data-m]), svg.draw:not([data-m])").forEach((el) => {
    el.setAttribute("data-m", "");
    observedAt.set(el, now);
    revealIO!.observe(el);
  });
  root.querySelectorAll<HTMLElement>("[data-count]:not([data-m])").forEach((el) => {
    el.setAttribute("data-m", "");
    observedAt.set(el, now);
    if (reducedMotion() || isLate(el)) return;            // keep the final number
    const job = prepareCount(el);
    if (!job) return;
    job.set(0);                                           // runs before first paint: no flash of the final value
    counts.set(el, job);
    countIO!.observe(el);
  });
}

function onReveal(entries: IntersectionObserverEntry[], io: IntersectionObserver) {
  let i = 0;
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    io.unobserve(e.target);
    const el = e.target as HTMLElement | SVGElement;
    if (reducedMotion() || isLate(el)) { el.classList.add("in", "now"); continue; }
    el.style.setProperty("--d", `${Math.min(i++, STAGGER_CAP - 1) * STAGGER_MS}ms`);
    el.classList.add("in");
  }
}

interface CountJob { set: (v: number) => void; target: number }
const counts = new WeakMap<Element, CountJob>();

function onCount(entries: IntersectionObserverEntry[], io: IntersectionObserver) {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    io.unobserve(e.target);
    const job = counts.get(e.target);
    if (job) run(job);
  }
}

const easeOut = (p: number) => (p >= 1 ? 1 : 1 - Math.pow(2, -10 * p));

function run(job: CountJob) {
  const t0 = performance.now();
  const tick = (t: number) => {
    const p = Math.min(1, (t - t0) / COUNT_MS);
    job.set(job.target * easeOut(p));
    if (p < 1) requestAnimationFrame(tick);
    else job.set(job.target);
  };
  requestAnimationFrame(tick);
}

/** Find the first locale-formatted number in the element's text and return a setter that
 *  rewrites only that number (sign, unit and surrounding text stay put). */
export function prepareCount(el: HTMLElement): CountJob | null {
  const fr = locale().startsWith("fr");
  const re = fr ? /\d{1,3}(?:[\s\u00a0\u202f]\d{3})*(?:,\d+)?|\d+(?:,\d+)?/ : /\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?/;
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode() as Text | null; node; node = walker.nextNode() as Text | null) {
    const m = node.data.match(re);
    if (!m || m.index === undefined) continue;
    const raw = m[0], dec = fr ? "," : ".";
    const decimals = raw.includes(dec) ? raw.length - raw.indexOf(dec) - 1 : 0;
    const target = Number(raw.replace(fr ? /[\s\u00a0\u202f]/g : /,/g, "").replace(",", "."));
    if (!Number.isFinite(target)) return null;
    const before = node.data.slice(0, m.index), after = node.data.slice(m.index + raw.length);
    const nf = new Intl.NumberFormat(locale(), { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    const text = node;
    // characterData edits do not trigger the childList MutationObserver above.
    return { target, set: (v) => { text.data = before + nf.format(v) + after; } };
  }
  return null;
}

/** Route changes cross-fade through the View Transitions API when available. */
export function withTransition(update: () => void) {
  const d = document as Document & { startViewTransition?: (cb: () => void) => unknown };
  const run = () => { markRoute(); update(); };
  if (!d.startViewTransition || reducedMotion()) { run(); return; }
  d.startViewTransition(run);
}
