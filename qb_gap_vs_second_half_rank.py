"""Study 6: first-half gaps vs. second-half rank.

For each QB-season 2010-2024 (cutoff week C), three first-half gaps:
  luck_gap   first-half PPG minus "sticky expected" PPG (own volume and yardage at
             league-average TD/INT rates)            -- Study 5's residual
  team_gap   first-half PPG minus expected PPG from team points per game (Study 4 line,
             refit on first-half team points)
  prior_gap  first-half PPG minus last season's PPG

Outcome: the QB's rank by PPG over weeks C+1..end, among every QB with 4+ games and 60+
attempts in that span of that season. Report, by quintile of each gap: mean second-half
rank, share top-6, top-12, top-24; plus the rank correlation (Spearman) of each gap with
second-half rank controlling for first-half PPG via partial correlation.
"""
import pandas as pd, numpy as np, os, glob, sys
from scipy.stats import spearmanr, pearsonr
from sklearn.linear_model import LinearRegression

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
C = int(sys.argv[1]) if len(sys.argv) > 1 else 7
RENAME = {"SD": "LAC", "OAK": "LV", "STL": "LA"}

ps = pd.concat([pd.read_csv(f, low_memory=False) for f in sorted(glob.glob(os.path.join(DATA, "ps_*.csv")))])
ps = ps[(ps.season_type == "REG") & (ps.position == "QB")].copy()
ps["team"] = ps.recent_team.replace(RENAME)
ps["fum"] = ps.sack_fumbles_lost.fillna(0) + ps.rushing_fumbles_lost.fillna(0)
AGG = dict(g=("week", "nunique"), att=("attempts", "sum"), pyds=("passing_yards", "sum"), ptd=("passing_tds", "sum"),
           ints=("interceptions", "sum"), car=("carries", "sum"), ryds=("rushing_yards", "sum"), rtd=("rushing_tds", "sum"),
           fum=("fum", "sum"), fp=("fantasy_points", "sum"))
key = ["season", "player_id", "player_display_name"]
early = ps[ps.week <= C].groupby(key).agg(**AGG).reset_index(); early["ppg"] = early.fp / early.g
late = ps[ps.week > C].groupby(key).agg(**AGG).reset_index(); late["ppg"] = late.fp / late.g
early = early[(early.g >= 4) & (early.att >= 60)]; late = late[(late.g >= 4) & (late.att >= 60)]
late["rank2"] = late.groupby("season").ppg.rank(ascending=False, method="min")
# primary team for team-context expectation
team_of = ps[ps.week <= C].groupby(key + ["team"]).attempts.sum().reset_index().sort_values("attempts", ascending=False).groupby(key).head(1)
early = early.merge(team_of[key + ["team"]], on=key)

# league-average rates (first half)
lg = early.groupby("season").agg(att=("att", "sum"), ptd=("ptd", "sum"), ints=("ints", "sum"), car=("car", "sum"), rtd=("rtd", "sum"))
lg["ptd_r"] = lg.ptd / lg.att; lg["int_r"] = lg.ints / lg.att; lg["rtd_r"] = lg.rtd / lg.car
def sticky(r):
    s = lg.loc[r.season]
    return (0.04 * r.pyds + 4 * s.ptd_r * r.att - 2 * s.int_r * r.att + 0.1 * r.ryds + 6 * s.rtd_r * r.car - 2 * r.fum) / r.g
early["luck_gap"] = early.ppg - early.apply(sticky, axis=1)

# team-context expectation from first-half team points per game
games = pd.read_csv(os.path.join(DATA, "games.csv"))
games = games[(games.game_type == "REG") & games.season.between(2010, 2024) & (games.week <= C)].copy()
for c in ("home_team", "away_team"): games[c] = games[c].replace(RENAME)
tp = pd.concat([games[["season", "home_team", "home_score"]].rename(columns={"home_team": "team", "home_score": "pf"}),
                games[["season", "away_team", "away_score"]].rename(columns={"away_team": "team", "away_score": "pf"})])
tp = tp.groupby(["season", "team"]).pf.mean().rename("team_ppg").reset_index()
early = early.merge(tp, on=["season", "team"])
m = LinearRegression().fit(early[["team_ppg"]], early.ppg)
early["team_gap"] = early.ppg - m.predict(early[["team_ppg"]])

# prior season
full = ps.groupby(["season", "player_id"]).agg(g=("week", "nunique"), fp=("fantasy_points", "sum")).reset_index()
full = full[full.g >= 8]; full["prior_ppg"] = full.fp / full.g; full["season"] += 1
early = early.merge(full[["season", "player_id", "prior_ppg"]], on=["season", "player_id"], how="left")
early["prior_gap"] = early.ppg - early.prior_ppg

df = early.merge(late[["season", "player_id", "ppg", "rank2"]], on=["season", "player_id"], suffixes=("", "_late"))
print(f"=== Cutoff week {C}: {len(df)} QB-seasons with 4+ games/60+ att both halves; second-half rank among all such QBs ===")
print(f"Team-context line (first half): QB PPG = {m.intercept_:.2f} + {m.coef_[0]:.3f} x team points/game\n")

def partial_spearman(x, y, z):
    rx = x - LinearRegression().fit(z, x).predict(z); ry = y - LinearRegression().fit(z, y).predict(z)
    return spearmanr(rx, ry)[0]

for gap, label in [("luck_gap", "Luck gap (actual - own volume/yardage at league-avg TD/INT rates)"),
                   ("team_gap", "Team gap (actual - what team points per game implies)"),
                   ("prior_gap", "Prior gap (actual - last season's PPG)")]:
    d = df.dropna(subset=[gap]).copy()
    d["q"] = pd.qcut(d[gap], 5, labels=["Q1 most negative", "Q2", "Q3", "Q4", "Q5 most positive"])
    print(f"-- {label}; n={len(d)} --")
    print(f"   rank corr with 2nd-half rank: {spearmanr(d[gap], d.rank2)[0]:+.2f}   controlling for 1st-half PPG: {partial_spearman(d[gap], d.rank2, d[['ppg']]):+.2f}   (negative = bigger gap, better rank)")
    t = d.groupby("q", observed=True).agg(n=("rank2", "size"), gap=(gap, "mean"), first_half_ppg=("ppg", "mean"), second_half_ppg=("ppg_late", "mean"),
                                        mean_rank=("rank2", "mean"), top6=("rank2", lambda x: (x <= 6).mean()),
                                        top12=("rank2", lambda x: (x <= 12).mean()), top24=("rank2", lambda x: (x <= 24).mean()))
    print(t.round(2).to_string()); print()

# head-to-head: among QBs with similar first-half PPG, does the gap sort second-half rank?
print("-- Within first-half PPG bands: second-half top-12 rate by luck-gap half --")
df["band"] = pd.cut(df.ppg, [0, 12, 15, 18, 21, 99], labels=["<12", "12-15", "15-18", "18-21", "21+"])
for b, d in df.groupby("band", observed=True):
    lo = d[d.luck_gap <= d.luck_gap.median()]; hi = d[d.luck_gap > d.luck_gap.median()]
    print(f"   {b:>6} PPG  n={len(d):3d}   negative-gap half: top-12 {100*(lo.rank2<=12).mean():4.0f}%  mean rank {lo.rank2.mean():5.1f}   positive-gap half: top-12 {100*(hi.rank2<=12).mean():4.0f}%  mean rank {hi.rank2.mean():5.1f}")
df.to_csv(os.path.join(HERE, f"qb_gap_vs_second_half_rank_week{C}.csv"), index=False)
