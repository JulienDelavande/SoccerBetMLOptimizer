"""https://github.com/luukhopman/football-logos.git"""
import os
import shutil
import unicodedata


# Répertoire source et destination
LOGO_BASE_PATH = "logos/teams"
DEST_PATH = "logos/teams"

# Création du dossier destination s'il n'existe pas
os.makedirs(DEST_PATH, exist_ok=True)

# Nom canonique à partir du nom du fichier (sans .png)
FBREF_TO_CANONICAL = {
    # Premier League (England)
    "AFC Bournemouth": "Bournemouth",
    "Arsenal FC": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Brentford FC": "Brentford",
    "Brighton & Hove Albion": "Brighton",
    "Burnley FC": "Burnley",
    "Chelsea FC": "Chelsea",
    "Crystal Palace": "Crystal Palace",
    "Everton FC": "Everton",
    "Fulham FC": "Fulham",
    "Leeds United": "Leeds United",
    "Liverpool FC": "Liverpool",
    "Manchester City": "Manchester City",
    "Manchester United": "Manchester United",
    "Newcastle United": "Newcastle United",
    "Nottingham Forest": "Nottingham Forest",
    "Sunderland AFC": "Sunderland",
    "Tottenham Hotspur": "Tottenham Hotspur",
    "West Ham United": "West Ham United",
    "Wolverhampton Wanderers": "Wolverhampton Wanderers",

    # Ligue 1 (France)
    "AJ Auxerre": "Auxerre",
    "Angers SCO": "Angers",
    "AS Monaco": "Monaco",
    "FC Lorient": "Lorient",
    "FC Metz": "Metz",
    "FC Nantes": "Nantes",
    "FC Toulouse": "Toulouse",
    "Le Havre AC": "Le Havre",
    "LOSC Lille": "Lille",
    "Olympique Lyon": "Lyon",
    "Olympique Marseille": "Marseille",
    "OGC Nice": "Nice",
    "Paris FC": "Paris FC",
    "Paris Saint-Germain": "Paris Saint-Germain",
    "RC Lens": "Lens",
    "RC Strasbourg Alsace": "Strasbourg",
    "Stade Brestois 29": "Brest",
    "Stade Rennais FC": "Rennes",

    # Bundesliga (Germany)
    "1.FC Heidenheim 1846": "Heidenheim",
    "1.FSV Mainz 05": "Mainz 05",
    "1.FC Köln": "Köln",
    "1.FC Union Berlin": "Union Berlin",
    "Bayer 04 Leverkusen": "Bayer Leverkusen",
    "Bayern Munich": "Bayern Munich",
    "Borussia Dortmund": "Borussia Dortmund",
    "Borussia Mönchengladbach": "Borussia Mönchengladbach",
    "Eintracht Frankfurt": "Eintracht Frankfurt",
    "FC Augsburg": "Augsburg",
    "FC St. Pauli": "St. Pauli",
    "Hamburger SV": "Hamburger SV",
    "RB Leipzig": "RB Leipzig",
    "SC Freiburg": "Freiburg",
    "SV Werder Bremen": "Werder Bremen",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    "VfB Stuttgart": "Stuttgart",
    "VfL Wolfsburg": "Wolfsburg",

    # Serie A (Italy)
    "AC Milan": "AC Milan",
    "ACF Fiorentina": "Fiorentina",
    "AS Roma": "Roma",
    "Atalanta BC": "Atalanta",
    "Bologna FC 1909": "Bologna",
    "Cagliari Calcio": "Cagliari",
    "Como 1907": "Como",
    "Frosinone": "Frosinone",
    "Genoa CFC": "Genoa",
    "Hellas Verona": "Hellas Verona",
    "Inter Milan": "Inter Milan",
    "Juventus FC": "Juventus",
    "Parma Calcio 1913": "Parma",
    "Pisa Sporting Club": "Pisa",
    "SS Lazio": "Lazio",
    "SSC Napoli": "Napoli",
    "Torino FC": "Torino",
    "Udinese Calcio": "Udinese",
    "US Cremonese": "Cremonese",
    "US Lecce": "Lecce",
    "US Sassuolo": "Sassuolo",

    # LaLiga (Spain)
    "Athletic Bilbao": "Athletic Club",
    "Atlético de Madrid": "Atlético Madrid",
    "CA Osasuna": "Osasuna",
    "Celta de Vigo": "Celta Vigo",
    "Deportivo Alavés": "Alavés",
    "Elche CF": "Elche",
    "FC Barcelona": "Barcelona",
    "Getafe CF": "Getafe",
    "Girona FC": "Girona",
    "Levante UD": "Levante",
    "Rayo Vallecano": "Rayo Vallecano",
    "RCD Espanyol Barcelona": "Espanyol",
    "RCD Mallorca": "Mallorca",
    "Real Betis Balompié": "Real Betis",
    "Real Madrid": "Real Madrid",
    "Real Oviedo": "Oviedo",
    "Real Sociedad": "Real Sociedad",
    "Sevilla FC": "Sevilla",
    "Valencia CF": "Valencia",
    "Villarreal CF": "Villarreal"
}


# Utilitaire pour normaliser les noms (accents, espaces, etc.)
def normalize_filename(name):
    return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')

# Boucle sur les ligues
for league_dir in os.listdir(LOGO_BASE_PATH):
    league_path = os.path.join(LOGO_BASE_PATH, league_dir)
    if not os.path.isdir(league_path):
        continue

    for filename in os.listdir(league_path):
        if not filename.endswith(".png"):
            continue

        base_name = filename.replace(".png", "")
        canonical = FBREF_TO_CANONICAL.get(base_name)

        if canonical:
            src_path = os.path.join(league_path, filename)
            normalized_name = normalize_filename(canonical.replace(" ", "_")) + ".png"
            dest_path = os.path.join(DEST_PATH, normalized_name)

            shutil.copyfile(src_path, dest_path)
            print(f"✔️ {base_name} → {canonical} → {normalized_name}")
        else:
            print(f"⚠️ Skipped: {base_name} (not in canonical mapping)")
