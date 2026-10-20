// Lightweight i18n: the French string is the key; EN[fr] gives the English text.
// Missing entries fall back to French, so partial coverage degrades gracefully.
export type Lang = "fr" | "en";

const KEY = "lang";
let lang: Lang = detect();

function detect(): Lang {
  if (typeof location !== "undefined") {
    const q = new URLSearchParams(location.search).get("lang");
    if (q === "fr" || q === "en") return q;
  }
  if (typeof localStorage !== "undefined") {
    const saved = localStorage.getItem(KEY);
    if (saved === "fr" || saved === "en") return saved;
  }
  if (typeof navigator !== "undefined" && navigator.language?.toLowerCase().startsWith("en")) return "en";
  return "fr";
}

export const getLang = (): Lang => lang;
export const setLang = (l: Lang) => { lang = l; if (typeof localStorage !== "undefined") localStorage.setItem(KEY, l); };
export const locale = () => (lang === "en" ? "en-GB" : "fr-FR");

/** Translate a French source string. `vars` fills {name} placeholders. */
export function t(fr: string, vars?: Record<string, string | number>): string {
  let s = lang === "en" ? EN[fr] ?? fr : fr;
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, String(v));
  return s;
}

const EN: Record<string, string> = {
  "Règle ton espace, puis bascule en « Moi » (en haut) pour voir les paris et tes stats à ta façon.": "Set up your space, then switch to \"Me\" (top) to see the bets and your stats your way.",
  "Vue": "View",
  "Mon historique": "My history",
  "Ma performance": "My performance",
  "Aucun pari chez tes bookmakers ce jour-là.": "No bet at your bookmakers that day.",
  "Mes paris de valeur du jour (tes bookmakers)": "Your value bets of the day (your bookmakers)",
  // nav / chrome
  "Aujourd'hui": "Today", "Performance": "Performance", "Historique": "History", "Méthode": "Method",
  "Compte": "Account", "Bot": "Bot", "Moi": "Me", "Mon espace": "My space", "CHARGEMENT…": "LOADING…", "LIVE": "LIVE", "MAJ": "UPD", "HORS LIGNE": "OFFLINE",
  "Chargement…": "Loading…",
  "OptiBet · paris de valeur, pas de conseil financier. Jouer comporte des risques.":
    "OptiBet · value bets, not financial advice. Gambling involves risk.",
  "18+ · Joueurs Info Service 09 74 75 13 13": "18+ · Please gamble responsibly",
  "Impossible de charger les données ({e}). Réessayez dans un instant.":
    "Could not load data ({e}). Please try again shortly.",
  // today / hero
  "Bankroll · départ {v} · {since}": "Bankroll · from {v} · {since}",
  "{n} paris réglés. ": "{n} settled bets. ",
  "On compare chaque cote à celle de Pinnacle, le bookmaker le plus précis du marché, et on ne joue que quand un bookmaker est en retard sur lui.":
    "We compare every price to Pinnacle, the sharpest bookmaker, and only bet when a bookmaker lags behind it.",
  "CLV moyen": "Average CLV", "vs clôture Pinnacle": "vs Pinnacle close",
  "Paris": "Bets", "{n} % gagnants": "{n}% won", "ROI / pari": "ROI / bet", "cote moy. {v}": "avg odds {v}",
  "Drawdown max": "Max drawdown",
  "Paris du jour": "Bets of the day", "Ma bankroll": "My bankroll",
  "Jour précédent": "Previous day", "Jour suivant": "Next day",
  "Aucun pari de valeur recommandé ce jour-là. Analyse quotidienne à 14 h 05 (heure de Paris).":
    "No value bet recommended that day. Daily analysis at 14:05 (Paris time).",
  "✓ Publié le {t}, avant les coups d'envoi": "✓ Published {t}, before kick-off",
  "Cotes relevées le {t}": "Odds recorded {t}",
  "{n} pari · total engagé": "{n} bet · total staked", "{n} paris · total engagé": "{n} bets · total staked",
  "À engager": "To stake", "{n} pari · {p} de la bankroll": "{n} bet · {p} of bankroll",
  "{n} paris · {p} de la bankroll": "{n} bets · {p} of bankroll",
  "Gain espéré": "Expected gain", "moyenne sur le long terme": "long-run average",
  "Si tout passe": "If all win", "tous les paris gagnants": "every bet wins",
  "Résultat": "Result", "{n}/{m} matchs joués · {w}": "{n}/{m} matches played · {w}",
  "{n} gagné": "{n} won", "{n} gagnés": "{n} won", "aucun match joué": "no match played",
  // bets table
  "Coup d'envoi": "Kick-off", "Match": "Match", "Pari · probabilités 1 / N / 2": "Bet · probabilities 1 / X / 2",
  "Pari": "Bet", "Cote": "Odds", "Juste prix": "Fair price", "Avantage": "Edge", "Mise": "Stake",
  "j'ai joué": "I bet this", "✓ joué": "✓ placed", "À venir": "Upcoming", "EN COURS": "LIVE",
  "Annulé": "Void", "en attente": "pending",
  "Victoire {team}": "{team} win", "Match nul": "Draw",
  // performance
  "Depuis le {d} · mises en demi-Kelly": "Since {d} · half-Kelly staking",
  "Bankroll": "Bankroll", "Rendement": "Return", "cumulé": "cumulative", "départ": "from",
  "{n} % des paris mesurés": "{n}% of bets measured", "mise fixe": "flat stake",
  "Cote moyenne": "Average odds", "avantage moyen {v}": "avg edge {v}",
  "Mise moyenne": "Average stake", "de la bankroll": "of bankroll",
  "Drawdown": "Drawdown", "Écart au plus haut historique": "Distance from the running peak",
  "Rendement mensuel": "Monthly return", "Closing line value": "Closing line value",
  "Chaque point = un pari · ligne = moyenne glissante 30 paris":
    "Each dot = one bet · line = 30-bet rolling mean",
  "Le CLV compare notre cote à la cote de clôture de Pinnacle. Positif en moyenne = on achète moins cher que le juste prix : c'est l'indicateur qui prédit les gains à long terme, bien avant le résultat des matchs.":
    "CLV compares our price to Pinnacle's closing price. Positive on average = we buy below fair value: the metric that predicts long-run profit, long before match results.",
  "Par championnat": "By league", "Par cote": "By odds", "Championnat": "League", "Réussite": "Win rate",
  "CLV": "CLV", "Gain sur 1 000 €": "Profit on 1,000 €",
  "Pas encore de pari réglé.": "No settled bet yet.", "Pas encore assez de paris réglés.": "Not enough settled bets yet.",
  "Pas assez de données.": "Not enough data.", "Pas encore assez de paris.": "Not enough bets yet.",
  "Année": "Year", "1A": "1Y", "TOUT": "ALL",
  // history
  "{n} paris · gain en % de la bankroll du jour": "{n} bets · gain as % of that day's bankroll",
  "{n} paris · mise pour {b} € · gain en % de la bankroll du jour":
    "{n} bets · stake for {b} € · gain as % of that day's bankroll",
  "Tous": "All", "Gagnés": "Won", "Perdus": "Lost", "Tous les championnats": "All leagues",
  "Aucun pari.": "No bet.", "Voir plus ({n})": "Show more ({n})", "Date": "Date", "Score": "Score",
  // match page
  "Paris du {d}": "Bets of {d}", "Impossible de charger ce match ({e}).": "Could not load this match ({e}).",
  "Retour": "Back", "Gagné · {p} de bankroll": "Won · {p} of bankroll", "Perdu · {p} de bankroll": "Lost · {p} of bankroll",
  "juste prix {v}": "fair price {v}", "vs juste prix": "vs fair price",
  "Mise · {b}": "Stake · {b}", "{p} de la bankroll": "{p} of bankroll",
  "Parier chez {book} ↗": "Bet at {book} ↗",
  "Cote Pinnacle · {label}": "Pinnacle odds · {label}",
  "Pinnacle jusqu'au coup d'envoi contre notre cote. Clôture sous notre cote = on a acheté moins cher que le marché (CLV).":
    "Pinnacle up to kick-off against our price. Close below our price = we bought below the market (CLV).",
  "Elo · 2 saisons": "Elo · 2 seasons",
  "Force des équipes (Elo maison, tous championnats FBref), avant chaque match.":
    "Team strength (in-house Elo, all FBref leagues), before each match.",
  "Elo indisponible.": "Elo unavailable.",
  "xG glissant · 8 matchs": "Rolling xG · 8 matches",
  "trait plein = xG pour · pointillé = xG contre": "solid = xG for · dashed = xG against",
  "Forme": "Form", "Confrontations": "Head-to-head", "Aucune confrontation récente.": "No recent meeting.",
  "Cotes au moment du pari": "Odds at bet time",
  "{n} bookmakers · meilleure cote en gras · notre ligne surlignée":
    "{n} bookmakers · best price in bold · our row highlighted",
  "Pas de cotes enregistrées.": "No odds recorded.", "Bookmaker": "Bookmaker", "Marge": "Margin",
  "Arbitre : {ref} · Données FBref, cotes The Odds API": "Referee: {ref} · Data FBref, odds The Odds API",
  "Données FBref, cotes The Odds API": "Data FBref, odds The Odds API",
  "Pas d'historique de cote Pinnacle.": "No Pinnacle odds history.",
  "coup d'envoi {d}": "kick-off {d}", "nous {v}": "us {v}", "clôt. {v}": "close {v}",
  // method
  "Pinnacle donne le juste prix": "Pinnacle gives the fair price",
  "Pinnacle est le bookmaker le plus précis du monde : marges faibles, il accepte les gros parieurs et corrige ses cotes avec leur argent. On retire sa marge (méthode de Shin) pour obtenir la vraie probabilité de chaque issue.":
    "Pinnacle is the sharpest bookmaker in the world: low margins, it welcomes big bettors and corrects its odds with their money. We strip its margin (Shin method) to get the true probability of each outcome.",
  "On cherche les bookmakers en retard": "We find the lagging bookmakers",
  "Chaque jour, on compare les cotes de 1xBet à ce juste prix. Quand une cote dépasse le juste prix d'au moins 2 % (cote ≤ 3,50, prix récent, avant le coup d'envoi), c'est un pari de valeur. Un seul pari par match, au premier signal.":
    "Each day we compare the bookmakers' prices to that fair price. When a price beats fair value by at least 2% (odds ≤ 3.50, fresh price, before kick-off), it's a value bet. One bet per match, at first signal.",
  "On mise avec Kelly": "We stake with Kelly",
  "La mise suit le critère de Kelly, divisé par deux : plus l'avantage est grand, plus on mise, sans jamais dépasser 5 % de la bankroll par pari ni 30 % par jour. En moyenne, moins de 2 % par pari.":
    "Stakes follow the Kelly criterion, halved: the bigger the edge, the bigger the stake, never above 5% of bankroll per bet or 30% per day. On average, under 2% per bet.",
  "On mesure avec le CLV": "We measure with CLV",
  "Les résultats des matchs sont bruités. Le vrai juge est la closing line value : notre cote comparée à la cote de clôture de Pinnacle. Elle est de {clv} en moyenne ici : on achète moins cher que le marché.":
    "Match results are noisy. The real judge is closing line value: our price versus Pinnacle's closing price. It averages {clv} here: we buy below the market.",
  "Les risques, honnêtement": "The risks, honestly",
  "Ça fluctue beaucoup.": "It swings a lot.",
  "L'avantage est d'environ 2 à 3 % par pari : sur une saison, on a à peu près 4 chances sur 10 d'être en perte malgré tout.":
    "The edge is about 2-3% per bet: over a season there's roughly a 4-in-10 chance of still being down.",
  "Les gains passés ne garantissent rien.": "Past results guarantee nothing.",
  "L'espérance tourne autour de quelques % de la bankroll par saison, pas +40 % par an.":
    "Expectation is a few % of bankroll per season, not +40% a year.",
  "Les bookmakers limitent les gagnants.": "Bookmakers limit winners.",
  "Un compte qui gagne finit souvent plafonné.": "A winning account often gets capped.",
  "Pas de modèle magique.": "No magic model.",
  "Un modèle maison a été testé sur 14 saisons et 22 championnats : il ne bat jamais Pinnacle. Toute la valeur vient de la comparaison des cotes.":
    "An in-house model was tested over 14 seasons and 22 leagues: it never beats Pinnacle. All the value comes from comparing odds.",
  "N'engagez que de l'argent que vous acceptez de perdre. 18+.":
    "Only stake money you can afford to lose. 18+.",
  "Historique avant le 19/10/2026 rejoué avec les mêmes règles sur les cotes enregistrées à l'époque.":
    "History before 19/10/2026 replayed with the same rules on the odds recorded at the time.",
  // account
  "Mon compte": "My account",
  "Un espace perso gratuit pour suivre la méthode à ta façon.":
    "A free personal space to follow the method your way.",
  "Tes bookmakers": "Your bookmakers", "ne vois que les paris jouables chez toi.": "see only the bets you can place.",
  "Ton risque": "Your risk", "prudent, équilibré ou agressif.": "cautious, balanced or aggressive.",
  "Ta bankroll": "Your bankroll", "mises calculées pour ton montant, suivi de tes gains réels.":
    "stakes sized to your amount, tracking of your real P&L.",
  "Alertes Telegram": "Telegram alerts", "les paris du jour, dès qu'ils sortent.": "the day's bets, as soon as they're out.",
  "La connexion sera bientôt disponible.": "Sign-in will be available soon.",
  "Déconnexion": "Sign out", "Réglages": "Settings",
  "Niveau de risque": "Risk level", "Prudent": "Cautious", "Équilibré": "Balanced", "Agressif": "Aggressive",
  "quart de Kelly · mises prudentes": "quarter Kelly · cautious stakes",
  "demi-Kelly · recommandé": "half Kelly · recommended", "Kelly plein · plus volatil": "full Kelly · more volatile",
  "Mes bookmakers": "My bookmakers", "(aucun = tous)": "(none = all)",
  "Relie Telegram pour recevoir les paris du jour dès leur sortie.":
    "Link Telegram to get the day's bets as soon as they're out.",
  "Relier Telegram": "Link Telegram", "✓ Telegram relié. Tu reçois les paris du jour.":
    "✓ Telegram linked. You'll receive the day's bets.",
  "Ouvre le bot et valide : ": "Open the bot and confirm: ", "Ouvrir @{bot}": "Open @{bot}",
  "Envoie {cmd} au bot Telegram.": "Send {cmd} to the Telegram bot.", "Indisponible pour l'instant.": "Unavailable for now.",
  "Mes stats": "My stats", "Confirme tes paris pour suivre ta bankroll réelle.":
    "Confirm your bets to track your real bankroll.",
  "Gain net": "Net gain", "Paris réglés": "Settled bets",
  "Mes paris": "My bets", "Erreur de chargement.": "Loading error.",
  "Aucun pari confirmé. Depuis les paris du jour, indique ceux que tu as joués.":
    "No confirmed bet. From the day's bets, mark the ones you placed.",
  "Supprimer ton compte efface définitivement tes réglages et tes paris.":
    "Deleting your account permanently erases your settings and bets.",
  "Supprimer mon compte": "Delete my account",
  "Supprimer définitivement ton compte et toutes tes données ?":
    "Permanently delete your account and all your data?",
  "Échec de la connexion.": "Sign-in failed.",
};
