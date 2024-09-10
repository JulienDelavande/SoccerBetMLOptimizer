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

    DB_TN_MATCHES_BIG5 = os.getenv('DB_TN_MATCHES_BIG5')

    connection_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(connection_url)

    leagues = ["Big 5 European Leagues Combined"]
    seasons = [f"{str(year)[2:]}-{str(year+1)[2:]}" for year in range(1930, 2025)]
    [seasons.remove(f"{str(year)[2:]}-{str(year+1)[2:]}") for year in range(1939, 1946)]

    fbref = sd.FBref(leagues=leagues, seasons=seasons)
    big5 = fbref.read_schedule(force_cache=True)

    big5['date'] = pd.to_datetime(big5['date'])
    big5['time'] = pd.to_datetime(big5['time']).dt.time

    import hashlib

    # Créer un nouvel index basé sur le hachage de la colonne 'game'
    big5.reset_index(inplace=True)
    big5['index'] = big5['game'].apply(lambda x: int(hashlib.sha256(x.encode()).hexdigest()[:6], 16))
    big5['home_g'] = big5['score'].apply(lambda x: x.split('–')[0][-1] if not pd.isna(x) else x)
    big5['away_g'] = big5['score'].apply(lambda x: x.split('–')[1][0] if not pd.isna(x) else x)
    big5['home_sat'] = big5['score'].apply(lambda x: x.split('–')[0].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
    big5['away_sat'] = big5['score'].apply(lambda x: x.split('–')[1].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
    # int for goals
    big5['home_g'] = pd.to_numeric(big5['home_g'], errors='coerce')
    big5['away_g'] = pd.to_numeric(big5['away_g'], errors='coerce')
    # int for sag
    big5['home_sat'] = pd.to_numeric(big5['home_sat'], errors='coerce')
    big5['away_sat'] = pd.to_numeric(big5['away_sat'], errors='coerce')

    # Définir le nouvel index
    #euro_schedule.set_index('index', inplace=True)

    with engine.connect() as conn:
        # Charger les données existantes
        existing_data = pd.read_sql(f'SELECT * FROM {DB_TN_MATCHES_BIG5}', conn)

        # Fusionner les nouvelles données avec les données existantes
        merged_data = pd.concat([existing_data, big5], ignore_index=True)
        merged_data = merged_data.drop_duplicates(subset=['index'], keep='last')

        # Supprimer les anciennes données
        conn.execute(text(f"DELETE FROM {DB_TN_MATCHES_BIG5}"))

        # Insérer les données fusionnées
        merged_data.to_sql(DB_TN_MATCHES_BIG5, conn, if_exists='append', index=False)
        conn.commit()

if __name__ == "__main__":
    init_db()
