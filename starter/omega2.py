"""Team omega v2: tracking + Smart Tagging team phases + dead-ball rules."""
import argparse, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
import baseline as bl
import load_smart_tagging as st
import omega as om

FPS = om.FPS
ATTACK = {"BUILD UP", "LONG BALL", "PROGRESSION", "ATTACKING TRANSITION"}
DEFEND = {"DEFENDING IN ATTACKING THIRD", "DEFENDING IN MIDDLE THIRD",
          "DEFENDING IN DEFENSIVE THIRD", "DEFENSIVE TRANSITION"}
TEAM = {"Barcelona": "H", "Atletic Club": "A"}
OPP = {"H": "A", "A": "H"}
RESTART_S = 3.5  # kick-off tag starts 88 frames (~3.5 s) before the real kick-off


def tag_team(events, n):
    hv = np.zeros(n, np.int32); av = np.zeros(n, np.int32)
    for e in events:
        t = TEAM.get(e["tags"].get("Team"))
        if t is None:
            continue
        if e["code"] in ATTACK:
            who = t
        elif e["code"] in DEFEND:
            who = OPP[t]
        else:
            continue
        s, f = max(e["start_frame"], 0), min(e["end_frame"], n)
        (hv if who == "H" else av)[s:f] += 1
    out = np.full(n, "", dtype="<U1")
    out[hv > av] = "H"; out[av > hv] = "A"
    return out


def live_mask(events, n):
    check = st.check_time_base(events)
    live = np.zeros(n, bool); spans = []
    for h in check["halves"]:
        k = h["true_kickoff_frame"]
        end = max(e["end_frame"] for e in events if e["tags"].get("Half") == h["half"])
        live[k:min(end, n)] = True; spans.append((h["half"], k, end))
    return live, spans


def build_labels(codes, w, min_len, mode, sp, tag, live, restarts):
    lab = bl.smooth(codes, w).copy()
    has = live & (tag != "")
    if mode == "fill":
        m = has & (lab == "D")
    elif mode == "override":
        m = has
    else:
        m = np.zeros(len(lab), bool)
    lab[m] = tag[m]
    lab[~live] = "D"
    lab = om.merge_short(lab, min_len)
    if sp:
        k = int(round(RESTART_S * FPS))
        for s in restarts:
            lab[max(s, 0):max(s, 0) + k] = "D"
    lab[~live] = "D"
    return lab


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--window", type=int, nargs="+", default=[50])
    p.add_argument("--min-sec", type=float, nargs="+", default=[3, 4])
    p.add_argument("--mode", nargs="+", default=["none", "fill", "override"])
    p.add_argument("--sp", type=int, nargs="+", default=[0, 1])
    a = p.parse_args()

    codes = om.get_codes(); n = len(codes)
    events = st.load()
    tag = tag_team(events, n)
    live, spans = live_mask(events, n)
    restarts = [e["start_frame"] for e in events if e["code"] == "SET PIECES"]
    for half, k, end in spans:
        print("{}: live frames {} - {} ({:.1f} min)".format(half, k, end, (end - k) / FPS / 60))
    print("tags give a team on {:.1f}% of live frames".format(100 * np.mean(tag[live] != "")))

    for w in a.window:
        for sec in a.min_sec:
            for mode in a.mode:
                for sp in a.sp:
                    lab = build_labels(codes, w, int(round(sec * FPS)), mode, sp, tag, live, restarts)
                    name = "o2_w{}_m{:g}_{}{}".format(w, sec, mode, "_sp" if sp else "")
                    bl.write_submission(os.path.join(om.RESULTS, name + ".csv"), lab)
                    d = 100 * np.mean(lab == "D")
                    print("{:<26} {}  D {:.1f}%".format(name, om.describe(lab), d))
    print("\nNow: python evaluation/run_evaluation.py --bootstrap 1000 | head -45")
