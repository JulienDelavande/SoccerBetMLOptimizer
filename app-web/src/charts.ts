import { drawdown, esc, eur, eur0, fmtDate, pct } from "./format";
import { locale, t } from "./i18n";
import type { EquityPoint, GroupStat, LinePoint, SeriesPoint } from "./types";

// Charts are plain SVG strings; colours come from CSS classes so the theme switch needs no re-render.

interface Box { w: number; h: number; top: number; right: number; bottom: number; left: number }

const scale = (d0: number, d1: number, r0: number, r1: number) => (v: number) =>
  d1 === d0 ? (r0 + r1) / 2 : r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

/** On narrow screens charts get a narrower, taller viewBox so 11px labels stay 11px-ish on screen. */
const narrow = () => typeof innerWidth === "number" && innerWidth < 700;
function fit(box: Box): Box {
  if (!narrow() || box.w <= 420) return box;
  return { ...box, w: 400, h: Math.round(box.h * 0.9), right: Math.min(box.right, box.right > 60 ? 84 : box.right), left: Math.min(box.left, 44) };
}

function ticks(min: number, max: number, count = 4) {
  const step = (max - min) / count;
  return Array.from({ length: count + 1 }, (_, i) => min + i * step);
}

export interface EquityOpts { box?: Box; draw?: boolean; callouts?: boolean }
/** Wide variant for full-width cards (Performance), so labels keep their size. */
export const EQ_WIDE: Box = { w: 1120, h: 400, top: 56, right: 24, bottom: 30, left: 58 };
const EQ_BOX: Box = { w: 760, h: 340, top: 64, right: 20, bottom: 30, left: 58 };

/** Step equity curve with grid, start-bankroll baseline, an end dot and tactics-board callouts
 *  (record high and worst trough) pinned to their points with leader lines. */
export function equityChart(eq: EquityPoint[], start: number, opts: EquityOpts = {}) {
  if (eq.length < 2) return `<div class="empty">${t("Pas encore assez de paris réglés.")}</div>`;
  const box = fit(opts.box ?? EQ_BOX);
  const vals = eq.map((p) => p.bankroll);
  const lo = Math.min(start, ...vals), hi = Math.max(start, ...vals), pad = (hi - lo) * 0.06 || 10;
  const t0 = new Date(eq[0].day).getTime(), t1 = new Date(eq[eq.length - 1].day).getTime();
  const x = scale(t0, t1, box.left, box.w - box.right);
  const y = scale(lo - pad, hi + pad, box.h - box.bottom, box.top);
  const X = (p: EquityPoint) => x(new Date(p.day).getTime());
  let d = `M${X(eq[0])},${y(eq[0].bankroll)}`;
  for (let i = 1; i < eq.length; i++) d += ` H${X(eq[i])} V${y(eq[i].bankroll)}`;
  const last = eq[eq.length - 1], lx = X(last), ly = y(last.bankroll);
  const grid = ticks(lo - pad, hi + pad).map((v) =>
    `<line class="c-grid" x1="${box.left}" x2="${box.w - box.right}" y1="${y(v)}" y2="${y(v)}"/>` +
    `<text class="c-axis" x="${box.left - 10}" y="${y(v) + 4}" text-anchor="end">${Math.round(v)}</text>`).join("");
  const months = monthTicks(t0, t1, box.w - box.left - box.right).map((t) =>
    `<text class="c-axis" x="${x(t)}" y="${box.h - 8}" text-anchor="middle">${new Date(t).toLocaleDateString(locale(), { month: "short", year: "2-digit" })}</text>`).join("");
  const svg = `<svg class="chart${opts.draw ? " draw" : ""}" viewBox="0 0 ${box.w} ${box.h}" role="img" aria-label="${t("Courbe de bankroll")}" data-eq='${JSON.stringify({ t0, t1, lo: lo - pad, hi: hi + pad, box })}'>
    ${grid}${months}
    <line class="c-base" x1="${box.left}" x2="${box.w - box.right}" y1="${y(start)}" y2="${y(start)}"/>
    <path class="c-area" d="${d} V${box.h - box.bottom} H${X(eq[0])}Z"/>
    <path class="c-line" pathLength="1" d="${d}"/>
    <circle class="c-end" cx="${lx}" cy="${ly}" r="6"/>
    <g class="c-hover" style="display:none"><line class="c-cross" y1="${box.top}" y2="${box.h - box.bottom}"/><circle class="c-hdot" r="5"/>
      <rect class="c-tip" width="164" height="44" rx="12"/><text class="c-tiptext" data-l="1"></text><text class="c-tiptext c-tipsub" data-l="2"></text></g>
  </svg>`;
  return `<div class="chart-wrap">${svg}${opts.callouts === false ? "" : equityCallouts(eq, X, y, box)}</div>`;
}

