import { drawdown, eur, fmtDate, pct } from "./format";
import type { EquityPoint, GroupStat } from "./types";

// Charts are plain SVG strings; colours come from CSS classes so the theme switch needs no re-render.

interface Box { w: number; h: number; top: number; right: number; bottom: number; left: number }

const scale = (d0: number, d1: number, r0: number, r1: number) => (v: number) =>
  d1 === d0 ? (r0 + r1) / 2 : r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

function ticks(min: number, max: number, count = 4) {
  const step = (max - min) / count;
  return Array.from({ length: count + 1 }, (_, i) => min + i * step);
}

/** Step equity curve with grid, start-bankroll baseline and a last-value tag. */
export function equityChart(eq: EquityPoint[], start: number, box: Box = { w: 760, h: 320, top: 16, right: 16, bottom: 28, left: 58 }) {
  if (eq.length < 2) return `<div class="empty">Pas encore assez de paris réglés.</div>`;
  const vals = eq.map((p) => p.bankroll);
  const lo = Math.min(start, ...vals), hi = Math.max(start, ...vals), pad = (hi - lo) * 0.08 || 10;
  const t0 = new Date(eq[0].day).getTime(), t1 = new Date(eq[eq.length - 1].day).getTime();
  const x = scale(t0, t1, box.left, box.w - box.right);
  const y = scale(lo - pad, hi + pad, box.h - box.bottom, box.top);
  const X = (p: EquityPoint) => x(new Date(p.day).getTime());
  let d = `M${X(eq[0])},${y(eq[0].bankroll)}`;
  for (let i = 1; i < eq.length; i++) d += ` H${X(eq[i])} V${y(eq[i].bankroll)}`;
  const last = eq[eq.length - 1], lx = X(last), ly = y(last.bankroll);
  const grid = ticks(lo - pad, hi + pad).map((v) =>
    `<line class="c-grid" x1="${box.left}" x2="${box.w - box.right}" y1="${y(v)}" y2="${y(v)}"/>` +
    `<text class="c-axis" x="${box.left - 8}" y="${y(v) + 4}" text-anchor="end">${Math.round(v)}</text>`).join("");
  const months = monthTicks(t0, t1).map((t) =>
    `<line class="c-grid" y1="${box.top}" y2="${box.h - box.bottom}" x1="${x(t)}" x2="${x(t)}"/>` +
    `<text class="c-axis" x="${x(t) + 4}" y="${box.h - 8}">${new Date(t).toLocaleDateString("fr-FR", { month: "short", year: "2-digit" })}</text>`).join("");
  const tagW = 92, tagX = Math.min(lx - tagW / 2, box.w - box.right - tagW), tagY = ly > box.h / 2 ? ly - 34 : ly + 12;
  return `<svg class="chart" viewBox="0 0 ${box.w} ${box.h}" data-eq='${JSON.stringify({ t0, t1, lo: lo - pad, hi: hi + pad, box })}'>
    ${grid}${months}
    <line class="c-base" x1="${box.left}" x2="${box.w - box.right}" y1="${y(start)}" y2="${y(start)}"/>
    <path class="c-area" d="${d} V${box.h - box.bottom} H${X(eq[0])}Z"/>
    <path class="c-line" d="${d}"/>
    <rect class="c-dot" x="${lx - 5}" y="${ly - 5}" width="10" height="10"/>
    <rect class="c-tag" x="${tagX}" y="${tagY}" width="${tagW}" height="22"/>
    <text class="c-tagtext" x="${tagX + tagW / 2}" y="${tagY + 15}" text-anchor="middle">${eur(last.bankroll).replace(" €", "")}</text>
    <g class="c-hover" style="display:none"><line class="c-cross" y1="${box.top}" y2="${box.h - box.bottom}"/><rect class="c-dot" width="8" height="8"/>
      <rect class="c-tip" width="150" height="40"/><text class="c-tiptext" data-l="1"></text><text class="c-tiptext c-tipsub" data-l="2"></text></g>
  </svg>`;
}

