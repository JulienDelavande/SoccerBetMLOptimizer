// Thin API client. Credentials are included so the session cookie travels with every call.
export interface UserProfile {
  user_id: number;
  email: string | null;
  name: string | null;
  avatar_url: string | null;
  bankroll: number;
  risk_preset: "prudent" | "balanced" | "aggressive";
  books: string[];
  min_edge: number | null;
  alerts_enabled: boolean;
  telegram_linked: boolean;
}
export interface PublicConfig { auth_enabled: boolean; google_client_id: string; telegram_bot: string }

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    credentials: "include",
    headers: init.body ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.status === 204 ? (undefined as T) : res.json();
}

export const getConfig = () => call<PublicConfig>("/config");
export const getMe = () => call<{ user: UserProfile | null }>("/auth/me").then((r) => r.user);
export const loginGoogle = (credential: string) =>
  call<{ user: UserProfile }>("/auth/google", { method: "POST", body: JSON.stringify({ credential }) }).then((r) => r.user);
export const logout = () => call("/auth/logout", { method: "POST" });
export const deleteAccount = () => call("/account", { method: "DELETE" });
export const updateSettings = (patch: Partial<Pick<UserProfile, "bankroll" | "risk_preset" | "books" | "min_edge" | "alerts_enabled">>) =>
  call<{ user: UserProfile }>("/me/settings", { method: "PUT", body: JSON.stringify(patch) }).then((r) => r.user);
export const getMyBets = () => call<{ bets: MyBet[]; stats: MyStats }>("/me/bets");
export const confirmBet = (b: { match_id: string; side: string; recommended_price?: number; placed_price?: number; stake?: number }) =>
  call("/me/bets", { method: "POST", body: JSON.stringify(b) });
export const removeBet = (match_id: string, side: string) =>
  call("/me/bets", { method: "DELETE", body: JSON.stringify({ match_id, side }) });
export const telegramLink = () => call<{ code: string; bot: string }>("/me/telegram/link", { method: "POST" });

export interface MyBet {
  match_id: string; side: string; recommended_price: number | null; placed_price: number | null;
  stake: number | null; status: string; settled_gain: number | null; created_at: string;
  league: string | null; home_team: string | null; away_team: string | null; commence_time: string | null;
}
export interface MyStats {
  bets: number; settled: number; bankroll_delta: number; roi: number | null; win_rate: number | null;
  equity: { t: string; delta: number }[];
}
