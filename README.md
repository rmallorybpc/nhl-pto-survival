# NHL PTO convert survival study

Does earning an NHL contract off a professional tryout predict
washing out faster than comparable signed players?

`definitions-lock-final.md` is the authoritative reference. Read it first.

## Run order

1. `scripts/build-openers.py` — per-team opening night dates, six seasons.
   Writes `data/openers.csv`. Runs in three stages; edit the call at the
   bottom of the file to advance.
2. `scripts/resolve-roster.py` — classifies each candidate against its
   team's opener and resolves whether the player appeared for the signing
   club. Reads `data/candidates.csv` and `data/openers.csv`, writes
   `data/candidates-resolved.csv`. Stage three is the one to run.

## Known limitations

`sign_team` in `data/candidates.csv` was derived from the signing GM field
in the PuckPedia exports. That is a proxy and it broke once, when Stan
Bowman moved from Chicago to Edmonton in July 2024. Rows checked against
GM moves carry an AUDIT note.

## Status

Candidate extraction and roster resolution complete. Verification against
tryout sources not yet done. 2020-21 requires hand assembly.
