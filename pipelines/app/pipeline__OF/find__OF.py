
import logging
import time
import datetime

import pandas as pd
from sqlalchemy import text

from app._config import DB_TN_OPTIM_RESULTS
from app._config import engine

from optibet_lib.optim.functions.player_utility_kelly_criteria import player_utility_kelly_criteria
from optibet_lib.optim.functions.player_expected_utility_log import player_expected_utility_log
from optibet_lib.optim.functions.player_expected_utility_exp_ce import player_expected_utility_exp_ce
from optibet_lib.optim.functions.player_utility_linear import player_utility_linear
from optibet_lib.optim.functions.player_utility_crra_power import player_utility_crra_power
from optibet_lib.optim.resolve.resolve_fik import resolve_fik


logger = logging.getLogger("OF")

def find__of(datetime_first_match: str = None, model: str = 'RSF_PR_LR', n_matches : int = None, same_day: bool = False,
             bookmakers : list[str] =  None, bankroll : float = 1, method='SLSQP', 
             utility_fn='Kelly', optim_label='manual', l=10, divisor: float = 2.0) -> datetime.datetime:
    """
    Find the optimal fraction to invest for each match based on the model results and the odds.
    Parameters
    ----------
    datetime_first_match : str, optional
        The datetime of the first match to consider for the optimization, by default None (today). 
        Will filter the models result by date (>=today 00:00:00 for example). 
        Will also filter the last odds for all matches before the given datetime.
        Format should be 'YYYY-MM-DD HH:MM:SS'. If None, will use the current date and time.
    model : str, optional
        The model to use for the optimization, by default 'RSF_PR_LR'
    n_matches : int, optional
        The number of matches to consider for the optimization, by default None (all matches)
    same_day : bool, optional
        If True, only consider matches of the same day as the first match, by default False
    bookmakers : list[str], optional
        The list of bookmakers to consider for the optimization, by default None (all bookmakers)
    bankroll : float, optional
        The initial bankroll to use for the optimization, by default 1
    method : str, optional
        The optimization method to use, by default 'SLSQP'
    utility_fn : str, optional
        The utility function to use for the optimization, by default 'Kelly'
    optim_label : str, optional
        The label to use to store the optimization results, by default 'manual'
    l : int, optional
        The lambda parameter for the Linear optimization, by default 10

    Returns
    -------
    datetime.datetime
        The datetime of the first match to consider for the optimization
    """

    logging.info(f"--- Starting the OF pipeline")
    # Retrieve data from the database
    start_processing = time.time()
    try:
        if datetime_first_match is None:
            datetime_first_match = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        df_models_results_joined = load_data_for_optimization(
            datetime_first_match=datetime_first_match,
            model=model,
            sports_filter=None,
            bookmakers=bookmakers,
            same_day=same_day
        )
        if df_models_results_joined.empty:
            logging.warning("No data available for optimization after loading")
            return datetime.datetime.now(), pd.DataFrame()

        # Sort by date start
        df_models_results_joined = df_models_results_joined.sort_values(by=['date_match', 'time_match'], ascending=True)

        # Note: Le filtrage same_day est maintenant géré dans load_data_for_optimization

        # if no match found
        if df_models_results_joined.empty:
            logger.warning(f"No matches found for optimization with parameters: model={model}, datetime_first_match={datetime_first_match}, same_day={same_day}, bookmakers={bookmakers}")
            return datetime.datetime.now(), pd.DataFrame()

        # Keep only the n_matches first matches
        if n_matches:
            df_models_results_joined = df_models_results_joined.head(n_matches)
            logger.info(f"Limited to first {n_matches} matches")
        
        logger.info(f"Number of matches to optimize: {df_models_results_joined.shape[0]}")

        # Vérification des colonnes nécessaires
        required_cols = ['odds_home', 'odds_draw', 'odds_away', 'prob_home_win', 'prob_draw', 'prob_away_win']
        missing_cols = [col for col in required_cols if col not in df_models_results_joined.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Compute the numpy arrays of odds (o) and probabilities (r)
        o = df_models_results_joined[['odds_home', 'odds_draw', 'odds_away']].to_numpy()
        r = df_models_results_joined[['prob_home_win', 'prob_draw', 'prob_away_win']].to_numpy()
        
        # Vérification des valeurs nulles ou invalides
        if pd.isna(o).any() or pd.isna(r).any():
            logger.error("Found NaN values in odds or probabilities")
            raise ValueError("Found NaN values in odds or probabilities")

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
            df_models_results_joined[['f_home', 'f_draw', 'f_away']] = result_kelly / divisor
            df_models_results_joined['utility_fn'] = utility_fn
            datetime_optim = datetime.datetime.now()
            df_models_results_joined['datetime_optim'] = datetime_optim
            logger.info(f"Kelly computed in {time.time() - start_invest:.2f} seconds")
            
        # Log
        if utility_fn == 'Log':
            obectif_log_fn = lambda  f, o, t : player_expected_utility_log(f, o, t, B=bankroll)
            result_log = resolve_fik(o, r, obectif_log_fn, logger=logger, method=method)
            result_log[result_log < 1e-10] = 0
            df_models_results_joined[['f_home', 'f_draw', 'f_away']] = result_log / divisor
            df_models_results_joined['utility_fn'] = utility_fn
            datetime_optim = datetime.datetime.now()
            df_models_results_joined['datetime_optim'] = datetime_optim
            logger.info(f"Log computed in {time.time() - start_invest:.2f} seconds")
            
        # Exponential
        if utility_fn == 'Exp':
            obectif_exp_fn = lambda  f, o, t : player_expected_utility_exp_ce(f, o, t, B=bankroll, alpha=l)
            result_exp = resolve_fik(o, r, obectif_exp_fn, logger=logger, method=method)
            result_exp[result_exp < 1e-10] = 0
            df_models_results_joined[['f_home', 'f_draw', 'f_away']] = result_exp / divisor
            df_models_results_joined['utility_fn'] = utility_fn
            datetime_optim = datetime.datetime.now()
            df_models_results_joined['datetime_optim'] = datetime_optim
            logger.info(f"Exp computed in {time.time() - start_invest:.2f} seconds")
            
        # Linear
        if utility_fn == 'Linear':
            obectif_linear_fn = lambda  f, o, t : player_utility_linear(f, o, t, B=bankroll, l=l)
            result_linear = resolve_fik(o, r, obectif_linear_fn, logger=logger, method=method)
            result_linear[result_linear < 1e-10] = 0
            df_models_results_joined[['f_home', 'f_draw', 'f_away']] = result_linear / divisor
            df_models_results_joined['utility_fn'] = utility_fn
            datetime_optim = datetime.datetime.now()
            df_models_results_joined['datetime_optim'] = datetime_optim
            logger.info(f"Linear computed in {time.time() - start_invest:.2f} seconds")

        if utility_fn == 'CRRA':
            obectif_crra_fn = lambda f, o, t: player_utility_crra_power(f, o, t, B=bankroll, gamma=l)
            result_crra = resolve_fik(o, r, obectif_crra_fn, logger=logger, method=method)
            result_crra[result_crra < 1e-10] = 0
            df_models_results_joined[['f_home', 'f_draw', 'f_away']] = result_crra / divisor
            df_models_results_joined['utility_fn'] = utility_fn
            datetime_optim = datetime.datetime.now()
            df_models_results_joined['datetime_optim'] = datetime_optim
            logger.info(f"CRRA computed in {time.time() - start_invest:.2f} seconds")
            
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
                'bookmaker_home', 'bookmaker_draw', 'bookmaker_away', 'bookmaker_home_key', 'bookmaker_draw_key', 'bookmaker_away_key',
                'f_home', 'f_draw', 'f_away', 'datetime_optim', 'utility_fn',
                 'odds_home_datetime', 'odds_draw_datetime', 'odds_away_datetime', 'optim_label']]
            df_models_results_joined_cols.to_sql(DB_TN_OPTIM_RESULTS, conn, if_exists='append', index=False)
        logger.info(f"Data exported in {time.time() - start_export:.2f} seconds")
    except Exception as e:
        logger.error(f"Error while exporting the data: {e}")
        raise

    logging.info(f"--- OF pipeline completed in {time.time() - start_processing:.2f} seconds ---")
    
    return datetime_optim, df_models_results_joined_cols

