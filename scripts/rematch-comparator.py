"""
Rebuild the matching using PRIOR-season games played as a constraint.

Replaces the original stage_three. Two errors are fixed:

1. The old tiebreaker sorted by -gp, which deliberately selected the
   highest-games-played player at each age. Comparators came out with a
   median of 82 games. Every one was a full-time regular.

2. That gp was games played DURING the matched season, which is an
   outcome, not a covariate. Matching on it was circular: it selected
   players who went on to play a full season, then found they survived.

The fix uses games played in the season BEFORE, for both groups, and
treats it as a hard band rather than a tiebreaker.

Reads  data/outcomes.csv and the cached data/pool-<season>.json files
Writes data/comparators-v2.csv and data/differential-v2.txt

Needs one extra cached season: the one before the earliest cohort.
Run stage_prior() first if data/pool-2017-18.json is missing.
"""

import csv
import json
import os
import statistics
import unicodedata

SOURCE = "data/outcomes.csv"
POOL = "data/pool-{}.json"
OUT = "data/comparators-v2.csv"
REPORT = "data/differential-v2.txt"

K = 3
MAX_AGE_GAP = 2
GP_BAND = 15          # prior-season games played must be within this many

PREV_SEASON = {
    "2018-19": "2017-18", "2019-20": "2018-19", "2020-21": "2019-20",
    "2021-22": "2020-21", "2022-23": "2021-22", "2023-24": "2022-23",
    "2024-25": "2023-24",
}
NEXT_SEASON = {
    "2018-19": "2019-20", "2019-20": "2020-21", "2020-21": "2021-22",
    "2021-22": "2022-23", "2022-23": "2023-24", "2023-24": "2024-25",
    "2024-25": "2025-26",
}
POS_GROUP = {"C": "F", "LW": "F", "RW": "F", "L": "F", "R": "F", "F": "F",
             "D": "D", "G": "G"}


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


def load_pool(season):
    path = POOL.format(season)
    if not os.path.exists(path):
        return None
    return json.load(open(path))


def prior_gp_map(season):
    """(last, initial) -> games played in that season. 0 if absent."""
    pool = load_pool(season)
    if pool is None:
        return None
    return {tuple(p["key"]): p["gp"] for p in pool}


