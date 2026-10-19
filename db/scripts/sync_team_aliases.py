"""Upsert teams and aliases from the JSON mappings without deleting anything.

Unlike load_team_aliases.py (full delete + reload, which renumbers team_ids),
this is safe to run on a live database: new canonical names are inserted, and
an alias whose canonical changed is re-pointed.

Usage: DATABASE_URL=postgresql+psycopg2://... python sync_team_aliases.py
"""
import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text

HERE = Path(__file__).parent
SOURCES = {"fbref": "teams_fbref_to_canonical.json", "sofifa": "teams_sofifa_to_canonical.json",
           "theoddsapi": "teams_theoddsapi_to_canonical.json"}


def main():
    engine = create_engine(os.environ["DATABASE_URL"])
    created = changed = 0
    with engine.begin() as conn:
        for source, filename in SOURCES.items():
            mapping = json.loads((HERE / filename).read_text())
            for raw_name, canonical in mapping.items():
                team_id = conn.execute(text(
                    "INSERT INTO teams (canonical_name) VALUES (:c) ON CONFLICT (canonical_name) DO UPDATE "
                    "SET canonical_name = EXCLUDED.canonical_name RETURNING team_id"), {"c": canonical.strip()}).scalar_one()
                res = conn.execute(text(
                    "INSERT INTO team_alias (source, raw_name, team_id) VALUES (:s, :r, :t) "
                    "ON CONFLICT (source, raw_name) DO UPDATE SET team_id = EXCLUDED.team_id "
                    "WHERE team_alias.team_id <> EXCLUDED.team_id RETURNING (xmax = 0) AS inserted"),
                    {"s": source, "r": raw_name, "t": team_id}).first()
                if res is not None:
                    created += bool(res.inserted)
                    changed += not res.inserted
    print(f"aliases created: {created}, re-pointed: {changed}")


if __name__ == "__main__":
    main()
