
import logging
import time
import json
import datetime

import pandas as pd
from sqlalchemy import text

from app._config import DB_TN_MODELS_RESULTS, DB_TN_ODDS, DB_TN_OPTIM_RESULTS
from app._config import engine

from optim.functions.player_utility_kelly_criteria import player_utility_kelly_criteria
from optim.resolve.resolve_fik import resolve_fik


logger = logging.getLogger("OF")

query_models_results = f"SELECT * FROM {DB_TN_MODELS_RESULTS} WHERE date_match >= :date_match AND model = :model"
query_odds = f"SELECT * FROM {DB_TN_ODDS} WHERE commence_time >= :commence_time"

mapping_dict = {
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


def find__of(datetime_first_match: datetime.datetime = None, model: str = 'RSF_PR_LR') -> None:

    # Retrieve data from the database
    start_data_retrieval = time.time()
    try:
        datetime_first_match = datetime_first_match if datetime_first_match else datetime.datetime.now()
        with engine.connect() as connection:
            df_models_results = pd.read_sql(text(query_models_results), connection, params={"date_match": datetime_first_match, "model": model})
            df_odds = pd.read_sql(text(query_odds), connection, params={"commence_time": datetime_first_match})
            logger.info(f"Data retrieved in {time.time() - start_data_retrieval:.2f} seconds")
    except Exception as e:
        logger.error(f"Error while retrieving data from the database: {e}")
        return None
    
    # Process the data
    start_processing = time.time()
    try:
        # Filter the odds data to keep only the last odds for each outcome
        df_odds__last_odds = df_odds.sort_values(by=['commence_time', 'match_id', 'bookmaker_key', 'bookmaker_last_update'], ascending=False)
        df_odds__last_odds = df_odds__last_odds.drop_duplicates(subset=['match_id', 'bookmaker_key', 'outcome_name'], keep='first')

        # Put on the same line the odds for each outcome for each match and each bookmaker
        df_odds__last_odds__home = df_odds__last_odds[df_odds__last_odds['outcome_name'] == df_odds__last_odds['home_team']]
        df_odds__last_odds__away = df_odds__last_odds[df_odds__last_odds['outcome_name'] == df_odds__last_odds['away_team']]
        df_odds__last_odds__draw = df_odds__last_odds[df_odds__last_odds['outcome_name'] == 'Draw']
        df_odds__last_odds__home = df_odds__last_odds__home.rename(columns={'outcome_price': 'odds_home'})
        df_odds__last_odds__away = df_odds__last_odds__away.rename(columns={'outcome_price': 'odds_away'})
        df_odds__last_odds__draw = df_odds__last_odds__draw.rename(columns={'outcome_price': 'odds_draw'})
        df_odds__last_odds__draw = df_odds__last_odds__draw[['match_id', 'bookmaker_key', 'odds_draw']]
        df_odds__last_odds__away = df_odds__last_odds__away[['match_id', 'bookmaker_key', 'odds_away']]
        df_odds__last_odds__home_draw = pd.merge(df_odds__last_odds__home, df_odds__last_odds__draw, on=['match_id', 'bookmaker_key'], how='inner')
        df_odds__last_odds__home_draw_away = pd.merge(df_odds__last_odds__home_draw, df_odds__last_odds__away, on=['match_id', 'bookmaker_key'], how='inner')

        # Keep only the highest odds for each outcome
        max_odds_df = df_odds__last_odds__home_draw_away.groupby('match_id').agg({
            'odds_home': 'max',
            'odds_draw': 'max',
            'odds_away': 'max'
        }).reset_index()
        max_odds_df['bookmaker_home'] = max_odds_df.apply(lambda x: df_odds__last_odds__home_draw_away[(df_odds__last_odds__home_draw_away['match_id'] == x['match_id']) & (df_odds__last_odds__home_draw_away['odds_home'] == x['odds_home'])]['bookmaker_title'].values[0], axis=1)
        max_odds_df['bookmaker_draw'] = max_odds_df.apply(lambda x: df_odds__last_odds__home_draw_away[(df_odds__last_odds__home_draw_away['match_id'] == x['match_id']) & (df_odds__last_odds__home_draw_away['odds_draw'] == x['odds_draw'])]['bookmaker_title'].values[0], axis=1)
        max_odds_df['bookmaker_away'] = max_odds_df.apply(lambda x: df_odds__last_odds__home_draw_away[(df_odds__last_odds__home_draw_away['match_id'] == x['match_id']) & (df_odds__last_odds__home_draw_away['odds_away'] == x['odds_away'])]['bookmaker_title'].values[0], axis=1)
        df_odds__last_odds__home_draw_away__no_bookie_col = df_odds__last_odds__home_draw_away.drop(columns=['bookmaker_title', 'bookmaker_key', 'bookmaker_last_update', 'market_key', 'market_last_update', 'outcome_name', 'odds_home', 'odds_draw', 'odds_away'])
        max_odds_df_all = max_odds_df.merge(df_odds__last_odds__home_draw_away__no_bookie_col, on='match_id', how='outer')
        max_odds_df_all = max_odds_df_all.drop_duplicates(subset=['match_id'], keep='first')

        # Keep only the odds for the big 5 leagues
        sports = ['soccer_france_ligue_one', 'soccer_spain_la_liga', 'soccer_italy_serie_a', 'soccer_germany_bundesliga', 'soccer_epl']
        max_odds_df_all_big5 = max_odds_df_all[max_odds_df_all['sport_key'].isin(sports)]
        max_odds_df_all_mapped = max_odds_df_all_big5.replace({'home_team': mapping_dict, 'away_team': mapping_dict})

        # Keep only the last inferred results for each game
        df_models_results_last_infered = df_models_results.sort_values(by=['datetime_inference'], ascending=False).drop_duplicates(subset=['game'], keep='first')
        max_odds_df_all_mapped['date_match'] = max_odds_df_all_mapped['commence_time'].dt.date

        # Merge the models results with the odds
        df_models_results_joined = df_models_results_last_infered.merge(max_odds_df_all_mapped, left_on=['home_team', 'away_team', 'date_match'], right_on=['home_team', 'away_team', 'date_match'], how='inner')

        # Compute the numpy arrays of odds (o) and probabilities (r)
        o = df_models_results_joined[['odds_home', 'odds_draw', 'odds_away']].to_numpy()
        r = df_models_results_joined[['prob_home_win', 'prob_draw', 'prob_away_win']].to_numpy()

        logger.info(f"Data processed in {time.time() - start_processing:.2f} seconds")

    except Exception as e:
        logger.error(f"Error while processing the data: {e}")
        return None
    

    # Compute bankroll fraction to invest
    start_invest = time.time()
    try:
        # Kelly
        result_kelly = resolve_fik(o, r, player_utility_kelly_criteria)
        result_kelly[result_kelly < 1e-10] = 0
        df_models_results_joined[['f_home_kelly', 'f_draw_kelly', 'f_away_kelly']] = result_kelly
        df_models_results_joined['datetime_optim'] = datetime.datetime.now()
        logger.info(f"Kelly computed in {time.time() - start_invest:.2f} seconds")
    except Exception as e:
        logger.error(f"Error while computing the bankroll fraction to invest: {e}")
        return None
    

    # Export to db
    start_export = time.time()
    try:
        with engine.begin() as conn:
            df_models_results_joined_cols = df_models_results_joined[[
                'match_id', 'sport_key', 'game', 'date_match', 'time_match', 'home_team', 'away_team', 
                'model','datetime_inference', 'prob_home_win', 'prob_draw', 'prob_away_win',
                'odds_home', 'odds_draw', 'odds_away', 
                'bookmaker_home', 'bookmaker_draw', 'bookmaker_away', 'f_home_kelly', 'f_draw_kelly', 'f_away_kelly', 'datetime_optim']]
            df_models_results_joined_cols.to_sql(DB_TN_OPTIM_RESULTS, conn, if_exists='append', index=False)
        logger.info(f"Data exported in {time.time() - start_export:.2f} seconds")
    except Exception as e:
        logger.error(f"Error while exporting the data: {e}")
        return None
    

if __name__ == '__main__':
    logging.info("-- Starting the OF pipeline --")
    datetime_first_match = '2024-08-26 00:00:00'
    model =  'RSF_PR_LR'
    find__of(datetime_first_match=datetime_first_match, model=model)
    logging.info("-- Pipeline completed --")
    print("Pipeline completed")
