# Print all tables in the database
\dt

# Describe the structure of a specific table
\d optim_results

# Select the last 1000 optim results for the 'auto_same_day' label
SELECT game, model, f_home, f_draw, f_away, datetime_optim, utility_fn, optim_label, datetime_inference, prob_home_win, prob_draw, prob_away_win, odds_home, odds_draw, odds_away, bookmaker_home, bookmaker_draw, bookmaker_away FROM optim_results WHERE optim_label = 'auto_same_day' ORDER BY datetime_optim DESC LIMIT 1000;