function monthTicks(t0: number, t1: number) {
  const out: number[] = [];
  const d = new Date(t0); d.setUTCDate(1); d.setUTCMonth(d.getUTCMonth() + 1);
  const months = (t1 - t0) / (30 * 86400000), every = months > 18 ? 3 : months > 8 ? 2 : 1;
  for (let i = 0; d.getTime() < t1; i++, d.setUTCMonth(d.getUTCMonth() + 1)) if (i % every === 0) out.push(d.getTime());
  return out;
}

/** Crosshair + tooltip on an equity chart rendered by equityChart. */
export function attachEquityHover(root: HTMLElement, eq: EquityPoint[]) {
  const svg = root.querySelector<SVGSVGElement>("svg.chart[data-eq]");
  if (!svg) return;
  const meta = JSON.parse(svg.dataset.eq!) as { t0: number; t1: number; lo: number; hi: number; box: Box };
  const { box } = meta, x = scale(meta.t0, meta.t1, box.left, box.w - box.right), y = scale(meta.lo, meta.hi, box.h - box.bottom, box.top);
  const g = svg.querySelector<SVGGElement>(".c-hover")!, cross = g.querySelector("line")!, dot = g.querySelector(".c-dot")!;
  const tip = g.querySelector(".c-tip")!, l1 = g.querySelector<SVGTextElement>("[data-l='1']")!, l2 = g.querySelector<SVGTextElement>("[data-l='2']")!;
  const times = eq.map((p) => new Date(p.day).getTime());
  svg.addEventListener("mousemove", (e) => {
    const r = svg.getBoundingClientRect(), px = ((e.clientX - r.left) / r.width) * box.w;
    const t = meta.t0 + ((px - box.left) / (box.w - box.left - box.right)) * (meta.t1 - meta.t0);
    let i = times.findIndex((v) => v > t) - 1;
    if (i < 0) i = t < times[0] ? 0 : eq.length - 1;
    const p = eq[i], cx = x(times[i]), cy = y(p.bankroll);
    g.style.display = "";
    cross.setAttribute("x1", `${cx}`); cross.setAttribute("x2", `${cx}`);
    dot.setAttribute("x", `${cx - 4}`); dot.setAttribute("y", `${cy - 4}`);
    const tx = cx + 160 > box.w ? cx - 158 : cx + 8, ty = Math.max(box.top, Math.min(cy - 48, box.h - box.bottom - 44));
    tip.setAttribute("x", `${tx}`); tip.setAttribute("y", `${ty}`);
    l1.setAttribute("x", `${tx + 10}`); l1.setAttribute("y", `${ty + 17}`); l1.textContent = eur(p.bankroll);
    const prev = i > 0 ? eq[i - 1].bankroll : p.bankroll;
    l2.setAttribute("x", `${tx + 10}`); l2.setAttribute("y", `${ty + 32}`);
    l2.textContent = `${fmtDate(p.day)} · jour ${pct(p.bankroll / prev - 1)}`;
  });
  svg.addEventListener("mouseleave", () => { g.style.display = "none"; });
}

