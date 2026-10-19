import type { Bet, EquityPoint } from "./types";

const nf = (min: number, max = min) =>
  new Intl.NumberFormat("fr-FR", { minimumFractionDigits: min, maximumFractionDigits: max });
const n0 = nf(0), n2 = nf(2), n1 = nf(1);

export const eur = (v: number) => `${n2.format(v)} €`;
export const eur0 = (v: number) => `${n0.format(Math.round(v))} €`;
export const odds = (v: number) => v.toFixed(2);
/** Signed percentage, e.g. +3,0 % / −11,2 % (true minus sign). */
export const pct = (v: number, digits = 1) => {
  const abs = Number(Math.abs(v * 100).toFixed(digits));
  const sign = abs === 0 ? "" : v > 0 ? "+" : "−";
  return `${sign}${(digits === 1 ? n1 : nf(digits)).format(abs)} %`;
};
export const pctPlain = (v: number) => `${n0.format(v * 100)} %`;

/** Bankroll split into integer and decimal parts for the big hero number. */
export const splitAmount = (v: number): [string, string] => {
  const [i, d] = n2.format(v).split(",");
  return [i, `,${d}€`];
};

export const SIDE_LABEL = { home: "1", draw: "N", away: "2" } as const;
export const betLabel = (b: Pick<Bet, "side" | "home" | "away">) =>
  b.side === "draw" ? "Match nul" : `Victoire ${b.side === "home" ? b.home : b.away}`;

export const BOOKS: Record<string, string> = { onexbet: "1xBet", williamhill: "William Hill", sport888: "888sport" };
export const bookName = (k: string) => BOOKS[k] ?? k;

const day = new Intl.DateTimeFormat("fr-FR", { weekday: "short", day: "2-digit", month: "short" });
const time = new Intl.DateTimeFormat("fr-FR", { hour: "2-digit", minute: "2-digit" });
const date = new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "2-digit", year: "2-digit" });
/** Backend timestamps are naive UTC. */
export const utc = (s: string) => new Date(s.endsWith("Z") || s.includes("+") ? s : `${s}Z`);
export const fmtDay = (s: string) => day.format(utc(s));
export const fmtTime = (s: string) => time.format(utc(s));
export const fmtDate = (s: string) => date.format(utc(s));
export const fmtMonth = (s: string) =>
  new Intl.DateTimeFormat("fr-FR", { month: "long", year: "numeric" }).format(new Date(`${s}-01T12:00:00Z`));

/** Euro stake for a bankroll, rounded to 10 cents (bookmakers dislike odd amounts anyway). */
export const stakeFor = (fraction: number, bankroll: number) => Math.round(fraction * bankroll * 10) / 10;

/** Keep the last `days` of the curve (all of it when days is null). */
export const sliceEquity = (eq: EquityPoint[], days: number | null) => {
  if (!days || eq.length === 0) return eq;
  const end = new Date(eq[eq.length - 1].day).getTime();
  return eq.filter((p) => end - new Date(p.day).getTime() <= days * 86400000);
};

export const drawdown = (eq: EquityPoint[]) => {
  let peak = -Infinity;
  return eq.map((p) => { peak = Math.max(peak, p.bankroll); return { day: p.day, dd: p.bankroll / peak - 1 }; });
};

export const esc = (s: string) =>
  s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

const parisDay = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Paris", year: "numeric", month: "2-digit", day: "2-digit" });
/** YYYY-MM-DD of a (naive UTC) timestamp in Paris time: the day a bet was recommended. */
export const dayKey = (s: string) => parisDay.format(utc(s));
export const todayKey = () => parisDay.format(new Date());
const longDay = new Intl.DateTimeFormat("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
export const fmtDayKey = (k: string) => longDay.format(new Date(`${k}T12:00:00Z`));
const stamp = new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Paris" });
export const fmtStamp = (s: string) => stamp.format(utc(s)).replace(" ", " à ");