/** Record high and worst trough as pill callouts. Positions are % of the viewBox so they track the
 *  responsive SVG; the leader line and pill are sized in px so they stay legible at any width. */
function equityCallouts(eq: EquityPoint[], X: (p: EquityPoint) => number, y: (v: number) => number, box: Box) {
  const out: string[] = [];
  let peak = 0;
  eq.forEach((p, i) => { if (p.bankroll >= eq[peak].bankroll) peak = i; });
  const dd = drawdown(eq);
  let trough = 0;
  dd.forEach((p, i) => { if (p.dd < dd[trough].dd) trough = i; });
  // Leader lines run vertically into free space; near the plot's sides or edges they turn horizontal.
  const pin = (i: number, prefer: "up" | "down", tone: string, label: string, value: string) => {
    const px = X(eq[i]) / box.w, py = y(eq[i].bankroll) / box.h;
    const edge = prefer === "up" ? py < 0.3 : py > 0.7;
    const dir = px > 0.7 && (edge || px > 0.85) ? "left" : px < 0.3 && (edge || px < 0.15) ? "right" : prefer;
    const align = px > 0.72 ? "end" : px < 0.28 ? "start" : "mid";
    out.push(`<div class="callout ${dir} ${align} ${tone}" style="left:${(px * 100).toFixed(2)}%;top:${(py * 100).toFixed(2)}%">
      <span class="co-pt"></span><span class="co-line"></span><span class="co-pill"><i class="co-dot"></i>${label}<b>${value}</b></span></div>`);
  };
  pin(peak, "up", "co-pos", t("Record"), eur0(eq[peak].bankroll));
  if (dd[trough].dd < -0.03 && Math.abs(trough - peak) > eq.length * 0.08)
    pin(trough, "down", "co-neg", t("Pire creux"), pct(dd[trough].dd));
  return out.join("");
}

/** First-of-month ticks, thinned so labels (~64 units wide) never collide on the plot width. */
function monthTicks(t0: number, t1: number, plotW = 700) {
  const out: number[] = [];
  const d = new Date(t0); d.setUTCDate(1); d.setUTCMonth(d.getUTCMonth() + 1);
  const months = (t1 - t0) / (30 * 86400000), every = Math.max(1, Math.ceil(months / Math.max(1, plotW / 72)));
  for (let i = 0; d.getTime() < t1; i++, d.setUTCMonth(d.getUTCMonth() + 1)) if (i % every === 0) out.push(d.getTime());
  return out;
}

/** Crosshair + tooltip on an equity chart rendered by equityChart. */
export function attachEquityHover(root: HTMLElement, eq: EquityPoint[]) {
  const svg = root.querySelector<SVGSVGElement>("svg.chart[data-eq]");
  if (!svg) return;
  const meta = JSON.parse(svg.dataset.eq!) as { t0: number; t1: number; lo: number; hi: number; box: Box };
  const { box } = meta, x = scale(meta.t0, meta.t1, box.left, box.w - box.right), y = scale(meta.lo, meta.hi, box.h - box.bottom, box.top);
  const g = svg.querySelector<SVGGElement>(".c-hover")!, cross = g.querySelector("line")!, dot = g.querySelector(".c-hdot")!;
  const tip = g.querySelector(".c-tip")!, l1 = g.querySelector<SVGTextElement>("[data-l='1']")!, l2 = g.querySelector<SVGTextElement>("[data-l='2']")!;
  const times = eq.map((p) => new Date(p.day).getTime());
  const wrap = svg.parentElement!;
  svg.addEventListener("pointermove", (e) => {
    const r = svg.getBoundingClientRect(), px = ((e.clientX - r.left) / r.width) * box.w;
    const tm = meta.t0 + ((px - box.left) / (box.w - box.left - box.right)) * (meta.t1 - meta.t0);
    let i = times.findIndex((v) => v > tm) - 1;
    if (i < 0) i = tm < times[0] ? 0 : eq.length - 1;
    const p = eq[i], cx = x(times[i]), cy = y(p.bankroll);
    g.style.display = "";
    wrap.classList.add("hovering");
    cross.setAttribute("x1", `${cx}`); cross.setAttribute("x2", `${cx}`);
    dot.setAttribute("cx", `${cx}`); dot.setAttribute("cy", `${cy}`);
    const tx = cx + 176 > box.w ? cx - 174 : cx + 12, ty = Math.max(box.top - 40, Math.min(cy - 56, box.h - box.bottom - 48));
    tip.setAttribute("x", `${tx}`); tip.setAttribute("y", `${ty}`);
    l1.setAttribute("x", `${tx + 14}`); l1.setAttribute("y", `${ty + 19}`); l1.textContent = eur(p.bankroll);
    const prev = i > 0 ? eq[i - 1].bankroll : p.bankroll;
    l2.setAttribute("x", `${tx + 14}`); l2.setAttribute("y", `${ty + 35}`);
    l2.textContent = `${fmtDate(p.day)} · ${t("jour")} ${pct(p.bankroll / prev - 1)}`;
  });
  svg.addEventListener("pointerleave", () => { g.style.display = "none"; wrap.classList.remove("hovering"); });
}

