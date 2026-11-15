// Hero football: markup (centre-circle rings, static SVG poster, pill callouts with leader lines)
// and the lazy WebGL upgrade. three.js is only fetched once the stage is near the viewport, after
// first paint; without WebGL the poster simply stays.
import { reducedMotion } from "../motion";
import { ballSvg } from "./geometry";
import type { Ball } from "./ball3d";

export interface Callout { label: string; value?: string; tone?: "accent"; valueFirst?: boolean }

/** Stage frame in its own units: `w` x `h` (the CSS aspect-ratio), ball radius `r`, ball centre at (w/2, cy). */
interface Frame { w: number; h: number; r: number; cy: number; rings: number[] }
/** A callout: anchor on the ball at angle `a` (degrees, screen space, 0 = right, 90 = down) and `k`
 *  ball radii from the centre; pill centred at (x, y) in % of the stage. */
interface Spot { a: number; k: number; x: number; y: number }

// Wide: the ball sits in the hero's right column. Narrow (<= 640px): under the bankroll, bigger.
export const WIDE: Frame = { w: 100, h: 112, r: 30, cy: 54, rings: [49, 41, 34.5] };
export const NARROW: Frame = { w: 100, h: 104, r: 34, cy: 52, rings: [49, 41] };
const SPOTS_WIDE: Spot[] = [
  { a: -132, k: 0.8, x: 24, y: 9 },
  { a: 62, k: 0.82, x: 64, y: 95 },
  { a: -32, k: 0.8, x: 78, y: 19 },
];
const SPOTS_NARROW: Spot[] = [
  { a: -140, k: 0.78, x: 26, y: 6 },
  { a: 35, k: 0.8, x: 74, y: 95 },
];

/** Anchor point of a spot in stage units. */
export function anchor(f: Frame, s: Spot): [number, number] {
  const rad = (s.a * Math.PI) / 180;
  return [f.w / 2 + Math.cos(rad) * s.k * f.r, f.cy + Math.sin(rad) * s.k * f.r];
}

function rings(f: Frame, cls: string) {
  return `<svg class="br-deco ${cls}" viewBox="0 0 ${f.w} ${f.h}" aria-hidden="true">
    <line class="br-half" x1="${f.w / 2}" y1="0" x2="${f.w / 2}" y2="${f.h}"/>${f.rings.map((r) => `<circle class="br-ring" cx="${f.w / 2}" cy="${f.cy}" r="${r}"/>`).join("")}</svg>`;
}

function leads(f: Frame, spots: Spot[], cls: string) {
  const lines = spots.map((s) => {
    const [ax, ay] = anchor(f, s), px = (s.x / 100) * f.w, py = (s.y / 100) * f.h;
    return `<line class="br-lead" x1="${ax.toFixed(2)}" y1="${ay.toFixed(2)}" x2="${px.toFixed(2)}" y2="${py.toFixed(2)}"/>` +
      `<circle class="br-pt" cx="${ax.toFixed(2)}" cy="${ay.toFixed(2)}" r="1.15"/>`;
  }).join("");
  return `<svg class="br-leads ${cls}" viewBox="0 0 ${f.w} ${f.h}" aria-hidden="true">${lines}</svg>`;
}

/** Stage markup. Callouts beyond the narrow layout's two spots are dropped on small screens. */
export function heroBall(callouts: Callout[]) {
  const cs = callouts.slice(0, SPOTS_WIDE.length);
  const narrowCount = Math.min(cs.length, SPOTS_NARROW.length);
  // Narrow layout keeps the first and the last callout (the ones that sit top and bottom).
  const narrowIdx = cs.length > narrowCount ? [0, cs.length - 1] : cs.map((_, i) => i);
  const pills = cs.map((c, i) => {
    const w = SPOTS_WIDE[i], ni = narrowIdx.indexOf(i), n = SPOTS_NARROW[ni];
    const pos = `--x:${w.x}%;--y:${w.y}%${n ? `;--nx:${n.x}%;--ny:${n.y}%` : ""}`;
    return `<span class="bc${n ? "" : " bc-wide"}" style="${pos}"><span class="co-pill"><i class="co-dot${c.tone === "accent" ? " acc" : ""}"></i>${c.valueFirst && c.value ? `<b>${c.value}</b>${c.label}` : `${c.label}${c.value ? `<b>${c.value}</b>` : ""}`}</span></span>`;
  }).join("");
  return `<div class="ball-stage" data-reveal>
    ${rings(WIDE, "br-wide")}${rings(NARROW, "br-narrow")}
    <div class="ball-obj">
      <span class="ball-shadow" aria-hidden="true"></span>
      ${ballSvg()}
      <canvas class="ball-gl" aria-hidden="true"></canvas>
    </div>
    ${leads(WIDE, SPOTS_WIDE.slice(0, cs.length), "br-wide")}${leads(NARROW, narrowIdx.map((_, i) => SPOTS_NARROW[i]), "br-narrow")}
    ${pills}
  </div>`;
}

let current: (() => void) | null = null;

/** Upgrade the poster to the WebGL ball, and tear it down when the stage leaves the page. */
export function mountHeroBall(stage: HTMLElement) {
  current?.();
  const obj = stage.querySelector<HTMLElement>(".ball-obj")!;
  const canvas = stage.querySelector<HTMLCanvasElement>(".ball-gl")!;
  let ball: Ball | null = null, onScreen = false, gone = false;
  const root = document.documentElement;
  const sync = () => ball?.setActive(onScreen && document.visibilityState === "visible");
  const io = new IntersectionObserver((es) => {
    onScreen = es.some((e) => e.isIntersecting);
    if (onScreen && !ball && !loading) load();
    sync();
  }, { rootMargin: "120px 0px" });
  const themeMo = new MutationObserver(() => ball?.setDark(root.dataset.theme === "dark"));
  // #app is re-rendered wholesale on navigation: when our stage is detached, release the GPU context.
  const host = stage.closest("#app") ?? stage.parentElement ?? document.body;
  const appMo = new MutationObserver(() => { if (!stage.isConnected) cleanup(); });
  let loading = false;

  function load() {
    loading = true;
    const idle = (cb: () => void) => ("requestIdleCallback" in window ? requestIdleCallback(cb, { timeout: 600 }) : setTimeout(cb, 120));
    idle(() => {
      import("./ball3d").then(({ createBall }) => {
        if (gone) return;
        try {
          ball = createBall(canvas, obj, {
            reducedMotion: reducedMotion(),
            dark: root.dataset.theme === "dark",
            hoverTilt: matchMedia("(hover: hover) and (pointer: fine)").matches,
            onFirstFrame: () => stage.classList.add("gl"),
          });
          stage.classList.add("live");
          sync();
        } catch {
          stage.classList.add("no-gl");      // no WebGL: keep the static poster
        }
      }).catch(() => stage.classList.add("no-gl"));
    });
  }

  function cleanup() {
    if (gone) return;
    gone = true;
    io.disconnect(); themeMo.disconnect(); appMo.disconnect();
    document.removeEventListener("visibilitychange", sync);
    ball?.dispose();
    ball = null;
    if (current === cleanup) current = null;
  }

  io.observe(stage);
  themeMo.observe(root, { attributes: true, attributeFilter: ["data-theme"] });
  appMo.observe(host, { childList: true });
  document.addEventListener("visibilitychange", sync);
  current = cleanup;
}
