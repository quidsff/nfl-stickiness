"""Study 8 pilot: which to-date statistic best predicts the result of a single matchup?

For every regular-season game from week MIN_WEEK on (both teams have 3+ games played),
using only games played BEFORE that week, compute for the home team H and away team A:

  raw_gap     H point diff/game  -  A point diff/game
  sos_gap     schedule-adjusted point diff gap:
                adj_pd(T) = pd_pg(T) + mean over T's past opponents of pd_pg(opp)
              (a team that outscored good opponents is credited; one that beat bad ones is not)
  od_gap      offense/defense-adjusted gap:
                adj_off(T) = pf_pg(T) - mean over T's past opponents of pa_pg(opp)   [scored vs what opponents usually allow]
                adj_def(T) = pa_pg(T) - mean over T's past opponents of pf_pg(opp)   [allowed vs what opponents usually score]
                od(T) = adj_off(T) - adj_def(T);  od_gap = od(H) - od(A)
  wpct_gap    win% gap
  spread      Vegas closing spread (home - away expected margin), from nflverse games.csv
  home        constant 1 (home field only)

Outcomes: home win (AUC, accuracy at the sign) and home margin (correlation).
Opponent stats used in the adjustments are also to-date (through the previous week).
Seasons 2016-2024, weeks 4-18 for the pilot.
"""
import pandas as pd, numpy as np, os, sys
from scipy.stats import pearsonr
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
S0, S1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (2016, 2024)
MIN_WEEK = 4
RENAME = {"SD": "LAC", "OAK": "LV", "STL": "LA"}

g = pd.read_csv(os.path.join(DATA, "games.csv"))
g = g[(g.game_type == "REG") & g.season.between(S0, S1) & g.home_score.notna()].copy()
for c in ("home_team", "away_team"): g[c] = g[c].replace(RENAME)
g["margin"] = g.home_score - g.away_score; g["home_win"] = (g.margin > 0).astype(int)
g = g[g.margin != 0]   # drop ties

# long form: one row per team-game
h = g[["season", "week", "game_id", "home_team", "away_team", "home_score", "away_score"]].rename(columns={"home_team": "team", "away_team": "opp", "home_score": "pf", "away_score": "pa"})
a = g[["season", "week", "game_id", "away_team", "home_team", "away_score", "home_score"]].rename(columns={"away_team": "team", "home_team": "opp", "away_score": "pf", "home_score": "pa"})
tg = pd.concat([h, a]).sort_values(["season", "team", "week"])

rows = []
for season, gs in g.groupby("season"):
    tgs = tg[tg.season == season]
    for week in sorted(gs.week.unique()):
        if week < MIN_WEEK: continue
        past = tgs[tgs.week < week]
        st = past.groupby("team").agg(gp=("pf", "size"), pf=("pf", "sum"), pa=("pa", "sum"), w=("pf", lambda x: 0)).reset_index()
        st["w"] = past.assign(w=(past.pf > past.pa).astype(float) + 0.5 * (past.pf == past.pa)).groupby("team").w.sum().values
        st["pf_pg"] = st.pf / st.gp; st["pa_pg"] = st.pa / st.gp; st["pd_pg"] = st.pf_pg - st.pa_pg; st["wpct"] = st.w / st.gp
        st = st.set_index("team")
        # opponent averages (to date) for each team
        opp = past.merge(st[["pd_pg", "pf_pg", "pa_pg"]], left_on="opp", right_index=True)
        oppavg = opp.groupby("team").agg(opp_pd=("pd_pg", "mean"), opp_pf=("pf_pg", "mean"), opp_pa=("pa_pg", "mean"))
        st = st.join(oppavg)
        st["adj_pd"] = st.pd_pg + st.opp_pd
        st["od"] = (st.pf_pg - st.opp_pa) - (st.pa_pg - st.opp_pf)
        for _, r in gs[gs.week == week].iterrows():
            if r.home_team not in st.index or r.away_team not in st.index: continue
            H, A = st.loc[r.home_team], st.loc[r.away_team]
            if H.gp < 3 or A.gp < 3: continue
            rows.append(dict(season=season, week=week, game_id=r.game_id, margin=r.margin, home_win=r.home_win, spread=r.spread_line,
                             raw_gap=H.pd_pg - A.pd_pg, sos_gap=H.adj_pd - A.adj_pd, od_gap=H.od - A.od, wpct_gap=H.wpct - A.wpct))
df = pd.DataFrame(rows).dropna(subset=["spread"])
print(f"=== Seasons {S0}-{S1}, weeks {MIN_WEEK}-18, {len(df)} games; home team won {df.home_win.mean():.1%} ===\n")

print(f"{'predictor':12}{'r with margin':>15}{'AUC (home win)':>16}{'pick accuracy':>15}{'LOSO logloss':>14}")
from sklearn.metrics import log_loss
def loso(col):
    pred = np.zeros(len(df))
    for s in df.season.unique():
        tr, te = df.season != s, df.season == s
        m = LogisticRegression().fit(df.loc[tr, [col]], df.loc[tr, "home_win"]); pred[te] = m.predict_proba(df.loc[te, [col]])[:, 1]
    return log_loss(df.home_win, pred)
df["home"] = 1.0
for col, name in [("raw_gap", "raw PD gap"), ("sos_gap", "SOS-adj PD"), ("od_gap", "off/def adj"), ("wpct_gap", "win% gap"), ("spread", "Vegas spread"), ("home", "home only")]:
    r = pearsonr(df[col], df.margin)[0] if col != "home" else float("nan")
    auc = roc_auc_score(df.home_win, df[col]) if col != "home" else 0.5
    # pick: predictor > 0 -> home; ties count half
    acc = ((df[col] > 0) == (df.home_win == 1)).mean() if col != "home" else df.home_win.mean()
    ll = loso(col)
    print(f"{name:12}{r:15.3f}{auc:16.3f}{acc:15.1%}{ll:14.3f}")

print("\nSame, split by week band (pick accuracy):")
df["band"] = pd.cut(df.week, [3, 7, 11, 18], labels=["wk 4-7", "wk 8-11", "wk 12-18"])
for b, d in df.groupby("band", observed=True):
    s = f"  {b:9} n={len(d):4d}  "
    for col in ["raw_gap", "sos_gap", "od_gap", "wpct_gap", "spread"]:
        s += f"{col}: {((d[col] > 0) == (d.home_win == 1)).mean():5.1%}   "
    print(s)

print("\nDo the adjusted gaps add anything to the raw gap? (LOSO logloss, lower is better)")
def loso_multi(cols):
    pred = np.zeros(len(df))
    for s in df.season.unique():
        tr, te = df.season != s, df.season == s
        m = LogisticRegression().fit(df.loc[tr, cols], df.loc[tr, "home_win"]); pred[te] = m.predict_proba(df.loc[te, cols])[:, 1]
    return log_loss(df.home_win, pred), roc_auc_score(df.home_win, pred)
for cols in [["raw_gap"], ["raw_gap", "sos_gap"], ["raw_gap", "od_gap"], ["raw_gap", "sos_gap", "od_gap", "wpct_gap"], ["spread"], ["spread", "raw_gap"]]:
    ll, auc = loso_multi(cols); print(f"  {' + '.join(cols):42} logloss {ll:.3f}  AUC {auc:.3f}")
print("\nCorrelations among predictors:"); print(df[["raw_gap", "sos_gap", "od_gap", "wpct_gap", "spread"]].corr().round(2).to_string())
df.to_csv(os.path.join(HERE, f"matchup_pilot_{S0}_{S1}.csv"), index=False)
