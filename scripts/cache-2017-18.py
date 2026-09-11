"""
Cache the 2017-18 pool.

The 2018-19 cohort needs prior-season games played from 2017-18, and that
pool was never built. Without it Sbisa, Chiasson and Stafford drop out of
the differential entirely.

Standalone rather than a change to build-comparator.py, because 2017-18 is
only ever needed as a prior season. It is never a cohort season and never a
following season, so it does not belong in that script's season maps.

Writes data/pool-2017-18.json in the same format as the other pools.

Slow: 31 clubs, roughly 750 players, a game log and an age lookup each.
Expect around an hour. Safe to stop and restart - it writes only at the end,
so a stopped run loses its progress, but the file is checked on entry.
"""

import json
import os
import time
import unicodedata
import requests

SEASON = "2017-18"
SEASON_ID = "20172018"
PATH = f"data/pool-{SEASON}.json"

# Vegas existed in 2017-18. Seattle did not. Arizona, not Utah.
TEAMS = [
    "ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL", "DET",
    "EDM", "FLA", "LAK", "MIN", "MTL", "NSH", "NJD", "NYI", "NYR", "OTT",
    "PHI", "PIT", "SJS", "STL", "TBL", "TOR", "VAN", "VGK", "WSH", "WPG",
    "ARI",
]


def norm(name):
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower()
    for ch in ".'-`":
        n = n.replace(ch, "")
    return " ".join(n.split())


def get(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def tenth_game(team):
    games = [g for g in get(
        f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{SEASON_ID}")
        .get("games", []) if g.get("gameType") == 2]
    games.sort(key=lambda g: g["gameDate"])
    if not games:
        return None
    return games[9]["gameDate"] if len(games) >= 10 else games[-1]["gameDate"]


def club_players(team):
    data = get(f"https://api-web.nhle.com/v1/club-stats/{team}/{SEASON_ID}/2")
    out = []
    for group, pos in (("skaters", None), ("goalies", "G")):
        for p in data.get(group, []):
            first = p.get("firstName", {}).get("default", "")
            last = p.get("lastName", {}).get("default", "")
            pid = p.get("playerId")
            if not (last and pid):
                continue
            out.append(((norm(last), norm(first)[:1]), pid,
                        pos or p.get("positionCode", ""),
                        p.get("gamesPlayed", 0)))
    return out


def first_appearance(pid, team):
    log = get(f"https://api-web.nhle.com/v1/player/{pid}/game-log/{SEASON_ID}/2")
    dates = [g["gameDate"] for g in log.get("gameLog", [])
             if g.get("teamAbbrev") == team]
    return min(dates) if dates else None


def player_age(pid):
    try:
        dob = get(f"https://api-web.nhle.com/v1/player/{pid}/landing").get("birthDate")
        return int(SEASON[:4]) - int(dob[:4]) if dob else None
    except Exception:
        return None


# ---------------------------------------------------------------
# STAGE 1. Confirm the API serves 2017-18 at all.
# This is a season earlier than anything used so far.
# ---------------------------------------------------------------
def stage_one():
    print("tenth game TOR:", tenth_game("TOR"))
    rows = club_players("TOR")
    print(f"TOR players: {len(rows)}")
    for key, pid, pos, gp in rows[:3]:
        print(f"  {key}  id={pid}  pos={pos}  gp={gp}")
    if rows:
        pid = rows[0][1]
        print("first appearance:", first_appearance(pid, "TOR"))
        print("age:", player_age(pid))
    print("\nVegas check (expansion season):", tenth_game("VGK"))


# ---------------------------------------------------------------
# STAGE 2. Build and cache. Slow.
# ---------------------------------------------------------------
def stage_two():
    if os.path.exists(PATH):
        print(f"{PATH} already exists. Delete it to rebuild.")
        return

    pool = []
    for team in TEAMS:
        try:
            cutoff = tenth_game(team)
            players = club_players(team)
        except Exception as e:
            print(f"  FAILED {team}: {e}")
            continue
        time.sleep(0.3)
        for key, pid, pos, gp in players:
            try:
                first = first_appearance(pid, team)
            except Exception:
                continue
            if not (first and cutoff and first <= cutoff):
                continue
            pool.append({"key": list(key), "id": pid, "team": team,
                         "pos": pos, "gp": gp, "age": player_age(pid)})
            time.sleep(0.2)
        print(f"  {team}: pool {len(pool)}")

    json.dump(pool, open(PATH, "w"))
    print(f"\n{SEASON}: {len(pool)} players cached to {PATH}")
    print("Now rerun scripts/rematch-comparator.py and scripts/sensitivity.py")


if __name__ == "__main__":
    stage_two()
