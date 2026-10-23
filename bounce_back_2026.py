"""Apply Studies 5-7 to the current season: which QBs are set up to bounce back after week 7?

Rule from the studies: sort by (2026 PPG through week 7) minus (2025 PPG, 8+ games).
Quarterbacks 5+ points below last season gained ~2.7 PPG over the second half historically.
Also shown: carries per game (sticky, adds signal) and the luck gap (shown for interest;
it predicted nothing). Traditional scoring.
"""
import pandas as pd, numpy as np, os
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
C = 7
cols = ["player_id", "player_display_name", "team", "week", "season_type", "position", "attempts", "passing_yards", "passing_tds",
        "passing_interceptions", "carries", "rushing_yards", "rushing_tds", "sack_fumbles_lost", "rushing_fumbles_lost", "fantasy_points"]
p25 = pd.read_csv(os.path.join(DATA, "spw_2025.csv"), low_memory=False)[cols]
p26 = pd.read_csv(os.path.join(DATA, "spw_2026.csv"), low_memory=False)[cols]
p25 = p25[(p25.position == "QB") & (p25.season_type == "REG")]; p26 = p26[(p26.position == "QB") & (p26.season_type == "REG") & (p26.week <= C)]

prior = p25.groupby(["player_id", "player_display_name"]).agg(g25=("week", "nunique"), fp=("fantasy_points", "sum")).reset_index()
prior = prior[prior.g25 >= 8]; prior["ppg25"] = prior.fp / prior.g25

cur = p26.groupby(["player_id", "player_display_name"]).agg(team=("team", "last"), g=("week", "nunique"), att=("attempts", "sum"), fp=("fantasy_points", "sum"),
                                                            car=("carries", "sum"), pyds=("passing_yards", "sum"), ptd=("passing_tds", "sum"),
                                                            ints=("passing_interceptions", "sum"), ryds=("rushing_yards", "sum"), rtd=("rushing_tds", "sum"),
                                                            fum=("sack_fumbles_lost", "sum")).reset_index()
cur = cur[(cur.g >= 4) & (cur.att >= 60)].copy()
cur["ppg26"] = cur.fp / cur.g; cur["car_pg"] = cur.car / cur.g
# luck gap at 2026 league-average rates
ptd_r = cur.ptd.sum() / cur.att.sum(); int_r = cur.ints.sum() / cur.att.sum(); rtd_r = cur.rtd.sum() / cur.car.sum()
cur["sticky"] = (0.04 * cur.pyds + 4 * ptd_r * cur.att - 2 * int_r * cur.att + 0.1 * cur.ryds + 6 * rtd_r * cur.car - 2 * cur.fum) / cur.g
cur["luck_gap"] = cur.ppg26 - cur.sticky
cur["rank26"] = cur.ppg26.rank(ascending=False, method="min").astype(int)

df = cur.merge(prior[["player_id", "g25", "ppg25"]], on="player_id", how="left")
df["gap"] = df.ppg26 - df.ppg25
df = df.sort_values("gap")
print(f"2026 through week {C}: {len(df)} QBs with 4+ games and 60+ attempts; {df.ppg25.notna().sum()} have a 2025 season of 8+ games\n")
print(f"{'QB':22}{'team':>5}{'2025 PPG':>9}{'2026 PPG':>9}{'rank':>5}{'gap':>7}{'car/g':>7}{'luck':>6}   read")
for _, r in df.iterrows():
    if pd.isna(r.ppg25): read = "no 2025 track record (rookie or <8 games)"
    elif r.gap <= -5: read = "BUY: 5+ below last season"
    elif r.gap <= -2: read = "lean buy"
    elif r.gap >= 5: read = "SELL-HIGH candidate: 5+ above last season"
    elif r.gap >= 2: read = "lean sell"
    else: read = "hold"
    print(f"{r.player_display_name:22}{r.team:>5}{(f'{r.ppg25:.1f}' if pd.notna(r.ppg25) else '--'):>9}{r.ppg26:9.1f}{r.rank26:5d}{(f'{r.gap:+.1f}' if pd.notna(r.gap) else '--'):>7}{r.car_pg:7.1f}{r.luck_gap:+6.1f}   {read}")
df.to_csv(os.path.join(HERE, "bounce_back_2026_week7.csv"), index=False)
