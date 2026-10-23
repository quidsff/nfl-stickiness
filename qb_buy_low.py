"""Spotting buy-low QBs: which parts of a QB's fantasy line are luck, and does the luck revert?

Steps
 1. Component stickiness: for each QB-season (2010-2024) with 4+ games on each side of the
    week-C cutoff, correlate weeks 1..C with weeks C+1..end for each rate stat.
 2. "Sticky" expected PPG: rebuild fantasy PPG from the QB's own early VOLUME and YARDAGE
    with league-average TD rate and INT rate substituted in. Residual = actual - sticky.
    Split the residual into td_luck (pass TD rate above/below league avg x attempts x 4 + rush TD
    luck) and int_luck (INT rate vs avg x attempts x -2).
 3. Test: late PPG ~ early PPG + residual (and its parts). Quintile table of late-minus-early.
    Survivorship: how many week-C QB1s fail the 4-game late threshold, by residual quintile.
 4. 2024 week-7 buy-low list.

Traditional scoring: 0.04/pass yd, 4/pass TD, -2/INT, 0.1/rush yd, 6/rush TD, -2/fumble lost.
"""
import pandas as pd, numpy as np, os, glob, sys
from scipy.stats import pearsonr, t as tdist
from sklearn.linear_model import LinearRegression

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
C = int(sys.argv[1]) if len(sys.argv) > 1 else 7
MIN_LATE = 4

ps = pd.concat([pd.read_csv(f, low_memory=False) for f in sorted(glob.glob(os.path.join(DATA, "ps_*.csv")))])
ps = ps[(ps.season_type == "REG") & (ps.position == "QB")].copy()
ps["team"] = ps.recent_team.replace({"SD": "LAC", "OAK": "LV", "STL": "LA"})
ps["fum_lost"] = ps.sack_fumbles_lost.fillna(0) + ps.rushing_fumbles_lost.fillna(0)
ps["half"] = np.where(ps.week <= C, "early", "late")

AGG = dict(g=("week", "nunique"), att=("attempts", "sum"), pyds=("passing_yards", "sum"), ptd=("passing_tds", "sum"),
           ints=("interceptions", "sum"), sacks=("sacks", "sum"), car=("carries", "sum"), ryds=("rushing_yards", "sum"),
           rtd=("rushing_tds", "sum"), fum=("fum_lost", "sum"), fp=("fantasy_points", "sum"))
agg = ps.groupby(["season", "player_id", "player_display_name", "half"]).agg(**AGG).reset_index()

def rates(d):
    d = d.copy()
    d["ppg"] = d.fp / d.g; d["att_pg"] = d.att / d.g; d["ypa"] = d.pyds / d.att
    d["ptd_rate"] = d.ptd / d.att; d["int_rate"] = d.ints / d.att
    d["car_pg"] = d.car / d.g; d["ypc"] = d.ryds / d.car.replace(0, np.nan); d["rtd_rate"] = d.rtd / d.car.replace(0, np.nan)
    d["ryds_pg"] = d.ryds / d.g
    return d
agg = rates(agg)
e = agg[agg.half == "early"].set_index(["season", "player_id"]); l = agg[agg.half == "late"].set_index(["season", "player_id"])
both = e.join(l, lsuffix="_e", rsuffix="_l", how="inner")
both = both[(both.g_e >= 4) & (both.g_l >= MIN_LATE) & (both.att_e >= 60) & (both.att_l >= 60)]

print(f"=== Cutoff week {C}; {len(both)} QB-seasons with 4+ games and 60+ attempts each side ===")
print("\n1. Component stickiness (r, early vs late, same QB)")
comps = [("att_pg", "Attempts/game"), ("ypa", "Yards/attempt"), ("ptd_rate", "Pass TD rate"), ("int_rate", "INT rate"),
         ("car_pg", "Carries/game"), ("ryds_pg", "Rush yds/game"), ("rtd_rate", "Rush TD rate"), ("ppg", "Fantasy PPG")]
for c, n in comps:
    d = both[[c + "_e", c + "_l"]].dropna()
    print(f"   {n:16} r = {pearsonr(d[c+'_e'], d[c+'_l'])[0]:5.2f}")