/** Underwater curve: distance to the running bankroll peak. */
export function drawdownChart(eq: EquityPoint[], box0: Box = { w: 1120, h: 220, top: 12, right: 16, bottom: 22, left: 58 }) {
  if (eq.length < 2) return "";
  const box = fit(box0);
  const dd = drawdown(eq), lo = Math.min(-0.01, ...dd.map((d) => d.dd)) * 1.1;
  const t0 = new Date(eq[0].day).getTime(), t1 = new Date(eq[eq.length - 1].day).getTime();
  const x = scale(t0, t1, box.left, box.w - box.right), y = scale(lo, 0, box.h - box.bottom, box.top);
  let d = `M${box.left},${y(0)}`;
  for (const p of dd) d += ` H${x(new Date(p.day).getTime())} V${y(p.dd)}`;
  const grid = ticks(lo, 0, 3).map((v) =>
    `<line class="c-grid" x1="${box.left}" x2="${box.w - box.right}" y1="${y(v)}" y2="${y(v)}"/>` +
    `<text class="c-axis" x="${box.left - 8}" y="${y(v) + 4}" text-anchor="end">${Math.round(v * 100)}%</text>`).join("");
  return `<svg class="chart draw" viewBox="0 0 ${box.w} ${box.h}" role="img" aria-label="${t("Drawdown")}">${grid}
    <path class="c-loss-area c-area" d="${d} V${y(0)}Z"/><path class="c-loss c-line" pathLength="1" d="${d}"/></svg>`;
}

/** One row per year, one cell per month, coloured by the month's return. */
export function monthlyGrid(monthly: { month: string; return: number }[]) {
  const byYear = new Map<string, Map<number, number>>();
  for (const m of monthly) {
    const [yr, mo] = m.month.split("-");
    if (!byYear.has(yr)) byYear.set(yr, new Map());
    byYear.get(yr)!.set(Number(mo), m.return);
  }
  const names = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];
  const max = Math.max(0.05, ...monthly.map((m) => Math.abs(m.return)));
  const head = `<div class="mg-row mg-head"><span></span>${names.map((n) => `<span>${n}</span>`).join("")}<span>${t("Année")}</span></div>`;
  const rows = [...byYear.entries()].map(([yr, months]) => {
    const year = [...months.values()].reduce((a, r) => a * (1 + r), 1) - 1;
    const cells = names.map((_, i) => {
      const r = months.get(i + 1);
      if (r === undefined) return `<span class="mg-cell mg-none"></span>`;
      const a = Math.min(1, Math.abs(r) / max);
      const alpha = 0.15 + 0.85 * a;
      return `<span class="mg-cell ${r >= 0 ? "mg-up" : "mg-down"}${alpha > 0.5 ? " mg-hi" : ""}" style="--a:${alpha.toFixed(2)}" title="${pct(r)}">${pct(r, 0).replace(" %", "")}</span>`;
    }).join("");
    return `<div class="mg-row"><span class="mg-year">${yr}</span>${cells}<span class="mg-total ${year >= 0 ? "up" : "down"}">${pct(year)}</span></div>`;
  }).join("");
  return `<div class="mgrid">${head}${rows}</div>`;
}

