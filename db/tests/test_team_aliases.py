import json
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "scripts"
# Odds-side teams from leagues FBref does not cover (no join expected).
NOT_ON_FBREF = {
    "AGF Aarhus", "Alanyaspor", "Atlético Tucumán", "Belgrano", "Tigre", "Ceará", "Central Córdoba", "CRB",
    "Corinthians", "Erzgebirge Aue", "Goiás", "Göztepe", "Grêmio", "Instituto", "Lanús", "Platense",
    "Radomiak Radom", "Vélez Sarsfield", "Víkingur Reykjavík",
}


def test_every_odds_team_joins_an_fbref_team():
    fbref = set(json.loads((SCRIPTS / "teams_fbref_to_canonical.json").read_text()).values())
    odds = set(json.loads((SCRIPTS / "teams_theoddsapi_to_canonical.json").read_text()).values())
    assert sorted(odds - fbref - NOT_ON_FBREF) == []
