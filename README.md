# Team omega — More than a Hack 2027 (Phase 1: Ball Possession)

Team: Kaisone, DEDTHANONGSIN, Navin

Our code on top of the official repo
[metrica-sports/more-than-a-hack-2027](https://github.com/metrica-sports/more-than-a-hack-2027).
It reuses the official `starter/baseline.py` and `starter/load_smart_tagging.py`.

## Method

1. **Tracking** — nearest tracked player to the ball each frame, smoothed over a window
   (the official baseline).
2. **Spell cleanup** (`starter/omega.py`) — merge every possession spell shorter than
   3–4 s into its neighbour. spellF1 rewards whole possessions, so fewer, longer spells score better.
3. **Smart Tagging** (`starter/omega2.py`)
   - frames before kick-off, at half-time and after the final tag → `D`
   - first 3.5 s of every set piece → `D` (the kick-off tag starts ~3.5 s before the real kick-off)
   - optional: where the ball is not tracked, use the team from tactical phases
     (`BUILD UP`, `PROGRESSION`, `LONG BALL`, `ATTACKING TRANSITION` = team in possession;
     `DEFENDING IN …`, `DEFENSIVE TRANSITION` = the other team). Checked in `starter/tags_check.py`.

## Results on the public 5 minutes

| submission | spellF1 | macroF1 |
|---|---|---|
| baseline_smooth125 (official best) | 0.4242 | 0.5812 |
| omega_w50_m4 | 0.5241 | 0.6771 |
| **o2_w50_m4_none_sp** | **0.5467** | **0.6949** |

The scorer reports a noise band of ~0.4 on only 17 possessions, so these numbers show direction, not a final ranking.

## Run

```bash
git clone https://github.com/metrica-sports/more-than-a-hack-2027
cd more-than-a-hack-2027
# copy starter/*.py from this repo into starter/
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# put the match data in data/tactical/ (not included here -- licensed)
python starter/omega.py
python starter/omega2.py
python evaluation/run_evaluation.py --bootstrap 1000 | head -45
python evaluation/validate_submission.py evaluation/results/o2_w50_m4_none_sp.csv
```

The match data is not in this repository: its terms forbid redistribution.
