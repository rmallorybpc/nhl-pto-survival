"""
Sensitivity check on the matched differential.

Reruns the v2 matching across K, age window, and prior-games-played band.
The point is to see whether the -19 point differential is stable or an
artifact of one configuration.

Reads the cached pools via rematch-comparator.
Writes data/sensitivity.txt

Nothing here touches the network. Runs in seconds.
"""

import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "rematch", "scripts/rematch-comparator.py")
rematch = importlib.util.module_from_spec(spec)
sys.modules["rematch"] = rematch
spec.loader.exec_module(rematch)

OUT = "data/sensitivity.txt"

# Baseline first, then one dimension varied at a time.
GRID = [
    (3, 2, 15),   # baseline
    (2, 2, 15),
    (5, 2, 15),
    (3, 1, 15),
    (3, 3, 15),
    (3, 2, 10),
    (3, 2, 25),
    (3, 1, 10),   # tightest
    (5, 3, 25),   # loosest
]


def run():
    rows = []
    for k, age, gp in GRID:
        try:
            r = rematch.main(K=k, MAX_AGE_GAP=age, GP_BAND=gp, quiet=True)
        except Exception as e:
            print(f"FAILED K={k} age={age} gp={gp}: {e}")
            continue
        if r:
            rows.append(r)

    if not rows:
        print("no results")
        return

    lines = [
        "Sensitivity of the one-year survival differential",
        "",
        "K   age  gp   converts  conv%   comp%   diff     95% CI          zero?",
        "-" * 74,
    ]
    for r in rows:
        crosses = "CROSSES" if r["lo"] <= 0 <= r["hi"] else ""
        lines.append(
            f"{r['k']:<3} {r['age']:<4} {r['gp']:<4} "
            f"{r['n_c']:>3}/{r['n_c'] + r['dropped']:<5} "
            f"{r['pc']:>5.1f}%  {r['pm']:>5.1f}%  "
            f"{r['diff']:>+6.1f}  "
            f"{r['lo']:>+6.1f} to {r['hi']:>+6.1f}  {crosses}"
        )

    diffs = [r["diff"] for r in rows]
    n_cross = sum(1 for r in rows if r["lo"] <= 0 <= r["hi"])
    lines += [
        "-" * 74,
        "",
        f"differential range: {min(diffs):+.1f} to {max(diffs):+.1f} points",
        f"configurations where the interval crosses zero: {n_cross} of {len(rows)}",
        "",
    ]
    if n_cross == 0:
        lines.append("Every configuration clears zero. The direction is stable.")
    elif n_cross == len(rows):
        lines.append("No configuration clears zero. The result is a null.")
    else:
        lines.append("The result depends on the configuration. Report it as "
                     "imprecise and say so plainly.")

    report = "\n".join(lines)
    open(OUT, "w").write(report)
    print(report)


if __name__ == "__main__":
    run()