def load_data_for_optimization(datetime_first_match: datetime.datetime,
                               model: str,
                               sports_filter: list[str],
                               bookmakers: list[str] = None, same_day: bool = False) -> pd.DataFrame:
    with engine.connect() as conn:

        conn.execute(text("REFRESH MATERIALIZED VIEW mv_models_results_last_inferred;"))
        conn.execute(text("REFRESH MATERIALIZED VIEW mv_soccer_odds_normalized;"))
        conn.execute(text("REFRESH MATERIALIZED VIEW mv_soccer_odds_last_normalized;"))
        conn.execute(text("REFRESH MATERIALIZED VIEW mv_models_results_last_inferred;"))

        if same_day:
            datetime_first_match = datetime_first_match.replace(hour=0, minute=0, second=0, microsecond=0)
            logging.info(f"Filtering matches for the same day: {datetime_first_match.date()}")
            datetime_last_match = datetime_first_match + pd.Timedelta(days=1)
            logging.info(f"Filtering matches until: {datetime_last_match}")
            
            # Query pour les résultats du modèle - jour même uniquement
            df_models_results = pd.read_sql(
                text("""
                    SELECT *
                    FROM mv_models_results_last_inferred
                    WHERE model = :model
                      AND date_match = :date_match
                """),
                conn,
                params={
                    "model": model,
                    "date_match": datetime_first_match.date()
                }
            )

            # Query pour les cotes - jour même uniquement
            df_odds = pd.read_sql(
                text("""
                    SELECT *
                    FROM mv_soccer_odds_last_normalized
                    WHERE commence_time >= :datetime_first_match
                      AND commence_time < :datetime_last_match
                """),
                conn,
                params={
                    "datetime_first_match": datetime_first_match,
                    "datetime_last_match": datetime_last_match
                }
            )
        else:
            datetime_last_match = None
            
            # Query pour les résultats du modèle - à partir de la date donnée
            df_models_results = pd.read_sql(
                text("""
                    SELECT *
                    FROM mv_models_results_last_inferred
                    WHERE model = :model
                      AND date_match >= :date_match
                """),
                conn,
                params={
                    "model": model,
                    "date_match": datetime_first_match.date()
                }
            )

            # Query pour les cotes - à partir de la datetime donnée
            df_odds = pd.read_sql(
                text("""
                    SELECT *
                    FROM mv_soccer_odds_last_normalized
                    WHERE commence_time >= :datetime_first_match
                """),
                conn,
                params={"datetime_first_match": datetime_first_match}
            )
    
    # Check si les datasets de base sont vides
    if df_models_results.empty:
        logging.warning(f"No model results found for model '{model}' and date >= {datetime_first_match.date()}")
        return pd.DataFrame()
    
    if df_odds.empty:
        logging.warning(f"No odds found for commence_time >= {datetime_first_match}")
        return pd.DataFrame()
    
    logging.info(f"Found {len(df_models_results)} model results and {len(df_odds)} odds records")

    if bookmakers:
        df_odds = df_odds[df_odds['bookmaker_key'].isin(bookmakers)]
        logging.info(f"After bookmaker filtering: {len(df_odds)} odds records")

    # remove matchbook
    df_odds = df_odds[df_odds['bookmaker_key'] != 'matchbook']
    logging.info(f"After removing 'matchbook': {len(df_odds)} odds records")

    if sports_filter:
        df_odds = df_odds[df_odds['sport_key'].isin(sports_filter)]
        logging.info(f"After sports filtering: {len(df_odds)} odds records")
    
    # Check si df_odds est vide après les filtres
    if df_odds.empty:
        logging.warning("No odds remaining after applying bookmaker and/or sports filters")
        return pd.DataFrame()

    # Pivot home/draw/away
    df_home = df_odds[df_odds['outcome_name'] == df_odds['home_team']].copy()
    df_draw = df_odds[df_odds['outcome_name'] == 'Draw'].copy()
    df_away = df_odds[df_odds['outcome_name'] == df_odds['away_team']].copy()

    # Check si les DataFrames pivotés sont vides
    if df_home.empty or df_draw.empty or df_away.empty:
        logging.warning(f"Missing outcome data after pivot: home={len(df_home)}, draw={len(df_draw)}, away={len(df_away)}")
        return pd.DataFrame()

    df_home = df_home.rename(columns={'outcome_price': 'odds_home', 'bookmaker_title': 'bookmaker_home', 'bookmaker_last_update': 'odds_home_datetime'})
    df_draw = df_draw.rename(columns={'outcome_price': 'odds_draw', 'bookmaker_title': 'bookmaker_draw', 'bookmaker_last_update': 'odds_draw_datetime'})
    df_away = df_away.rename(columns={'outcome_price': 'odds_away', 'bookmaker_title': 'bookmaker_away', 'bookmaker_last_update': 'odds_away_datetime'})
    df_home['bookmaker_home_key'] = df_home['bookmaker_key']
    df_draw['bookmaker_draw_key'] = df_draw['bookmaker_key']
    df_away['bookmaker_away_key'] = df_away['bookmaker_key']

    df_home = df_home[['match_id', 'bookmaker_key', 'odds_home', 'odds_home_datetime', 'bookmaker_home', 'bookmaker_home_key']]
    df_draw = df_draw[['match_id', 'bookmaker_key', 'odds_draw', 'odds_draw_datetime', 'bookmaker_draw', 'bookmaker_draw_key']]
    df_away = df_away[['match_id', 'bookmaker_key', 'odds_away', 'odds_away_datetime', 'bookmaker_away', 'bookmaker_away_key']]

    df_pivot = df_home.merge(df_draw, on=['match_id', 'bookmaker_key']).merge(df_away, on=['match_id', 'bookmaker_key'])
    
    # Check si le pivot est vide
    if df_pivot.empty:
        logging.warning("No matches found with complete home/draw/away odds")
        return pd.DataFrame()
    
    logging.info(f"Found {len(df_pivot)} complete odds combinations")

    def get_best(df, col):
        return df.loc[df[col].idxmax()]

    best_odds = df_pivot.groupby('match_id').apply(lambda g: pd.Series({
        'odds_home': g['odds_home'].max(),
        'odds_draw': g['odds_draw'].max(),
        'odds_away': g['odds_away'].max(),
        'bookmaker_home': get_best(g, 'odds_home')['bookmaker_home'],
        'bookmaker_draw': get_best(g, 'odds_draw')['bookmaker_draw'],
        'bookmaker_away': get_best(g, 'odds_away')['bookmaker_away'],
        'bookmaker_home_key': get_best(g, 'odds_home')['bookmaker_home_key'],
        'bookmaker_draw_key': get_best(g, 'odds_draw')['bookmaker_draw_key'],
        'bookmaker_away_key': get_best(g, 'odds_away')['bookmaker_away_key'],
        'odds_home_datetime': get_best(g, 'odds_home')['odds_home_datetime'],
        'odds_draw_datetime': get_best(g, 'odds_draw')['odds_draw_datetime'],
        'odds_away_datetime': get_best(g, 'odds_away')['odds_away_datetime'],
    })).reset_index()
    
    # Check si best_odds est vide
    if best_odds.empty:
        logging.warning("No best odds could be computed")
        return pd.DataFrame()

    df_match_info = df_odds.drop_duplicates(subset='match_id')[
        ['match_id', 'home_team_canonical', 'away_team_canonical', 'commence_time', 'sport_key']
    ]
    df_odds_final = best_odds.merge(df_match_info, on='match_id', how='left')
    df_odds_final['date_match'] = df_odds_final['commence_time'].dt.date

    df_final = df_models_results.merge(
        df_odds_final,
        left_on=['home_team', 'away_team', 'date_match'],
        right_on=['home_team_canonical', 'away_team_canonical', 'date_match'],
        how='inner'
    )
    
    # Check final
    if df_final.empty:
        logging.warning("No matches found after joining model results with odds data")
        return pd.DataFrame()
    
    logging.info(f"Final dataset contains {len(df_final)} matches ready for optimization")

    return df_final


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
    
    n_matches = 100
    logging.info("-- Starting the OF pipeline --")
    datetime_first_match = '2025-09-16 00:00:00'
    datetime_first_match = pd.to_datetime(datetime_first_match)
    model =  'RSF_PR_LR'
    find__of(datetime_first_match=datetime_first_match, model=model, n_matches=n_matches, bookmakers=bookmaker_keys, same_day=False)
    logging.info("-- Pipeline completed --")
    print("Pipeline completed")
