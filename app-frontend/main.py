import streamlit as st
import requests
import os
import pandas as pd

from app._config import APP_BACKEND_API, APP_BACKEND_ENDPOINT_COMPUTE_PREDICTIONS, APP_BACKEND_ENDPOINT_FETCH_LAST_PREDICTIONS

st.set_page_config(page_title="BetMind", page_icon="⚽️",
                    layout="wide",
                   initial_sidebar_state="collapsed")

if "optim_results_df" not in st.session_state:
    st.session_state.optim_results_df = None
if "metrics" not in st.session_state:
    st.session_state.metrics = None
if "durations" not in st.session_state:
    st.session_state.durations = None
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1

st.title("📰 BetMind")

st.write("Welcome to BetMind, the app that helps you make the best bets on football matches!")

PAGE1 = 'auto strategy'
PAGE2 = 'perform optim'

menu = st.sidebar.selectbox('Navigation', [PAGE1, PAGE2])

if menu == PAGE2:
    
    col1, col2, col3, col4 = st.columns(4)

    bookmaker_keys_values = [
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

    date = col1.date_input("Enter the date", value='today', min_value=None, max_value=None, key=None)
    bankroll_initial = col2.number_input("Enter your initial bankroll", min_value=0, max_value=None, value=100, step=1, format=None, key=None)
    bankroll_actual = col3.number_input("Enter your actual bankroll", min_value=0, max_value=None, value=100, step=1, format=None, key=None)
    n_matches = col4.number_input("Number of upcoming matches", min_value=0, max_value=None, value=10, step=1, format=None, key=None)

    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
    bookmaker_keys = col1.multiselect("Select bookmakers", bookmaker_keys_values, default='betclic')
    method = col2.selectbox("Select optimization method", ['SLSQP', 'COBYLA', 'trust-constr'])
    utility_fn = col3.selectbox("Select utility function", ['Kelly'])

    search_button = st.button("Search")

    if search_button:
        datetime_first_match = date.strftime("%Y-%m-%d %H:%M:%S")
        bankroll = bankroll_actual / bankroll_initial
        st.session_state.bankroll = bankroll
        bookmakers = ','.join(bookmaker_keys)
        params = {"datetime_first_match": datetime_first_match, "n_matches": n_matches, "bookmakers": bookmakers, "bankroll": bankroll, "method": method, "utility_fn": utility_fn}
        response = requests.get(f"{APP_BACKEND_API}/{APP_BACKEND_ENDPOINT_COMPUTE_PREDICTIONS}", params=params)
        if response.status_code == 200:
            response_json = response.json()
            df_optim_results, metrics, durations = response_json['df_optim_results'], response_json['metrics'], response_json['durations']
            optim_results_df = pd.DataFrame(df_optim_results)
            st.session_state.optim_results_df = optim_results_df
            st.session_state.metrics = metrics
            st.session_state.durations = durations

    options_expander = st.expander("Options")
    if options_expander:
        display_prob = options_expander.checkbox("Display probabilities", value=True, key=None)
        display_odds = options_expander.checkbox("Display odds", value=True, key=None)
        decimal = options_expander.number_input("How many_decimal", min_value=0, max_value=None, value=1, step=1, format=None, key=None)

    if st.session_state.optim_results_df is not None:
        optim_results_df = st.session_state.optim_results_df.copy()
        optim_results_df = optim_results_df[['home_team', 'away_team', 'date_match', 'time_match',
                    'prob_home_win', 'prob_draw', 'prob_away_win',  
                    'odds_home', 'odds_draw', 'odds_away', 'odds_home_datetime', 'odds_draw_datetime', 'odds_away_datetime',
                    'bookmaker_away', 'bookmaker_draw', 'bookmaker_home',
                    'f_home', 'f_draw', 'f_away']]
        optim_results_df.rename(columns={'home_team': 'Home Team', 'away_team': 'Away Team', 'date_match': 'Date', 'time_match': 'Time',
                                            'prob_home_win': 'Prob. Home', 'prob_draw': 'Prob. Draw', 'prob_away_win': 'Prob. Away',
                                            'odds_home': 'Odds Home', 'odds_draw': 'Odds Draw', 'odds_away': 'Odds Away',
                                            'bookmaker_away': 'Bookie Away', 'bookmaker_draw': 'Bookie Draw', 'bookmaker_home': 'Bookie Home',
                                            'f_home': 'Money Home', 'f_draw': 'Money Draw', 'f_away': 'Money Away',
                                            'odds_home_datetime': 'Odds Home Datetime', 'odds_draw_datetime': 'Odds Draw Datetime', 'odds_away_datetime': 'Odds Away Datetime'
                                            }, inplace=True)
        optim_results_df[['Money Home', 'Money Draw', 'Money Away']] = optim_results_df[['Money Home', 'Money Draw', 'Money Away']]*bankroll_actual
        optim_results_df[['Money Home', 'Money Draw', 'Money Away']] = optim_results_df[['Money Home', 'Money Draw', 'Money Away']].round(decimal)
        if st.session_state.metrics['total_invested'] == 0:
            st.warning("Optimization failed try with another optmization method [trust-constr]")
        if not display_prob:
            optim_results_df = optim_results_df.drop(columns=['Prob. Home', 'Prob. Draw', 'Prob. Away', 'Odds Home Datetime', 'Odds Draw Datetime', 'Odds Away Datetime'])
        if not display_odds:
            optim_results_df = optim_results_df.drop(columns=['Odds Home', 'Odds Draw', 'Odds Away'])
        st.dataframe(optim_results_df)
    else:
        st.write("No matchs found")

    stats = st.expander("Statistics")
    if stats:

        if st.session_state.optim_results_df is not None:
            stats.markdown("#### Sum of money to invest")
            df = st.session_state.optim_results_df.copy()
            money_to_invest_home = round(float((df[['f_home']]*bankroll_actual).sum().iloc[0]), decimal)
            money_to_invest_draw = round(float((df[['f_draw']]*bankroll_actual).sum().iloc[0]), decimal)
            money_to_invest_away = round(float((df[['f_away']]*bankroll_actual).sum().iloc[0]), decimal)
            total_money_to_invest = money_to_invest_home + money_to_invest_draw + money_to_invest_away
            col1, col2, col3, col4 = stats.columns(4)
            col1.write(f"Money to invest on Home: {money_to_invest_home:.2f}".rstrip('0').rstrip('.'))
            col2.write(f"Money to invest on Draw: {money_to_invest_draw:.2f}".rstrip('0').rstrip('.'))
            col3.write(f"Money to invest on Away: {money_to_invest_away:.2f}".rstrip('0').rstrip('.'))
            col4.write(f"Total money to invest: {total_money_to_invest:.2f}".rstrip('0').rstrip('.'))

        if st.session_state.metrics is not None:
            stats.markdown("#### Expected return and variance")
            metrics = st.session_state.metrics
            st.write('Metrics:', metrics)
            expected_bankroll= round((metrics['expected_value'] + 1)*bankroll_actual , decimal)
            variance = round(metrics['variance']*bankroll_actual, decimal)
            col1, col2 = stats.columns(2)
            col1.write(f"Expected bankroll: {expected_bankroll}")
            col2.write(f"Variance bankroll: {variance}")

        if st.session_state.durations is not None:
            stats.markdown("#### Durations")
            durations = st.session_state.durations
            col1, col2, col3, col4 = stats.columns(4)
            col1.write(f"Validation time: {durations['duration_validation']:.4f} seconds")
            col2.write(f"Optim request time: {durations['duration_request']:.4f} seconds")
            col3.write(f"DB results time: {durations['duration_db_results']:.4f} seconds")
            col4.write(f"Compute metrics time: {durations['duration_compute_metrics']:.4f} seconds")

if menu == PAGE1:

    if 'optim_results_df_page1' not in st.session_state:
        st.session_state.optim_results_df_page1 = None

    cols = st.columns(6)

    date = cols[0].date_input("Enter the date", value='today', min_value=None, max_value=None, key=None)
    time = cols[1].time_input("Enter the time", value='now', key=None)
    tag = cols[2].selectbox("Select tag", ['auto_regular', 'auto_same_day', 'manual'])
    bankroll_page1 = cols[3].number_input("Enter your bankroll", min_value=0, max_value=None, value=100, step=1, format=None, key=None)
    search_button = cols[4].button("Search")
    all_info = cols[5].checkbox("All Info", value=False, key=None)
    datetime = pd.to_datetime(str(date) + ' ' + str(time))

    if search_button:
        response = requests.get(f"{APP_BACKEND_API}/{APP_BACKEND_ENDPOINT_FETCH_LAST_PREDICTIONS}", params={"optim_label": tag, "datetime_optim_last": datetime})
        if response.status_code == 200:
            response_json = response.json()
            df_optim_results = pd.DataFrame(response_json['results'])
            if not df_optim_results.empty:
                st.session_state.optim_results_df_page1 = df_optim_results
            else:
                st.write("No results found")
        else:
            st.write("Internal server error")


    if st.session_state.optim_results_df_page1 is not None:
        df_optim_results = st.session_state.optim_results_df_page1.copy()
        df_optim_results[['f_home', 'f_draw', 'f_away']] = df_optim_results[['f_home', 'f_draw', 'f_away']]*bankroll_page1
        if all_info:
            st.dataframe(df_optim_results)
        else:
            df_optim_results = df_optim_results[['home_team', 'away_team', 'date_match', 'time_match', 'f_home', 'f_draw', 'f_away', 'odds_home', 'odds_draw', 'odds_away', 'bookmaker_home', 'bookmaker_draw', 'bookmaker_away']]
            st.dataframe(df_optim_results)