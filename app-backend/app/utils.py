"""Utility functions for the FastAPI application."""

import time
import asyncio
from typing import Any, Dict, List
from functools import wraps
import logging
import pandas as pd

logger = logging.getLogger("app-backend.utils")


def timing_decorator(func):
    """Decorator to measure function execution time."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {str(e)}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {str(e)}")
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

def dataframe_to_dict_safe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Safely convert DataFrame to dictionary with proper handling of NaN values."""
    try:
        # Replace NaN with None for JSON serialization
        df_clean = df.where(pd.notnull(df), None)
        return df_clean.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Error converting DataFrame to dict: {str(e)}")
        return []


def format_performance_data(results_df: pd.DataFrame, bankroll: float = 100.0, divisor: float = 2.0) -> tuple[list, dict, dict]:
    """
    Format performance data from DataFrame into structured matches, metrics, and period info.
    
    Args:
        results_df: DataFrame containing performance data
        bankroll: Bankroll amount used for stake calculations
        
    Returns:
        tuple: (matches_list, metrics_dict, period_info_dict)
    """
    matches = []
    total_stake = 0.0
    total_payout = 0.0
    winning_matches = 0
    losing_matches = 0
    break_even_matches = 0
    home_bets = 0
    draw_bets = 0
    away_bets = 0
    total_odds = 0.0
    odds_count = 0
    
    for _, row in results_df.iterrows():
        # Calculate stakes based on fractions
        stake_home = (row.get('f_home', 0) or 0) * bankroll / divisor
        stake_draw = (row.get('f_draw', 0) or 0) * bankroll / divisor
        stake_away = (row.get('f_away', 0) or 0) * bankroll / divisor
        match_total_stake = stake_home + stake_draw + stake_away
        
        # Determine actual result
        home_goals = row.get('home_g', 0) or 0
        away_goals = row.get('away_g', 0) or 0
        
        if home_goals > away_goals:
            match_result = "H"
            winning_stake = stake_home
            winning_odds = row.get('odds_home', 1) or 1
        elif home_goals < away_goals:
            match_result = "A"
            winning_stake = stake_away
            winning_odds = row.get('odds_away', 1) or 1
        else:
            match_result = "D"
            winning_stake = stake_draw
            winning_odds = row.get('odds_draw', 1) or 1
        
        # Calculate payout and profit
        payout = winning_stake * winning_odds
        profit_loss = payout - match_total_stake
        
        # Update counters
        total_stake += match_total_stake
        total_payout += payout
        
        if profit_loss > 0:
            winning_matches += 1
        elif profit_loss < 0:
            losing_matches += 1
        else:
            break_even_matches += 1
        
        if stake_home > 1e-3:
            home_bets += 1
            total_odds += row.get('odds_home', 1) or 1
            odds_count += 1
        if stake_draw > 1e-3:
            draw_bets += 1
            total_odds += row.get('odds_draw', 1) or 1
            odds_count += 1
        if stake_away > 1e-3:
            away_bets += 1
            total_odds += row.get('odds_away', 1) or 1
            odds_count += 1
        
        match_performance = {
            "match_id": str(row.get('match_id', '')),
            "game": str(row.get('game', '')),
            "home_team": str(row.get('home_team', '')),
            "away_team": str(row.get('away_team', '')),
            "date_match": str(row.get('date_match', '')),
            "time_match": str(row.get('time_match', '')),
            "model": str(row.get('model', '')),
            "datetime_inference": str(row.get('datetime_inference', '')),
            "prob_home_win": float(row.get('prob_home_win', 0) or 0),
            "prob_draw": float(row.get('prob_draw', 0) or 0),
            "prob_away_win": float(row.get('prob_away_win', 0) or 0),
            "odds_home": float(row.get('odds_home', 1) or 1),
            "odds_draw": float(row.get('odds_draw', 1) or 1),
            "odds_away": float(row.get('odds_away', 1) or 1),
            "bookmaker_home": str(row.get('bookmaker_home', '')),
            "bookmaker_draw": str(row.get('bookmaker_draw', '')),
            "bookmaker_away": str(row.get('bookmaker_away', '')),
            "bookmaker_home_key": str(row.get('bookmaker_home_key', '')),
            "bookmaker_draw_key": str(row.get('bookmaker_draw_key', '')),
            "bookmaker_away_key": str(row.get('bookmaker_away_key', '')),
            "f_home": float(row.get('f_home', 0) or 0),
            "f_draw": float(row.get('f_draw', 0) or 0),
            "f_away": float(row.get('f_away', 0) or 0),
            "utility_fn": str(row.get('utility_fn', '')),
            "datetime_optim": str(row.get('datetime_optim', '')),
            "optim_label": str(row.get('optim_label', '')),
            "home_goals": int(home_goals),
            "away_goals": int(away_goals),
            "match_result": match_result,
            "stake_home": stake_home,
            "stake_draw": stake_draw,
            "stake_away": stake_away,
            "total_stake": match_total_stake,
            "payout": payout,
            "profit_loss": profit_loss
        }
        matches.append(match_performance)
    
    # Calculate performance metrics
    total_matches = len(matches)
    total_profit_loss = total_payout - total_stake
    roi_percentage = (total_profit_loss / total_stake * 100) if total_stake > 0 else 0
    win_rate = (winning_matches / total_matches * 100) if total_matches > 0 else 0
    avg_stake_per_match = total_stake / total_matches if total_matches > 0 else 0
    avg_profit_per_match = total_profit_loss / total_matches if total_matches > 0 else 0
    avg_odds = total_odds / odds_count if odds_count > 0 else 0
    
    metrics = {
        "total_matches": total_matches,
        "total_bets_placed": home_bets + draw_bets + away_bets,
        "total_stake": total_stake,
        "total_payout": total_payout,
        "total_profit_loss": total_profit_loss,
        "roi_percentage": roi_percentage,
        "winning_matches": winning_matches,
        "losing_matches": losing_matches,
        "break_even_matches": break_even_matches,
        "win_rate": win_rate,
        "home_bets": home_bets,
        "draw_bets": draw_bets,
        "away_bets": away_bets,
        "avg_stake_per_match": avg_stake_per_match,
        "avg_profit_per_match": avg_profit_per_match,
        "avg_odds": avg_odds
    }
    
    # Calculate period info
    period_info = {}
    if not results_df.empty and 'date_match' in results_df.columns:
        try:
            period_info["total_days"] = str((results_df['date_match'].max() - results_df['date_match'].min()).days)
        except:
            period_info["total_days"] = "0"
    else:
        period_info["total_days"] = "0"
    
    return matches, metrics, period_info


