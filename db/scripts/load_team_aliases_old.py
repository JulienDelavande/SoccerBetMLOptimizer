# scripts/load_team_aliases.py
from __future__ import annotations
import os
from typing import Dict, Mapping
from sqlalchemy import create_engine, text

DB_URL = f"{os.environ['DB_TYPE']}+{os.environ['DB_PILOT']}://" \
         f"{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@" \
         f"{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/" \
         f"{os.environ['DB_NAME']}"
engine = create_engine(DB_URL, future=True)

SOFIFA_TO_FBREF: Dict[str, str] = {
    "VfL Bochum 1848": "Bochum",
    "Tottenham Hotspur": "Tottenham",
    "Paris Saint-Germain": "Paris S-G",
    "FC Köln": "Köln",
    "Real Zaragoza": "Zaragoza",
    "Wolverhampton Wanderers": "Wolves",
    "Sheffield United": "Sheffield Utd",
    "Amiens SC": "Amiens",
    "FSV Mainz 05": "Mainz 05",
    "Paderborn": "Paderborn 07",
    "Bolton Wanderers": "Bolton",
    "Huddersfield Town": "Huddersfield",
    "Olympique de Marseille": "Marseille",
    "LOSC Lille": "Lille",
    "Grenoble Foot 38": "Grenoble",
    "Racing Santander": "Racing Sant",
    "Eintracht Frankfurt": "Eint Frankfurt",
    "Fortuna Düsseldorf": "Düsseldorf",
    "Queens Park Rangers": "QPR",
    "SC Freiburg": "Freiburg",
    "DSC Arminia Bielefeld": "Arminia",
    "Republic of Ireland": "Rep. of Ireland",
    "Evian TG": "Evian",
    "FC Barcelona": "Barcelona",
    "Brighton & Hove Albion": "Brighton",
    "Deportivo La Coruña": "La Coruña",
    "Angers SCO": "Angers",
    "West Ham United": "West Ham",
    "VfL Wolfsburg": "Wolfsburg",
    "FC Augsburg": "Augsburg",
    "India": "India",
    "Bari 1908": "Bari",
    "Czech Republic": "Czechia",
    "Nottingham Forest": "Nott'ham Forest",
    "Newcastle United": "Newcastle Utd",
    "Borussia Dortmund": "Dortmund",
    "AFC Bournemouth": "Bournemouth",
    "Iran": "IR Iran",
    "Borussia Mönchengladbach": "Gladbach",
    "Olympique Lyonnais": "Lyon",
    "Venezuela": "Venezuela",
    "TSG Hoffenheim": "Hoffenheim",
    "SD Eibar": "Eibar",
    "West Bromwich Albion": "West Brom",
    "VfB Stuttgart": "Stuttgart",
    "Arles": "Arles-Avignon",
    "Stade de Reims": "Reims",
    "Stade Brestois 29": "Brest",
    "Real Valladolid": "Valladolid",
    "Clermont": "Clermont Foot",
    "FC Union Berlin": "Union Berlin",
    "Manchester United": "Manchester Utd",
    "Deportivo Alavés": "Alavés",
    "Celta de Vigo": "Celta Vigo",
    "Bayer 04 Leverkusen": "Leverkusen",
    "FC Bayern München": "Bayern Munich",
    "SpVgg Greuther Fürth": "Greuther Fürth",
    "Ingolstadt": "Ingolstadt 04",
    "Eintracht Braunschweig": "Braunschweig",
    "Blackburn Rovers": "Blackburn",
    "Stade de Reims ": "Reims",
}

THEODDSAPI_TO_FBREF: Dict[str, str] = {
    '1. FC Heidenheim': 'Heidenheim',
    'AC Milan': 'Milan',
    'AS Monaco': 'Monaco',
    'AS Roma': 'Roma',
    'Atalanta BC': 'Atalanta',
    'Athletic Bilbao': 'Athletic Club',
    'Bayer Leverkusen': 'Leverkusen',
    'Borussia Dortmund': 'Dortmund',
    'Borussia Monchengladbach': 'Gladbach',
    'Brighton and Hove Albion': 'Brighton',
    'CA Osasuna': 'Osasuna',
    'Eintracht Frankfurt': 'Eint Frankfurt',
    'FC St. Pauli': 'St. Pauli',
    'FSV Mainz 05': 'Mainz 05',
    'Inter Milan': 'Inter',
    'Manchester United': 'Manchester Utd',
    'Newcastle United': 'Newcastle Utd',
    'Nottingham Forest': "Nott'ham Forest",
    'Paris Saint Germain': 'Paris S-G',
    'RC Lens': 'Lens',
    'SC Freiburg': 'Freiburg',
    'Saint Etienne': 'Saint-Étienne',
    'TSG Hoffenheim': 'Hoffenheim',
    'Tottenham Hotspur': 'Tottenham',
    'VfB Stuttgart': 'Stuttgart',
    'VfL Bochum': 'Bochum',
    'VfL Wolfsburg': 'Wolfsburg',
    'West Ham United': 'West Ham',
    'Wolverhampton Wanderers': 'Wolves'
}

SOURCES: Mapping[str, Dict[str, str]] = {
    "sofifa": SOFIFA_TO_FBREF,
    "theoddsapi": THEODDSAPI_TO_FBREF,
    # Add more sources as needed
}

UPSERT_TEAM = text("""
    INSERT INTO teams (canonical_name)
    VALUES (:canonical_name)
    ON CONFLICT (canonical_name) DO NOTHING
    RETURNING team_id;
""")

GET_TEAM_ID = text("""
    SELECT team_id FROM teams WHERE canonical_name = :canonical_name;
""")

UPSERT_ALIAS = text("""
    INSERT INTO team_alias (source, raw_name, team_id)
    VALUES (:source, :raw_name, :team_id)
    ON CONFLICT (source, raw_name) DO UPDATE
      SET team_id = EXCLUDED.team_id
    ;
""")

def ensure_team(conn, canonical_name: str) -> int:
    canonical_name = canonical_name.strip()
    res = conn.execute(UPSERT_TEAM, {"canonical_name": canonical_name}).first()
    if res is not None:
        return res[0]
    return conn.execute(GET_TEAM_ID, {"canonical_name": canonical_name}).scalar_one()

def main():
    fbref_names = set()
    for mapping in SOURCES.values():
        fbref_names.update(v.strip() for v in mapping.values())

    with engine.begin() as conn:
        name_to_id = {}
        for fb in sorted(fbref_names):
            team_id = ensure_team(conn, fb)
            name_to_id[fb] = team_id

        for fb, team_id in name_to_id.items():
            conn.execute(UPSERT_ALIAS, {"source": "fbref", "raw_name": fb, "team_id": team_id})

        for source, mapping in SOURCES.items():
            for raw_name, fbref_name in mapping.items():
                raw = raw_name.strip()
                fb = fbref_name.strip()
                team_id = name_to_id[fb]
                conn.execute(UPSERT_ALIAS, {"source": source, "raw_name": raw, "team_id": team_id})

    print("OK: teams / team_alias upserted for sources:", ", ".join(SOURCES.keys()))

if __name__ == "__main__":
    main()
