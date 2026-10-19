export type Side = "home" | "draw" | "away";
export type Status = "upcoming" | "pending" | "won" | "lost" | "void";

export interface Bet {
  kickoff: string;
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
  today: Bet[];
  history: Bet[];
  equity: EquityPoint[];
  kpis: Kpis | null;
  monthly: { month: string; return: number }[];
  by_league: GroupStat[];
  by_odds: GroupStat[];
  clv_series: { day: string; clv: number; rolling: number | null }[];
}
