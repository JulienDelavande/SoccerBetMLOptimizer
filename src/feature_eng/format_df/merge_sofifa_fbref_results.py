import pandas as pd
import json
from pathlib import Path

MAPPING_SOFIFA_FBREF = Path(__file__).resolve().parents[0] / 'mapping_sofifa_team_name_to_fbref.json'

def merge_sofifa_fbref_results(fbref_results_df, sofifa_teams_stats_df,
                               MAPPING_SOFIFA_FBREF=MAPPING_SOFIFA_FBREF,
                               team_col='team', update_col='update',
                               home_team_col='home_team', away_team_col='away_team',
                               date_col='date'):
    """
    Merge the fbref results with the sofifa teams stats.

    Parameters
    ----------
    fbref_results_df : pd.DataFrame
        The dataset containing the fbref results.
    sofifa_teams_stats_df : pd.DataFrame
        The dataset containing the sofifa teams stats.
    MAPPING_SOFIFA_FBREF : str (Optional, default=MAPPING_SOFIFA_FBREF)
        The path to the mapping sofifa team name to fbref.
    team_col : str (Optional, default='team')
        The column name of the team.
    update_col : str (Optional, default='update')
        The column name of the update.
    home_team_col : str (Optional, default='home_team')
        The column name of the home team.
    away_team_col : str (Optional, default='away_team')
        The column name of the away team.
    date_col : str (Optional, default='date')
        The column name of the date.

    Returns
    -------
    fbref_df_date_filtered_concat : pd.DataFrame
        The merged dataset.
    """
    
    #mapping = json.load(open(MAPPING_SOFIFA_FBREF))
    mapping = {
    "VfL Bochum 1848": "Bochum",
    "Tottenham Hotspur": "Tottenham",
    "Paris Saint Germain": "Paris S-G",
    "FC Köln": "Köln",
    "Real Zaragoza": "Zaragoza",
    "Wolverhampton Wanderers": "Wolves",
    "Sheffield United": "Sheffield Utd",
    "Amiens SC": "Amiens",
    "FSV Mainz 05": "Mainz 05",
    "Paderborn": "Paderborn 07",
    "Bolton Wanderers": "Bolton",
    "Huddersfield Town": "Huddersfield",
    "Olympique de Marseille": "Marseille",
    "LOSC Lille": "Lille",
    "Grenoble Foot 38": "Grenoble",
    "Racing Santander": "Racing Sant",
    "Eintracht Frankfurt": "Eint Frankfurt",
    "Fortuna Düsseldorf": "Düsseldorf",
    "Queens Park Rangers": "QPR",
    "SC Freiburg": "Freiburg",
    "DSC Arminia Bielefeld": "Arminia",
    "Republic of Ireland": "Rep. of Ireland",
    "Evian TG": "Evian",
    "FC Barcelona": "Barcelona",
    "Brighton & Hove Albion": "Brighton",
    "Deportivo La Coruña": "La Coruña",
    "Angers SCO": "Angers",
    "West Ham United": "West Ham",
    "VfL Wolfsburg": "Wolfsburg",
    "FC Augsburg": "Augsburg",
    "India": "India",
    "Bari 1908": "Bari",
    "Czech Republic": "Czechia",
    "Nottingham Forest": "Nott'ham Forest",
    "Newcastle United": "Newcastle Utd",
    "Borussia Dortmund": "Dortmund",
    "AFC Bournemouth": "Bournemouth",
    "Iran": "IR Iran",
    "Borussia Mönchengladbach": "Gladbach",
    "Olympique Lyonnais": "Lyon",
    "Venezuela": "Venezuela",
    "TSG Hoffenheim": "Hoffenheim",
    "SD Eibar": "Eibar",
    "West Bromwich Albion": "West Brom",
    "VfB Stuttgart": "Stuttgart",
    "Arles": "Arles-Avignon",
    "Stade de Reims": "Reims",
    "Stade Brestois 29": "Brest",
    "Real Valladolid": "Valladolid",
    "Clermont": "Clermont Foot",
    "FC Union Berlin": "Union Berlin",
    "Manchester United": "Manchester Utd",
    "Deportivo Alavés": "Alavés",
    "Celta de Vigo": "Celta Vigo",
    "Bayer 04 Leverkusen": "Leverkusen",
    "FC Bayern München": "Bayern Munich",
    "SpVgg Greuther Fürth": "Greuther Fürth",
    "Ingolstadt": "Ingolstadt 04",
    "Eintracht Braunschweig": "Braunschweig",
    "Blackburn Rovers": "Blackburn"
}


    # Appliquer le mapping au DataFrame sofifa_teams_stats_df
    sofifa_teams_stats_df[team_col] = sofifa_teams_stats_df[team_col].replace(mapping)
                                                                        
    fbref_results_df[date_col] = pd.to_datetime(fbref_results_df[date_col])
    fbref_results_df_date = fbref_results_df[fbref_results_df["date"] >= min(sofifa_teams_stats_df[update_col])]

    # Extraire la liste des équipes du DataFrame sofifa_teams_stats_df
    sofifa_teams = set(sofifa_teams_stats_df[team_col].unique())

    # Filtrer les lignes de fbref_results_df
    fbref_df_date_filtered = fbref_results_df_date[
        (fbref_results_df_date[home_team_col].isin(sofifa_teams)) & 
        (fbref_results_df_date[away_team_col].isin(sofifa_teams))
    ]

    # Assurance que les dates sont correctement formatées
    fbref_df_date_filtered[date_col] = pd.to_datetime(fbref_df_date_filtered[date_col])
    sofifa_teams_stats_df[update_col] = pd.to_datetime(sofifa_teams_stats_df[update_col])

    # Trier les dataframes pour la jointure asynchrone
    fbref_df_date_filtered = fbref_df_date_filtered.sort_values(by=date_col)
    sofifa_teams_stats_df = sofifa_teams_stats_df.sort_values(by=update_col)

    # Effectuer une jointure asynchrone pour les équipes à domicile
    home_stats = pd.merge_asof(
        fbref_df_date_filtered[[home_team_col, date_col]].rename(columns={home_team_col: team_col, date_col: 'match_date'}),
        sofifa_teams_stats_df,
        left_on='match_date',
        right_on=update_col,
        by=team_col,
        direction='backward'
    ).drop(columns=[team_col, 'match_date'])

    # Renommer les colonnes pour éviter les conflits
    home_stats.columns = ['home_' + col for col in home_stats.columns]

    # Effectuer une jointure asynchrone pour les équipes à l'extérieur
    away_stats = pd.merge_asof(
        fbref_df_date_filtered[[away_team_col, date_col]].rename(columns={away_team_col: team_col, date_col: 'match_date'}),
        sofifa_teams_stats_df,
        left_on='match_date',
        right_on=update_col,
        by=team_col,
        direction='backward'
    ).drop(columns=[team_col, 'match_date'])

    # Renommer les colonnes pour éviter les conflits
    away_stats.columns = ['away_' + col for col in away_stats.columns]

    # Fusionner les stats avec le dataframe initial
    fbref_df_date_filtered_concat = pd.concat([fbref_df_date_filtered.reset_index(drop=True), home_stats.reset_index(drop=True), away_stats.reset_index(drop=True)], axis=1)

    return fbref_df_date_filtered_concat