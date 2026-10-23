"""Pilot: which early-season team metrics are stickiest and most predictive of playoff outcomes?

Metrics (all per game, computed through CUTOFF week of the regular season):
  ppg            points per game
  pd_pg          point differential per game
  off_epa_pg     offensive EPA per game
  def_epa_pg     defensive EPA per game (opponent EPA; sign flipped so higher = better)
  to_diff_pg     turnover differential per game
  win_pct        (reference) win percentage

Two questions per metric:
  1. Stickiness: Pearson/Spearman r between the metric through CUTOFF and the same metric
     over the remaining regular-season games (weeks CUTOFF+1 .. end).
  2. Playoff predictiveness: AUC of the metric for each outcome:
       made_playoffs, won_wc (or bye), reached_conf (won divisional), reached_sb, won_sb
     plus Spearman r with "playoff wins" (0..4; bye counts as a WC win).
Also: a leave-one-season-out logistic regression per metric for made_playoffs to show
how much each metric adds vs. win% alone.
"""
import pandas as pd, numpy as np, os, sys
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from scipy.stats import spearmanr, pearsonr

HERE = os.path.dirname(os.path.abspath(__file__))
CUTOFF = int(sys.argv[1]) if len(sys.argv) > 1 else 9
tg = pd.read_csv(os.path.join(HERE, "data", "team_games.csv"))
reg = tg[tg.season_type == "REG"].copy()
post = tg[tg.season_type == "POST"].copy()

def agg(df):
    g = df.groupby(["season", "team"]).agg(
        games=("win", "size"), wins=("win", "sum"),
        pf=("points_for", "sum"), pa=("points_against", "sum"),
        off_epa=("off_epa", "sum"), def_epa=("def_epa", "sum"),
        to_diff=("to_diff", "sum")).reset_index()
    g["win_pct"] = g.wins / g.games
    g["ppg"] = g.pf / g.games
    g["pd_pg"] = (g.pf - g.pa) / g.games
    g["off_epa_pg"] = g.off_epa / g.games
    g["def_epa_pg"] = -g.def_epa / g.games
    g["to_diff_pg"] = g.to_diff / g.games
    return g

METRICS = ["win_pct", "ppg", "pd_pg", "off_epa_pg", "def_epa_pg", "to_diff_pg"]
early = agg(reg[reg.week <= CUTOFF])
late = agg(reg[reg.week > CUTOFF])

# ---- playoff outcomes ----
# rounds in games.csv: WC, DIV, CON, SB. Teams with a bye appear first in DIV.
games = pd.read_csv(os.path.join(HERE, "data", "games.csv"))
games = games[games.season.between(2016, 2024) & games.game_type.isin(["WC", "DIV", "CON", "SB"])].copy()
for c in ("home_team", "away_team"):
    games[c] = games[c].replace({"SD": "LAC", "OAK": "LV", "STL": "LA"})
games["winner"] = np.where(games.home_score > games.away_score, games.home_team, games.away_team)
rows = []
for s, gs in games.groupby("season"):
    teams = set(gs.home_team) | set(gs.away_team)
    for t in teams:
        wc = gs[(gs.game_type == "WC") & ((gs.home_team == t) | (gs.away_team == t))]
        div = gs[(gs.game_type == "DIV") & ((gs.home_team == t) | (gs.away_team == t))]
        con = gs[(gs.game_type == "CON") & ((gs.home_team == t) | (gs.away_team == t))]
        sb = gs[(gs.game_type == "SB") & ((gs.home_team == t) | (gs.away_team == t))]
        bye = len(wc) == 0 and len(div) > 0
        reached_div = bye or (len(wc) and (wc.winner == t).any())
        reached_conf = bool(len(con))
        reached_sb = bool(len(sb))
        won_sb = bool(len(sb) and (sb.winner == t).any())
        pw = int(bye) + int((wc.winner == t).sum() + (div.winner == t).sum() + (con.winner == t).sum() + (sb.winner == t).sum())
        rows.append(dict(season=s, team=t, made_playoffs=1, bye=int(bye), reached_div=int(reached_div),
                         reached_conf=int(reached_conf), reached_sb=int(reached_sb), won_sb=int(won_sb), playoff_wins=pw))
