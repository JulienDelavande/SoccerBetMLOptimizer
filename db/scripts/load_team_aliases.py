# scripts/load_team_aliases.py
from __future__ import annotations
import os
import json
from typing import Dict, Mapping
from sqlalchemy import create_engine, text

DB_URL = f"{os.environ['DB_TYPE']}+{os.environ['DB_PILOT']}://" \
         f"{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@" \
         f"{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/" \
         f"{os.environ['DB_NAME']}"
engine = create_engine(DB_URL, future=True)

with open("scripts/teams_fbref_to_canonical.json") as f:
    FBREF_TO_CANONICAL: Dict[str, str] = json.load(f)

with open("scripts/teams_sofifa_to_canonical.json") as f:
    SOFIFA_TO_CANONICAL: Dict[str, str] = json.load(f)

with open("scripts/teams_theoddsapi_to_canonical.json") as f:
    THEODDSAPI_TO_CANONICAL: Dict[str, str] = json.load(f)

SOURCES: Mapping[str, Dict[str, str]] = {
    "fbref": FBREF_TO_CANONICAL,
    "sofifa": SOFIFA_TO_CANONICAL,
    "theoddsapi": THEODDSAPI_TO_CANONICAL,
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

DELETE_ALIAS = text("DELETE FROM team_alias;")
DELETE_TEAMS = text("DELETE FROM teams;")

def ensure_team(conn, canonical_name: str) -> int:
    canonical_name = canonical_name.strip()
    res = conn.execute(UPSERT_TEAM, {"canonical_name": canonical_name}).first()
    if res is not None:
        return res[0]
    return conn.execute(GET_TEAM_ID, {"canonical_name": canonical_name}).scalar_one()

def main():
    canonical_names = set()
    for mapping in SOURCES.values():
        canonical_names.update(v.strip() for v in mapping.values())

    with engine.begin() as conn:
        conn.execute(DELETE_ALIAS)
        conn.execute(DELETE_TEAMS)

        name_to_id = {}
        for canonical in sorted(canonical_names):
            team_id = ensure_team(conn, canonical)
            name_to_id[canonical] = team_id

        for source, mapping in SOURCES.items():
            for raw_name, canonical in mapping.items():
                raw = raw_name.strip()
                canonical = canonical.strip()
                team_id = name_to_id[canonical]
                conn.execute(UPSERT_ALIAS, {"source": source, "raw_name": raw, "team_id": team_id})

    print("✅ Done: tables cleared and reloaded for", ", ".join(SOURCES.keys()))

if __name__ == "__main__":
    main()
