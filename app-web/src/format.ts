import type { Bet, EquityPoint } from "./types";
import { getLang, locale, t } from "./i18n";

const nf = (min: number, max = min) =>
  new Intl.NumberFormat(locale(), { minimumFractionDigits: min, maximumFractionDigits: max });

export const eur = (v: number) => `${nf(2).format(v)} €`;
export const eur0 = (v: number) => `${nf(0).format(Math.round(v))} €`;
export const odds = (v: number) => v.toFixed(2);
/** Signed percentage, e.g. +3,0 % / −11,2 % (true minus sign). */
export const pct = (v: number, digits = 1) => {
  const abs = Number(Math.abs(v * 100).toFixed(digits));
  const sign = abs === 0 ? "" : v > 0 ? "+" : "−";
  return `${sign}${nf(digits).format(abs)} %`;
};
export const pctPlain = (v: number) => `${nf(0).format(v * 100)} %`;

/** Bankroll split into integer and decimal parts for the big hero number. */
export const splitAmount = (v: number): [string, string] => {
  const parts = nf(2).formatToParts(v);
  const dec = parts.find((p) => p.type === "decimal")?.value ?? ",";
  const frac = parts.find((p) => p.type === "fraction")?.value ?? "00";
  const int = parts.filter((p) => p.type === "integer" || p.type === "group").map((p) => p.value).join("");
  return [int, `${dec}${frac}€`];
};

export const SIDE_LABEL = { home: "1", draw: "N", away: "2" } as const;
export const betLabel = (b: Pick<Bet, "side" | "home" | "away">) =>
  b.side === "draw" ? t("Match nul") : t("Victoire {team}", { team: b.side === "home" ? b.home : b.away });

export const BOOKS: Record<string, string> = { onexbet: "1xBet", williamhill: "William Hill", sport888: "888sport" };
export const bookName = (k: string) => BOOKS[k] ?? k;

/** Backend timestamps are naive UTC. */
export const utc = (s: string) => new Date(s.endsWith("Z") || s.includes("+") ? s : `${s}Z`);
const dtf = (opts: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat(locale(), opts);
export const fmtDay = (s: string) => dtf({ weekday: "short", day: "2-digit", month: "short" }).format(utc(s));
export const fmtTime = (s: string) => dtf({ hour: "2-digit", minute: "2-digit" }).format(utc(s));
export const fmtDate = (s: string) => dtf({ day: "2-digit", month: "2-digit", year: "2-digit" }).format(utc(s));
export const fmtMonth = (s: string) =>
  dtf({ month: "long", year: "numeric" }).format(new Date(`${s}-01T12:00:00Z`));

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
export const fmtDayKey = (k: string) =>
  dtf({ weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(new Date(`${k}T12:00:00Z`));
export const fmtStamp = (s: string) => {
  const str = dtf({ day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "Europe/Paris" }).format(utc(s));
  return getLang() === "fr" ? str.replace(" ", " à ") : str;
};
