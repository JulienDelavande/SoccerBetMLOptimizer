import soccerdata as sd
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
import os

def init_db():
    load_dotenv()
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')

    DB_TN_MATCHES_WC = os.getenv('DB_TN_MATCHES_WC')

    connection_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(connection_url)

    leagues = ["INT-World Cup"]
    seasons = [f"{str(year)}-{str(year+1)[2:]}" for year in range(1930, 2024, 4)]
    [seasons.remove(f"{str(year)}-{str(year+1)[2:]}") for year in range(1942, 1948, 4)]

    fbref = sd.FBref(leagues=leagues, seasons=seasons)
    matches_wc = fbref.read_schedule(force_cache=True)

    matches_wc['date'] = pd.to_datetime(matches_wc['date'])
    matches_wc['time'] = pd.to_datetime(matches_wc['time']).dt.time

    import hashlib

    # Créer un nouvel index basé sur le hachage de la colonne 'game'
    matches_wc.reset_index(inplace=True)
    matches_wc['index'] = matches_wc['game'].apply(lambda x: int(hashlib.sha256(x.encode()).hexdigest()[:6], 16))
    matches_wc['home_g'] = matches_wc['score'].apply(lambda x: x.split('–')[0][-1] if not pd.isna(x) else x)
    matches_wc['away_g'] = matches_wc['score'].apply(lambda x: x.split('–')[1][0] if not pd.isna(x) else x)
    matches_wc['home_sat'] = matches_wc['score'].apply(lambda x: x.split('–')[0].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
    matches_wc['away_sat'] = matches_wc['score'].apply(lambda x: x.split('–')[1].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
    # int for goals
    matches_wc['home_g'] = pd.to_numeric(matches_wc['home_g'], errors='coerce')
    matches_wc['away_g'] = pd.to_numeric(matches_wc['away_g'], errors='coerce')
    # int for sag
    matches_wc['home_sat'] = pd.to_numeric(matches_wc['home_sat'], errors='coerce')
    matches_wc['away_sat'] = pd.to_numeric(matches_wc['away_sat'], errors='coerce')

    # Définir le nouvel index
    #euro_schedule.set_index('index', inplace=True)

    with engine.connect() as conn:
        # Charger les données existantes
        existing_data = pd.read_sql(f'SELECT * FROM {DB_TN_MATCHES_WC}', conn)

        # Fusionner les nouvelles données avec les données existantes
        merged_data = pd.concat([existing_data, matches_wc], ignore_index=True)
        merged_data = merged_data.drop_duplicates(subset=['index'], keep='last')

        # Supprimer les anciennes données
        conn.execute(text(f"DELETE FROM {DB_TN_MATCHES_WC}"))

        # Insérer les données fusionnées
        merged_data.to_sql(DB_TN_MATCHES_WC, conn, if_exists='append', index=False)
        conn.commit()

if __name__ == "__main__":
    init_db()
