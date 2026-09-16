"""
Sensitivity to the two converts whose tryout status is unresolved.

Ben Hutton (2019-20 LAK) and Max McCormick (2021-22 SEA) are in the analysis
with tracker_confirmed == "unclear". Neither has been shown to be a tryout.
The published audit flags this as the largest gap between what it recommends
and what the site shows.

This reruns the matched differential three ways:
  all        - as published, both retained
  drop_both  - both excluded
  drop_each  - one at a time, to see which drives any movement

Reads the cached pools via rematch-comparator. No network calls.
Writes data/sensitivity-unresolved.txt
"""

import csv
import importlib.util
import shutil
import sys
import os

SOURCE = "data/outcomes.csv"
BACKUP = "data/outcomes.csv.bak"
OUT = "data/sensitivity-unresolved.txt"

UNRESOLVED = [
    ("2019-20", "Ben Hutton"),
    ("2021-22", "Max McCormick"),
]

spec = importlib.util.spec_from_file_location(
    "rematch", "scripts/rematch-comparator.py")
rematch = importlib.util.module_from_spec(spec)
sys.modules["rematch"] = rematch
spec.loader.exec_module(rematch)


def run_excluding(drop):
    """Rerun the matching with `drop` (a set of (season, player)) removed.

    rematch reads SOURCE from disk, so the file is swapped, the run is made,
    and the original is restored. The backup is restored in a finally block
    so an exception cannot leave the real data file overwritten.
    """
    with open(SOURCE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())
    kept = [r for r in rows if (r["season"], r["player"]) not in drop]

    shutil.copy(SOURCE, BACKUP)
    try:
        with open(SOURCE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(kept)
        return rematch.main(quiet=True)
    finally:
        shutil.copy(BACKUP, SOURCE)
        os.remove(BACKUP)


def line(label, r):
    if not r:
        return f"{label:<26} FAILED"
    crosses = "CROSSES ZERO" if r["lo"] <= 0 <= r["hi"] else ""
    return (f"{label:<26} {r['n_c']:>2} converts  "
            f"{r['pc']:>5.1f}%  vs {r['pm']:>5.1f}%  "
            f"{r['diff']:>+6.1f}  "
            f"({r['lo']:>+6.1f} to {r['hi']:>+6.1f})  {crosses}")


def main():
    results = []

    base = run_excluding(set())
    results.append(("as published", base))

    both = run_excluding(set(UNRESOLVED))
    results.append(("both excluded", both))

    for s, p in UNRESOLVED:
        r = run_excluding({(s, p)})
        results.append((f"without {p}", r))

    lines = [
        "Sensitivity to unresolved tryout status",
        "",
        "Ben Hutton (2019-20 LAK) and Max McCormick (2021-22 SEA) are counted as",
        "converts but neither has been confirmed on a tryout by any source found.",
        "This shows what the result looks like without them.",
        "",
        f"{'specification':<26} {'n':>2}          converts   comparators  diff    95% CI",
        "-" * 92,
    ]
    lines += [line(lbl, r) for lbl, r in results]
    lines += ["-" * 92, ""]

    diffs = [r["diff"] for _, r in results if r]
    crossing = [lbl for lbl, r in results if r and r["lo"] <= 0 <= r["hi"]]
    lines.append(f"differential range: {min(diffs):+.1f} to {max(diffs):+.1f} points")
    if crossing:
        lines.append("crosses zero in: " + ", ".join(crossing))
        lines.append("")
        lines.append("The result depends on two players whose tryout status is unknown.")
        lines.append("Report that plainly. It is a real limit, not a footnote.")
    else:
        lines.append("no specification crosses zero")
        lines.append("")
        lines.append("The finding does not rest on either unresolved player.")

    report = "\n".join(lines)
    open(OUT, "w").write(report)
    print(report)


if __name__ == "__main__":
    main()
