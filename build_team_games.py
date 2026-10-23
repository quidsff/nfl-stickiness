"""Build a team-game table from nflverse play-by-play and schedules.

One row per team per game (regular season + playoffs) with:
  points_for, points_against, off_epa, def_epa (opponent's EPA, lower is better),
  takeaways, giveaways, off_plays, def_plays.
Output: data/team_games.csv
"""
import pandas as pd, glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

USECOLS = ["game_id", "season", "week", "season_type", "posteam", "defteam",
           "home_team", "away_team", "epa", "play_type", "interception", "fumble_lost",
           "play"]

frames = []
for f in sorted(glob.glob(os.path.join(DATA, "pbp_*.csv.gz"))):
    df = pd.read_csv(f, usecols=USECOLS, low_memory=False)
    # real offensive plays only (nflverse 'play' flag = 1 for pass/run plays incl. penalties-with-play)
    df = df[(df["play"] == 1) & df["posteam"].notna() & df["epa"].notna()]
    df["turnover"] = ((df["interception"] == 1) | (df["fumble_lost"] == 1)).astype(int)
    off = df.groupby(["game_id", "season", "week", "season_type", "posteam"]).agg(
        off_epa=("epa", "sum"), off_plays=("epa", "size"), giveaways=("turnover", "sum")).reset_index()
    off = off.rename(columns={"posteam": "team"})
    de = df.groupby(["game_id", "defteam"]).agg(
        def_epa=("epa", "sum"), def_plays=("epa", "size"), takeaways=("turnover", "sum")).reset_index()
    de = de.rename(columns={"defteam": "team"})
    frames.append(off.merge(de, on=["game_id", "team"], how="left"))
    print(f, len(off))

tg = pd.concat(frames, ignore_index=True)

games = pd.read_csv(os.path.join(DATA, "games.csv"))
games = games[games["season"].between(2016, 2024)].copy()
# nflverse pbp uses current franchise codes throughout; align the schedule file
RENAME = {"SD": "LAC", "OAK": "LV", "STL": "LA"}
for c in ("home_team", "away_team"):
    games[c] = games[c].replace(RENAME)
home = games[["game_id", "home_team", "home_score", "away_score"]].rename(
    columns={"home_team": "team", "home_score": "points_for", "away_score": "points_against"})
away = games[["game_id", "away_team", "away_score", "home_score"]].rename(
    columns={"away_team": "team", "away_score": "points_for", "home_score": "points_against"})
scores = pd.concat([home, away], ignore_index=True)

tg = tg.merge(scores, on=["game_id", "team"], how="inner")
tg["point_diff"] = tg["points_for"] - tg["points_against"]
tg["to_diff"] = tg["takeaways"] - tg["giveaways"]
tg["win"] = (tg["point_diff"] > 0).astype(float)
tg.loc[tg["point_diff"] == 0, "win"] = 0.5
tg = tg.sort_values(["season", "week", "game_id", "team"])
tg.to_csv(os.path.join(DATA, "team_games.csv"), index=False)
print(tg.shape)
print(tg.groupby("season_type").size())
print(tg.head())