# league-average rates per season (early half, all QBs) for substitution
lg = agg[agg.half == "early"].groupby("season").agg(att=("att", "sum"), ptd=("ptd", "sum"), ints=("ints", "sum"), car=("car", "sum"), rtd=("rtd", "sum"))
lg["ptd_rate"] = lg.ptd / lg.att; lg["int_rate"] = lg.ints / lg.att; lg["rtd_rate"] = lg.rtd / lg.car

def sticky_ppg(r, sfx="_e"):
    s = lg.loc[r.name[0]]; v = lambda k: r[k + sfx]
    pts = 0.04 * v("pyds") + 4 * s.ptd_rate * v("att") - 2 * s.int_rate * v("att") + 0.1 * v("ryds") + 6 * s.rtd_rate * v("car") - 2 * v("fum")
    return pts / v("g")
both["sticky_ppg"] = both.apply(sticky_ppg, axis=1)
both["resid"] = both.ppg_e - both.sticky_ppg
both["td_luck"] = both.apply(lambda r: (4 * (r.ptd_e - lg.loc[r.name[0]].ptd_rate * r.att_e) + 6 * (r.rtd_e - lg.loc[r.name[0]].rtd_rate * r.car_e)) / r.g_e, axis=1)
both["int_luck"] = both.apply(lambda r: -2 * (r.ints_e - lg.loc[r.name[0]].int_rate * r.att_e) / r.g_e, axis=1)
both["gain"] = both.ppg_l - both.ppg_e
full = agg.groupby(["season", "player_id"]).agg(g=("g", "sum"), fp=("fp", "sum")).reset_index()
full = full[full.g >= 8]; full["prior_ppg"] = full.fp / full.g; full["season"] += 1
both = both.reset_index().merge(full[["season", "player_id", "prior_ppg"]], on=["season", "player_id"], how="left").set_index(["season", "player_id"])

print("\n2. Residual stickiness: r(early residual, late residual-equivalent) and r(td_luck early, td_luck late)")
late_td_luck = both.apply(lambda r: (4 * (r.ptd_l - lg.loc[r.name[0]].ptd_rate * r.att_l) + 6 * (r.rtd_l - lg.loc[r.name[0]].rtd_rate * r.car_l)) / r.g_l, axis=1)
print(f"   TD luck early vs late: r = {pearsonr(both.td_luck, late_td_luck)[0]:5.2f}")

print("\n3. Test: late PPG ~ early PPG + residual")
def ols(cols):
    X = both[cols].values; m = LinearRegression().fit(X, both.ppg_l); pred = m.predict(X)
    n, k = X.shape; resid = both.ppg_l - pred; s2 = (resid ** 2).sum() / (n - k - 1)
    Xc = np.column_stack([np.ones(n), X]); cov = s2 * np.linalg.inv(Xc.T @ Xc); se = np.sqrt(np.diag(cov))[1:]
    tt = m.coef_ / se; p = 2 * tdist.sf(np.abs(tt), n - k - 1)
    return m, se, p, m.score(X, both.ppg_l)
for cols in [["ppg_e"], ["ppg_e", "resid"], ["ppg_e", "td_luck", "int_luck"], ["sticky_ppg"], ["sticky_ppg", "resid"]]:
    m, se, p, r2 = ols(cols)
    terms = "  ".join(f"{c}: {b:+.2f} (p={pp:.3f})" for c, b, pp in zip(cols, m.coef_, p))
    print(f"   R2 {r2:.3f}   {terms}")
print("\n3b. With prior-season PPG (QBs who had 8+ games the year before, n=%d)" % both.prior_ppg.notna().sum())
sub = both[both.prior_ppg.notna()].copy(); sub["drop_vs_prior"] = sub.ppg_e - sub.prior_ppg
both_all = both; both = sub
for cols in [["ppg_e"], ["prior_ppg"], ["ppg_e", "prior_ppg"], ["ppg_e", "prior_ppg", "resid"], ["ppg_e", "prior_ppg", "car_pg_e"]]:
    m, se, p, r2 = ols(cols)
    terms = "  ".join(f"{c}: {b:+.2f} (p={pp:.3f})" for c, b, pp in zip(cols, m.coef_, p))
    print(f"   R2 {r2:.3f}   {terms}")