po = pd.DataFrame(rows)
full = agg(reg).merge(po, on=["season", "team"], how="left").fillna(
    {"made_playoffs": 0, "bye": 0, "reached_div": 0, "reached_conf": 0, "reached_sb": 0, "won_sb": 0, "playoff_wins": 0})
OUTCOMES = ["made_playoffs", "reached_div", "reached_conf", "reached_sb", "won_sb"]
df = early.merge(full[["season", "team"] + OUTCOMES + ["playoff_wins"]], on=["season", "team"])
df = df.merge(late[["season", "team"] + METRICS], on=["season", "team"], suffixes=("", "_late"))
NAMES = {"win_pct": "Win %", "ppg": "Points/game", "pd_pg": "Point diff/game", "off_epa_pg": "Off EPA/game",
         "def_epa_pg": "Def EPA/game", "to_diff_pg": "TO diff/game"}

print(f"\n=== Through week {CUTOFF}, seasons 2016-2024, n={len(df)} team-seasons ===")

# 1. stickiness
print("\n-- Stickiness: same metric, weeks 1-%d vs weeks %d+ --" % (CUTOFF, CUTOFF + 1))
print(f"{'metric':18}{'pearson r':>11}{'spearman r':>12}")
stick = {}
for m in METRICS:
    pr = pearsonr(df[m], df[m + "_late"])[0]; sr = spearmanr(df[m], df[m + "_late"])[0]
    stick[m] = pr
    print(f"{NAMES[m]:18}{pr:11.3f}{sr:12.3f}")

# cross-prediction: early metric -> late win pct and late point diff
print("\n-- Early metric -> rest-of-season WIN % (pearson r) --")
for m in METRICS:
    print(f"{NAMES[m]:18}{pearsonr(df[m], df['win_pct_late'])[0]:11.3f}")

# 2. AUC per outcome
print("\n-- AUC for each playoff outcome (0.5 = coin flip) --")
hdr = f"{'metric':18}" + "".join(f"{o:>14}" for o in OUTCOMES) + f"{'r(PO wins)':>12}"
print(hdr)
auc_tab = {}
for m in METRICS:
    aucs = [roc_auc_score(df[o], df[m]) for o in OUTCOMES]
    auc_tab[m] = aucs
    r = spearmanr(df[m], df["playoff_wins"])[0]
    print(f"{NAMES[m]:18}" + "".join(f"{a:14.3f}" for a in aucs) + f"{r:12.3f}")
print("base rates:        " + "".join(f"{df[o].mean():14.3f}" for o in OUTCOMES))

# 3. incremental value over win% (leave-one-season-out logistic, made_playoffs)
print("\n-- Leave-one-season-out log loss for made_playoffs (lower = better) --")
from sklearn.metrics import log_loss
def loso(cols):
    preds = np.zeros(len(df))
    for s in df.season.unique():
        tr, te = df.season != s, df.season == s
        X = df.loc[tr, cols].values; Xs = (X - X.mean(0)) / X.std(0)
        mdl = LogisticRegression(C=1.0).fit(Xs, df.loc[tr, "made_playoffs"])
        preds[te] = mdl.predict_proba((df.loc[te, cols].values - X.mean(0)) / X.std(0))[:, 1]
    return log_loss(df.made_playoffs, preds), roc_auc_score(df.made_playoffs, preds)
for cols in [["win_pct"], ["ppg"], ["pd_pg"], ["off_epa_pg"], ["def_epa_pg"], ["to_diff_pg"],
             ["win_pct", "pd_pg"], ["win_pct", "off_epa_pg", "def_epa_pg"], ["win_pct", "pd_pg", "to_diff_pg"],
             ["win_pct", "ppg", "pd_pg", "off_epa_pg", "def_epa_pg", "to_diff_pg"]]:
    ll, a = loso(cols)
    print(f"{' + '.join(NAMES[c] for c in cols):60}  logloss {ll:.3f}   AUC {a:.3f}")

out = pd.DataFrame({"metric": [NAMES[m] for m in METRICS], "stickiness_r": [stick[m] for m in METRICS],
                    **{f"auc_{o}": [auc_tab[m][i] for m in METRICS] for i, o in enumerate(OUTCOMES)}})
out.to_csv(os.path.join(HERE, f"results_week{CUTOFF}.csv"), index=False)
df.to_csv(os.path.join(HERE, f"team_seasons_week{CUTOFF}.csv"), index=False)
