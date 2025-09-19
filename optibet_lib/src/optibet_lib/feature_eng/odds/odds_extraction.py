import pandas as pd

def json_to_pandas_the_odds_api_get_odds(data):
    """
    Transform json request to df
    sport = 'Soccer'
    apiKey = API_KEY
    regions = 'eu'
    markets = 'h2h'
    url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={apiKey}&regions={regions}&markets={markets}'
    data = requests.get(url)
    """
    flattened_data = []

    for match in data:
        for bookmaker in match['bookmakers']:
            for market in bookmaker['markets']:
                for outcome in market['outcomes']:
                    flattened_data.append({
                        'match_id': match['id'],
                        'sport_key': match['sport_key'],
                        'sport_title': match['sport_title'],
                        'commence_time': match['commence_time'],
                        'home_team': match['home_team'],
                        'away_team': match['away_team'],
                        'bookmaker_key': bookmaker['key'],
                        'bookmaker_title': bookmaker['title'],
                        'bookmaker_last_update': bookmaker['last_update'],
                        'market_key': market['key'],
                        'market_last_update': market['last_update'],
                        'outcome_name': outcome['name'],
                        'outcome_price': outcome['price']
                    })

    df = pd.DataFrame(flattened_data)

    df['commence_time'] = pd.to_datetime(df['commence_time'])
    df['bookmaker_last_update'] = pd.to_datetime(df['bookmaker_last_update'])
    df['market_last_update'] = pd.to_datetime(df['market_last_update'])
    return df