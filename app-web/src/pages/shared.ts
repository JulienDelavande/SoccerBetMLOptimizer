/** Row of big KPI cells: [label, value, sub, tone]. */
export const kpiStrip = (items: [string, string, string, string][]) =>
  `<section class="kpis">${items.map(([l, v, s, tone]) =>
    `<div class="kpi"><div class="k">${l}</div><div class="v num ${tone}">${v}</div><div class="s">${s}</div></div>`).join("")}</section>`;
