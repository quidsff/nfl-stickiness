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

## Expected QB fantasy PPG from team context

`expected_qb_ppg.py`. Pooled OLS on 468 team-seasons (2010–2024, QB1 with 8+ games,
traditional scoring).

| Model | Equation | R² | RMSE |
|---|---|---|---|
| A: point differential | QB PPG = 16.0 + 0.38 × (point diff / game) | 0.37 | 3.1 |
| B: points scored | QB PPG = 0.8 + 0.67 × (team points / game) | 0.57 | 2.5 |
| C: both | adds nothing over B (point-diff coefficient ≈ 0) | 0.58 | 2.5 |

Points scored is the better predictor of QB fantasy output, by a lot: a team's point
differential tells you about its defense too, which the QB doesn't get paid for.
Rule of thumb: **expected QB1 PPG ≈ two-thirds of the team's points per game.** A 24
ppg offense should carry a ~17 PPG QB; a 30 ppg offense a ~21 PPG QB. Typical miss ±2.5.

`expected_qb_ppg.csv` has every QB1 2010–2024 with expected PPG and the residual
(actual − expected). Positive residual = the QB produces more fantasy points than his
team's scoring implies (rushing, high TD share); negative = the offense scores without
him (run game, defense/special teams, short fields).

## Buy-low QBs: what actually predicts positive regression

`qb_buy_low.py` (cutoff week 7, 2010–2024, 413 QB-seasons with 4+ games and 60+ attempts
on each side). The hypothesis was "TD/INT luck reverts, so a QB with a bad TD rate is a
buy." That is mostly wrong. What works is simpler.

**Component stickiness, weeks 1–7 vs 8+, same QB**

| Component | r | | Component | r |
|---|---|---|---|---|
| Carries/game | 0.84 | | Pass TD rate | 0.38 |
| Rush yds/game | 0.82 | | Rush TD rate | 0.17 |
| Attempts/game | 0.48 | | INT rate | 0.16 |
| Yards/attempt | 0.42 | | Fantasy PPG | 0.55 |

Rushing volume is the stickiest thing a QB does, by a mile. Pass TD rate is a real skill
(0.38), not noise. INT rate and rush TD rate are noise.

**Does a "luck residual" predict rest-of-season gain?** No. Late PPG ~ early PPG +
residual (actual − expected from volume/yardage with league-average TD/INT rates): the
residual's coefficient is +0.08, p = 0.50. Splitting into TD luck and INT luck: both n.s.
Once you know a QB's early PPG, knowing *why* it was high or low adds nothing.

**What does add signal:**

| Model for late PPG | R² |
|---|---|
| early PPG | 0.30 |
| early PPG + prior-season PPG | 0.33 |
| early PPG + prior-season PPG + carries/game | 0.35 |

Prior-season PPG (β = +0.21, p < .001) and rushing volume (β = +0.33 per carry/game,
p = .001) both matter on top of early PPG. Luck does not.

**The buy-low rule that the data supports:** sort by (early PPG − last season's PPG).

| Early PPG vs last season | n | prior | early | late | gain | top-12 QB rest of way |
|---|---|---|---|---|---|---|
| Q1 biggest drop (−5.4) | 61 | 18.7 | 13.4 | 16.1 | **+2.7** | 49% |
| Q2 (−2.1) | 60 | 17.8 | 15.8 | 15.6 | −0.2 | 45% |
| Q3 (0.0) | 60 | 16.4 | 16.4 | 15.3 | −1.1 | 45% |
| Q4 (+2.3) | 60 | 16.2 | 18.4 | 16.9 | −1.6 | 63% |
| Q5 biggest jump (+6.3) | 60 | 14.8 | 21.1 | 18.3 | **−2.8** | 77% |

QBs scoring 5+ PPG below last year gain ~2.7 PPG the rest of the way and finish as a
top-12 QB half the time, despite looking like QB2s at the cutoff. Breakout QBs give back
~2.8 PPG but still mostly stay top-12: a jump is partly real, a slump is mostly not.

**Survivorship.** 83% of the "unluckiest" quintile kept starting vs 92% of the luckiest,
so the gains above are for QBs who held the job; a slumping QB carries some bench risk.

**2024 at week 7, sanity check.** Biggest negative residuals: Minshew, Stafford,
Richardson, Levis, Mahomes, Bryce Young. Gains the rest of the way: +3.8, +6.7, +6.9, +3.9,
+6.3, +14.4. Biggest positive residuals: Mayfield, Allen, Love, Lamar, Burrow: −2.8, +6.0,
−7.5, −0.2, +4.4. The direction is right on the low side; the high side splits between
real (Allen, Burrow) and not (Love, Mayfield), which is the prior-season point again.