print("\n   Quintiles of (early PPG - prior-season PPG):")
sub["qd"] = pd.qcut(sub.drop_vs_prior, 5, labels=["Q1 biggest drop", "Q2", "Q3", "Q4", "Q5 biggest jump"])
sub["late_rank"] = sub.groupby(level=0).ppg_l.rank(ascending=False)
print(sub.groupby("qd", observed=True).agg(n=("gain", "size"), drop_vs_prior=("drop_vs_prior", "mean"), prior=("prior_ppg", "mean"), early_ppg=("ppg_e", "mean"), late_ppg=("ppg_l", "mean"), gain=("gain", "mean"), pct_top12_late=("late_rank", lambda x: (x <= 12).mean())).round(2).to_string())
both = both_all
for cols in []:
    m, se, p, r2 = ols(cols)
    terms = "  ".join(f"{c}: {b:+.2f} (p={pp:.3f})" for c, b, pp in zip(cols, m.coef_, p))
    print(f"   R2 {r2:.3f}   {terms}")

print("\n4. Quintiles of early residual (actual - sticky expected), week-%d cutoff" % C)
both["q"] = pd.qcut(both.resid, 5, labels=["Q1 unluckiest", "Q2", "Q3", "Q4", "Q5 luckiest"])
tab = both.groupby("q", observed=True).agg(n=("gain", "size"), resid=("resid", "mean"), early_ppg=("ppg_e", "mean"),
                                           late_ppg=("ppg_l", "mean"), gain=("gain", "mean"))
# top-12 finish: rank late ppg within season among all qualifying QBs
both["late_rank"] = both.groupby(level=0).ppg_l.rank(ascending=False)
tab["pct_top12_late"] = both.groupby("q", observed=True).apply(lambda d: (d.late_rank <= 12).mean())
tab["pct_top12_early"] = both.assign(er=both.groupby(level=0).ppg_e.rank(ascending=False)).groupby("q", observed=True).apply(lambda d: (d.er <= 12).mean())
print(tab[["n", "resid", "early_ppg", "late_ppg", "gain", "pct_top12_early", "pct_top12_late"]].round(2).to_string())

# survivorship
allE = agg[(agg.half == "early") & (agg.g >= 4) & (agg.att >= 60)].set_index(["season", "player_id"])
allE["sticky_ppg"] = allE.apply(lambda r: sticky_ppg(r, ""), axis=1); allE["resid"] = allE.ppg - allE.sticky_ppg
allE["survived"] = allE.index.isin(both.index)
allE["q"] = pd.qcut(allE.resid, 5, labels=["Q1 unluckiest", "Q2", "Q3", "Q4", "Q5 luckiest"])
print("\n5. Survivorship: share of early qualifiers who kept starting (4+ late games, 60+ att)")
print(allE.groupby("q", observed=True).survived.agg(["size", "mean"]).round(2).to_string())

print(f"\n6. 2024 at week {C}: buy-low candidates (most negative residual first)")
d24 = both.loc[2024].sort_values("resid")
print(f"   {'QB':22}{'early PPG':>10}{'sticky exp':>11}{'resid':>7}{'TD luck':>9}{'INT luck':>9}{'late PPG':>9}{'gain':>7}")
for _, r in d24.iterrows():
    print(f"   {r.player_display_name_e:22}{r.ppg_e:10.1f}{r.sticky_ppg:11.1f}{r.resid:+7.1f}{r.td_luck:+9.1f}{r.int_luck:+9.1f}{r.ppg_l:9.1f}{r.gain:+7.1f}")
both.reset_index()[["season", "player_display_name_e", "g_e", "ppg_e", "sticky_ppg", "resid", "td_luck", "int_luck", "ppg_l", "gain"]].to_csv(
    os.path.join(HERE, f"qb_buy_low_week{C}.csv"), index=False)
