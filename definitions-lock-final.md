# NHL PTO convert survival: definitions lock

Authoritative reference for the study. Read this first. Any change from here
is a decision and gets logged at the bottom.

Status: analysis complete. Writing and the back-on-a-PTO count outstanding.

## The claim

Players who make an NHL roster out of camp on a professional tryout survive in
the league at a lower rate one year later than comparable players who made the
same rosters without a tryout.

## Scope

Seven cohorts: 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25.

2025-26 is excluded. No one-year outcome exists yet.

The 2018-19 boundary is a data-availability limit, not a design choice.
PuckPedia contract season filters do not run earlier. State it that way. The
brief's rough ten-season scope is not available.

## Locked definitions

- Convert: a player who was in an NHL training camp on a professional tryout,
  signed a standard NHL contract with that same club on or before that club's
  opening night, and appeared in at least one of that club's first ten
  regular-season games.
- Same-club rule. A player on a tryout with one club who signs with a different
  club is not a convert. Erik Gustafsson is the worked example: tryout with the
  Islanders in 2021-22, signed with Chicago October 11, excluded. Zach
  Aston-Reese in 2023-24 is the second: tryout with Carolina, signed with
  Detroit, excluded.
- Late signers do not count. A player who signs with the tryout club after that
  club's opening night is not a convert. The study is about making the team out
  of camp.
- Survived: appeared in any NHL club's first ten regular-season games of the
  following season. Both ends of the study use the same ten-game rule, so entry
  and exit are measured identically.
- Moved: survived, but with a different club than the signing club.
- Back on a PTO: in an NHL camp on a tryout the following season. NOT YET
  COUNTED. See outstanding work.

## Why ten games, not five

The roster test was first built at five games. That run excluded three
confirmed tryout converts who were healthy scratches in October: Chiasson, who
then scored 22 goals for Edmonton in 2018-19, Brassard, and Yamamoto. All three
were two or three days past the five-game cutoff.

Ten games recovers all three and still excludes every AHL assignment in the
set. The four clearest removals hold at both thresholds: Letestu first appeared
January 31, Berube February 20, White January 13, Rinaldo November 19.

Report this as a threshold chosen after a first pass showed five was too tight,
not as a natural break in the data. A first look suggested a clean
discontinuity at five games; widening to ten produced new marginal cases at the
new boundary, which means the apparent gap was a property of where the line sat
rather than structure in the data.

## Identification method

Two steps. Neither works alone.

**Step one, the contract-date signature.** Standard-level contracts, UFA or UFA
with no qualifying offer, signed between camp opening and the club's opening
night. Generates candidates.

Near-zero false negatives on the contract requirement, since a player cannot
appear without a contract on file. But the window boundary does produce misses:
Claesson signed four days into camp in 2019 and Makiniemi five days into camp
in 2024, and both were excluded by an earlier twelve-day window. The window was
widened to camp opening for this reason.

**Step two, verification against tryout sources.** Required, not cleanup.

Two distinct false-positive modes make this necessary.

Paperwork timing. PuckPedia's signing date is the NHL central registry filing
date, not the date terms were agreed. Chara agreed September 18, 2021 and
Parise in the summer; both show October 10 because Lamoriello filed on the
roster deadline. Any club that files late produces false positives that are
invisible in the data.

Eve-of-camp signings and re-signings. Schneider, Soshnikov and Ritchie in
2022-23 and Lankinen in 2024-25 all signed within days of camp opening and none
was on a tryout. These are indistinguishable from early conversions without a
tryout source.

Of the six candidates signing within days of camp opening across all seasons,
two were genuine converts and four were ordinary signings. The early edge of
the window is where the method is weakest.

**Sources.** HFBoards annual training-camp threads record tryouts with outcomes
and are the best source found. NHL.com publishes an annual tryout page, curated
to notable players. Pro Hockey Rumors and Daily Faceoff run trackers of varying
quality by year. CapFriendly held the complete database and went dark in July
2024; nothing replaced it retroactively.

## 2020-21 season note

Included. Camps opened December 31 for the seven teams that did not participate
in the 2019-20 Return to Play Plan and January 3 for the remaining 24, with the
regular season starting January 13.

There was a training camp. There were no preseason games. Since a tryout
permits camp and exhibition play only, conversions that season happened on
practice sessions alone, with no games to showcase in.

The contract-date signature does not work for this season. Free agency ran late
into camp and no pre-camp trough exists, so normal signings and camp
conversions are indistinguishable by date. This cohort was hand-assembled from
the NHL.com tryout tracker, which lists fifteen tryouts with their outcomes.
That list is curated to notable players, so completeness is lower for this
season than for the others.

Taxi squads of four to six players were in effect. Taxi squad assignment does
NOT count toward the roster test. The same ten-game rule applies as in every
other cohort. Craig Anderson is the worked example: signed January 13, waived,
assigned to the Washington taxi squad, first appeared February 7, excluded.

## Comparator

For each convert, K comparators drawn from players who appeared in a club's
first ten games that same season without a tryout.

Matched on:
- Position group exact (forward, defence, goaltender)
- Age within 2 years
- Prior-season NHL games played within 15

K = 3. Comparators are used once per season and converts are excluded from
every pool so they cannot match each other.

