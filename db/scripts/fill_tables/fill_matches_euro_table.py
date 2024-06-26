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

    connection_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(connection_url)

    leagues = ['INT-European Championships']
    seasons = [2000, 2004, 2008, 2012, 2016, 2020, 2024]

    fbref = sd.FBref(leagues=leagues, seasons=seasons)
    euro_schedule = fbref.read_schedule()

    euro_schedule['date'] = pd.to_datetime(euro_schedule['date'])
    euro_schedule['time'] = pd.to_datetime(euro_schedule['time']).dt.time

    import hashlib

    # Créer un nouvel index basé sur le hachage de la colonne 'game'
    euro_schedule.reset_index(inplace=True)
    euro_schedule['index'] = euro_schedule['game'].apply(lambda x: int(hashlib.sha256(x.encode()).hexdigest()[:6], 16))
    euro_schedule['home_g'] = euro_schedule['score'].apply(lambda x: x.split('–')[0][-1] if not pd.isna(x) else x)
    euro_schedule['away_g'] = euro_schedule['score'].apply(lambda x: x.split('–')[1][0] if not pd.isna(x) else x)
    euro_schedule['home_sat'] = euro_schedule['score'].apply(lambda x: x.split('–')[0].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
    euro_schedule['away_sat'] = euro_schedule['score'].apply(lambda x: x.split('–')[1].split('(')[1][0] if not pd.isna(x) and '(' in x else pd.NA)
    # int for goals
    euro_schedule['home_g'] = pd.to_numeric(euro_schedule['home_g'], errors='coerce')
    euro_schedule['away_g'] = pd.to_numeric(euro_schedule['away_g'], errors='coerce')
    # int for sag
    euro_schedule['home_sat'] = pd.to_numeric(euro_schedule['home_sat'], errors='coerce')
    euro_schedule['away_sat'] = pd.to_numeric(euro_schedule['away_sat'], errors='coerce')

    # Définir le nouvel index
    #euro_schedule.set_index('index', inplace=True)

    with engine.connect() as conn:
        # Charger les données existantes
        existing_data = pd.read_sql('SELECT * FROM matches_euro', conn)

        # Fusionner les nouvelles données avec les données existantes
        merged_data = pd.concat([existing_data, euro_schedule], ignore_index=True)
        merged_data = merged_data.drop_duplicates(subset=['index'], keep='last')

        # Supprimer les anciennes données
        conn.execute(text("DELETE FROM matches_euro"))

        # Insérer les données fusionnées
        merged_data.to_sql('matches_euro', conn, if_exists='append', index=False)
        conn.commit()

if __name__ == "__main__":
    init_db()
