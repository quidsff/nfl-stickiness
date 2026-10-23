# NFL metric stickiness

This project asks which early-season team statistics tell you the most about how the rest
of the season will go. It uses [nflverse](https://github.com/nflverse/nflverse-data)
play-by-play, schedule, and player data. Each section below describes one study, the
method in plain terms, and what the numbers showed.

A note on the numbers. Most results are reported as a correlation, written as r. A
correlation measures how closely two things move together. It runs from 0, meaning no
relationship, to 1, meaning a perfect one. Some results use AUC instead. AUC measures how
well a statistic ranks teams that reach an outcome above teams that do not. A score of 0.5
means the ranking is a coin flip, and 1.0 means it is perfect.

## Study 1: which team statistics stick from the first half of the season to the second?

**The question.** At the midpoint of a season, which team statistic best identifies a team
that will keep succeeding? The candidates were points per game, point differential per
game, offensive EPA per game, defensive EPA per game, and turnover differential per game.
Win percentage is included because it is the statistic everyone already uses.

**The method.** The study covers the 2016 through 2024 seasons, which gives 288
team-seasons. Each statistic was computed through week 9, then compared against the same
statistic over the rest of the regular season. The study then checked how well each
statistic ranked teams on five playoff outcomes: making the playoffs, winning in the
wild-card round, reaching the conference championship, reaching the Super Bowl, and
winning it.

**Finding 1. Point differential and offensive EPA stick best. Turnover differential barely sticks at all.**

| Statistic through week 9 | Correlation with the same statistic from week 10 on |
|---|---|
| Offensive EPA per game | 0.53 |
| Point differential per game | 0.51 |
| Points per game | 0.48 |
| Win percentage | 0.41 |
| Defensive EPA per game | 0.36 |
| **Turnover differential per game** | **0.12** |

A team's turnover margin in the first half of the season tells you almost nothing about its
turnover margin in the second half. Defense holds up far less than offense does. The same
order appears when the season is cut at week 5, week 7, or week 12.

**Finding 2. Point differential predicts playoff outcomes as well as win percentage does, and nothing else comes close.**

| Statistic | Made playoffs | Reached divisional round | Reached conference championship | Reached Super Bowl | Won Super Bowl |
|---|---|---|---|---|---|
| Win percentage | 0.89 | 0.84 | 0.85 | 0.90 | 0.89 |
| Point differential per game | 0.88 | 0.84 | 0.85 | 0.90 | 0.88 |
| Offensive EPA per game | 0.78 | 0.80 | 0.84 | 0.87 | 0.85 |
| Points per game | 0.77 | 0.76 | 0.80 | 0.86 | 0.83 |
| Turnover differential per game | 0.73 | 0.67 | 0.64 | 0.68 | 0.67 |
| Defensive EPA per game | 0.68 | 0.62 | 0.56 | 0.62 | 0.64 |

Win percentage has an unfair advantage in this table. A team's record through week 9 is
part of the record that decides whether it makes the playoffs, so win percentage gets
credit for something it already contains. Point differential has no such advantage and
ties it anyway. That is the real result. Offensive EPA also gains ground as the rounds get
deeper, rising from 0.78 to 0.85, while defensive EPA tells you almost nothing about who
advances once the playoffs begin.

**Finding 3. Combining statistics adds little once you have point differential.** A model
that predicts playoff berths from win percentage alone scores 0.410 on log loss, where a
lower score is better. Adding point differential improves it to 0.398. Adding all six
statistics only reaches 0.395. Once you know a team's point differential, the other numbers
mostly repeat what it already told you.

**What this means for ranking fantasy teams.** Point differential per game is the single
best measure of how good a team really is. It holds up over time, it predicts what comes
next, and no other statistic adds much to it. Points scored works as a stand-in, and it is
the number fantasy managers actually see, but it trails point differential because it
ignores the other side of the ball. Turnover differential is the classic statistic that
regresses, because it is nearly all luck from one half of the season to the next. A strong
first-half defense is a weaker bet to stay strong than a strong first-half offense.

## Study 2: how closely does a quarterback's fantasy scoring track his team's point differential?

**The method.** The study covers the 2010 through 2024 seasons and uses traditional
quarterback scoring, which awards four points per passing touchdown and subtracts two per
interception. Each team's leading passer by attempts counts as its starter. His fantasy
points per game were compared against the team's point differential per game over the
full regular season.

**The finding.** The two track each other closely and the relationship has not changed in
fifteen years.

| Season | Correlation | | Season | Correlation |
|---|---|---|---|---|
| 2010 | 0.65 | | 2018 | 0.70 |
| 2011 | 0.70 | | 2019 | 0.53 |
| 2012 | 0.55 | | 2020 | 0.47 |
| 2013 | 0.77 | | 2021 | 0.73 |
| 2014 | 0.67 | | 2022 | 0.57 |
| 2015 | 0.38 | | 2023 | 0.62 |
| 2016 | 0.63 | | 2024 | 0.80 |
| 2017 | 0.64 | | **Average** | **0.63** |

A typical season lands near 0.6. The weakest year was 2015 at 0.38 and the strongest was
2024 at 0.80, and there is no trend up or down across the period. Counting every
quarterback who played for the team, rather than only the starter, gives the same answer.
The correlation with points scored is higher still, at 0.76, which makes sense because a
quarterback's fantasy points come from offense alone while point differential also
reflects the defense. As a rough exchange rate, one extra fantasy point per game from the
quarterback goes with one extra point of team point differential per game.

**A variation with six-point passing touchdowns.** Some leagues score passing and rushing
touchdowns the same, at six points each. Rerunning the study under that rule
(`python3 qb_vs_pointdiff.py 6`) moves the numbers up slightly and changes nothing about
the conclusion.

| Season | 4-point passing TD | 6-point passing TD | | Season | 4-point | 6-point |
|---|---|---|---|---|---|---|
| 2010 | 0.65 | 0.67 | | 2018 | 0.70 | 0.71 |
| 2011 | 0.70 | 0.72 | | 2019 | 0.53 | 0.54 |
| 2012 | 0.55 | 0.58 | | 2020 | 0.47 | 0.50 |
| 2013 | 0.77 | 0.76 | | 2021 | 0.73 | 0.75 |
| 2014 | 0.67 | 0.67 | | 2022 | 0.57 | 0.60 |
| 2015 | 0.38 | 0.38 | | 2023 | 0.62 | 0.64 |
| 2016 | 0.63 | 0.64 | | 2024 | 0.80 | 0.81 |
| 2017 | 0.64 | 0.67 | | **Average** | **0.63** | **0.64** |

The correlation rises by about 0.01 to 0.03 in most seasons and never falls by more than
0.01. That makes sense. Six-point passing touchdowns give more weight to the part of a
quarterback's line that most directly produces team points, so his fantasy score tracks
team scoring a little more closely. The correlation with points scored rises from 0.76 to
0.79. The exchange rate changes too: under six-point scoring, one extra quarterback fantasy
point per game goes with about 0.8 points of team point differential, because each
touchdown now carries more fantasy points.

## Study 3: does a team's early point differential predict its quarterback's fantasy scoring later in the season?

**The method.** For each team and season from 2010 through 2024, the study took the team's
point differential per game through a cutoff week and compared it with the team's
quarterback fantasy points per game over the remaining weeks. It then asked whether point
differential still mattered once the quarterback's own early fantasy scoring was known.

**The finding.** Early point differential predicts later quarterback scoring moderately, and
it adds information that the quarterback's own numbers do not contain.

| Cutoff week | Point differential predicts later QB scoring | QB's own early scoring predicts later QB scoring | Both together | Does point differential add signal? |
|---|---|---|---|---|
| 5 | 0.40 | 0.54 | 0.57 | Yes |
| 7 | 0.41 | 0.56 | 0.58 | Yes |
| 9 | 0.40 | 0.55 | 0.57 | Yes |
| 12 | 0.37 | 0.53 | 0.53 | Yes |

The quarterback's own early scoring is the better predictor, which is what you would
expect. Point differential is not redundant, though. If two quarterbacks have scored the
same so far, the one on the team with the better point differential scores more the rest
of the way. The result holds when the study is restricted to quarterbacks who kept the
same starting job all season. Season by season the strength varies, from 0.07 in 2019 to
0.66 in 2022, but the direction is positive every year.

## Study 4: what should a quarterback score, given his team?

**The method.** The study fit a straight line through 468 team-seasons from 2010 through
2024, relating a starter's fantasy points per game to his team's point differential, to
its points scored, and to both.

**The finding.** Points scored predicts quarterback fantasy output far better than point
differential does, and combining the two adds nothing.

| Based on | Formula | Share of variation explained | Typical miss |
|---|---|---|---|
| Point differential | QB PPG = 16.0 + 0.38 × (point differential per game) | 37% | 3.1 points |
| Points scored | QB PPG = 0.8 + 0.67 × (team points per game) | 57% | 2.5 points |
| Both | adds nothing over points scored | 58% | 2.5 points |

The rule of thumb is that a starting quarterback should score about two-thirds of his
team's points per game in fantasy points. An offense that scores 24 points a game should
carry a quarterback near 17 fantasy points a game, and an offense that scores 30 should
carry one near 21. The file `expected_qb_ppg.csv` lists every starter since 2010 with his
expected score and the gap between his actual and expected score. A positive gap means the
quarterback produces more fantasy points than his team's scoring implies, usually because
he runs or throws a large share of the touchdowns. A negative gap means the offense scores
without him, through the run game, the defense, or short fields.

## Study 5: how do you spot a quarterback who is due to improve?

**The question.** A common theory says that touchdown and interception luck evens out, so a
quarterback with a poor touchdown rate is a buy. This study tested that theory and found a
better one.

**The method.** The study covers 2010 through 2024 and uses week 7 as the cutoff. It
includes 413 quarterback-seasons in which the player had at least four games and sixty
attempts on each side of the cutoff. It first measured which parts of a quarterback's
statistical line carry over from the first half of the season to the second. It then built
an expected score from the parts that carry over and tested whether the gap between a
player's actual and expected score predicted his scoring in the second half. Finally, it
tested whether the player's scoring from the previous season predicted anything.

**Finding 1. Rushing volume carries over almost perfectly, and touchdown rate carries over more than the theory assumes.**

| Part of the line | Correlation, weeks 1–7 vs. weeks 8 on |
|---|---|
| Carries per game | 0.84 |
| Rushing yards per game | 0.82 |
| Fantasy points per game | 0.55 |
| Attempts per game | 0.48 |
| Yards per attempt | 0.42 |
| Passing touchdown rate | 0.38 |
| Rushing touchdown rate | 0.17 |
| Interception rate | 0.16 |

How often a quarterback runs is the most stable thing about him. Passing touchdown rate is
a real skill, not noise. Interception rate and rushing touchdown rate are noise.

**Finding 2. The luck gap predicts nothing.** Once you know a quarterback's early fantasy
scoring, knowing whether it came from good or bad touchdown and interception luck adds no
information about the rest of his season. The theory that bad luck evens out does not hold
up for fantasy purposes.

**Finding 3. Last season's scoring and rushing volume do add information.** A model that
predicts second-half scoring from first-half scoring alone explains 30% of the variation.
Adding last season's scoring raises that to 33%, and adding carries per game raises it to
35%. Both additions are reliable.

**The rule the data supports.** Compare a quarterback's early-season scoring with his
scoring from the previous season.

| Early scoring vs. last season | Players | Last season | Weeks 1–7 | Weeks 8 on | Change | Top-12 QB over weeks 8 on |
|---|---|---|---|---|---|---|
| Fell the most (5.4 points below) | 61 | 18.7 | 13.4 | 16.1 | **+2.7** | 49% |
| Fell some (2.1 below) | 60 | 17.8 | 15.8 | 15.6 | −0.2 | 45% |
| About the same | 60 | 16.4 | 16.4 | 15.3 | −1.1 | 45% |
| Rose some (2.3 above) | 60 | 16.2 | 18.4 | 16.9 | −1.6 | 63% |
| Rose the most (6.3 above) | 60 | 14.8 | 21.1 | 18.3 | **−2.8** | 77% |

Quarterbacks who were scoring five or more points below their previous season gained
about 2.7 points per game the rest of the way, and half of them ranked as top-12
quarterbacks over the second half alone, even though they looked like backups at the
cutoff. Every rank in this study uses second-half scoring only, so a hot first half
cannot carry a player into the top 12 here. Quarterbacks who broke
out gave back about 2.8 points per game but mostly stayed in the top 12. A hot start is
partly real, and a slump is mostly not.

**A caution about benchings.** Among the quarterbacks with the worst luck, 83% kept their
starting job through the second half, compared with 92% of those with the best luck. The
gains above belong to the players who held the job, so a slumping quarterback carries some
risk of being benched.

**A check against 2024.** The six quarterbacks with the worst luck through week 7 were
Minshew, Stafford, Richardson, Levis, Mahomes, and Bryce Young. All six improved the rest
of the way, by 3.8, 6.7, 6.9, 3.9, 6.3, and 14.4 points per game. The five with the best
luck were Mayfield, Allen, Love, Lamar Jackson, and Burrow, and their results were mixed:
−2.8, +6.0, −7.5, −0.2, and +4.4.

The previous-season rule did not sort the 2024 hot starts well, and that is worth stating
plainly.

| Quarterback | 2023 | 2024 through week 7 | Gap from 2023 | 2024 from week 8 |
|---|---|---|---|---|
| Mayfield | 16.1 | 23.2 | +7.0, a sell | 20.4, held |
| Burrow | 14.7 in 10 games | 19.4 | +4.6, a sell | 23.7, improved |
| Lamar Jackson | 20.7 | 25.4 | +4.7, a sell | 25.2, held |
| Love | 18.8 | 20.6 | +1.8, a hold | 13.1, collapsed |
| Allen | 23.2 | 19.9 | −3.3, a buy | 25.9, improved |

Allen is the only clean confirmation. Mayfield, Burrow, and Jackson all counted as sells
under the rule and all stayed elite, while Love counted as a hold and fell apart. The rule
describes an average across three hundred seasons with a lot of spread around it. Treat it
as a starting point, not a verdict.

## Study 6: do first-half gaps predict a quarterback's rank over the second half alone?

**The question.** Study 5 reported the share of players who ranked in the top 12 over the
second half. This study makes that the whole focus. It asks whether any of three first-half
gaps tells you where a quarterback will rank from week 8 on, when the ranking ignores
everything he did before the cutoff. The three gaps are the luck gap from Study 5 (actual
scoring minus what his own volume and yardage imply at league-average touchdown and
interception rates), the team gap (actual scoring minus what his team's points per game
imply), and the prior gap (actual scoring minus his scoring the season before).

**The method.** The study covers 2010 through 2024 at a week 7 cutoff, with 413
quarterback-seasons. Each player's second-half rank is his place by points per game over
weeks 8 on, among every quarterback with at least four games and sixty attempts in that
span. For each gap, the study sorts players into five groups and reports the average
second-half rank and the share who ranked in the top 6, top 12, and top 24. It also asks
whether each gap still matters once you account for the player's first-half scoring.

**Finding 1. Hot starters do not fade. The luckiest group ranked near the top in the second half too.**

| Luck gap | Players | Weeks 1–7 PPG | Weeks 8 on PPG | Average rank, weeks 8 on | Top 6 | Top 12 | Top 24 |
|---|---|---|---|---|---|---|---|
| Most negative (−3.1) | 83 | 12.1 | 14.1 | 21.8 | 7% | 18% | 55% |
| −1.3 | 82 | 14.0 | 15.2 | 19.1 | 18% | 32% | 67% |
| Near zero | 83 | 15.4 | 14.8 | 18.9 | 13% | 31% | 70% |
| +1.6 | 82 | 18.3 | 17.2 | 13.4 | 24% | 48% | 90% |
| Most positive (+3.9) | 83 | 21.7 | 19.5 | 9.5 | 41% | 73% | 94% |

The quarterbacks with the best first-half luck averaged a rank of 9.5 over the second
half and placed in the top 12 nearly three times out of four. They gave back about two
points per game, but their first-half production did not carry them, because the second
half on its own put them at the top. Once you account for first-half scoring, the luck gap
has no relation to second-half rank at all. Within any band of first-half scoring, players
with positive luck ranked as well as or better than players with negative luck. Among
quarterbacks scoring 15 to 18 points per game, for example, the lucky half ranked in the top
12 over the second half 45% of the time and the unlucky half 36%.

**Finding 2. The team gap and the prior gap do carry information, in the opposite direction from the luck gap.**

Once you account for first-half scoring, a quarterback who is scoring more than his team's
points imply ranks a little worse in the second half, and a quarterback who is scoring more
than he did last season ranks noticeably worse. The prior gap is the stronger of the two.

| Prior gap | Players | Last season | Weeks 1–7 PPG | Weeks 8 on PPG | Average rank, weeks 8 on | Top 6 | Top 12 | Top 24 |
|---|---|---|---|---|---|---|---|---|
| Fell the most (−5.4) | 61 | 18.7 | 13.4 | 16.1 | 16.5 | 20% | 39% | 77% |
| −2.1 | 60 | 17.8 | 15.8 | 15.6 | 17.7 | 18% | 30% | 73% |
| About the same | 60 | 16.4 | 16.4 | 15.3 | 19.1 | 15% | 32% | 70% |
| +2.3 | 60 | 16.2 | 18.4 | 16.9 | 14.5 | 20% | 42% | 85% |
| Rose the most (+6.3) | 60 | 14.8 | 21.1 | 18.3 | 12.5 | 37% | 62% | 87% |

The group that fell furthest from last season scored the least in the first half, yet
ranked better in the second half than the two groups above them. A quarterback at 13.4
points per game who had scored 18.7 the year before ranked, on average, 16.5 over the
second half, while a quarterback at 16.4 points per game who was simply repeating last
season ranked 19.1.

**What this means.** The luck gap identifies no one. A quarterback whose scoring comes from
a high touchdown rate keeps ranking well, and a quarterback whose scoring is held down by
a low one keeps ranking poorly. Last season's scoring is the number that moves the second-
half ranking, and it moves it in both directions: a proven quarterback in a slump climbs,
and a quarterback with no track record who has broken out slips.

## Study 7: how should "track record" be defined?

**The question.** Studies 5 and 6 define a quarterback's track record as his points per
game over the previous season, counted if he played at least eight games. That is a thin
definition. It lets in a partial season cut short by injury, and it ignores anything older
than one year. This study tests whether a fuller definition works better.

**The method.** Four definitions were compared: last season with at least eight games
(the original), last season with at least fourteen games, the best of the previous two
seasons, and the best of the previous three seasons. Each was used to build the gap
between a player's first-half scoring and his prior level, and each gap was tested
against second-half scoring and second-half rank, with first-half scoring accounted for.
The cutoff is week 7. Because the data begin in 2010, the two- and three-season
definitions start from 2012 and 2013.

**The finding. The fuller definitions do no better, and the three-season version does worse.**

| Definition | Players | Improvement in explaining second-half scoring, beyond first-half scoring | Reliable? |
|---|---|---|---|
| Last season, 8+ games | 301 | 0.300 → 0.329 | Yes |
| Last season, 14+ games | 229 | 0.309 → 0.336 | Yes |
| Best of previous two seasons | 299 | 0.272 → 0.295 | Yes |
| Best of previous three seasons | 277 | 0.252 → 0.266 | Weakly |

On the 202 seasons where all four definitions can be computed, the first three are
nearly identical and the three-season version falls behind and loses reliability. Reaching
further back adds noise rather than signal, because a quarterback's level three years ago
has less to do with his level now than last season does. Requiring a full season drops
a quarter of the sample without improving the result.

The groups sorted by the three-season definition tell the same story as before. Players
scoring furthest below their best recent season gained 2.8 points per game over the
second half and ranked 16 on average, better than the two groups just above them, while
players scoring furthest above their best recent season gave back 2.7 points per game.

**What this means.** The simple definition holds up. Last season's points per game, with
the eight-game minimum, is the right version of track record for this purpose, and there
is no reason to replace it. The caution from Study 6 still stands: a low number from last
season can mean a weak player, a good player on a weak team, or a good player who missed
time, and the study does not tell those apart.

## Reproduce

```
python3 build_team_games.py        # builds data/team_games.csv from nflverse files in data/
python3 pilot.py 9                 # Study 1, with the cutoff week as the argument
python3 qb_vs_pointdiff.py         # Study 2
python3 pointdiff_predicts_qb.py   # Study 3
python3 expected_qb_ppg.py         # Study 4
python3 qb_buy_low.py 7            # Study 5, with the cutoff week as the argument
python3 qb_gap_vs_second_half_rank.py 7   # Study 6
python3 qb_track_record.py 7       # Study 7
```

The raw nflverse files are not committed. Place them in `data/` from these addresses:

```
https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv
https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_YYYY.csv.gz
https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_YYYY.csv
```

## Next steps

- Extend Study 1 back to 1999 and check whether the ordering has changed over time.
- Try EPA per play and success rate, which may hold up better than EPA per game.
- Compare Pythagorean win expectation against point differential.
- Ask whether a fantasy team's own point differential predicts better than its points scored.
- Run Study 5 for running backs, receivers, and tight ends.