/** Horizontal profit bars with the group's stats. */
export function groupTable(groups: GroupStat[], label: string) {
  const max = Math.max(1, ...groups.map((g) => Math.abs(g.profit)));
  return `<div class="tbl-scroll"><table class="tbl groups"><thead><tr><th>${label}</th><th class="r">${t("Paris")}</th><th class="r">${t("Réussite")}</th><th class="r">ROI</th><th class="r">${t("CLV")}</th><th>${t("Gain sur 1 000 €")}</th></tr></thead><tbody>
    ${groups.map((g) => `<tr><td class="strong">${esc(g.name)}</td><td class="r mono">${g.bets}</td><td class="r mono">${Math.round(g.win_rate * 100)} %</td>
      <td class="r mono ${g.roi >= 0 ? "up" : "down"}">${pct(g.roi)}</td><td class="r mono">${g.clv === null ? "–" : pct(g.clv)}</td>
      <td><div class="gbar"><span class="${g.profit >= 0 ? "gb-up" : "gb-down"}" style="width:${(Math.abs(g.profit) / max) * 100}%"></span><b>${g.profit >= 0 ? "+" : "−"}${Math.abs(Math.round(g.profit))} €</b></div></td></tr>`).join("")}
  </tbody></table></div>`;
}

/** CLV per bet (dots) and its 30-bet rolling mean (line). */
export function clvChart(series: { day: string; clv: number; rolling: number | null }[], box0: Box = { w: 1120, h: 300, top: 12, right: 16, bottom: 24, left: 58 }) {
  const box = fit(box0);
  if (series.length < 5) return `<div class="empty">${t("Pas encore assez de paris.")}</div>`;
  const vals = series.map((s) => s.clv), lim = Math.max(0.05, Math.min(0.25, Math.max(...vals.map(Math.abs))));
  const x = scale(0, series.length - 1, box.left, box.w - box.right), y = scale(-lim, lim, box.h - box.bottom, box.top);
  const dots = series.map((s, i) => `<circle class="${s.clv >= 0 ? "c-dot-up" : "c-dot-down"}" cx="${x(i)}" cy="${y(Math.max(-lim, Math.min(lim, s.clv)))}" r="2.4"/>`).join("");
  let line = "";
  series.forEach((s, i) => { if (s.rolling !== null) line += `${line ? " L" : "M"}${x(i)},${y(s.rolling)}`; });
  const grid = [-lim, -lim / 2, 0, lim / 2, lim].map((v) =>
    `<line class="${v === 0 ? "c-base" : "c-grid"}" x1="${box.left}" x2="${box.w - box.right}" y1="${y(v)}" y2="${y(v)}"/>` +
    `<text class="c-axis" x="${box.left - 8}" y="${y(v) + 4}" text-anchor="end">${v > 0 ? "+" : ""}${Math.round(v * 100)}%</text>`).join("");
  return `<svg class="chart draw" viewBox="0 0 ${box.w} ${box.h}" role="img" aria-label="${t("Closing line value")}">${grid}<g class="c-area">${dots}</g><path class="c-line" pathLength="1" d="${line}"/></svg>`;
}

