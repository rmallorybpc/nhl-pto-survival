"""
Tighten the roster test to first-five-games.

Reads  data/candidates-resolved.csv and data/openers.csv
Writes data/candidates-final.csv

Adds two columns:
  first_five_cutoff  date of the club's fifth regular-season game
  made_roster        yes | no | UNKNOWN

made_roster is yes when the player's first appearance for the signing club
falls on or before that club's fifth game. This is the proxy for making the
team out of camp. It replaces the looser at-least-one-game test, which
counted March recalls as having made the roster.

Run in stages. Do not run stage three until stage two looks right.
"""

import csv
import time
import unicodedata
import requests

RESOLVED = "data/candidates-resolved.csv"
OUT = "data/candidates-final.csv"

SEASON_ID = {
    "2018-19": "20182019",
    "2019-20": "20192020",
    "2020-21": "20202021",
    "2021-22": "20212022",
    "2022-23": "20222023",
    "2023-24": "20232024",
    "2024-25": "20242025",
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
    """Map (last_name, first_initial) -> playerId for everyone who appeared."""
    out = {}
    for group in ("skaters", "goalies"):
        for p in payload.get(group, []):
            first = p.get("firstName", {}).get("default", "")
            last = p.get("lastName", {}).get("default", "")
            pid = p.get("playerId")
            if last and pid:
                out[(norm(last), norm(first)[:1])] = pid
    return out


def fetch_fifth_game_date(team, season_id):
    """Date of the club's fifth regular-season game."""
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{season_id}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    games = [g for g in r.json().get("games", []) if g.get("gameType") == 2]
    games.sort(key=lambda g: g["gameDate"])
    if len(games) < 5:
        return games[-1]["gameDate"] if games else None
    return games[9]["gameDate"]


def fetch_first_appearance(player_id, season_id, team):
    """Earliest regular-season game date this player played FOR this club."""
    url = f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season_id}/2"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    dates = [g["gameDate"] for g in r.json().get("gameLog", [])
             if g.get("teamAbbrev") == team]
    return min(dates) if dates else None


# ---------------------------------------------------------------
# STAGE 1. Confirm the two new endpoints on one known case.
# Jimmy Vesey, NYR 2022-23. Confirmed convert who made the roster.
# ---------------------------------------------------------------
def stage_one():
    stats = fetch_club_stats("NYR", "20222023")
    ids = club_player_ids(stats)
    pid = None
    for k in player_key("Jimmy Vesey"):
        if k in ids:
            pid = ids[k]
    print("vesey playerId:", pid)

    fifth = fetch_fifth_game_date("NYR", "20222023")
    print("NYR fifth game:", fifth)

    if pid:
        first = fetch_first_appearance(pid, "20222023", "NYR")
        print("vesey first appearance:", first)
        print("made roster:", bool(first and fifth and first <= fifth))


# ---------------------------------------------------------------
# STAGE 2. Fifth-game dates for every team-season in the set.
# No game-log calls. Check the dates look sane before going on.
# ---------------------------------------------------------------
def stage_two():
    with open(RESOLVED, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    pairs = sorted({(r["season"], r["sign_team"]) for r in rows})
    fifth = {}
    for season, team in pairs:
        try:
            d = fetch_fifth_game_date(team, SEASON_ID[season])
        except Exception as e:
            d = None
            print(f"FAILED {team} {season}: {e}")
        fifth[(season, team)] = d
        print(f"{season}  {team}  fifth game {d}")
        time.sleep(0.3)
    return rows, fifth


# ---------------------------------------------------------------
# STAGE 3. Resolve first appearance per candidate. Writes output.
# ---------------------------------------------------------------
def stage_three():
    rows, fifth = stage_two()

    stats_cache = {}
    print("\nresolving appearances...\n")

    for r in rows:
        season, team = r["season"], r["sign_team"]
        season_id = SEASON_ID[season]
        cutoff = fifth.get((season, team))
        r["first_five_cutoff"] = cutoff or ""

        # Players who never appeared for the club already fail.
        if r.get("played_for_club") != "yes":
            r["made_roster"] = "no"
            continue

        key = (team, season_id)
        if key not in stats_cache:
            try:
                stats_cache[key] = club_player_ids(fetch_club_stats(team, season_id))
            except Exception as e:
                stats_cache[key] = None
                print(f"STATS FAILED {team} {season}: {e}")
            time.sleep(0.3)

        ids = stats_cache[key]
        if not ids or not cutoff:
            r["made_roster"] = "UNKNOWN"
            continue

        pid = None
        for k in player_key(r["player"]):
            if k in ids:
                pid = ids[k]
        if not pid:
            r["made_roster"] = "UNKNOWN"
            continue

        try:
            first = fetch_first_appearance(pid, season_id, team)
        except Exception as e:
            print(f"GAMELOG FAILED {r['player']}: {e}")
            r["made_roster"] = "UNKNOWN"
            time.sleep(0.3)
            continue
        time.sleep(0.3)

        if not first:
            r["made_roster"] = "no"
        else:
            r["made_roster"] = "yes" if first <= cutoff else "no"
            if first > cutoff:
                print(f"  TIGHTENED OUT  {season} {team} {r['player']}  "
                      f"first {first} vs cutoff {cutoff}")

    fields = list(rows[0].keys())
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    yes = sum(1 for r in rows if r["made_roster"] == "yes")
    no = sum(1 for r in rows if r["made_roster"] == "no")
    unk = sum(1 for r in rows if r["made_roster"] == "UNKNOWN")
    print(f"\nwrote {len(rows)} rows to {OUT}")
    print(f"made roster: {yes}   did not: {no}   unknown: {unk}")


if __name__ == "__main__":
    stage_three()
