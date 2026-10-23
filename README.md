# NFL metric stickiness: a pilot

**Question.** Which early-season team stats are the "stickiest," meaning they best identify
rest-of-season success and playoff outcomes? Candidates: points per game, point
differential, offensive EPA/game, defensive EPA/game, turnover differential. Win% is
included as the reference everyone already uses.

**Data.** [nflverse](https://github.com/nflverse/nflverse-data) play-by-play and schedules,
seasons 2016–2024 (288 team-seasons). Metrics are computed through a cutoff week of the
regular season (default week 9) and tested against (a) the same metric over the remaining
regular-season games, and (b) playoff outcomes for that season.

## Findings (through week 9)

**1. Point differential and offensive EPA are the stickiest. Turnover differential barely sticks at all.**

| Metric (wks 1–9) | r with same metric, wks 10+ |
|---|---|
| Off EPA/game | 0.53 |
| Point diff/game | 0.51 |
| Points/game | 0.48 |
| Win % | 0.41 |
| Def EPA/game | 0.36 |
| **TO diff/game** | **0.12** |

Turnover margin is close to noise from one half of the season to the next. Defense is
much less stable than offense. This ordering holds at week 5, 7 and 12 cutoffs.

**2. For playoff outcomes, point differential matches win% and beats everything else; offense beats defense; turnovers are weak.**

AUC (1.0 = perfect ranking, 0.5 = coin flip):

| Metric | Made playoffs | Reached div. round | Reached conf. champ. | Reached SB | Won SB |
|---|---|---|---|---|---|
| Win % | 0.89 | 0.84 | 0.85 | 0.90 | 0.89 |
| Point diff/game | 0.88 | 0.84 | 0.85 | 0.90 | 0.88 |
| Off EPA/game | 0.78 | 0.80 | 0.84 | 0.87 | 0.85 |
| Points/game | 0.77 | 0.76 | 0.80 | 0.86 | 0.83 |
| TO diff/game | 0.73 | 0.67 | 0.64 | 0.68 | 0.67 |
| Def EPA/game | 0.68 | 0.62 | 0.56 | 0.62 | 0.64 |

Caveat on win%: the week-1–9 record is literally part of the thing being predicted for
"made playoffs," so its edge there is partly baked in. That point differential ties it
anyway, with no such advantage, is the real result. Note also that offensive EPA closes the
gap with win% as the rounds get deeper (0.78 → 0.85), while defensive EPA says almost
nothing about who advances once you're in.

**3. Stacking metrics adds little over point differential.** Leave-one-season-out logistic
regression for made_playoffs: win% alone 0.410 log loss; win% + point diff 0.398; all six
metrics 0.395. Once you have point differential, the other stats are mostly redundant.

## Takeaways for the fantasy/tier argument

- Point differential per game is the single best "how good are you really" number: it
  sticks, it predicts, and nothing else adds much to it.
- Points scored is a decent stand-in and is the stat fantasy managers actually see, but it
  trails point differential because it ignores the other side of the ball.
- Turnover differential is the classic "regression candidate" stat. It is almost pure luck
  half-season to half-season.
- Defense is less predictable than offense; a great first-half defense is a weaker bet to
  stay great than a great first-half offense.

## Reproduce

```
python3 build_team_games.py      # builds data/team_games.csv from nflverse files in data/
python3 pilot.py 9               # cutoff week; writes results_week9.csv and team_seasons_week9.csv
```

Raw nflverse files (`games.csv`, `pbp_YYYY.csv.gz`) go in `data/` and are not committed:

```
https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv
https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_YYYY.csv.gz
```

## Next steps

- Extend to 1999–2024 for a bigger sample and check whether the ordering has drifted.
- Per-play rather than per-game EPA, and success rate, which may be stickier than raw EPA.
- Pythagorean win expectation vs. point differential.
- Translate to fantasy: does a fantasy team's "point differential" (points for minus
  points against) outpredict points for alone?

## Side study: QB fantasy scoring vs. team point differential (2010–2024)

`qb_vs_pointdiff.py`. Traditional QB scoring (nflverse `fantasy_points`: 4-pt pass TD,
−2 INT). QB1 = each team's leading passer by attempts; his fantasy PPG over games played,
correlated with the team's full-season point differential per game.

| Season | r |   | Season | r |
|---|---|---|---|---|
| 2010 | 0.65 | | 2018 | 0.70 |
| 2011 | 0.70 | | 2019 | 0.53 |
| 2012 | 0.55 | | 2020 | 0.47 |
| 2013 | 0.77 | | 2021 | 0.73 |
| 2014 | 0.67 | | 2022 | 0.57 |
| 2015 | 0.38 | | 2023 | 0.62 |
| 2016 | 0.63 | | 2024 | 0.80 |
| 2017 | 0.64 | | **mean / pooled** | **0.63 / 0.61** |

- Strong and steady: r ≈ 0.6 in a typical year, range 0.38 (2015) to 0.80 (2024), no
  trend over the 15 years (slope ≈ 0, p = 0.89).
- Using all of a team's QB fantasy points per team game instead of QB1 gives the same
  answer (pooled r = 0.61).
- Correlation with points *scored* is higher still (0.76 pooled), as expected: QB fantasy
  points are mostly offensive production, and point differential also carries the defense.
- Rough exchange rate: +1 QB fantasy point per game ≈ +1 point of team point differential
  per game.

## Side study: does early-season point differential predict rest-of-season QB fantasy PPG?

`pointdiff_predicts_qb.py`. Team QB fantasy points per team game (traditional scoring),
2010–2024, 479 team-seasons. "Early" = weeks 1..C, "late" = weeks C+1..end.

| Cutoff | r: early point diff → late QB PPG | r: early QB PPG → late QB PPG | Both (R) | Point diff adds signal beyond QB's own early PPG? |
|---|---|---|---|---|
| wk 5 | 0.40 | 0.54 | 0.57 | yes (p < .001) |
| wk 7 | 0.41 | 0.56 | 0.58 | yes (p < .001) |
| wk 9 | 0.40 | 0.55 | 0.57 | yes (p < .001) |
| wk 12 | 0.37 | 0.53 | 0.53 | yes (p = .02) |

- Early point differential predicts rest-of-season QB fantasy PPG moderately (r ≈ 0.4).
- The QB's own early fantasy PPG is the better predictor (r ≈ 0.55), as you'd expect.
- But point differential is not redundant: holding the QB's early PPG fixed, a team with a
  better point differential still produces more QB fantasy points later. Combined R ≈ 0.57.
- Same-player check (QB1 through the cutoff who also started 4+ late games): r ≈ 0.4 for
  point diff, ≈ 0.55 for own early PPG. Same story.
- Per-season r for point diff → late QB PPG at week 7 ranges 0.07 (2019) to 0.66 (2022);
  noisy year to year, positive every year.

Reading for fantasy: if two QBs have the same early-season fantasy PPG, take the one on the
team with the better point differential.
