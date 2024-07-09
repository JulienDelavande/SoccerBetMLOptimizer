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
    sofifa = sd.SoFIFA(versions="all", no_cache=True)
    team_ratings_nat = sofifa.read_team_ratings_nationals()

    # Convertir les types de données
    team_ratings_nat.reset_index(inplace=True)
    team_ratings_nat["league"] = "INT"
    team_ratings_nat.loc[team_ratings_nat["update"] == "World Cup 2022", "update"] = "Nov 20, 2022"
    team_ratings_nat['update'] = team_ratings_nat['update'].apply(lambda x: pd.to_datetime(x))
    team_ratings_nat["overall"] = team_ratings_nat["overall"].astype(int)
    team_ratings_nat["attack"] = team_ratings_nat["attack"].astype(int)
    team_ratings_nat["midfield"] = team_ratings_nat["midfield"].astype(int)
    team_ratings_nat["defence"] = team_ratings_nat["defence"].astype(int)
    team_ratings_nat["transfer_budget"] = team_ratings_nat["transfer_budget"].str.replace("€", "").str.replace("M", "0000").str.replace("K", "000").str.replace(".", "").astype(int)
    team_ratings_nat["club_worth"] = team_ratings_nat["club_worth"].apply(lambda x: str(x).replace("€", "").replace("M", "0000").replace("K", "000").replace("B", "000000000").replace(".", "")).astype(float)
    team_ratings_nat["defence_domestic_prestige"] = team_ratings_nat["defence_domestic_prestige"].astype(int)
    team_ratings_nat["international_prestige"] = team_ratings_nat["international_prestige"].astype(int)
    team_ratings_nat["players"] = team_ratings_nat["players"].astype(int)
    team_ratings_nat["starting_xi_average_age"] = team_ratings_nat["starting_xi_average_age"].astype(float)
    team_ratings_nat["whole_team_average_age"] = team_ratings_nat["whole_team_average_age"].astype(float)
    team_ratings_nat.sort_values('update', ascending=False)


    with engine.connect() as conn:
        # Charger les données existantes
        existing_data = pd.read_sql(f'SELECT * FROM {DB_TN_SOFIFA_TEAMS_STATS}', conn)

        # Fusionner les nouvelles données avec les données existantes
        merged_data = pd.concat([existing_data, team_ratings_nat], ignore_index=True)
        merged_data = merged_data.drop_duplicates(subset=['team', 'update'], keep='last')

        # Supprimer les anciennes données
        conn.execute(text(f"DELETE FROM {DB_TN_SOFIFA_TEAMS_STATS}"))

        # Insérer les données fusionnées
        merged_data.to_sql(DB_TN_SOFIFA_TEAMS_STATS, conn, if_exists='append', index=False)
        conn.commit()

if __name__ == "__main__":
    init_db()