Prior-season games played is the quality control and it must be a constraint,
not a tiebreaker. A first specification matched on position and age alone with
current-season games played as a tiebreaker. That produced comparators with a
median of 82 games played and a minimum of 51, every one a full-time regular,
and a spurious 47-point differential. Two errors caused it: the tiebreaker
sorted descending, selecting the highest-games-played player at each age, and
the variable was games played during the matched season, which is an outcome
rather than a covariate.

The corrected specification matches on the season before. Convert prior games
played averages 41.0, comparators 41.4, medians 46 and 46. Both groups are
part-time NHLers from the previous year.

## Results

One-year survival, 43 converts across seven cohorts:

- Converts: 21/43 = 48.8% (95% CI 33.9 to 63.8)
- Comparators: 88/128 = 68.8% (95% CI 60.7 to 76.8)
- Differential: -19.9 points (95% CI -36.9 to -3.0)

Sensitivity across nine configurations varying K, age window and games-played
band: the differential ranges from -18.5 to -20.9 points. Every configuration
clears zero. The tightest configuration, age within 1 and games played within
10, gives the weakest result at -18.5 with an upper bound of -1.1.

Fit durability, reported separately per the brief:

- Same team at one year: 6 of 43 (14.0%)
- Moved: 15 of 43
- Out: 22 of 43

Among survivors, better than two in three have changed clubs. A traded player
still playing is not a failure, which is why this is reported apart from the
survival result.

Cohort-level survival is not a finding. Cohorts run from 2 to 10 players and
the spread is noise. 2020-21 in particular resolves against 2021-22, a return
to normal schedules and roster sizes, which would inflate survival for reasons
unrelated to tryouts.

## Dropped analyses

Both were conditional on n in the brief and both fail that condition.

- Logistic regression on the pooled matched sample with covariates.
- Three-year Kaplan-Meier curves per group.

Report one-year outcomes only and say why.

## Null result

Decided publishable before any outcome was resolved. Record that fact in the
writeup; it is the defence against the obvious criticism. The result did clear
zero, but the decision was made in advance either way.

## Stated limitations

- sign_team was derived from the signing GM field in the PuckPedia exports.
  That is a proxy and it broke once, when Stan Bowman moved from Chicago to
  Edmonton in July 2024. Rows checked against GM moves carry an AUDIT note.
- Signing dates are registry filing dates, not agreement dates.
- Camp opening dates are sourced for 2022-23 and 2020-21 only. The rest are
  estimates and they determine which candidates enter the set.
- Ben Hutton, 2019-20, could not be resolved either way as a tryout. One
  unresolved case in 49.
- 2020-21 candidates come from a curated list, so that cohort's completeness is
  lower than the others.
- Two PuckPedia views were used across seasons and they filter differently, one
  on contract start year and one on contracts active in the season.

## Outstanding work

1. Count the back-on-a-PTO cell. The brief says to count it before writing any
   framing. Scoped to the 22 converts who did not survive, since recirculation
   only matters for players who fell out. Needs tryout sources for the
   following season across seven cohorts.
2. Resolve Yannick Weber, 2020-21: tryout with Nashville, signing GM field
   points to Pittsburgh. Same pattern as Gustafsson if confirmed.
3. Confirm the Letestu 2018-19 tryout club. The Hockey News has him on a
   Florida tryout; he signed with Columbus. He fails the roster test regardless.

## Change log

- Made the roster changed from opening-night active roster to appearing in the
  club's first ten games. Reason: the API cannot serve historical opening-night
  active rosters.
- Threshold moved from five games to ten after five excluded three confirmed
  converts who were healthy scratches in October.
- Late signers folded into the primary, then reversed. Reason for reversal: the
  group had no defined end boundary and confirmed same-club conversions in late
  October and beyond were being missed unsystematically.
- Same-club rule made explicit after verification surfaced cross-club cases.
- 2020-21 moved from excluded to included with notes.
- Taxi squad rule reversed. Originally counted toward the roster test; reversed
  once the run showed it applied a looser standard to 2020-21 than to any other
  cohort.
- Signature window widened from twelve days before the opener to camp opening,
  after Makiniemi and Claesson were found to be false negatives.
- Comparator specification corrected from current-season to prior-season games
  played, as a constraint rather than a tiebreaker.
- Scope reduced from ten seasons to seven. Reason: data availability at 2018-19.
- Verification results backfilled into data/candidates.csv and the analysis
  chain rerun. An earlier run counted three confirmed non-tryouts as converts
  (Ritchie and Soshnikov in 2022-23, Lankinen in 2024-25) because verification
  findings were never written back to the data file. resolve-roster.py now
  filters tracker_confirmed == "no" at the front of the chain. Converts fell
  from 46 to 43; the differential moved from -22.2 to -19.9 points and stayed
  clear of zero in every configuration.

## Verification status

54 rows confirmed as tryouts with the signing club. 7 confirmed NOT tryouts
and filtered out. 3 unresolved.

The three unresolved are Ben Hutton (2019-20), Max McCormick (2021-22) and
Pierre-Cedric Labrie (2022-23). Labrie fails the roster test regardless, so
two carry into the analysis. Both are retained and both belong in a
sensitivity note rather than being dropped silently.
