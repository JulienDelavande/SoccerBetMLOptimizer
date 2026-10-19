from app.insert_data.utils import json_to_pandas_the_odds_api_get_odds

EVENT = {
    "id": "e1", "sport_key": "soccer_spain_la_liga", "sport_title": "La Liga - Spain",
    "commence_time": "2026-10-19T19:00:00Z", "home_team": "Getafe", "away_team": "Rayo Vallecano",
    "bookmakers": [
        {"key": "onexbet", "title": "1xBet", "last_update": "2026-10-19T12:45:40Z",
         "link": "https://1xbet.com/en/line/football/127733-spain-la-liga/371901094-getafe-rayo-vallecano",
         "markets": [{"key": "h2h", "last_update": "2026-10-19T12:45:40Z",
                      "outcomes": [{"name": "Getafe", "price": 3.13}, {"name": "Draw", "price": 3.16},
                                   {"name": "Rayo Vallecano", "price": 2.5}]}]},
        {"key": "pinnacle", "title": "Pinnacle", "last_update": "2026-10-19T12:45:00Z",
         "markets": [{"key": "h2h", "last_update": "2026-10-19T12:45:00Z",
                      "outcomes": [{"name": "Getafe", "price": 3.0}]}]},
    ],
}


def test_flatten_keeps_bookmaker_link_when_present():
    df = json_to_pandas_the_odds_api_get_odds([EVENT])
    assert len(df) == 4
    assert df.loc[df["bookmaker_key"] == "onexbet", "bookmaker_link"].str.startswith("https://1xbet.com/").all()
    assert df.loc[df["bookmaker_key"] == "pinnacle", "bookmaker_link"].isna().all()
