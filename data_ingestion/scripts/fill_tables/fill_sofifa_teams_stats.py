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

    DB_TN_SOFIFA_TEAMS_STATS = os.getenv('DB_TN_SOFIFA_TEAMS_STATS')

    connection_url = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(connection_url)

    # Charger les données
    sofifa = sd.SoFIFA(versions="all", no_cache=False)
    team_ratings = sofifa.read_team_ratings()

    # Convertir les types de données
    team_ratings.reset_index(inplace=True)
    team_ratings['update'] = team_ratings['update'].apply(lambda x: pd.to_datetime(x))
    team_ratings["overall"] = team_ratings["overall"].astype(int)
    team_ratings["attack"] = team_ratings["attack"].astype(int)
    team_ratings["midfield"] = team_ratings["midfield"].astype(int)
    team_ratings["defence"] = team_ratings["defence"].astype(int)
    team_ratings["transfer_budget"] = team_ratings["transfer_budget"].str.replace("€", "").str.replace("M", "0000").str.replace("K", "000").str.replace(".", "").astype(int)
    team_ratings["club_worth"] = team_ratings["club_worth"].str.replace("€", "").str.replace("M", "0000").str.replace("K", "000").str.replace("B", "000000000").str.replace(".", "").astype(float)
    team_ratings["defence_domestic_prestige"] = team_ratings["defence_domestic_prestige"].astype(int)
    team_ratings["international_prestige"] = team_ratings["international_prestige"].astype(int)
    team_ratings["players"] = team_ratings["players"].astype(int)
    team_ratings["starting_xi_average_age"] = team_ratings["starting_xi_average_age"].astype(float)
    team_ratings["whole_team_average_age"] = team_ratings["whole_team_average_age"].astype(float)
    team_ratings.sort_values('update', ascending=False)


    with engine.connect() as conn:
        # Charger les données existantes
        existing_data = pd.read_sql(f'SELECT * FROM {DB_TN_SOFIFA_TEAMS_STATS}', conn)

        # Fusionner les nouvelles données avec les données existantes
        merged_data = pd.concat([existing_data, team_ratings], ignore_index=True)
        merged_data = merged_data.drop_duplicates(subset=['team', 'update'], keep='last')

        # Supprimer les anciennes données
        conn.execute(text(f"DELETE FROM {DB_TN_SOFIFA_TEAMS_STATS}"))

        # Insérer les données fusionnées
        merged_data.to_sql(DB_TN_SOFIFA_TEAMS_STATS, conn, if_exists='append', index=False)
        conn.commit()

if __name__ == "__main__":
    init_db()
