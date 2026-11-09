"""Team omega -- baseline + spell cleanup for More than a Hack 2027.

Idea: spellF1 rewards recovering whole possessions. The baseline flips team
too often (too many short spells). We keep the baseline's per-frame codes,
smooth them, then merge every spell shorter than MIN_LEN frames into its
neighbour, so possessions come out long and few, like the real ones.

Usage (from the repo root, venv active):
    python starter/omega.py                 # writes a small grid to results/
    python evaluation/run_evaluation.py     # score them on the public 5 min

The first run reads the 196 MB tracking file once and caches the result in
data/omega_codes_cache.npy, so every run after that takes a few seconds.
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import baseline as bl  # noqa: E402  (the repository's own reference baseline)

FPS = 25  # 5 min of public ground truth = 7,500 frames -> 25 frames per second
CACHE = os.path.join(ROOT, "data", "omega_codes_cache.npy")
RESULTS = bl.RESULTS_DIR


def get_codes():
    """Per-frame nearest-player team codes, read once then cached."""
    if os.path.exists(CACHE):
        print("using cached codes:", os.path.relpath(CACHE, ROOT))
        return np.load(CACHE, allow_pickle=True)
    codes = bl.build()
    np.save(CACHE, codes)
    return codes


def spells(labels):
    """Start and end (exclusive) of every run of identical labels."""
    change = np.flatnonzero(labels[1:] != labels[:-1]) + 1
    starts = np.r_[0, change]
    ends = np.r_[change, len(labels)]
    return starts, ends


def merge_short(labels, min_len):
    """Repeatedly absorb the shortest spell into a neighbour until every
    spell is at least min_len frames long.

    Neighbour choice: if both sides agree (e.g. A D A) the gap takes that
    label; otherwise it joins the longer neighbour.
    """
    labels = labels.copy()
    while True:
        starts, ends = spells(labels)
        if len(starts) <= 1:
            return labels
        lengths = ends - starts
        i = int(np.argmin(lengths))
        if lengths[i] >= min_len:
            return labels
        left = labels[starts[i] - 1] if i > 0 else None
        right = labels[ends[i]] if i < len(starts) - 1 else None
        if left is None:
            fill = right
        elif right is None:
            fill = left
        elif left == right:
            fill = left
        else:
            fill = left if lengths[i - 1] >= lengths[i + 1] else right
        labels[starts[i]:ends[i]] = fill


def describe(labels):
    starts, ends = spells(labels)
    team = np.isin(labels[starts], ["H", "A"])
    n = int(team.sum())
    mean_s = float((ends - starts)[team].mean()) / FPS if n else 0.0
    return "{} team spells, mean {:.1f} s".format(n, mean_s)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--window", type=int, nargs="+", default=[25, 50, 125],
                        help="smoothing half-widths in frames")
    parser.add_argument("--min-sec", type=float, nargs="+", default=[1, 2, 3, 4],
                        help="shortest spell to keep, in seconds")
    parser.add_argument("--out", default=RESULTS)
    args = parser.parse_args()

    codes = get_codes()
    for window in args.window:
        smoothed = bl.smooth(codes, window)
        for sec in args.min_sec:
            min_len = int(round(sec * FPS))
            labels = merge_short(smoothed, min_len)
            name = "omega_w{}_m{:g}".format(window, sec)
            path = bl.write_submission(os.path.join(args.out, name + ".csv"), labels)
            print("{:<18} {}  -> {}".format(name, describe(labels),
                                            os.path.relpath(path, ROOT)))

    print("\nNow score them:  python evaluation/run_evaluation.py")
    print("Before submitting one: python evaluation/validate_submission.py results/<file>.csv")
