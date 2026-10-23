"""Study 7: how should "track record" be defined?

Compares four definitions of a quarterback's prior scoring level, each used to build the
gap (first-half PPG minus prior level) and tested against second-half rank and second-half
PPG, controlling for first-half PPG:
  prev1_8g    last season's PPG, 8+ games (Studies 5 and 6)
  prev1_full  last season's PPG, 14+ games only (a full season)
  best2       best PPG of the previous two seasons, each 8+ games
  best3       best PPG of the previous three seasons, each 8+ games
Cutoff week 7, seasons 2010-2024 (prior seasons back to 2007 are not in the data, so best2
and best3 start from 2012 and 2013).
"""
import pandas as pd, numpy as np, os, glob, sys
from scipy.stats import spearmanr, pearsonr, t as tdist
from sklearn.linear_model import LinearRegression

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
C = int(sys.argv[1]) if len(sys.argv) > 1 else 7

ps = pd.concat([pd.read_csv(f, low_memory=False) for f in sorted(glob.glob(os.path.join(DATA, "ps_*.csv")))])
ps = ps[(ps.season_type == "REG") & (ps.position == "QB")].copy()
key = ["season", "player_id", "player_display_name"]
early = ps[ps.week <= C].groupby(key).agg(g=("week", "nunique"), att=("attempts", "sum"), fp=("fantasy_points", "sum")).reset_index()
late = ps[ps.week > C].groupby(key).agg(g=("week", "nunique"), att=("attempts", "sum"), fp=("fantasy_points", "sum")).reset_index()
early = early[(early.g >= 4) & (early.att >= 60)]; late = late[(late.g >= 4) & (late.att >= 60)]
early["ppg"] = early.fp / early.g; late["ppg"] = late.fp / late.g
late["rank2"] = late.groupby("season").ppg.rank(ascending=False, method="min")
df = early.merge(late[["season", "player_id", "ppg", "rank2"]], on=["season", "player_id"], suffixes=("", "_late"))

full = ps.groupby(["season", "player_id"]).agg(g=("week", "nunique"), fp=("fantasy_points", "sum")).reset_index()
full["ppg"] = full.fp / full.g
def prior(row, years, min_g):
    h = full[(full.player_id == row.player_id) & (full.season < row.season) & (full.season >= row.season - years) & (full.g >= min_g)]
    return h.ppg.max() if len(h) else np.nan
df["prev1_8g"] = df.apply(lambda r: prior(r, 1, 8), axis=1)
df["prev1_full"] = df.apply(lambda r: prior(r, 1, 14), axis=1)
df["best2"] = df.apply(lambda r: prior(r, 2, 8), axis=1)
df["best3"] = df.apply(lambda r: prior(r, 3, 8), axis=1)

def ols_p(X, y):
    m = LinearRegression().fit(X, y); n, k = X.shape; res = y - m.predict(X)
    Xc = np.column_stack([np.ones(n), X]); s2 = (res ** 2).sum() / (n - k - 1)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(Xc.T @ Xc)))[1:]; p = 2 * tdist.sf(np.abs(m.coef_ / se), n - k - 1)
    return m, p, m.score(X, y)
def partial_spearman(x, y, z):
    rx = x - LinearRegression().fit(z, x).predict(z); ry = y - LinearRegression().fit(z, y).predict(z)
    return spearmanr(rx, ry)[0]

print(f"=== Cutoff week {C} ===")
print(f"{'definition':12}{'n':>5}{'r prior->2nd-half PPG':>23}{'R2 1st-half only':>18}{'R2 + prior':>12}{'prior beta':>12}{'p':>8}{'partial rank corr':>19}")
rows = []
for d in ["prev1_8g", "prev1_full", "best2", "best3"]:
    s = df.dropna(subset=[d])
    s = s[s.season >= {"prev1_8g": 2011, "prev1_full": 2011, "best2": 2012, "best3": 2013}[d]]
    r0 = pearsonr(s[d], s.ppg_late)[0]
    _, _, r2a = ols_p(s[["ppg"]].values, s.ppg_late); m, p, r2b = ols_p(s[["ppg", d]].values, s.ppg_late)
    pr = partial_spearman(s.ppg - s[d], s.rank2, s[["ppg"]])
    print(f"{d:12}{len(s):>5}{r0:23.2f}{r2a:18.3f}{r2b:12.3f}{m.coef_[1]:12.2f}{p[1]:8.3f}{pr:19.2f}")
    rows.append(dict(definition=d, n=len(s), r_prior_late=r0, r2_first_only=r2a, r2_with_prior=r2b, beta=m.coef_[1], p=p[1], partial_rank_corr=pr))

# same players, all four definitions available, so the comparison is apples to apples
s = df.dropna(subset=["prev1_8g", "prev1_full", "best2", "best3"]); s = s[s.season >= 2013]
print(f"\nSame {len(s)} QB-seasons (2013+, all four definitions available):")
for d in ["prev1_8g", "prev1_full", "best2", "best3"]:
    m, p, r2b = ols_p(s[["ppg", d]].values, s.ppg_late)
    print(f"   {d:12} R2 {r2b:.3f}   beta {m.coef_[1]:+.2f}   p {p[1]:.3f}   partial rank corr {partial_spearman(s.ppg - s[d], s.rank2, s[['ppg']]):+.2f}")
_, _, r2a = ols_p(s[["ppg"]].values, s.ppg_late); print(f"   {'first half only':12} R2 {r2a:.3f}")

# quintiles for best3 gap
d = "best3"; s = df.dropna(subset=[d]); s = s[s.season >= 2013].copy(); s["gap"] = s.ppg - s[d]
s["q"] = pd.qcut(s.gap, 5, labels=["Q1 furthest below best", "Q2", "Q3", "Q4", "Q5 furthest above best"])
print(f"\nQuintiles of (first-half PPG - best of previous three seasons), n={len(s)}:")
print(s.groupby("q", observed=True).agg(n=("gap", "size"), gap=("gap", "mean"), best3=(d, "mean"), first_half=("ppg", "mean"), second_half=("ppg_late", "mean"),
                                        gain=("ppg_late", lambda x: (x - s.loc[x.index, "ppg"]).mean()), mean_rank=("rank2", "mean"),
                                        top12=("rank2", lambda x: (x <= 12).mean())).round(2).to_string())
pd.DataFrame(rows).to_csv(os.path.join(HERE, f"qb_track_record_week{C}.csv"), index=False)