/** Underwater curve: distance to the running bankroll peak. */
export function drawdownChart(eq: EquityPoint[], box: Box = { w: 760, h: 150, top: 10, right: 16, bottom: 22, left: 58 }) {
  if (eq.length < 2) return "";
  const dd = drawdown(eq), lo = Math.min(-0.01, ...dd.map((d) => d.dd)) * 1.1;
  const t0 = new Date(eq[0].day).getTime(), t1 = new Date(eq[eq.length - 1].day).getTime();
  const x = scale(t0, t1, box.left, box.w - box.right), y = scale(lo, 0, box.h - box.bottom, box.top);
  let d = `M${box.left},${y(0)}`;
  for (const p of dd) d += ` H${x(new Date(p.day).getTime())} V${y(p.dd)}`;
  const grid = ticks(lo, 0, 3).map((v) =>
    `<line class="c-grid" x1="${box.left}" x2="${box.w - box.right}" y1="${y(v)}" y2="${y(v)}"/>` +
    `<text class="c-axis" x="${box.left - 8}" y="${y(v) + 4}" text-anchor="end">${Math.round(v * 100)}%</text>`).join("");
  return `<svg class="chart" viewBox="0 0 ${box.w} ${box.h}">${grid}
    <path class="c-loss-area" d="${d} V${y(0)}Z"/><path class="c-loss" d="${d}"/></svg>`;
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
  const head = `<div class="mg-row mg-head"><span></span>${names.map((n) => `<span>${n}</span>`).join("")}<span>Année</span></div>`;
  const rows = [...byYear.entries()].map(([yr, months]) => {
    const year = [...months.values()].reduce((a, r) => a * (1 + r), 1) - 1;
    const cells = names.map((_, i) => {
      const r = months.get(i + 1);
      if (r === undefined) return `<span class="mg-cell mg-none"></span>`;
      const a = Math.min(1, Math.abs(r) / max);
      return `<span class="mg-cell ${r >= 0 ? "mg-up" : "mg-down"}" style="--a:${(0.15 + 0.85 * a).toFixed(2)}" title="${pct(r)}">${pct(r, 0).replace(" %", "")}</span>`;
    }).join("");
    return `<div class="mg-row"><span class="mg-year">${yr}</span>${cells}<span class="mg-total ${year >= 0 ? "up" : "down"}">${pct(year)}</span></div>`;
  }).join("");
  return `<div class="mgrid">${head}${rows}</div>`;
}

/** Horizontal profit bars with the group's stats. */
export function groupTable(groups: GroupStat[], label: string) {
  const max = Math.max(1, ...groups.map((g) => Math.abs(g.profit)));
  return `<table class="tbl groups"><thead><tr><th>${label}</th><th class="r">Paris</th><th class="r">Réussite</th><th class="r">ROI</th><th class="r">CLV</th><th>Gain sur 1 000 €</th></tr></thead><tbody>
    ${groups.map((g) => `<tr><td class="strong">${g.name}</td><td class="r">${g.bets}</td><td class="r">${Math.round(g.win_rate * 100)} %</td>
      <td class="r ${g.roi >= 0 ? "up" : "down"}">${pct(g.roi)}</td><td class="r">${g.clv === null ? "–" : pct(g.clv)}</td>
      <td><div class="gbar"><span class="${g.profit >= 0 ? "gb-up" : "gb-down"}" style="width:${(Math.abs(g.profit) / max) * 100}%"></span><b>${g.profit >= 0 ? "+" : "−"}${Math.abs(Math.round(g.profit))} €</b></div></td></tr>`).join("")}
  </tbody></table>`;
}

/** CLV per bet (dots) and its 30-bet rolling mean (line). */
export function clvChart(series: { day: string; clv: number; rolling: number | null }[], box: Box = { w: 760, h: 220, top: 12, right: 16, bottom: 24, left: 58 }) {
  if (series.length < 5) return `<div class="empty">Pas encore assez de paris.</div>`;
  const vals = series.map((s) => s.clv), lim = Math.max(0.05, Math.min(0.25, Math.max(...vals.map(Math.abs))));
  const x = scale(0, series.length - 1, box.left, box.w - box.right), y = scale(-lim, lim, box.h - box.bottom, box.top);
  const dots = series.map((s, i) => `<rect class="${s.clv >= 0 ? "c-dot-up" : "c-dot-down"}" x="${x(i) - 2}" y="${y(Math.max(-lim, Math.min(lim, s.clv))) - 2}" width="4" height="4"/>`).join("");
  let line = "";
  series.forEach((s, i) => { if (s.rolling !== null) line += `${line ? " L" : "M"}${x(i)},${y(s.rolling)}`; });
  const grid = [-lim, -lim / 2, 0, lim / 2, lim].map((v) =>
    `<line class="${v === 0 ? "c-base" : "c-grid"}" x1="${box.left}" x2="${box.w - box.right}" y1="${y(v)}" y2="${y(v)}"/>` +
    `<text class="c-axis" x="${box.left - 8}" y="${y(v) + 4}" text-anchor="end">${v > 0 ? "+" : ""}${Math.round(v * 100)}%</text>`).join("");
  return `<svg class="chart" viewBox="0 0 ${box.w} ${box.h}">${grid}${dots}<path class="c-line" d="${line}"/></svg>`;
}
