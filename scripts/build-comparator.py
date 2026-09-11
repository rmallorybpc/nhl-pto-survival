"""
Build the matched comparator and compute the survival differential.

For each convert, pull K comparators: players who made the same season's
opening rosters WITHOUT a tryout, matched on position exactly and age
nearest. Prior NHL games played breaks ties among players already close
in age.

Matching is deliberately simple. Age carries the weight because it captures
career stage, which is what the study is about. A 35-year-old fourth-liner
and a 35-year-old convert are comparable regardless of where either played
the previous season.

Reads  data/outcomes.csv
Writes data/pool-<season>.json   (cache, slow first run only)
       data/comparators.csv
       data/differential.txt

Run in stages. Stage two caches the pools and is the slow part.
"""

import csv
import json
import os
import time
import unicodedata
import requests

SOURCE = "data/outcomes.csv"
POOL = "data/pool-{}.json"
OUT = "data/comparators.csv"
REPORT = "data/differential.txt"

K = 3                 # comparators per convert
MAX_AGE_GAP = 3       # years; wider than this is not a match

SEASON_ID = {
    "2018-19": "20182019", "2019-20": "20192020", "2020-21": "20202021",
    "2021-22": "20212022", "2022-23": "20222023", "2023-24": "20232024",
    "2024-25": "20242025", "2025-26": "20252026",
}
NEXT_SEASON = {
    "2018-19": "2019-20", "2019-20": "2020-21", "2020-21": "2021-22",
    "2021-22": "2022-23", "2022-23": "2023-24", "2023-24": "2024-25",
    "2024-25": "2025-26",
}
BASE = ["ANA","BOS","BUF","CGY","CAR","CHI","COL","CBJ","DAL","DET","EDM",
        "FLA","LAK","MIN","MTL","NSH","NJD","NYI","NYR","OTT","PHI","PIT",
        "SJS","STL","TBL","TOR","VAN","VGK","WSH","WPG"]
TEAMS = {
    "2018-19": BASE + ["ARI"], "2019-20": BASE + ["ARI"],
    "2020-21": BASE + ["ARI"], "2021-22": BASE + ["ARI","SEA"],
    "2022-23": BASE + ["ARI","SEA"], "2023-24": BASE + ["ARI","SEA"],
    "2024-25": BASE + ["UTA","SEA"], "2025-26": BASE + ["UTA","SEA"],
}
POS_GROUP = {"C":"F","LW":"F","RW":"F","L":"F","R":"F","F":"F","D":"D","G":"G"}


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


