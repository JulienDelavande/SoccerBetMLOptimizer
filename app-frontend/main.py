import streamlit as st
import requests
import os
import pandas as pd

from app._config import APP_BACKEND_API

st.set_page_config(layout="wide")

if "optim_results_df" not in st.session_state:
    st.session_state.optim_results_df = None
if "metrics" not in st.session_state:
    st.session_state.metrics = None
if "durations" not in st.session_state:
    st.session_state.durations = None
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1

st.title("BetMind")

st.write("Welcome to BetMind, the app that helps you make the best bets on football matches!")

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

col1, col2 = st.columns([0.75, 0.25])
bookmaker_keys = col1.multiselect("Select bookmakers", bookmaker_keys_values, default='betclic')
method = col2.selectbox("Select optimization method", ['SLSQP', 'COBYLA', 'trust-constr'])

search_button = st.button("Search")

if search_button:
    datetime_first_match = date.strftime("%Y-%m-%d %H:%M:%S")
    bankroll = bankroll_actual / bankroll_initial
    st.session_state.bankroll = bankroll
    bookmakers = ','.join(bookmaker_keys)
    params = {"datetime_first_match": datetime_first_match, "n_matches": n_matches, "bookmakers": bookmakers, "bankroll": bankroll, "method": method}
    response = requests.get(f"{APP_BACKEND_API}/optim_results", params=params)
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
                'odds_home', 'odds_draw', 'odds_away',
                'bookmaker_away', 'bookmaker_draw', 'bookmaker_home',
                'f_home_kelly', 'f_draw_kelly', 'f_away_kelly']]
    optim_results_df.rename(columns={'home_team': 'Home Team', 'away_team': 'Away Team', 'date_match': 'Date', 'time_match': 'Time',
                                        'prob_home_win': 'Prob. Home', 'prob_draw': 'Prob. Draw', 'prob_away_win': 'Prob. Away',
                                        'odds_home': 'Odds Home', 'odds_draw': 'Odds Draw', 'odds_away': 'Odds Away',
                                        'bookmaker_away': 'Bookie Away', 'bookmaker_draw': 'Bookie Draw', 'bookmaker_home': 'Bookie Home',
                                        'f_home_kelly': 'Money Home Kelly', 'f_draw_kelly': 'Money Draw Kelly', 'f_away_kelly': 'Money Away Kelly'}, inplace=True)
    optim_results_df[['Money Home Kelly', 'Money Draw Kelly', 'Money Away Kelly']] = optim_results_df[['Money Home Kelly', 'Money Draw Kelly', 'Money Away Kelly']]*bankroll_actual
    optim_results_df[['Money Home Kelly', 'Money Draw Kelly', 'Money Away Kelly']] = optim_results_df[['Money Home Kelly', 'Money Draw Kelly', 'Money Away Kelly']].round(decimal)
    if not display_prob:
        optim_results_df = optim_results_df.drop(columns=['Prob. Home', 'Prob. Draw', 'Prob. Away'])
    if not display_odds:
        optim_results_df = optim_results_df.drop(columns=['Odds Home', 'Odds Draw', 'Odds Away'])
    if st.session_state.metrics['total_invested'] == 0:
        st.warning("Optimization failed try with another optmization method [trust-constr]")
    st.dataframe(optim_results_df)
else:
    st.write("No matchs found")

stats = st.expander("Statistics")
if stats:

    if st.session_state.optim_results_df is not None:
        stats.markdown("#### Sum of money to invest")
        df = st.session_state.optim_results_df.copy()
        money_to_invest_home = round(float((df[['f_home_kelly']]*bankroll_actual).sum().iloc[0]), decimal)
        money_to_invest_draw = round(float((df[['f_draw_kelly']]*bankroll_actual).sum().iloc[0]), decimal)
        money_to_invest_away = round(float((df[['f_away_kelly']]*bankroll_actual).sum().iloc[0]), decimal)
        total_money_to_invest = money_to_invest_home + money_to_invest_draw + money_to_invest_away
        col1, col2, col3, col4 = stats.columns(4)
        col1.write(f"Money to invest on Home: {money_to_invest_home:.2f}".rstrip('0').rstrip('.'))
        col2.write(f"Money to invest on Draw: {money_to_invest_draw:.2f}".rstrip('0').rstrip('.'))
        col3.write(f"Money to invest on Away: {money_to_invest_away:.2f}".rstrip('0').rstrip('.'))
        col4.write(f"Total money to invest: {total_money_to_invest:.2f}".rstrip('0').rstrip('.'))

    if st.session_state.metrics is not None:
        stats.markdown("#### Expected return and variance")
        metrics = st.session_state.metrics
        expected_bankroll_kelly = round((metrics['expected_value_kelly'] + 1)*bankroll_actual , decimal)
        variance_kelly = round(metrics['variance_kelly']*bankroll_actual, decimal)
        col1, col2 = stats.columns(2)
        col1.write(f"Expected bankroll: {expected_bankroll_kelly}")
        col2.write(f"Variance bankroll: {variance_kelly}")

    if st.session_state.durations is not None:
        stats.markdown("#### Durations")
        durations = st.session_state.durations
        col1, col2, col3, col4 = stats.columns(4)
        col1.write(f"Validation time: {durations['duration_validation']:.4f} seconds")
        col2.write(f"Optim request time: {durations['duration_request']:.4f} seconds")
        col3.write(f"DB results time: {durations['duration_db_results']:.4f} seconds")
        col4.write(f"Compute metrics time: {durations['duration_compute_metrics']:.4f} seconds")