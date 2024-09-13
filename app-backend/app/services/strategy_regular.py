from app.services.get_optim_results import get_optim_results
import pandas as pd
import datetime

from app._config import DB_TN_FBREF_RESULTS
from app._config import engine

def strategy_regular(datetime_first_match: str = None, steps = None, 
                     n_matches: int = None, bet_days_timedelta: int = 1, # if n_match is None, then we take the n_matches else we take all the matches for each day that coorespond to the bet_days_timedelta
                     bet_one_time_per_match : bool = True, bookmakers: str = None, 
                     method: str = 'SLSQP', keely_fraction: float = 0.5):
    """Compute regular strategy"""

    if not datetime_first_match:
        datetime_first_match = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datetime_first_match = datetime.datetime.strptime(datetime_first_match, "%Y-%m-%d %H:%M:%S")
    datetime_today = datetime.datetime.now()

    bankroll = 1
    bankroll_beforebet = 1
    bankrolls = []
    bankrolls_beforebet = []
    dates = []
    on_bets = []

    matches_bet_on = {}
    # {
    #     'match_name': {
    #           'date_bet1': {
    #             'home_expected': 0.5, odds*f_bankroll (get it if win, errase match key after checking)
    #             'draw_expected': 0.25,
    #             'away_expected': 0.25,
    #           },
    #           'date_bet2': {
    #             'home_expected': 0.5,
    #             'draw_expected': 0.25,
    #             'away_expected': 0.25,
    #           }
    #     }
    # }

    if not steps:
        steps = (datetime_today - datetime_first_match).days

    for i in range(steps):
        datetime_i = datetime_first_match + datetime.timedelta(days=i)
        date_i = datetime_i.date()
        dates.append(date_i)

        print(f"\n date: {date_i} ----------------")
        print(f'matches_bet_on: {matches_bet_on}')

        # GATHER GAINS FROM PREVIOUS MATCHES WE BET ON
        # get results of the matchs from the db if match_name in matches_bet_on and score of the match is available in the db
        matches_bet_on_list = list(matches_bet_on.keys())
        matches_bet_on_list_copy = matches_bet_on_list.copy()
        if matches_bet_on_list_copy:
            for i in range(len(matches_bet_on_list_copy)):
                matches_bet_on_list_copy[i] = matches_bet_on_list_copy[i].replace("'", "''")

            print(f'matches_bet_on_list: {matches_bet_on_list_copy}')

            matches_bet_on_list_query_proof = str(tuple(matches_bet_on_list_copy)).replace(',)', ')').replace('"', "'")

            print(f'matches_bet_on_list_query_proof: {matches_bet_on_list_query_proof}')

            query = f"SELECT * FROM {DB_TN_FBREF_RESULTS} WHERE date < DATE('{date_i}') AND game IN {matches_bet_on_list_query_proof}"
            print(query)
            with engine.connect() as connection:
                df_results = pd.read_sql(query, connection)

            for match_name in matches_bet_on_list:
                df_match = df_results[df_results['game'] == match_name]
                if not df_match.empty:
                    home_score = df_match['home_g'].values[0]
                    away_score = df_match['away_g'].values[0]
                    if home_score is not None and away_score is not None:
                        # compute the result of the match
                        if home_score > away_score:
                            result = 'home'
                        elif home_score < away_score:
                            result = 'away'
                        else:
                            result = 'draw'
                        for date_bet in matches_bet_on[match_name]:
                            expected = matches_bet_on[match_name][date_bet]
                            if result == 'home':
                                bankroll += expected['home_expected']
                            elif result == 'draw':
                                bankroll += expected['draw_expected']
                            else:
                                bankroll += expected['away_expected']
                        del matches_bet_on[match_name]
                

        # MAKE THE OPTIMIZATION ON THE n_matches NEXT MATCHES
            
        df_optim_results, metrics, durations = get_optim_results(
            datetime_first_match=datetime_i.strftime("%Y-%m-%d %H:%M:%S"), 
            n_matches=n_matches, 
            bookmakers=bookmakers, 
            bankroll=bankroll, 
            method=method
            )
        df_optim_results_print = df_optim_results[['game', 'date_match']]
        print(f'df_optim_results: {df_optim_results_print}')
        print(f'date: {date_i}')
        print(f'bet_days_timedelta: {datetime.timedelta(days=bet_days_timedelta)}')
        print(f'date match: {date_i + datetime.timedelta(days=bet_days_timedelta)}')
        
        if bet_days_timedelta is not None:
            df_optim_results = df_optim_results[df_optim_results['date_match'] == date_i + datetime.timedelta(days=bet_days_timedelta)]
        
        df_optim_results_print = df_optim_results[['game', 'date_match']]
        print(f'df_optim_results: {df_optim_results_print}')

        bankroll_beforebet = bankroll
        bankrolls_beforebet.append(bankroll_beforebet)

        for i, row in df_optim_results.iterrows():
            match_name = row['game']
            if bet_one_time_per_match and match_name in matches_bet_on:
                continue
            if match_name not in matches_bet_on:
                matches_bet_on[match_name] = {}
            matches_bet_on[match_name][date_i] = {
                'home_expected': row['f_home_kelly']*bankroll*row['odds_home']*keely_fraction,
                'draw_expected': row['f_draw_kelly']*bankroll*row['odds_draw']*keely_fraction,
                'away_expected': row['f_away_kelly']*bankroll*row['odds_away']*keely_fraction,
                'bet_home': row['f_home_kelly']*bankroll*keely_fraction,
                'bet_draw': row['f_draw_kelly']*bankroll*keely_fraction,
                'bet_away': row['f_away_kelly']*bankroll*keely_fraction
            }

            bankroll -= matches_bet_on[match_name][date_i]['bet_home'] + matches_bet_on[match_name][date_i]['bet_draw'] + matches_bet_on[match_name][date_i]['bet_away']
        bankrolls.append(bankroll)

        # COMPUTE THE MONEY ON BET
        on_bet = 0
        for match_name in matches_bet_on:
            for date_bet in matches_bet_on[match_name]:
                expected = matches_bet_on[match_name][date_bet]
                on_bet += expected['bet_home'] + expected['bet_draw'] + expected['bet_away']
        on_bets.append(on_bet)
        
    results = pd.DataFrame({'date': dates, 'bankroll_beforebet': bankrolls_beforebet,
                            'bankroll': bankrolls, 'on_bet': on_bets})
    return results


if __name__ == '__main__':
    datetime_first_match = '2024-08-23 00:00:00'
    n_matches = 20
    method = 'SLSQP'
    steps = 14
    bet_days_timedelta = 0
    results = strategy_regular(datetime_first_match=datetime_first_match, n_matches=n_matches, method=method, steps=steps, bet_days_timedelta=bet_days_timedelta)
    print(results)
        



