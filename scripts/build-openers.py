"""
Build per-team opening-night dates for the six signature seasons.

Run in stages. Do not run the whole file until Stage 1 returns 200.
Output: data/openers.csv with season, team, opener_date.
"""

import csv
import time
import requests

# Team codes vary by season.
# Seattle joined in 2021-22. Arizona became Utah in 2024-25.
BASE = [
    "ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL", "DET",
    "EDM", "FLA", "LAK", "MIN", "MTL", "NSH", "NJD", "NYI", "NYR", "OTT",
    "PHI", "PIT", "SJS", "STL", "TBL", "TOR", "VAN", "VGK", "WSH", "WPG",
]

SEASONS = {
    "20182019": BASE + ["ARI"],
    "20192020": BASE + ["ARI"],
    "20202021": BASE + ["ARI"],
    "20212022": BASE + ["ARI", "SEA"],
    "20212022_label": None,
    "20222023": BASE + ["ARI", "SEA"],
    "20232024": BASE + ["ARI", "SEA"],
    "20242025": BASE + ["UTA", "SEA"],
}
SEASONS.pop("20212022_label")

LABEL = {
    "20182019": "2018-19",
    "20192020": "2019-20",
    "20202021": "2020-21",
    "20212022": "2021-22",
    "20222023": "2022-23",
    "20232024": "2023-24",
    "20242025": "2024-25",
}


def fetch_schedule(team, season):
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{season}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def first_regular_game(payload):
    """Return the date of the team's first regular-season game.

    gameType 2 is regular season. gameType 1 is preseason.
    Games come back in date order, but sort anyway rather than trusting it.
    """
    games = [g for g in payload.get("games", []) if g.get("gameType") == 2]
    if not games:
        return None
    games.sort(key=lambda g: g["gameDate"])
    return games[0]["gameDate"]


# ---------------------------------------------------------------
# STAGE 1. Test one team, one season. Run this alone first.
# ---------------------------------------------------------------
def stage_one():
    payload = fetch_schedule("TOR", "20222023")
    print("keys:", list(payload.keys()))
    print("game count:", len(payload.get("games", [])))
    print("first regular-season game:", first_regular_game(payload))


# ---------------------------------------------------------------
# STAGE 2. One full season. Check the spread looks sane.
# ---------------------------------------------------------------
def stage_two(season="20222023"):
    for team in SEASONS[season]:
        try:
            date = first_regular_game(fetch_schedule(team, season))
            print(team, date)
        except Exception as e:
            print(team, "FAILED", e)
        time.sleep(0.3)


# ---------------------------------------------------------------
# STAGE 3. All six seasons to CSV.
# ---------------------------------------------------------------
def stage_three(path="data/openers.csv"):
    rows = []
    for season, teams in SEASONS.items():
        for team in teams:
            try:
                date = first_regular_game(fetch_schedule(team, season))
                rows.append([LABEL[season], team, date or "MISSING"])
            except Exception as e:
                rows.append([LABEL[season], team, f"FAILED {e}"])
            time.sleep(0.3)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["season", "team", "opener_date"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {path}")


if __name__ == "__main__":
    stage_three()
