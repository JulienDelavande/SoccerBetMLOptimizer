def get_all_seasons_string(first_season, last_season, step=1, skip_seasons=None):
    """
    Returns a string representation of all seasons from first_season to last_season.
    first_season 9798, last_season 1819, skip_season 1516
    8596, 9697, 9798, 9899, 9900, 0001, 0102, 0203, 0304, 0405, 0506, 0607, 0708, 0809, 0910, 1011, 1112, 1213, 1314, 1415, 1516, 1617, 1718, 1819
    """
    seasons = []
    season_year1, season_year2 = str(first_season)[:2], str(first_season)[2:]
    last_season_year1, _ = str(last_season)[:2], str(last_season)[2:]
    while (season_year1 != last_season_year1):
        if skip_seasons and f"{season_year1}{season_year2}" in skip_seasons:
            pass
        else:
            seasons.append(f"{season_year1}{season_year2}")
        season_year2 = str((int(season_year2) + step)%100).zfill(2)
        season_year1 = str((int(season_year1) + step)%100).zfill(2)
    if skip_seasons and f"{season_year1}{season_year2}" in skip_seasons:
        pass
    else:
        seasons.append(f"{season_year1}{season_year2}")
    return seasons