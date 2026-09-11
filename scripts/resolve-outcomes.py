"""
Resolve the one-year outcome for each convert.

The one-year mark is opening night of the following season. A player counts
as surviving if he appeared for any NHL club in that club's first ten games
of the following season. Same ten-game rule as the roster test, so the two
ends of the study are measured the same way.

Reads  data/candidates-final.csv and data/openers.csv
Writes data/outcomes.csv

Adds three columns:
  one_year_state  same_team | moved | out | NO_FOLLOWING_SEASON
  one_year_team   club he appeared for, blank when out
  survived        yes | no

Only rows with made_roster == yes are resolved. Everything else is carried
through untouched, because a player who never made the roster has no
one-year outcome to measure.

Run in stages. Stage three takes a few minutes: 32 clubs per season.
"""

import csv
import time
import unicodedata
import requests

SOURCE = "data/candidates-final.csv"
OUT = "data/outcomes.csv"

SEASON_ID = {
    "2018-19": "20182019",
    "2019-20": "20192020",
    "2020-21": "20202021",
    "2021-22": "20212022",
    "2022-23": "20222023",
    "2023-24": "20232024",
    "2024-25": "20242025",
    "2025-26": "20252026",
}

# The season each cohort is measured against.
NEXT_SEASON = {
    "2018-19": "2019-20",
    "2019-20": "2020-21",
    "2020-21": "2021-22",
    "2021-22": "2022-23",
    "2022-23": "2023-24",
    "2023-24": "2024-25",
    "2024-25": "2025-26",
}

BASE = [
    "ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL", "DET",
    "EDM", "FLA", "LAK", "MIN", "MTL", "NSH", "NJD", "NYI", "NYR", "OTT",
    "PHI", "PIT", "SJS", "STL", "TBL", "TOR", "VAN", "VGK", "WSH", "WPG",
]

TEAMS = {
    "2019-20": BASE + ["ARI"],
    "2020-21": BASE + ["ARI"],
    "2021-22": BASE + ["ARI", "SEA"],
    "2022-23": BASE + ["ARI", "SEA"],
    "2023-24": BASE + ["ARI", "SEA"],
    "2024-25": BASE + ["UTA", "SEA"],
    "2025-26": BASE + ["UTA", "SEA"],
}


def norm(name):
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower()
    for ch in ".'-`":
        n = n.replace(ch, "")
    return " ".join(n.split())


def player_key(full_name):
    parts = norm(full_name).split()
    if len(parts) < 2:
        return {(norm(full_name), "")}
    initial = parts[0][:1]
    keys = {(parts[-1], initial)}
    if len(parts) >= 3:
        keys.add((" ".join(parts[-2:]), initial))
    return keys


def fetch_club_stats(team, season_id):
    url = f"https://api-web.nhle.com/v1/club-stats/{team}/{season_id}/2"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def club_player_ids(payload):
    out = {}
    for group in ("skaters", "goalies"):
        for p in payload.get(group, []):
            first = p.get("firstName", {}).get("default", "")
            last = p.get("lastName", {}).get("default", "")
            pid = p.get("playerId")
            if last and pid:
                out[(norm(last), norm(first)[:1])] = pid
    return out


def fetch_tenth_game_date(team, season_id):
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{season_id}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    games = [g for g in r.json().get("games", []) if g.get("gameType") == 2]
    games.sort(key=lambda g: g["gameDate"])
    if not games:
        return None
    return games[9]["gameDate"] if len(games) >= 10 else games[-1]["gameDate"]


def fetch_first_appearance(player_id, season_id, team):
    url = f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season_id}/2"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    dates = [g["gameDate"] for g in r.json().get("gameLog", [])
             if g.get("teamAbbrev") == team]
    return min(dates) if dates else None


