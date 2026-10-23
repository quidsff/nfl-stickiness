"""How correlated is QB fantasy PPG with team point differential, season by season (2010-2024)?

Scoring: nflverse `fantasy_points` = standard/traditional (4 pts per pass TD, -2 INT,
0.04/pass yd, 0.1/rush yd, 6 per rush TD, -2 fumble lost).

Two QB definitions per team-season:
  qb1  the team's leading passer by attempts; his fantasy PPG over games he played
  all  all QB fantasy points the team produced, divided by team games (what the team's
       QB slot actually delivered regardless of who played)
Point differential per game uses the full regular season from games.csv.
"""
import pandas as pd, numpy as np, os, glob, sys
PASS_TD = int(sys.argv[1]) if len(sys.argv) > 1 else 4   # points per passing TD (4 = traditional, 6 = equal to rushing)
from scipy.stats import pearsonr, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
RENAME = {"SD": "LAC", "OAK": "LV", "STL": "LA"}

ps = pd.concat([pd.read_csv(f, low_memory=False) for f in sorted(glob.glob(os.path.join(DATA, "ps_*.csv")))])
ps = ps[(ps.season_type == "REG") & (ps.position == "QB")].copy()
ps["recent_team"] = ps["recent_team"].replace(RENAME)
ps["fantasy_points"] = ps["fantasy_points"] + (PASS_TD - 4) * ps["passing_tds"].fillna(0)
print(f"Scoring: {PASS_TD} points per passing TD\n")

games = pd.read_csv(os.path.join(DATA, "games.csv"))
games = games[(games.game_type == "REG") & games.season.between(2010, 2024)].copy()
for c in ("home_team", "away_team"):
    games[c] = games[c].replace(RENAME)
home = games[["season", "home_team", "home_score", "away_score"]].rename(columns={"home_team": "team", "home_score": "pf", "away_score": "pa"})
away = games[["season", "away_team", "away_score", "home_score"]].rename(columns={"away_team": "team", "away_score": "pf", "home_score": "pa"})
team = pd.concat([home, away]).groupby(["season", "team"]).agg(g=("pf", "size"), pf=("pf", "sum"), pa=("pa", "sum")).reset_index()
team["pd_pg"] = (team.pf - team.pa) / team.g
team["ppg"] = team.pf / team.g

# all-QB fantasy per team game
allqb = ps.groupby(["season", "recent_team"]).fantasy_points.sum().reset_index().rename(columns={"recent_team": "team", "fantasy_points": "qb_fp"})
# QB1 = most attempts for that team that season
qb = ps.groupby(["season", "recent_team", "player_id", "player_display_name"]).agg(
    att=("attempts", "sum"), gp=("week", "nunique"), fp=("fantasy_points", "sum")).reset_index()
qb1 = qb.sort_values("att", ascending=False).groupby(["season", "recent_team"]).head(1).rename(columns={"recent_team": "team"})
qb1["qb1_ppg"] = qb1.fp / qb1.gp

df = team.merge(allqb, on=["season", "team"]).merge(qb1[["season", "team", "player_display_name", "gp", "qb1_ppg"]], on=["season", "team"])
df["allqb_ppg"] = df.qb_fp / df.g

print(f"{'season':8}{'n':>4}{'r QB1 ppg':>11}{'r all-QB ppg':>14}{'r QB1 vs PPG':>14}   top QB1 / bottom QB1")
rows = []
for s, d in df.groupby("season"):
    r1 = pearsonr(d.qb1_ppg, d.pd_pg)[0]; r2 = pearsonr(d.allqb_ppg, d.pd_pg)[0]; r3 = pearsonr(d.qb1_ppg, d.ppg)[0]
    top = d.sort_values("qb1_ppg").iloc[-1]; bot = d.sort_values("qb1_ppg").iloc[0]
    rows.append(dict(season=s, n=len(d), r_qb1_pd=r1, r_allqb_pd=r2, r_qb1_ppg=r3))
    print(f"{s:<8}{len(d):>4}{r1:11.2f}{r2:14.2f}{r3:14.2f}   {top.player_display_name} {top.qb1_ppg:.1f} / {bot.player_display_name} {bot.qb1_ppg:.1f}")
res = pd.DataFrame(rows)
print(f"\n{'mean':8}{'':4}{res.r_qb1_pd.mean():11.2f}{res.r_allqb_pd.mean():14.2f}{res.r_qb1_ppg.mean():14.2f}")
print(f"{'pooled':8}{len(df):>4}{pearsonr(df.qb1_ppg, df.pd_pg)[0]:11.2f}{pearsonr(df.allqb_ppg, df.pd_pg)[0]:14.2f}{pearsonr(df.qb1_ppg, df.ppg)[0]:14.2f}")
# trend
from scipy.stats import linregress
lr = linregress(res.season, res.r_qb1_pd)
print(f"\ntrend in r(QB1 ppg, point diff): {lr.slope:+.4f} per season, p={lr.pvalue:.2f}")
print("\nslope: each +1 QB1 fantasy point per game ~ {:+.2f} team point diff per game (pooled)".format(
    np.polyfit(df.qb1_ppg, df.pd_pg, 1)[0]))
res.to_csv(os.path.join(HERE, f"qb_vs_pointdiff_by_season_{PASS_TD}pt.csv"), index=False)
df.to_csv(os.path.join(HERE, "qb_vs_pointdiff_teams.csv" if PASS_TD == 4 else f"qb_vs_pointdiff_teams_{PASS_TD}pt.csv"), index=False)