/** Pinnacle price of the chosen outcome over time, with our entry price as a reference line. */
export function oddsChart(points: LinePoint[], ours: number, kickoff: string, box0: Box = { w: 560, h: 240, top: 14, right: 78, bottom: 26, left: 44 }) {
  const box = fit(box0);
  if (points.length === 0) return `<div class="empty">${t("Pas d'historique de cote Pinnacle.")}</div>`;
  const pts = points.map((p) => ({ t: new Date(`${p.t}Z`).getTime(), v: p.price }));
  const end = Math.max(pts[pts.length - 1].t, new Date(`${kickoff}Z`).getTime());
  const t0 = pts[0].t, t1 = end > t0 ? end : t0 + 3600000;
  const vals = [ours, ...pts.map((p) => p.v)], lo = Math.min(...vals), hi = Math.max(...vals), pad = (hi - lo) * 0.25 || 0.1;
  const x = scale(t0, t1, box.left, box.w - box.right), y = scale(lo - pad, hi + pad, box.h - box.bottom, box.top);
  let d = `M${x(pts[0].t)},${y(pts[0].v)}`;
  for (let i = 1; i < pts.length; i++) d += ` H${x(pts[i].t)} V${y(pts[i].v)}`;
  d += ` H${x(t1)}`;
  const last = pts[pts.length - 1];
  const grid = ticks(lo - pad, hi + pad, 3).map((v) =>
    `<line class="c-grid" x1="${box.left}" x2="${box.w - box.right}" y1="${y(v)}" y2="${y(v)}"/>` +
    `<text class="c-axis" x="${box.left - 6}" y="${y(v) + 4}" text-anchor="end">${v.toFixed(2)}</text>`).join("");
  const day = (t: number) => new Date(t).toLocaleDateString(locale(), { day: "2-digit", month: "2-digit" });
  return `<svg class="chart draw" viewBox="0 0 ${box.w} ${box.h}">${grid}
    <line class="c-ours" x1="${box.left}" x2="${box.w - box.right}" y1="${y(ours)}" y2="${y(ours)}"/>
    <text class="c-ours-t" x="${box.w - box.right + 6}" y="${y(ours) + 4}">${t("nous {v}", { v: ours.toFixed(2) })}</text>
    <path class="c-line" pathLength="1" d="${d}"/>
    <circle class="c-end" cx="${x(t1)}" cy="${y(last.v)}" r="5"/>
    <text class="c-axis-strong" x="${box.w - box.right + 6}" y="${y(last.v) + (Math.abs(y(last.v) - y(ours)) < 14 ? 16 : 4)}">${t("clôt. {v}", { v: last.v.toFixed(2) })}</text>
    <text class="c-axis" x="${box.left}" y="${box.h - 8}">${day(t0)}</text>
    <text class="c-axis" x="${box.w - box.right}" y="${box.h - 8}" text-anchor="end">${t("coup d'envoi {d}", { d: day(t1) })}</text></svg>`;
}

export interface Series { label: string; cls: string; points: SeriesPoint[]; dashed?: boolean }

/** Several dated series on one chart (Elo, xG), labelled at their last point. */
export function multiLineChart(series: Series[], digits = 0, box0: Box = { w: 560, h: 240, top: 14, right: 110, bottom: 26, left: 46 }) {
  const box = fit(box0);
  const all = series.flatMap((s) => s.points);
  if (all.length < 2) return `<div class="empty">${t("Pas assez de données.")}</div>`;
  const ts = all.map((p) => new Date(p.d).getTime()), vs = all.map((p) => p.v);
  const t0 = Math.min(...ts), t1 = Math.max(...ts), lo = Math.min(...vs), hi = Math.max(...vs), pad = (hi - lo) * 0.12 || 1;
  const x = scale(t0, t1, box.left, box.w - box.right), y = scale(lo - pad, hi + pad, box.h - box.bottom, box.top);
  const grid = ticks(lo - pad, hi + pad, 3).map((v) =>
    `<line class="c-grid" x1="${box.left}" x2="${box.w - box.right}" y1="${y(v)}" y2="${y(v)}"/>` +
    `<text class="c-axis" x="${box.left - 6}" y="${y(v) + 4}" text-anchor="end">${v.toFixed(digits)}</text>`).join("");
  const months = monthTicks(t0, t1, box.w - box.left - box.right).map((t) =>
    `<text class="c-axis" x="${x(t)}" y="${box.h - 8}" text-anchor="middle">${new Date(t).toLocaleDateString(locale(), { month: "short", year: "2-digit" })}</text>`).join("");
  const labels: number[] = [];
  const lines = series.filter((s) => s.points.length).map((s) => {
    const d = s.points.map((p, i) => `${i ? "L" : "M"}${x(new Date(p.d).getTime())},${y(p.v)}`).join(" ");
    const last = s.points[s.points.length - 1];
    let ly = y(last.v) + 4;
    while (labels.some((l) => Math.abs(l - ly) < 13)) ly += 13;
    labels.push(ly);
    return `<path class="c-series ${s.cls}${s.dashed ? " dashed" : ""}" d="${d}"/>
      <text class="c-series-t ${s.cls}" x="${box.w - box.right + 8}" y="${ly}">${s.label} ${last.v.toFixed(digits)}</text>`;
  }).join("");
  return `<svg class="chart" viewBox="0 0 ${box.w} ${box.h}">${grid}${months}${lines}</svg>`;
}
