"""
Resolve the roster test for each candidate.

Fills two columns in data/candidates.csv:
  window_class    convert | late      (signed on/before team opener, or after)
  played_for_club yes | no | UNKNOWN  (played >=1 NHL game for the signing club)

Reads  data/candidates.csv and data/openers.csv
Writes data/candidates-resolved.csv

Run in stages. Do not run stage three until stage two looks right.
"""

import csv
import time
import unicodedata
import requests

CANDIDATES = "data/candidates.csv"
OPENERS = "data/openers.csv"
OUT = "data/candidates-resolved.csv"

# season label -> API season id
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
    """Strip accents, punctuation and case so names match across sources."""
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower()
    for ch in ".'-`":
        n = n.replace(ch, "")
    return " ".join(n.split())


def load_openers():
    op = {}
    with open(OPENERS, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            op[(r["season"], r["team"])] = r["opener_date"]
    return op


def fetch_roster(team, season_id):
    """Every player who appeared in a regular-season game for this club.

    gameType 2 is regular season. This is the roster test from the
    definitions lock: played at least one NHL game for the signing club.
    """
    url = f"https://api-web.nhle.com/v1/club-stats/{team}/{season_id}/2"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def roster_names(payload):
    """Return (last_name, first_initial) keys.

    The API uses legal first names (Zachary) where signing sources use
    short forms (Zach). Last name plus initial matches both.
    """
    keys = set()
    for group in ("skaters", "goalies"):
        for p in payload.get(group, []):
            first = p.get("firstName", {}).get("default", "")
            last = p.get("lastName", {}).get("default", "")
            if last:
                keys.add((norm(last), norm(first)[:1]))
    return keys


def player_key(full_name):
    """Turn 'Zach Aston-Reese' into a set of candidate keys.

    Multi-word surnames (Dal Colle, de Haan) mean the surname is not
    always the final word, so return both possibilities.
    """
    parts = norm(full_name).split()
    if len(parts) < 2:
        return {(norm(full_name), "")}
    initial = parts[0][:1]
    keys = {(parts[-1], initial)}
    if len(parts) >= 3:
        keys.add((" ".join(parts[-2:]), initial))
    return keys


def fetch_gamelog(player_id, season_id):
    """Per-game log. gameTypeId 2 is regular season."""
    url = f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season_id}/2"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def stage_diag():
    payload = fetch_roster("TOR", "20222023")
    print("groups:", list(payload.keys()))
    for group in ("skaters", "goalies"):
        print(f"\n--- {group}: {len(payload.get(group, []))} ---")
        for p in payload.get(group, [])[:3]:
            print(repr(p.get("firstName")), repr(p.get("lastName")))
    print("\nsearching for aston:")
    for group in ("skaters", "goalies"):
        for p in payload.get(group, []):
            ln = str(p.get("lastName", ""))
            if "ston" in ln.lower():
                print(" raw:", repr(p.get("firstName")), repr(p.get("lastName")))


# ---------------------------------------------------------------
# STAGE 1. Confirm the roster endpoint and inspect its shape.
# ---------------------------------------------------------------
def stage_one():
    payload = fetch_roster("TOR", "20222023")
    print("groups:", list(payload.keys()))
    names = roster_names(payload)
    print("players who appeared:", len(names))
    print("aston-reese present:", player_key("Zach Aston-Reese") & names)


# ---------------------------------------------------------------
# STAGE 2. Window classification only. No API calls. Fast.
# ---------------------------------------------------------------
def stage_two():
    op = load_openers()
    with open(CANDIDATES, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        key = (r["season"], r["sign_team"])
        opener = op.get(key)
        if not opener:
            r["window_class"] = "NO_OPENER"
            continue
        r["window_class"] = "convert" if r["sign_date"] <= opener else "late"

    for r in rows:
        print(f"{r['season']}  {r['sign_team']}  {r['sign_date']}  "
              f"{r['window_class']:8}  {r['player']}")
    return rows


# ---------------------------------------------------------------
# STAGE 3. Roster lookup per candidate. Writes the output file.
# ---------------------------------------------------------------
def stage_three():
    rows = stage_two()

    cache = {}
    for r in rows:
        season_id = SEASON_ID[r["season"]]
        team = r["sign_team"]
        key = (team, season_id)

        if key not in cache:
            try:
                cache[key] = roster_names(fetch_roster(team, season_id))
            except Exception as e:
                cache[key] = None
                print(f"ROSTER FAILED {team} {season_id}: {e}")
            time.sleep(0.3)

        names = cache[key]
        if names is None:
            r["played_for_club"] = "UNKNOWN"
        else:
            r["played_for_club"] = "yes" if player_key(r["player"]) & names else "no"

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    yes = sum(1 for r in rows if r["played_for_club"] == "yes")
    no = sum(1 for r in rows if r["played_for_club"] == "no")
    unk = sum(1 for r in rows if r["played_for_club"] == "UNKNOWN")
    print(f"\nwrote {len(rows)} rows to {OUT}")
    print(f"on roster: {yes}   not found: {no}   unknown: {unk}")
    print("\nNOT FOUND (check these by hand):")
    for r in rows:
        if r["played_for_club"] != "yes":
            print(f"  {r['season']} {r['sign_team']} {r['player']}")


if __name__ == "__main__":
    stage_three()
