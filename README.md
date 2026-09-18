# NHL PTO convert survival

Players who make an NHL roster on a professional tryout survive one year at
**48.8 percent**, against **68.8 percent** for comparable players who made the
same rosters without one. A gap of **19.9 points**, stable across nine matching
specifications.

**Site: https://rmallorybpc.github.io/nhl-pto-survival/**

Findings, full methods, and a hostile audit of the study are there. This
repository holds the dataset and the scripts that built it.

## What this is

Every September a few veterans arrive at an NHL training camp with no contract.
A professional tryout buys them practice time and preseason games, nothing more.
Some earn a deal and make the roster.

This study follows 43 of them across seven seasons, 2018-19 through 2024-25, and
asks whether they are still in the league a year later. Each convert is matched
to three players who made the same season's opening rosters without a tryout, at
the same position, within two years of age, and within 15 games of the same
prior-season playing time.

Treat 43 as a lower bound rather than a census. Several annual tryout lists cover
notable players only, so an unlisted tryout cannot be ruled out.

### Why it had to be rebuilt

CapFriendly held the most complete public record of NHL tryouts. It was bought by
the Washington Capitals and taken offline in July 2024, and nothing replaced it
retroactively.

So the population was generated from contract timing instead, then verified season
by season against published tryout coverage. A player cannot appear in an NHL game
without a contract on file, so every convert has a signing date inside the camp
window. That generates candidates. It does not identify converts, because late
paperwork filing and eve-of-camp signings produce the same date pattern. Only a
tryout source separates them.

## Results

| Measure | Value |
| --- | --- |
| Convert one-year survival | 21 of 43, 48.8 percent (95% CI 33.9 to 63.8) |
| Comparator one-year survival | 88 of 128, 68.8 percent (95% CI 60.7 to 76.8) |
| Differential | -19.9 points (95% CI -36.9 to -3.0) |
| Sensitivity, nine matching specifications | -18.5 to -20.9, none crossing zero |
| Sensitivity, two unresolved converts excluded | -19.6 to -20.4, none crossing zero |
| Still with the signing club after one year | 6 of 43 |
| Non-survivors back on a tryout the next season | 4 of 22, treat as a floor |

## The dataset

`data/outcomes.csv` is the file most people will want. One row per candidate,
carrying the signing club and date, contract level and status, tryout verification
status with its source, whether the player made the roster, and the one-year
outcome.

| File | Contents |
| --- | --- |
| `data/openers.csv` | Per-team opening night dates, seven seasons |
| `data/candidates.csv` | Candidate set with tryout verification filled in |
| `data/candidates-resolved.csv` | Window classification and appearance check |
| `data/candidates-final.csv` | After the ten-game roster test |
| `data/outcomes.csv` | One-year outcomes resolved |
| `data/comparators-v2.csv` | Matched comparator pairs |
| `data/differential-v2.txt` | The headline result |
| `data/sensitivity.txt` | Nine matching specifications |
| `data/sensitivity-unresolved.txt` | Result excluding the two unverified converts |
| `data/pool-*.json` | Cached player pools, one per season |

## Authoritative reference

`definitions-lock-final.md` is the source of truth for every definition, decision
and limitation, including a change log of what was reversed and why. Read it
before drawing conclusions from any file here.

## Run order

Python 3 and `requests`. Everything runs locally against the public NHL API.

```
pip install requests
```

Each script runs in stages. Edit the function call at the bottom of the file to
advance from one stage to the next, and check the output before continuing.

| Step | Script | Writes |
| --- | --- | --- |
| 1 | `scripts/build-openers.py` | `data/openers.csv` |
| 2 | `scripts/resolve-roster.py` | `data/candidates-resolved.csv` |
| 3 | `scripts/tighten-roster-test.py` | `data/candidates-final.csv` |
| 4 | `scripts/resolve-outcomes.py` | `data/outcomes.csv` |
| 5 | `scripts/build-comparator.py` | `data/pool-<season>.json` |
| 6 | `scripts/cache-2017-18.py` | `data/pool-2017-18.json` |
| 7 | `scripts/rematch-comparator.py` | `data/comparators-v2.csv`, `data/differential-v2.txt` |
| 8 | `scripts/sensitivity.py` | `data/sensitivity.txt` |
| 9 | `scripts/sensitivity-unresolved.py` | `data/sensitivity-unresolved.txt` |

Steps 4, 5 and 6 are slow. Step 5 takes roughly an hour and caches each season as
it finishes, so it is safe to stop and restart. Steps 7 through 9 read from that
cache and take seconds, which means the matching parameters can be retuned without
paying for the data again.

`scripts/build-comparator.py` contains an earlier matching specification that was
found to be wrong. It is kept because `rematch-comparator.py` reuses its pool
builder, and because the error is documented rather than hidden. Use
`rematch-comparator.py` for any result.

## Known limitations

- **Camp opening dates are sourced for two seasons of seven.** The rest are
  estimates, and they set the boundary that decides which players are candidates.
  This is the largest unverified input.
- **Completeness cannot be proven.** Several annual tryout lists cover notable
  players only, so an unlisted tryout cannot be ruled out in any season.
- **Two converts have unresolved tryout status.** Ben Hutton and Max McCormick.
  `data/sensitivity-unresolved.txt` shows the result without them, and it holds.
- **Signing dates are registry filing dates, not agreement dates.** Verification
  catches the cases it can reach. It cannot catch a club that filed late and was
  never written about.
- **`sign_team` was derived from the signing general manager field.** A proxy that
  broke once, when Stan Bowman moved from Chicago to Edmonton in July 2024.
  Corrected rows carry an AUDIT note.
- **Cohort-level rates are not findings.** Cohorts run from two to ten players.
  The spread between seasons is noise.
- **2020-21 is structurally different.** A January start, no preseason games, and
  taxi squads. That cohort was hand-assembled and carries its own notes.
- **Sensitivity testing varies the matching, not the population.** Population
  construction carries the larger risk.

## Corrections

Three substantial errors were found and fixed during the build. All are documented
in the change log and on the site.

1. A comparator specification that matched on current-season games played as a
   descending tiebreaker, which selected full-time regulars and produced a
   spurious 47-point differential.
2. Signing clubs derived from a general manager field that broke on a mid-study
   club change.
3. Three verified non-tryouts counted as converts because verification findings
   were never written back to the data file.

A fourth pass audited the published pages themselves and found six wording and
arithmetic errors. Those are listed on the audit page.

## Status

Complete. Analysis finished, site published, dataset released.

Outstanding: source the five estimated camp opening dates, resolve two loose
threads on players already excluded, and re-resolve the 2024-25 cohort once
2025-26 is complete.
