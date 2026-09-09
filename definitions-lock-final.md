# NHL PTO survival: definitions lock (final)

Supersedes the provisional lock. All decisions settled. Any change from here is a decision and gets logged at the bottom.

## Scope

Six cohorts: 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25.

2025-26 is excluded. No one-year outcome exists until October 2026.

The 2018-19 boundary is a data-availability limit, not a design choice. PuckPedia contract season filters do not run earlier. State it that way.

## Locked definitions

- Convert: a player who was in an NHL training camp on a professional tryout and signed a standard NHL contract with that club during the same season, and played at least one NHL game for that club that season.
- Cross-club conversions do not count. A player on a tryout with one club
  who signs with a different club that season is not a convert. The tryout
  club and signing club must match. Erik Gustafsson is the worked example:
  on a tryout with the Islanders in 2021-22, signed with Chicago October 11,
  excluded.
- Played at least one NHL game: the roster test. It replaces the opening-night active roster rule, which the NHL API does not serve for historical seasons.
- Survived: on an NHL roster at the one-year mark, defined as opening night of the following season.
- Moved: on a different NHL team's roster at the one-year mark.
- Back on a PTO: in an NHL camp on a tryout the following season, whether or not it converted.
- Censoring: the most recent completed season supports one-year outcomes only.

## Why the roster test changed

Two decisions collided. Late signers are folded into the primary, and the roster test was going to be "played in the first five games." Those are incompatible. Players who signed after their team's opener, such as Pitlick on October 25 and Sbisa on October 23, cannot appear in the first five games because those games were already played.

The one-game test resolves it. It applies uniformly to both groups and preserves the intent of the first-five rule, which was to catch players who made the roster but were a healthy scratch on opening night.

It also enforces the brief's existing rule that signing off a PTO and starting in the AHL does not count. Aston-Reese is the worked example: released from his Toronto tryout October 6, 2023, signed a two-way deal with Detroit October 8, assigned to Grand Rapids the next day. Signed off a tryout, never played, not a convert.

## What folding in late signers costs

The claim broadens. It is no longer "making the team out of camp on a PTO." It is "earning an NHL contract off a PTO and playing."

Write the headline to match. Anything narrower will not be supported by the sample.

## Season notes to publish alongside results

**2020-21.** Included. Camps opened December 31 for the seven teams that did not participate in the 2019-20 Return to Play Plan and January 3 for the remaining 24, with the season starting January 13. There was a training camp. There were no preseason games. Since a tryout permits camp and exhibition play only, conversions that season happened on practice sessions alone, with no games to showcase in.

Taxi squads of four to six players were in effect from the season's start. Taxi squad assignment counts toward the roster test. This season is the only cohort where that applies, because taxi squads did not return until December 26, 2021, well after that season's openers.

Two effects run the same direction and do not cancel. The extra roster spots admit players who would have gone to the AHL in a normal year, so the convert count inflates and the cohort's average quality falls. Expect this cohort's survival rate to run low for structural reasons.

Related: The Win Column reported 2020-21 as the most successful season for PTO players getting contracts. Treat that as a possible taxi squad artifact rather than a signal about tryouts, and say so.

**2019-20.** Included with a note. Its one-year outcome resolves at opening night 2020-21, which was January 2021 under compressed rosters and taxi squads. The outcome is measurable but not comparable to other cohorts. Report it and flag it.

## Analysis plan

Primary: one-year survival rate for converts versus the matched comparator, each with a confidence interval, plus the differential with a confidence interval.

Secondary: same team versus moved. Reported separately. A traded player still playing is not a failure.

Secondary: back on a PTO the following season.

Dropped, both conditional in the brief and both failing the n condition:
- Logistic regression with age and prior workload covariates.
- Three-year Kaplan-Meier curves.

Expected n is roughly fifty to sixty converts across six cohorts. Intervals will run near plus or minus twelve points per group.

## Null result

Publishable. If the differential does not clear zero, that is the finding and it gets written as the finding, not buried or reframed.

This is decided before any outcome is resolved. Record that fact in the writeup. It is the defense against the obvious criticism.

## Identification method

Primary: the contract-date signature. Standard-level contracts, UFA or UFA with no qualifying offer, signed within roughly twelve days before the team's opener. Validated across 2019-20, 2021-22, 2022-23, 2023-24, and 2024-25.

2020-21 exception. The signature fails there because free agency ran late into camp and no pre-camp trough exists. Assemble that season by hand from the NHL.com tryout tracker instead.

Confirmation: HFBoards annual training-camp threads record tryouts and their outcomes directly. Use these to confirm candidates and remove false positives. In 2021-22 they confirmed ten of the candidate set and excluded the four-player Islanders cluster, which were late free-agent signings rather than conversions.

Known noise pattern: a single team signing several veterans late at or near minimum in a cap-tight year produces false positives. Verify any single-team cluster individually.

## Data handling

- Deduplicate on player and signing date before counting. Craig Anderson appears twice in the 2020-21 export.
- Opening night is team-specific. Build a per-season table of team opener dates. The window is team-relative and this is required.
- Normalize names before matching across sources. Accents, hyphens, suffixes. Log every hand resolution.
- All live data runs locally.

## Change log

- Made the roster changed from opening-night active roster to played at
  least one NHL game for the signing club. Reason: API cannot serve
  historical opening-night active rosters, and the first-five-games
  alternative collided with folding in late signers.
- Late signers moved from undecided to folded into the primary.
- 2020-21 moved from excluded to included with notes.
- Scope reduced from ten seasons to six. Reason: data availability at 2018-19.
- Same-club rule made explicit. A player on a tryout with one club who signs
  with a different club that season is not a convert. Erik Gustafsson is the
  worked example: tryout with the Islanders in 2021-22, signed with Chicago
  October 11, excluded. Decided before the remaining seasons were verified.
- sign_team corrected for two 2024-25 rows. Derived from signing GM, which
  broke when Stan Bowman moved from Chicago to Edmonton in July 2024.
- 2020-21 moved from excluded to included with notes.
- Scope reduced from ten seasons to six. Reason: data availability at 2018-19.