def format_performance_gains_data(results_df: pd.DataFrame, bankroll: float = 100) -> tuple[list, dict]:
    """
    Format performance gains data from DataFrame into structured gains list and total summary.
    
    Args:
        results_df: DataFrame containing columns ['day', 'daily_gain', 'bankroll']
        
    Returns:
        tuple: (gains_list, total_gain_dict)
    """
    gains_data = []
    initial_bankroll = bankroll  # Use the provided bankroll

    for _, row in results_df.iterrows():
        gain_result = {
            "period": str(row['day']),
            "initial_bankroll": initial_bankroll if len(gains_data) == 0 else gains_data[-1]["final_bankroll"],
            "final_bankroll": float(row['bankroll']) * bankroll,
            "absolute_gain": float(row['daily_gain']) * bankroll,
            "percentage_gain": float(row['daily_gain']) * 100,  # Convert to percentage
            "number_of_bets": 1,  # Daily aggregation, so 1 per day
            "average_bet_size": abs(float(row['daily_gain'])) * bankroll if row['daily_gain'] != 0 else 0.0
        }
        gains_data.append(gain_result)
    
    # Calculate total gain summary
    if gains_data:
        first_bankroll = gains_data[0]["initial_bankroll"] # Initial bankroll
        last_bankroll = gains_data[-1]["final_bankroll"]
        total_absolute_gain = last_bankroll - first_bankroll
        total_percentage_gain = ((last_bankroll - first_bankroll) / first_bankroll) * 100 if first_bankroll != 0 else 0.0
        
        total_gain = {
            "period": f"{gains_data[0]['period']} to {gains_data[-1]['period']}",
            "initial_bankroll": first_bankroll,
            "final_bankroll": last_bankroll,
            "absolute_gain": total_absolute_gain,
            "percentage_gain": total_percentage_gain,
            "number_of_bets": len(gains_data),
            "average_bet_size": sum(g["average_bet_size"] for g in gains_data) / len(gains_data) if gains_data else 0.0
        }
    else:
        total_gain = {
            "period": "no data",
            "initial_bankroll": initial_bankroll,
            "final_bankroll": initial_bankroll,
            "absolute_gain": 0.0,
            "percentage_gain": 0.0,
            "number_of_bets": 0,
            "average_bet_size": 0.0
        }
    
    return gains_data, total_gain