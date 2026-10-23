"""Does early-season team point differential predict rest-of-season QB fantasy PPG?

For each season 2010-2024 and cutoff week C:
  early_pd      team point differential per game, weeks 1..C
  early_qb      team QB fantasy points per team game, weeks 1..C   (traditional scoring)
  late_qb       team QB fantasy points per team game, weeks C+1..end
Team-level QB points (all QBs on the roster that week) so injuries/benchings don't drop rows.
Also a same-player variant: QB1 (most attempts through C) who also started >= 4 late games.

Reports pooled Pearson r for: early_pd -> late_qb, early_qb -> late_qb, and the partial
contribution of early_pd once early_qb is known (multiple regression), per cutoff.
"""
import pandas as pd, numpy as np, os, glob, sys
from scipy.stats import pearsonr
from sklearn.linear_model import LinearRegression

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
RENAME = {"SD": "LAC", "OAK": "LV", "STL": "LA"}
CUTS = [int(a) for a in sys.argv[1:]] or [5, 7, 9]

ps = pd.concat([pd.read_csv(f, low_memory=False) for f in sorted(glob.glob(os.path.join(DATA, "ps_*.csv")))])
ps = ps[(ps.season_type == "REG") & (ps.position == "QB")].copy()
ps["team"] = ps["recent_team"].replace(RENAME)

games = pd.read_csv(os.path.join(DATA, "games.csv"))
games = games[(games.game_type == "REG") & games.season.between(2010, 2024)].copy()
for c in ("home_team", "away_team"):
    games[c] = games[c].replace(RENAME)
h = games[["season", "week", "home_team", "home_score", "away_score"]].rename(columns={"home_team": "team", "home_score": "pf", "away_score": "pa"})
a = games[["season", "week", "away_team", "away_score", "home_score"]].rename(columns={"away_team": "team", "away_score": "pf", "home_score": "pa"})
tg = pd.concat([h, a]); tg["pd"] = tg.pf - tg.pa

def team_qb(df):
    return df.groupby(["season", "team"]).fantasy_points.sum()

print(f"{'cutoff':>7}{'n':>5}{'r early PD -> late QB':>24}{'r early QB -> late QB':>24}{'r both (R)':>12}{'PD beta|QB':>12}{'p':>8}   same-QB1: r PD->late | r QB->late")
for C in CUTS:
    e = tg[tg.week <= C].groupby(["season", "team"]).agg(g=("pd", "size"), pd=("pd", "sum"))
    l = tg[tg.week > C].groupby(["season", "team"]).agg(g=("pd", "size"), pd=("pd", "sum"))
    eq = team_qb(ps[ps.week <= C]); lq = team_qb(ps[ps.week > C])
    d = pd.DataFrame({"early_pd": e.pd / e.g, "early_qb": eq / e.g, "late_qb": lq / l.g, "late_pd": l.pd / l.g}).dropna()
    r1 = pearsonr(d.early_pd, d.late_qb)[0]; r2 = pearsonr(d.early_qb, d.late_qb)[0]
    Z = (d[["early_qb", "early_pd"]] - d[["early_qb", "early_pd"]].mean()) / d[["early_qb", "early_pd"]].std()
    m = LinearRegression().fit(Z, d.late_qb); R = np.sqrt(m.score(Z, d.late_qb)); beta_pd = m.coef_[1]
    # p-value for the PD coefficient via partial correlation t-test
    from scipy.stats import t as tdist
    resid_y = d.late_qb - LinearRegression().fit(Z[["early_qb"]], d.late_qb).predict(Z[["early_qb"]])
    resid_x = Z.early_pd - LinearRegression().fit(Z[["early_qb"]], Z.early_pd).predict(Z[["early_qb"]])
    pr = pearsonr(resid_x, resid_y)[0]; n = len(d); tstat = pr*np.sqrt((n-3)/(1-pr**2)); p_pd = 2*tdist.sf(abs(tstat), n-3)
    # same-player variant
    qb1 = ps[ps.week <= C].groupby(["season", "team", "player_id"]).attempts.sum().reset_index()
    qb1 = qb1.sort_values("attempts", ascending=False).groupby(["season", "team"]).head(1)
    late_p = ps[ps.week > C].groupby(["season", "team", "player_id"]).agg(gp=("week", "nunique"), fp=("fantasy_points", "sum")).reset_index()
    early_p = ps[ps.week <= C].groupby(["season", "team", "player_id"]).agg(gp=("week", "nunique"), fp=("fantasy_points", "sum")).reset_index()
    s = qb1.merge(late_p, on=["season", "team", "player_id"]).merge(early_p, on=["season", "team", "player_id"], suffixes=("_l", "_e"))
    s = s[s.gp_l >= 4].merge(d[["early_pd"]], left_on=["season", "team"], right_index=True)
    s["late_ppg"] = s.fp_l / s.gp_l; s["early_ppg"] = s.fp_e / s.gp_e
    r3 = pearsonr(s.early_pd, s.late_ppg)[0]; r4 = pearsonr(s.early_ppg, s.late_ppg)[0]
    print(f"{C:>7}{len(d):>5}{r1:24.2f}{r2:24.2f}{R:12.2f}{beta_pd:12.2f}{p_pd:8.3f}   n={len(s):<4} {r3:.2f} | {r4:.2f}")

# per-season view at week 7
C = 7
e = tg[tg.week <= C].groupby(["season", "team"]).agg(g=("pd", "size"), pd=("pd", "sum"))
l = tg[tg.week > C].groupby(["season", "team"]).agg(g=("pd", "size"))
eq = team_qb(ps[ps.week <= C]); lq = team_qb(ps[ps.week > C])
d = pd.DataFrame({"early_pd": e.pd / e.g, "early_qb": eq / e.g, "late_qb": lq / l.g}).dropna().reset_index()
print(f"\nPer season, cutoff week {C}:  r(early PD -> late QB ppg)   r(early QB ppg -> late QB ppg)")
rows = []
for s_, g in d.groupby("season"):
    r1 = pearsonr(g.early_pd, g.late_qb)[0]; r2 = pearsonr(g.early_qb, g.late_qb)[0]
    rows.append((s_, r1, r2)); print(f"  {s_}   {r1:5.2f}   {r2:5.2f}")
pd.DataFrame(rows, columns=["season", "r_pd_to_lateqb", "r_qb_to_lateqb"]).to_csv(os.path.join(HERE, "pointdiff_predicts_qb_week7.csv"), index=False)
