
import logging
import time
import json
import datetime

import pandas as pd
from sqlalchemy import text

from app._config import DB_TN_MODELS_RESULTS, DB_TN_ODDS, DB_TN_OPTIM_RESULTS
from app._config import engine

from optim.functions.player_utility_kelly_criteria import player_utility_kelly_criteria
from optim.functions.player_expected_utility_log import player_expected_utility_log
from optim.functions.player_expected_utility_exp_ce import player_expected_utility_exp_ce
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


def find__of(datetime_first_match: datetime.datetime = None, model: str = 'RSF_PR_LR', n_matches : int = None, same_day: bool = False,  
             bookmakers : list[str] =  None, bankroll : float = 1, method='SLSQP', 
             utility_fn='Kelly', optim_label='manual', l=10) -> datetime.datetime:

    logging.info(f"--- Starting the OF pipeline")
    # Retrieve data from the database
    start_data_retrieval = time.time()
    try:
        logging.info(f"datetime_first_match: {datetime_first_match}")
        logging.info(f"model: {model}")
        logging.info(f"n_matches: {n_matches}")
        logging.info(f"bookmakers: {bookmakers}")
        logging.info(f"bankroll: {bankroll}")
        logging.info(f"method: {method}")
        datetime_first_match = datetime_first_match if datetime_first_match else datetime.datetime.now()
        date_first_match = datetime_first_match.date()
        time_first_match = datetime_first_match.time()

        logging.info(f"Retrieving data from the database, table {DB_TN_MODELS_RESULTS}")
        with engine.connect() as connection:
            logging.info("Database connection established")
            logging.info(f"DB_HOST: {engine.url.host}")
            logging.info(f"DB_PORT: {engine.url.port}")
            logging.info(f"DB_NAME: {engine.url.database}")

            df_models_results = pd.read_sql(text(query_models_results), connection, params={"date_match": date_first_match, "model": model})
            df_odds = pd.read_sql(text(query_odds), connection, params={"commence_time": datetime_first_match})
            logger.info(f"Data retrieved in {time.time() - start_data_retrieval:.2f} seconds")
    except Exception as e:
        logger.error(f"Error while retrieving data from the database: {e}")
        raise
    
    # Process the data
    start_processing = time.time()
    logging.info(f"Processing the data")
    try:
        # Filter the odds data to keep only the last odds before last_odds_datetime for each outcome
        last_odds_datetime = datetime_first_match
        df_odds__last_odds = df_odds[df_odds['bookmaker_last_update'] <= last_odds_datetime]
        df_odds__last_odds = df_odds.sort_values(by=['commence_time', 'match_id', 'bookmaker_key', 'bookmaker_last_update'], ascending=False)
        df_odds__last_odds = df_odds__last_odds.drop_duplicates(subset=['match_id', 'bookmaker_key', 'outcome_name'], keep='first')

        # Put on the same line the odds for each outcome for each match and each bookmaker
        df_odds__last_odds__home = df_odds__last_odds[df_odds__last_odds['outcome_name'] == df_odds__last_odds['home_team']]
        df_odds__last_odds__away = df_odds__last_odds[df_odds__last_odds['outcome_name'] == df_odds__last_odds['away_team']]
        df_odds__last_odds__draw = df_odds__last_odds[df_odds__last_odds['outcome_name'] == 'Draw']
        df_odds__last_odds__home = df_odds__last_odds__home.rename(columns={'outcome_price': 'odds_home'})
        df_odds__last_odds__away = df_odds__last_odds__away.rename(columns={'outcome_price': 'odds_away'})
        df_odds__last_odds__draw = df_odds__last_odds__draw.rename(columns={'outcome_price': 'odds_draw'})
        df_odds__last_odds__home['odds_home_datetime'] = df_odds__last_odds__home['bookmaker_last_update']
        df_odds__last_odds__draw['odds_draw_datetime'] = df_odds__last_odds__draw['bookmaker_last_update']
        df_odds__last_odds__away['odds_away_datetime'] = df_odds__last_odds__away['bookmaker_last_update']
        df_odds__last_odds__draw = df_odds__last_odds__draw[['match_id', 'bookmaker_key', 'odds_draw', 'odds_draw_datetime']]
        df_odds__last_odds__away = df_odds__last_odds__away[['match_id', 'bookmaker_key', 'odds_away', 'odds_away_datetime']]
        df_odds__last_odds__home_draw = pd.merge(df_odds__last_odds__home, df_odds__last_odds__draw, on=['match_id', 'bookmaker_key'], how='inner')
        df_odds__last_odds__home_draw_away = pd.merge(df_odds__last_odds__home_draw, df_odds__last_odds__away, on=['match_id', 'bookmaker_key'], how='inner')

        # keep only the bookmakers in the list
        if bookmakers:
            df_odds__last_odds__home_draw_away = df_odds__last_odds__home_draw_away[df_odds__last_odds__home_draw_away['bookmaker_key'].isin(bookmakers)]

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

        # Sort by date start
        df_models_results_joined = df_models_results_joined.sort_values(by=['date_match', 'time_match'], ascending=True)

        # Keep only the matches of the same day
        if same_day:
            df_models_results_joined = df_models_results_joined[df_models_results_joined['date_match'] == df_models_results_joined['date_match'].min()]
        
        # Keep only the n_matches first matches
        if n_matches:
            df_models_results_joined = df_models_results_joined.head(n_matches)

        # Compute the numpy arrays of odds (o) and probabilities (r)
        o = df_models_results_joined[['odds_home', 'odds_draw', 'odds_away']].to_numpy()
        r = df_models_results_joined[['prob_home_win', 'prob_draw', 'prob_away_win']].to_numpy()

        logger.info(f"Data processed in {time.time() - start_processing:.2f} seconds")

    except Exception as e:
        logger.error(f"Error while processing the data: {e}")
        raise
    

    # Compute bankroll fraction to invest
    start_invest = time.time()
    logging.info(f"Computing the bankroll fraction to invest")
    try:
        # Kelly
        if utility_fn == 'Kelly':
            obectif_kelly_fn = lambda f, o, r: player_utility_kelly_criteria(f, o, r, bankroll)
            result_kelly = resolve_fik(o, r, obectif_kelly_fn, logger=logger, method=method)
            result_kelly[result_kelly < 1e-10] = 0
            df_models_results_joined[['f_home', 'f_draw', 'f_away']] = result_kelly
            df_models_results_joined['utility_fn'] = utility_fn
            datetime_optim = datetime.datetime.now()
            df_models_results_joined['datetime_optim'] = datetime_optim
            logger.info(f"Kelly computed in {time.time() - start_invest:.2f} seconds")
            
        # Log
        if utility_fn == 'Log':
            obectif_log_fn = lambda  f, o, t : - player_expected_utility_log(f, o, t, B=bankroll)
            result_log = resolve_fik(o, r, obectif_log_fn, logger=logger, method=method)
            result_log[result_log < 1e-10] = 0
            df_models_results_joined[['f_home', 'f_draw', 'f_away']] = result_log
            df_models_results_joined['utility_fn'] = utility_fn
            datetime_optim = datetime.datetime.now()
            df_models_results_joined['datetime_optim'] = datetime_optim
            logger.info(f"Log computed in {time.time() - start_invest:.2f} seconds")
            
        # Exponential
        if utility_fn == 'Exp':
            obectif_exp_fn = lambda  f, o, t : - player_expected_utility_exp_ce(f, o, t, B=B_exp)
            result_exp = resolve_fik(o, r, obectif_exp_fn, logger=logger, method=method)
            result_exp[result_exp < 1e-10] = 0
            df_models_results_joined[['f_home', 'f_draw', 'f_away']] = result_exp
            df_models_results_joined['utility_fn'] = utility_fn
            datetime_optim = datetime.datetime.now()
            df_models_results_joined['datetime_optim'] = datetime_optim
            logger.info(f"Exp computed in {time.time() - start_invest:.2f} seconds")
            
        # Linear
        if utility_fn == 'Linear':
            obectif_linear_fn = lambda  f, o, t : player_utility_linear(f, o, t, B=B_linar, l=l)
            result_linear = resolve_fik(o, r, obectif_linear_fn, logger=logger, method=method)
            result_linear[result_linear < 1e-10] = 0
            df_models_results_joined[['f_home', 'f_draw', 'f_away']] = result_linear
            df_models_results_joined['utility_fn'] = utility_fn
            datetime_optim = datetime.datetime.now()
            df_models_results_joined['datetime_optim'] = datetime_optim
            logger.info(f"Linear computed in {time.time() - start_invest:.2f} seconds")
            
    except Exception as e:
        logger.error(f"Error while computing the bankroll fraction to invest: {e}")
        raise
    

    # Export to db
    start_export = time.time()
    logging.info(f"Exporting the data to db, table {DB_TN_OPTIM_RESULTS}")
    try:
        df_models_results_joined['optim_label'] = optim_label
        with engine.begin() as conn:
            df_models_results_joined_cols = df_models_results_joined[[
                'match_id', 'sport_key', 'game', 'date_match', 'time_match', 'home_team', 'away_team', 
                'model','datetime_inference', 'prob_home_win', 'prob_draw', 'prob_away_win',
                'odds_home', 'odds_draw', 'odds_away', 
                'bookmaker_home', 'bookmaker_draw', 'bookmaker_away', 'f_home', 'f_draw', 'f_away', 'datetime_optim', 'utility_fn',
                 'odds_home_datetime', 'odds_draw_datetime', 'odds_away_datetime', 'optim_label']]
            df_models_results_joined_cols.to_sql(DB_TN_OPTIM_RESULTS, conn, if_exists='append', index=False)
        logger.info(f"Data exported in {time.time() - start_export:.2f} seconds")
    except Exception as e:
        logger.error(f"Error while exporting the data: {e}")
        raise
    
    return datetime_optim, df_models_results_joined_cols
    

if __name__ == '__main__':
    bookmaker_keys = [
    "onexbet",
    "sport888",
    "betclic",
    "betanysports",
    "betfair_ex_eu",
    "betonlineag",
    "betsson",
    "betvictor",
    "coolbet",
    "everygame",
    "gtbets",
    "livescorebet_eu",
    "marathonbet",
    "matchbook",
    "mybookieag",
    "nordicbet",
    "pinnacle",
    "suprabets",
    "tipico_de",
    "unibet_eu",
    "williamhill"
]
    bookmaker_keys = [
    "onexbet",
    "sport888",
    "betclic"
        ]
    
    n_matches = 10
    logging.info("-- Starting the OF pipeline --")
    datetime_first_match = '2024-08-26 00:00:00'
    model =  'RSF_PR_LR'
    find__of(datetime_first_match=datetime_first_match, model=model, n_matches=n_matches, bookmakers=bookmaker_keys)
    logging.info("-- Pipeline completed --")
    print("Pipeline completed")