def get(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def tenth_game(team, sid):
    games = [g for g in get(f"https://api-web.nhle.com/v1/club-schedule-season/{team}/{sid}")
             .get("games", []) if g.get("gameType") == 2]
    games.sort(key=lambda g: g["gameDate"])
    if not games:
        return None
    return games[9]["gameDate"] if len(games) >= 10 else games[-1]["gameDate"]


def club_players(team, sid):
    """[(key, playerId, pos, gp)] for everyone who appeared for the club."""
    data = get(f"https://api-web.nhle.com/v1/club-stats/{team}/{sid}/2")
    out = []
    for group, pos in (("skaters", None), ("goalies", "G")):
        for p in data.get(group, []):
            first = p.get("firstName", {}).get("default", "")
            last = p.get("lastName", {}).get("default", "")
            pid = p.get("playerId")
            if not (last and pid):
                continue
            pp = pos or p.get("positionCode", "")
            out.append(((norm(last), norm(first)[:1]), pid, pp,
                        p.get("gamesPlayed", 0)))
    return out


def first_appearance(pid, sid, team):
    log = get(f"https://api-web.nhle.com/v1/player/{pid}/game-log/{sid}/2")
    dates = [g["gameDate"] for g in log.get("gameLog", [])
             if g.get("teamAbbrev") == team]
    return min(dates) if dates else None


def player_age(pid, season):
    """Age at the start of the season, from the player landing endpoint."""
    try:
        d = get(f"https://api-web.nhle.com/v1/player/{pid}/landing")
        dob = d.get("birthDate")
        if not dob:
            return None
        return int(season[:4]) - int(dob[:4])
    except Exception:
        return None


# ---------------------------------------------------------------
# STAGE 1. One club, one season. Confirm the fields come back.
# ---------------------------------------------------------------
def stage_one():
    rows = club_players("NYR", "20222023")
    print(f"NYR 2022-23: {len(rows)} players")
    for key, pid, pos, gp in rows[:5]:
        print(f"  {key}  id={pid}  pos={pos}  gp={gp}")
    pid = rows[0][1]
    print("age of first player:", player_age(pid, "2022-23"))
    print("tenth game:", tenth_game("NYR", "20222023"))


# ---------------------------------------------------------------
# STAGE 2. Cache the pool for every season we need. SLOW.
# Safe to stop and restart: finished seasons are skipped.
# ---------------------------------------------------------------
def build_pool(season):
    path = POOL.format(season)
    if os.path.exists(path):
        print(f"{season}: cached")
        return json.load(open(path))

    sid = SEASON_ID[season]
    pool = []
    for team in TEAMS[season]:
        try:
            cutoff = tenth_game(team, sid)
            players = club_players(team, sid)
        except Exception as e:
            print(f"  FAILED {team}: {e}")
            continue
        time.sleep(0.3)
        for key, pid, pos, gp in players:
            try:
                first = first_appearance(pid, sid, team)
            except Exception:
                continue
            if not (first and cutoff and first <= cutoff):
                continue
            pool.append({"key": list(key), "id": pid, "team": team,
                         "pos": pos, "gp": gp,
                         "age": player_age(pid, season)})
            time.sleep(0.2)
        print(f"  {team}: pool {len(pool)}")

    json.dump(pool, open(path, "w"))
    print(f"{season}: {len(pool)} players cached")
    return pool


def stage_two():
    with open(SOURCE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    live = [r for r in rows if r.get("made_roster") == "yes"]
    needed = sorted({r["season"] for r in live} |
                    {NEXT_SEASON[r["season"]] for r in live})
    for s in needed:
        print(f"\n=== {s} ===")
        build_pool(s)


# ---------------------------------------------------------------
# STAGE 3. Match, resolve comparator outcomes, report.
# ---------------------------------------------------------------
def stage_three():
    with open(SOURCE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    live = [r for r in rows if r.get("made_roster") == "yes"]

    pools = {}
    for s in sorted({r["season"] for r in live} |
                    {NEXT_SEASON[r["season"]] for r in live}):
        pools[s] = build_pool(s)

    # Exclude every convert from every pool so they cannot match each other.
    convert_keys = set()
    for r in live:
        convert_keys |= player_key(r["player"])

    # Index of who appeared in the following season, for outcomes.
    next_index = {}
    for s, pool in pools.items():
        idx = {}
        for p in pool:
            idx.setdefault(tuple(p["key"]), set()).add(p["team"])
        next_index[s] = idx

    matched = []
    used = set()
    for r in live:
        season = r["season"]
        want_pos = POS_GROUP.get(r["position"], r["position"])
        try:
            want_age = int(r["sign_age"])
        except (ValueError, KeyError):
            want_age = None

        cands = []
        for p in pools[season]:
            k = tuple(p["key"])
            if k in convert_keys or (season, k) in used:
                continue
            if POS_GROUP.get(p["pos"], p["pos"]) != want_pos:
                continue
            if want_age is None or p["age"] is None:
                continue
            gap = abs(p["age"] - want_age)
            if gap > MAX_AGE_GAP:
                continue
            cands.append((gap, -p["gp"], p))

        cands.sort(key=lambda c: (c[0], c[1]))
        for _, _, p in cands[:K]:
            used.add((season, tuple(p["key"])))
            nxt = NEXT_SEASON[season]
            clubs = next_index.get(nxt, {}).get(tuple(p["key"]), set())
            if not clubs:
                state, survived = "out", "no"
            elif p["team"] in clubs:
                state, survived = "same_team", "yes"
            else:
                state, survived = "moved", "yes"
            matched.append({
                "season": season, "convert": r["player"],
                "convert_survived": r["survived"],
                "comparator_key": " ".join(p["key"]),
                "comparator_team": p["team"], "pos": p["pos"],
                "age": p["age"], "age_gap": abs(p["age"] - want_age),
                "prior_gp": p["gp"], "one_year_state": state,
                "survived": survived,
            })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(matched[0].keys()))
        w.writeheader()
        w.writerows(matched)

    n_c = len(live)
    s_c = sum(1 for r in live if r["survived"] == "yes")
    n_m = len(matched)
    s_m = sum(1 for m in matched if m["survived"] == "yes")

    def ci(s, n):
        if not n:
            return (0.0, 0.0, 0.0)
        p = s / n
        se = (p * (1 - p) / n) ** 0.5
        return (100 * p, 100 * max(0, p - 1.96 * se), 100 * min(1, p + 1.96 * se))

    pc, lc, hc = ci(s_c, n_c)
    pm, lm, hm = ci(s_m, n_m)
    diff = pc - pm
    se_d = ((s_c/n_c*(1-s_c/n_c)/n_c) + (s_m/n_m*(1-s_m/n_m)/n_m)) ** 0.5 * 100
    lo, hi = diff - 1.96 * se_d, diff + 1.96 * se_d

    lines = [
        "NHL PTO convert survival: one-year differential",
        "",
        f"Converts:    {s_c}/{n_c} survived = {pc:.1f}%  (95% CI {lc:.1f} to {hc:.1f})",
        f"Comparators: {s_m}/{n_m} survived = {pm:.1f}%  (95% CI {lm:.1f} to {hm:.1f})",
        "",
        f"Differential: {diff:+.1f} points  (95% CI {lo:+.1f} to {hi:+.1f})",
        "",
        "Crosses zero: " + ("YES - null result" if lo <= 0 <= hi else "no"),
        "",
        f"Matching: position group exact, age nearest within {MAX_AGE_GAP} years,",
        f"K={K} comparators per convert, prior games played as tiebreaker.",
        "Survival = appeared in a club's first ten games the following season.",
    ]
    report = "\n".join(lines)
    open(REPORT, "w").write(report)
    print("\n" + report)


if __name__ == "__main__":
    stage_three()
