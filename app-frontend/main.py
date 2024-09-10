import streamlit as st
import requests
import os
import pandas as pd

from app._config import APP_BACKEND_API

st.set_page_config(layout="wide")



st.title("BetMind")

st.write("Welcome to BetMind, the app that helps you make the best bets on football matches!")

if 'prev_date' not in st.session_state:
    st.session_state.prev_date = None
if 'optim_results_df' not in st.session_state:
            st.session_state.optim_results_df = None

col1, col2, col3, col4 = st.columns(4)


date = col1.date_input("Select a date", value=None, min_value=None, max_value=None, key=None)
bankroll = col2.number_input("Enter your bankroll", min_value=0, max_value=None, value=1, step=1, format=None, key=None)
display_prob = col3.checkbox("Display probabilities", value=True, key=None)
display_odds = col3.checkbox("Display odds", value=True, key=None)
decimal = col4.number_input("How many_decimal", min_value=0, max_value=None, value=0, step=1, format=None, key=None)

if date and date.strftime("%Y-%m-%d") != st.session_state.prev_date:
    print(f'date: {date}')
    print(f'st.session_state.prev_date: {st.session_state.prev_date}')
    date = date.strftime("%Y-%m-%d")
    response = requests.get(f"{APP_BACKEND_API}/optim_results", params={"datetime_computation": date})
    if response.status_code == 200:
        optim_results_df = pd.DataFrame(response.json())
        optim_results_df = optim_results_df[['home_team', 'away_team', 'date_match', 'time_match',
                  'prob_home_win', 'prob_draw', 'prob_away_win',  
                  'odds_home', 'odds_draw', 'odds_away',
                  'bookmaker_away', 'bookmaker_draw', 'bookmaker_home',
                  'f_home_kelly', 'f_draw_kelly', 'f_away_kelly']]
        optim_results_df.rename(columns={'home_team': 'Home Team', 'away_team': 'Away Team', 'date_match': 'Date', 'time_match': 'Time',
                                            'prob_home_win': 'Prob. Home', 'prob_draw': 'Prob. Draw', 'prob_away_win': 'Prob. Away',
                                            'odds_home': 'Odds Home', 'odds_draw': 'Odds Draw', 'odds_away': 'Odds Away',
                                            'bookmaker_away': 'Bookie Away', 'bookmaker_draw': 'Bookie Draw', 'bookmaker_home': 'Bookie Home',
                                            'f_home_kelly': 'F Home Kelly', 'f_draw_kelly': 'F Draw Kelly', 'f_away_kelly': 'F Away Kelly'}, inplace=True)
        st.session_state.optim_results_df = optim_results_df
        st.session_state.prev_date = date

if st.session_state.optim_results_df is not None:
    df = st.session_state.optim_results_df.copy()
    df[['F Home Kelly', 'F Draw Kelly', 'F Away Kelly']] = df[['F Home Kelly', 'F Draw Kelly', 'F Away Kelly']]*bankroll
    df[['F Home Kelly', 'F Draw Kelly', 'F Away Kelly']] = df[['F Home Kelly', 'F Draw Kelly', 'F Away Kelly']].round(decimal)
    if not display_prob:
        df = df.drop(columns=['Prob. Home', 'Prob. Draw', 'Prob. Away'])
    if not display_odds:
        df = df.drop(columns=['Odds Home', 'Odds Draw', 'Odds Away'])
    st.dataframe(df)

else:
    st.write("No results found for the given date")

stats = st.expander("Statistics")
if stats and st.session_state.optim_results_df is not None:
    df = st.session_state.optim_results_df.copy()
    money_to_invest_home = float(df[['F Home Kelly']].sum())
    money_to_invest_draw = float(df[['F Draw Kelly']].sum())
    money_to_invest_away = float(df[['F Away Kelly']].sum())

    stats.write(f"Money to invest on Home: {money_to_invest_home:.2f}".rstrip('0').rstrip('.'))
    stats.write(f"Money to invest on Draw: {money_to_invest_draw:.2f}".rstrip('0').rstrip('.'))
    stats.write(f"Money to invest on Away: {money_to_invest_away:.2f}".rstrip('0').rstrip('.'))

    total_money_to_invest = money_to_invest_home + money_to_invest_draw + money_to_invest_away
    stats.write(f"Total money to invest: {total_money_to_invest:.2f}".rstrip('0').rstrip('.'))