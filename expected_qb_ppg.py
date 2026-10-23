"""Expected QB fantasy PPG from team context (2010-2024, traditional scoring).

Fits three pooled OLS models on full regular seasons (479 team-seasons):
  A: QB1 fantasy PPG ~ team point diff / game
  B: QB1 fantasy PPG ~ team points scored / game
  C: QB1 fantasy PPG ~ both
Prints the equations, a lookup table, and 2024 QB1s ranked by actual minus expected.
QB1 = team's leading passer by attempts, PPG over games he played.
"""
import pandas as pd, numpy as np, os
from sklearn.linear_model import LinearRegression

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "qb_vs_pointdiff_teams.csv"))  # from qb_vs_pointdiff.py
df = df[df.gp >= 8].copy()                                           # QB1 played at least half a season
y = df.qb1_ppg

def fit(cols):
    m = LinearRegression().fit(df[cols], y); pred = m.predict(df[cols])
    rmse = np.sqrt(np.mean((y - pred) ** 2)); r2 = m.score(df[cols], y)
    return m, pred, rmse, r2

mA, pA, rmseA, r2A = fit(["pd_pg"]); mB, pB, rmseB, r2B = fit(["ppg"]); mC, pC, rmseC, r2C = fit(["pd_pg", "ppg"])
print(f"n = {len(df)} team-seasons (QB1 with 8+ games)\n")
print(f"A  expected QB PPG = {mA.intercept_:.2f} + {mA.coef_[0]:.3f} x (point diff/game)            R2 {r2A:.2f}  RMSE {rmseA:.2f}")
print(f"B  expected QB PPG = {mB.intercept_:.2f} + {mB.coef_[0]:.3f} x (team points/game)           R2 {r2B:.2f}  RMSE {rmseB:.2f}")
print(f"C  expected QB PPG = {mC.intercept_:.2f} + {mC.coef_[0]:.3f} x (point diff/game) + {mC.coef_[1]:.3f} x (team points/game)   R2 {r2C:.2f}  RMSE {rmseC:.2f}")

print("\nLookup (model B, team points per game -> expected QB1 fantasy PPG):")
for ppg in range(14, 34, 2):
    print(f"  {ppg:>2} pts/game  ->  {mB.intercept_ + mB.coef_[0]*ppg:5.1f} QB PPG")
print("\nLookup (model A, team point differential per game):")
for pd_ in range(-12, 14, 3):
    print(f"  {pd_:+3d} pt diff   ->  {mA.intercept_ + mA.coef_[0]*pd_:5.1f} QB PPG")

df["exp_ppg"] = pC; df["over_exp"] = df.qb1_ppg - df.exp_ppg
d24 = df[df.season == 2024].sort_values("over_exp", ascending=False)
print("\n2024 QB1s: actual vs expected from team context (model C)")
print(f"{'QB':22}{'team':>5}{'actual':>8}{'expected':>10}{'diff':>7}")
for _, r in d24.iterrows():
    print(f"{r.player_display_name:22}{r.team:>5}{r.qb1_ppg:8.1f}{r.exp_ppg:10.1f}{r.over_exp:+7.1f}")
df[["season", "team", "player_display_name", "gp", "ppg", "pd_pg", "qb1_ppg", "exp_ppg", "over_exp"]].to_csv(
    os.path.join(HERE, "expected_qb_ppg.csv"), index=False)