# ---------------------------------------------------------------
# STAGE 1. One known case end to end.
# Jimmy Vesey converted with NYR in 2022-23. Did he survive to 2023-24?
# ---------------------------------------------------------------
def stage_one():
    season_id = SEASON_ID["2023-24"]
    found = []
    for team in TEAMS["2023-24"][:8]:
        ids = club_player_ids(fetch_club_stats(team, season_id))
        if player_key("Jimmy Vesey") & set(ids):
            found.append(team)
        time.sleep(0.3)
    print("sampled 8 clubs, vesey found on:", found or "none of the sample")
    print("(NYR is not in the first 8 - this only proves the calls work)")


# ---------------------------------------------------------------
# STAGE 2. Build the league index for ONE following season.
# Check the size looks right before doing all seven.
# ---------------------------------------------------------------
def build_index(season):
    """(last, initial) -> set of clubs he appeared for in first 10 games."""
    season_id = SEASON_ID[season]
    index = {}
    for team in TEAMS[season]:
        try:
            cutoff = fetch_tenth_game_date(team, season_id)
            ids = club_player_ids(fetch_club_stats(team, season_id))
        except Exception as e:
            print(f"  FAILED {team} {season}: {e}")
            time.sleep(0.3)
            continue
        time.sleep(0.3)

        for key, pid in ids.items():
            try:
                first = fetch_first_appearance(pid, season_id, team)
            except Exception:
                continue
            if first and cutoff and first <= cutoff:
                index.setdefault(key, set()).add(team)
        print(f"  {team} indexed")
    return index


def stage_two(season="2023-24"):
    print(f"building index for {season}...")
    idx = build_index(season)
    print(f"\n{len(idx)} players appeared in a club's first ten games")
    hit = player_key("Jimmy Vesey") & set(idx)
    for k in hit:
        print("vesey:", idx[k])
    return idx


# ---------------------------------------------------------------
# STAGE 3. All cohorts. Writes the output file.
# ---------------------------------------------------------------
def stage_three():
    with open(SOURCE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    seasons = sorted({NEXT_SEASON[r["season"]] for r in rows
                      if r.get("made_roster") == "yes"})
    indexes = {}
    for s in seasons:
        print(f"\n=== indexing {s} ===")
        indexes[s] = build_index(s)

    for r in rows:
        if r.get("made_roster") != "yes":
            r["one_year_state"] = ""
            r["one_year_team"] = ""
            r["survived"] = ""
            continue

        nxt = NEXT_SEASON[r["season"]]
        idx = indexes.get(nxt)
        if idx is None:
            r["one_year_state"] = "NO_FOLLOWING_SEASON"
            r["one_year_team"] = ""
            r["survived"] = ""
            continue

        clubs = set()
        for k in player_key(r["player"]):
            clubs |= idx.get(k, set())

        if not clubs:
            r["one_year_state"] = "out"
            r["one_year_team"] = ""
            r["survived"] = "no"
        elif r["sign_team"] in clubs:
            r["one_year_state"] = "same_team"
            r["one_year_team"] = r["sign_team"]
            r["survived"] = "yes"
        else:
            r["one_year_state"] = "moved"
            r["one_year_team"] = "/".join(sorted(clubs))
            r["survived"] = "yes"

    fields = list(rows[0].keys())
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    live = [r for r in rows if r.get("made_roster") == "yes"]
    same = sum(1 for r in live if r["one_year_state"] == "same_team")
    moved = sum(1 for r in live if r["one_year_state"] == "moved")
    out = sum(1 for r in live if r["one_year_state"] == "out")
    surv = same + moved
    print(f"\nwrote {len(rows)} rows to {OUT}")
    print(f"\nconverts resolved: {len(live)}")
    print(f"  same team: {same}")
    print(f"  moved:     {moved}")
    print(f"  out:       {out}")
    if live:
        print(f"\none-year survival: {surv}/{len(live)} = {100*surv/len(live):.1f}%")

    print("\nBY COHORT")
    for s in sorted({r["season"] for r in live}):
        c = [r for r in live if r["season"] == s]
        sv = sum(1 for r in c if r["survived"] == "yes")
        print(f"  {s}: {sv}/{len(c)}")


if __name__ == "__main__":
    stage_three()
