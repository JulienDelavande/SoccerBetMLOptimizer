export type Side = "home" | "draw" | "away";
export type Status = "upcoming" | "pending" | "won" | "lost" | "void";

export interface Bet {
  id: string;
  kickoff: string;
  odds_at: string;
  published: boolean;
  league_key: string | null;
  link: string | null;
  home: string;
  away: string;
  league: string;
  side: Side;
  price: number;
  fair_price: number;
  edge: number;
  stake: number;
  book: string;
  status: Status;
  score: string | null;
  gain: number;
  clv: number | null;
}

export interface Kpis {
  bankroll: number;
  return: number;
  bets: number;
  win_rate: number;
  roi: number;
  avg_price: number;
  avg_stake: number;
  avg_edge: number;
  clv: number | null;
  clv_coverage: number;
  max_drawdown: number;
  max_drawdown_day: string;
  since: string;
}

export interface GroupStat { name: string; bets: number; win_rate: number; roi: number; clv: number | null; profit: number }
export interface EquityPoint { day: string; bankroll: number }

export interface SiteData {
  generated_at: string;
  start_bankroll: number;
  live_since: string;
  bets: Bet[];
  equity: EquityPoint[];
  kpis: Kpis | null;
  monthly: { month: string; return: number }[];
  by_league: GroupStat[];
  by_odds: GroupStat[];
  clv_series: { day: string; clv: number; rolling: number | null }[];
}

export interface FormGame { date: string; opponent: string; venue: "H" | "A"; score: string; result: "W" | "D" | "L"; league: string }
export interface BookPrices { key: string; title: string; home: number; draw: number; away: number; margin: number; ours: boolean }
export interface LinePoint { t: string; price: number }

export interface MatchDetail {
  id: string;
  home: string;
  away: string;
  league: string;
  league_key: string | null;
  kickoff: string;
  odds_at: string;
  status: Status;
  score: string | null;
  xg: [number, number] | null;
  venue: string | null;
  referee: string | null;
  bet: { side: Side; book: string; price: number; fair_price: number; edge: number; stake: number; gain: number; clv: number | null; link: string | null };
  closing_fair_price: Record<Side, number> | null;
  pinnacle: Record<Side, LinePoint[]>;
  books: BookPrices[];
  form: { home: FormGame[]; away: FormGame[] };
  h2h: { date: string; home: string; away: string; score: string; league: string }[];
}