def main(K=K, MAX_AGE_GAP=MAX_AGE_GAP, GP_BAND=GP_BAND, quiet=False):
    with open(SOURCE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    live = [r for r in rows if r.get("made_roster") == "yes"]

    seasons = sorted({r["season"] for r in live})
    pools, priors, nexts = {}, {}, {}
    missing = []

    for s in seasons:
        pools[s] = load_pool(s)
        prev = PREV_SEASON[s]
        priors[s] = prior_gp_map(prev)
        if priors[s] is None:
            missing.append(prev)
        nxt = NEXT_SEASON[s]
        pool_next = load_pool(nxt)
        idx = {}
        if pool_next:
            for p in pool_next:
                idx.setdefault(tuple(p["key"]), set()).add(p["team"])
        nexts[s] = idx

    if missing:
        print("MISSING cached pools for:", sorted(set(missing)))
        print("Cohorts using those seasons cannot be matched on prior GP.")
        print("Build them with build-comparator.py stage_two, or accept")
        print("that those converts drop out of the differential.\n")

    convert_keys = set()
    for r in live:
        convert_keys |= player_key(r["player"])

    matched, unmatched = [], []
    used = set()

    for r in live:
        season = r["season"]
        prior = priors.get(season)
        if prior is None:
            unmatched.append((r, "no prior-season pool"))
            continue

        # Convert's own prior-season games played. 0 means AHL/Europe/gap.
        c_gp = 0
        for k in player_key(r["player"]):
            if k in prior:
                c_gp = max(c_gp, prior[k])

        want_pos = POS_GROUP.get(r["position"], r["position"])
        try:
            want_age = int(r["sign_age"])
        except (ValueError, KeyError):
            unmatched.append((r, "no age"))
            continue

        cands = []
        for p in pools[season] or []:
            k = tuple(p["key"])
            if k in convert_keys or (season, k) in used:
                continue
            if POS_GROUP.get(p["pos"], p["pos"]) != want_pos:
                continue
            if p["age"] is None:
                continue
            age_gap = abs(p["age"] - want_age)
            if age_gap > MAX_AGE_GAP:
                continue
            p_gp = prior.get(k, 0)
            gp_gap = abs(p_gp - c_gp)
            if gp_gap > GP_BAND:
                continue
            cands.append((gp_gap, age_gap, p_gp, p))

        cands.sort(key=lambda c: (c[0], c[1]))
        if not cands:
            unmatched.append((r, f"no match at prior GP {c_gp}"))
            continue

        for gp_gap, age_gap, p_gp, p in cands[:K]:
            used.add((season, tuple(p["key"])))
            clubs = nexts[season].get(tuple(p["key"]), set())
            if not clubs:
                state, survived = "out", "no"
            elif p["team"] in clubs:
                state, survived = "same_team", "yes"
            else:
                state, survived = "moved", "yes"
            matched.append({
                "season": season, "convert": r["player"],
                "convert_prior_gp": c_gp,
                "convert_survived": r["survived"],
                "comparator_key": " ".join(p["key"]),
                "comparator_team": p["team"], "pos": p["pos"],
                "age": p["age"], "age_gap": age_gap,
                "comparator_prior_gp": p_gp, "gp_gap": gp_gap,
                "one_year_state": state, "survived": survived,
            })

    if not matched:
        print("No matches. Check that the prior-season pools exist.")
        return

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(matched[0].keys()))
        w.writeheader()
        w.writerows(matched)

    # Only converts that actually found comparators enter the differential.
    used_converts = {(m["season"], m["convert"]) for m in matched}
    live_m = [r for r in live if (r["season"], r["player"]) in used_converts]

    n_c = len(live_m)
    s_c = sum(1 for r in live_m if r["survived"] == "yes")
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
    se_d = ((s_c / n_c * (1 - s_c / n_c) / n_c) +
            (s_m / n_m * (1 - s_m / n_m) / n_m)) ** 0.5 * 100
    lo, hi = diff - 1.96 * se_d, diff + 1.96 * se_d

    cgp = [m["convert_prior_gp"] for m in matched]
    mgp = [m["comparator_prior_gp"] for m in matched]

    lines = [
        "NHL PTO convert survival: one-year differential (v2)",
        "",
        "Matched on prior-season NHL games played, not current season.",
        f"  convert prior GP    mean {statistics.mean(cgp):.1f}  median {statistics.median(cgp)}",
        f"  comparator prior GP mean {statistics.mean(mgp):.1f}  median {statistics.median(mgp)}",
        "",
        f"Converts:    {s_c}/{n_c} survived = {pc:.1f}%  (95% CI {lc:.1f} to {hc:.1f})",
        f"Comparators: {s_m}/{n_m} survived = {pm:.1f}%  (95% CI {lm:.1f} to {hm:.1f})",
        "",
        f"Differential: {diff:+.1f} points  (95% CI {lo:+.1f} to {hi:+.1f})",
        "",
        "Crosses zero: " + ("YES - null result" if lo <= 0 <= hi else "no"),
        "",
        f"Converts matched: {n_c} of {len(live)}",
        f"Converts dropped: {len(unmatched)}",
    ]
    for r, why in unmatched:
        lines.append(f"  {r['season']} {r['player']}: {why}")
    lines += [
        "",
        f"Matching: position group exact, age within {MAX_AGE_GAP}, prior-season",
        f"games played within {GP_BAND}, K={K} per convert.",
        "Survival = appeared in a club's first ten games the following season.",
    ]
    report = "\n".join(lines)
    if not quiet:
        open(REPORT, "w").write(report)
        print(report)
    return {"k": K, "age": MAX_AGE_GAP, "gp": GP_BAND,
            "n_c": n_c, "s_c": s_c, "n_m": n_m, "s_m": s_m,
            "pc": pc, "pm": pm, "diff": diff, "lo": lo, "hi": hi,
            "dropped": len(unmatched), "n_live": len(live)}


if __name__ == "__main__":
    main()
