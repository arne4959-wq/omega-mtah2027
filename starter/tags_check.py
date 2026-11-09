"""Check what each Smart Tagging code means against the public 5-min ground truth."""
import os, sys, glob
from collections import defaultdict
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
import load_smart_tagging as st

gt_path = glob.glob(os.path.join(ROOT, "**", "BAR-ATH_possession_gt_public.csv"), recursive=True)[0]
lab = pd.read_csv(gt_path)["label"].astype(str).values
graded = np.flatnonzero(np.isin(lab, ["H", "A", "D"]))
print("GT:", os.path.relpath(gt_path, ROOT), " graded frames", graded.min(), "-", graded.max())

TEAM = {"Barcelona": "H", "Atletic Club": "A"}
OPP = {"H": "A", "A": "H"}
stats = defaultdict(lambda: [0, 0, 0])  # same team, opponent, dead

for e in st.load():
    t = TEAM.get(e["tags"].get("Team"))
    key = e["code"] + (" / " + e["tags"]["Type"] if "Type" in e["tags"] else "")
    s, f = max(e["start_frame"], 0), min(e["end_frame"], len(lab))
    seg = lab[s:f]
    seg = seg[np.isin(seg, ["H", "A", "D"])]
    if len(seg) == 0:
        continue
    if t is None:
        stats[key][2] += int((seg == "D").sum())
        stats[key][0] += int((seg != "D").sum())
        continue
    stats[key][0] += int((seg == t).sum())
    stats[key][1] += int((seg == OPP[t]).sum())
    stats[key][2] += int((seg == "D").sum())

print("\n{:<45} {:>6} {:>6} {:>6}   frames".format("code / type", "same%", "opp%", "dead%"))
for k, (a, b, d) in sorted(stats.items(), key=lambda x: -sum(x[1])):
    n = a + b + d
    print("{:<45} {:>6.0f} {:>6.0f} {:>6.0f}   {}".format(k, 100*a/n, 100*b/n, 100*d/n, n))
