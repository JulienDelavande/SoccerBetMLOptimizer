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

  "CLV moyen": "Average CLV", "vs clôture Pinnacle": "vs Pinnacle close",

    "Paris": "Bets", "{n} % gagnants": "{n}% won", "ROI / pari": "ROI / bet",
  "Drawdown max": "Max drawdown",
  "Paris du jour": "Bets of the day", "Ma bankroll": "My bankroll",
  "Jour précédent": "Previous day", "Jour suivant": "Next day",
  "Aucun pari de valeur recommandé ce jour-là. Analyse quotidienne à 14 h 05 (heure de Paris).":
    "No value bet recommended that day. Daily analysis at 14:05 (Paris time).",
  "Publié le {t}, avant les coups d'envoi": "Published {t}, before kick-off",

  "{n} pari · total engagé": "{n} bet · total staked", "{n} paris · total engagé": "{n} bets · total staked",
  "À engager": "To stake", "{n} pari · {p} de la bankroll": "{n} bet · {p} of bankroll",
  "{n} paris · {p} de la bankroll": "{n} bets · {p} of bankroll",

  "Résultat": "Result", "{n}/{m} matchs joués · {w}": "{n}/{m} matches played · {w}",
  "{n} gagné": "{n} won", "{n} gagnés": "{n} won", "aucun match joué": "no match played",
  // bets table
  "Coup d'envoi": "Kick-off", "Match": "Match", "Pari · probabilités 1 / N / 2": "Bet · probabilities 1 / X / 2",
  "Pari": "Bet", "Cote": "Odds", "Juste prix": "Fair price", "Avantage": "Edge", "Mise": "Stake",
  "j'ai joué": "I bet this", "joué": "placed", "À venir": "Upcoming", "EN COURS": "LIVE",
  "Annulé": "Void", "en attente": "pending",
  "Victoire {team}": "{team} win", "Match nul": "Draw",
  // performance

  "Bankroll": "Bankroll", "Rendement": "Return", "cumulé": "cumulative", "départ": "from",
  "{n} % des paris mesurés": "{n}% of bets measured", "mise fixe": "flat stake",
  "Cote moyenne": "Average odds", "avantage moyen {v}": "avg edge {v}",
  "Mise moyenne": "Average stake", "de la bankroll": "of bankroll",
  "Drawdown": "Drawdown", "Écart au plus haut historique": "Distance from the running peak",
  "Rendement mensuel": "Monthly return", "Closing line value": "Closing line value",
  "Chaque point = un pari · ligne = moyenne glissante 30 paris":
    "Each dot = one bet · line = 30-bet rolling mean",

  "Par championnat": "By league", "Par cote": "By odds", "Championnat": "League", "Réussite": "Win rate",
  "CLV": "CLV",
  "Pas encore de pari réglé.": "No settled bet yet.", "Pas encore assez de paris réglés.": "Not enough settled bets yet.",
  "Pas assez de données.": "Not enough data.", "Pas encore assez de paris.": "Not enough bets yet.",
  "Année": "Year", "1A": "1Y", "TOUT": "ALL",
  // history

  "Tous": "All", "Gagnés": "Won", "Perdus": "Lost", "Tous les championnats": "All leagues",
  "Aucun pari.": "No bet.", "Voir plus ({n})": "Show more ({n})", "Date": "Date", "Score": "Score",
  // match page
  "Paris du {d}": "Bets of {d}", "Impossible de charger ce match ({e}).": "Could not load this match ({e}).",
  "Retour": "Back",
  "juste prix {v}": "fair price {v}", "vs juste prix": "vs fair price",
  "Mise · {b}": "Stake · {b}", "{p} de la bankroll": "{p} of bankroll",
  "Parier chez {book}": "Bet at {book}",
  "Cote Pinnacle · {label}": "Pinnacle odds · {label}",

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
  "Chaque jour, on compare à ce juste prix les cotes de plus de vingt bookmakers grand public (Pinnacle sert de référence, les bourses d'échange sont exclues). Quand une cote dépasse le juste prix d'au moins 2 % (cote ≤ 3,50, prix récent, avant le coup d'envoi), c'est un pari de valeur. Un bookmaker seul est rarement en retard : l'avantage vient du nombre de bookmakers surveillés. Un seul pari par match, au premier signal.":
    "Each day we compare that fair price with the odds of more than twenty mainstream bookmakers (Pinnacle is the reference, betting exchanges are left out). When a price beats fair value by at least 2% (odds ≤ 3.50, fresh price, before kick-off), it's a value bet. A single bookmaker rarely lags: the edge comes from watching many of them. One bet per match, at first signal.",
  "On mise avec Kelly": "We stake with Kelly",
  "La mise suit le critère de Kelly, divisé par deux : plus l'avantage est grand, plus on mise, sans jamais dépasser 5 % de la bankroll par pari ni 30 % par jour. En moyenne, moins de 2 % par pari.":
    "Stakes follow the Kelly criterion, halved: the bigger the edge, the bigger the stake, never above 5% of bankroll per bet or 30% per day. On average, under 2% per bet.",
  "On mesure avec le CLV": "We measure with CLV",

  "Les risques, honnêtement": "The risks, honestly",
  "Ça fluctue beaucoup.": "It swings a lot.",

  "Pas de modèle magique.": "No magic model.",
  "Un modèle maison a été testé sur 14 saisons et 22 championnats : il ne bat jamais Pinnacle. Toute la valeur vient de la comparaison des cotes.":
    "An in-house model was tested over 14 seasons and 22 leagues: it never beats Pinnacle. All the value comes from comparing odds.",


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
  "Relier Telegram": "Link Telegram", "Telegram relié. Tu reçois les paris du jour.":
    "Telegram linked. You'll receive the day's bets.",
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
  // redesign (Barley / Hunter / Tomato)
  "Aller au contenu": "Skip to content", "Navigation": "Navigation",
  "Passer en thème clair": "Switch to light theme", "Passer en thème sombre": "Switch to dark theme",
 "Période": "Period", "Record": "Record high", "Pire creux": "Worst trough",
  "jour": "day",
  "{n} pari de valeur ce jour": "{n} value bet on the day", "{n} paris de valeur ce jour": "{n} value bets on the day",
  "{n} paris réglés": "{n} settled bets", 
  "Analyse quotidienne 14 h 05": "Daily analysis at 14:05", "En direct": "Live", "Choisir un jour": "Pick a day",
  "Retirer ce pari": "Remove this bet",
  // fixes round (a11y, edge cases, signed-in)
  "Paris de valeur du jour": "Today's value bets", "{home} contre {away}": "{home} vs {away}",
  "départ {v}": "from {v}", "Dernière sélection": "Latest picks",
  "Dernière sélection · {d} · {n} pari": "Latest picks · {d} · {n} bet", "Dernière sélection · {d} · {n} paris": "Latest picks · {d} · {n} bets",
  "Mettre le bandeau en pause": "Pause the ticker",
  "N": "X", "pari : {s}": "bet: {s}",
  "Courbe de bankroll : de {a} à {b}, du {d0} au {d1}": "Bankroll curve: from {a} to {b}, {d0} to {d1}",
  "Drawdown : pire creux {v}": "Drawdown: worst trough {v}",
  "Closing line value : {n} paris, moyenne glissante finale {v}": "Closing line value: {n} bets, latest rolling mean {v}",
  "Cote Pinnacle de {a} à {b} jusqu'au coup d'envoi, notre cote {o}": "Pinnacle odds from {a} to {b} up to kick-off, our price {o}",
  "Elo": "Elo", "xG glissant": "Rolling xG",
  "Gagné": "Won", "Perdu": "Lost", "En cours": "Live", "mise remboursée": "stake refunded", "match en cours": "match in progress",
  "Impossible de retirer ce pari. Réessaie dans un instant.": "Could not remove this bet. Try again in a moment.",
  "Réglage non enregistré. Réessaie dans un instant.": "Setting not saved. Try again in a moment.",
  "Suppression impossible pour l'instant. Réessaie dans un instant.": "Could not delete the account right now. Try again in a moment.",
  "Impossible de charger les données. Vérifie ta connexion puis réessaie.": "Could not load the data. Check your connection and try again.",
  "Réessayer": "Try again", "({n} paris)": "({n} bets)", "({n} pari)": "({n} bet)",
  // live-only track record, neutral framing (L121-2 / L121-4 Code de la consommation)
  "{n} jours":
    "{n} days",
  "{n} jour":
    "{n} day",
  "{n} semaines":
    "{n} weeks",
  "{n} mois":
    "{n} months",
  "en cours":
    "in progress",
  "depuis le {d}":
    "since {d}",
  "Résultat sur {v} fictifs":
    "Result on a fictitious {v}",
  "Résultats passés : aucune garantie pour la suite":
    "Past results: no guarantee for the future",
  "Historique publié en direct depuis le {d} : {p}, {n} paris réglés. C'est un échantillon court et la variance est élevée : sur une période aussi courte, le rendement dépend surtout du hasard et peut s'inverser.":
    "Record published live since {d}: {p}, {n} settled bets. This is a short sample with high variance: over such a short period the return mostly reflects luck and can reverse.",
  "Information uniquement, pas un conseil de pari adapté à votre situation. Ne misez que ce que vous pouvez vous permettre de perdre. Interdit aux moins de 18 ans.":
    "Information only, not betting advice tailored to your situation. Only bet what you can afford to lose. Over 18s only.",
  "Joueurs Info Service :":
    "Gambling help (France), Joueurs Info Service:",
  "(appel non surtaxé).":
    "(standard call rate).",
  "Simulation : {v} fictifs au départ, en suivant les mises publiées (demi-Kelly) aux cotes publiées. Les résultats réels diffèrent : limites de mise, cotes qui bougent, paris indisponibles.":
    "Simulation: a fictitious {v} at the start, following the published stakes (half Kelly) at the published odds. Real results differ: stake limits, moving odds, unavailable bets.",
  "historique publié depuis le {d} · {p}":
    "record published since {d} · {p}",
  "paris réglés":
    "settled bets",
  "pari réglé":
    "settled bet",
  "{n} publiés":
    "{n} published",
  "Bankroll fictive":
    "Fictitious bankroll",
  "{w} gagnés · {l} perdus":
    "{w} won · {l} lost",
  "Rendement fictif":
    "Fictitious return",
  "bankroll fictive {v}":
    "fictitious bankroll {v}",
  "bankroll fictive":
    "fictitious bankroll",
  "pire recul depuis un sommet":
    "worst fall from a peak",
  "échantillon court":
    "short sample",
  "Publié en direct depuis le {d}":
    "Published live since {d}",
  "pour calculer mes mises":
    "to size my stakes",
  "Écart théorique":
    "Theoretical edge",
  "mise × avantage, non garanti":
    "stake × edge, not guaranteed",
  "Fourchette":
    "Range",
  "tout perdu / tout gagné":
    "all lost / all won",
  "Paris publiés en direct depuis le {d} · {p} · mises en demi-Kelly":
    "Bets published live since {d} · {p} · half-Kelly stakes",
  "vs clôture Pinnacle · {n} % des paris mesurés":
    "vs Pinnacle close · {n}% of bets measured",
  "Écart moyen":
    "Average edge",
  "cote publiée vs juste prix":
    "published price vs fair price",
  "mise fixe · échantillon court":
    "flat stake · short sample",
  "Le CLV compare la cote publiée à la cote de clôture de Pinnacle. Une moyenne positive signifie que les cotes publiées étaient en moyenne au-dessus du prix final du marché. C'est un écart mesuré, pas une garantie : le résultat des matchs reste aléatoire.":
    "CLV compares the published price with Pinnacle's closing price. A positive average means the published prices were, on average, above the market's final price. It is a measured gap, not a guarantee: match results stay random.",
  "{n} paris réglés, publiés en direct depuis le {d} · mise pour ta bankroll de {b} € · résultat en % de la bankroll du jour":
    "{n} settled bets, published live since {d} · stake for your {b} € bankroll · result as % of that day's bankroll",
  "Comment chaque pari est choisi, misé et mesuré.":
    "How each bet is picked, staked and measured.",
  "Les résultats des matchs sont bruités. La mesure suivie est la closing line value : la cote publiée comparée à la cote de clôture de Pinnacle. Sur les paris publiés depuis le {d}, elle est de {clv} en moyenne. C'est un écart mesuré avec le marché, pas une garantie de résultat.":
    "Match results are noisy. The measure we track is closing line value: the published price versus Pinnacle's closing price. On the bets published since {d} it averages {clv}. It is a measured gap with the market, not a guarantee of results.",
  "L'écart mesuré est de quelques % par pari : même s'il se maintient, une saison peut finir en perte (à peu près 4 chances sur 10).":
    "The measured edge is a few % per bet: even if it holds, a season can end in a loss (roughly 4 chances in 10).",
  "Les résultats passés ne garantissent pas les résultats futurs.":
    "Past results do not guarantee future results.",
  "L'historique publié est court ({p}) : il ne permet pas de conclure, et l'écart peut disparaître.":
    "The published record is short ({p}): it proves nothing yet, and the edge can disappear.",
  "Les bookmakers limitent les comptes.":
    "Bookmakers limit accounts.",
  "Un compte qui prend ces cotes est souvent plafonné : les résultats réels s'écartent alors de l'historique publié.":
    "An account taking these prices is often capped: real results then drift from the published record.",
  "Bankroll fictive.":
    "Fictitious bankroll.",
  "Information, pas conseil.":
    "Information, not advice.",
  "Ce site publie une méthode et son historique ; ce n'est pas un conseil de pari adapté à votre situation. Ne misez que ce que vous pouvez vous permettre de perdre. Interdit aux moins de 18 ans.":
    "This site publishes a method and its record; it is not betting advice tailored to your situation. Only bet what you can afford to lose. Over 18s only.",
  "Publié le {t}":
    "Published {t}",
  "Pinnacle jusqu'au coup d'envoi, face à la cote publiée. Clôture sous la cote publiée = CLV positif.":
    "Pinnacle up to kick-off against the published price. Close below the published price = positive CLV.",
  "bookmakers retenus": "bookmakers picked", "bookmaker retenu": "bookmaker picked",
  "{n} bookmakers avec un pari publié": "{n} bookmakers with a published bet", "{n} bookmaker avec un pari publié": "{n} bookmaker with a published bet",
  "Écart moyen entre la cote publiée et la cote de clôture de Pinnacle, le bookmaker de référence. Chaque jour, les cotes de plus de vingt bookmakers sont comparées à son juste prix ; un pari est publié quand une cote le dépasse.":
    "Average gap between the published price and Pinnacle's closing price, the reference bookmaker. Every day the odds of more than twenty bookmakers are compared with its fair price; a bet is published when a price beats it.",
  "Probabilités au moment du pari (juste prix Pinnacle)":
    "Probabilities at bet time (Pinnacle fair price)",
  "À la clôture":
    "At the close",
};
