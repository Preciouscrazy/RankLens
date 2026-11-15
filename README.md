# RankLens

**Hypothetical rating-update explainer · Python 3.10+ · Offline JSON analysis**

RankLens is a small, deterministic Python model for exploring how **opponent ratings, match outcomes, and a declared uncertainty parameter** affect a fictional skill-rating update. It takes local JSON match records and produces a reproducible explanation for each result.

**This is not Riot Games' ranking formula, a player rank prediction, or a live game integration.** All committed player IDs and matches are synthetic. The model uses a familiar logistic expectation as an educational example and makes its assumptions visible.

[Engineering case study](docs/case-study.md) · [Golden sample report](evidence/sample-report.json) · [Validation record](evidence/validation.md) · [Input fixture](data/sample_matches.json)

## Sample outcomes

The [three-row synthetic fixture](data/sample_matches.json) and [committed report](evidence/sample-report.json) demonstrate:

| Scenario | Outcome | Expected score | Illustrative update |
| --- | --- | ---: | ---: |
| `demo-01` · rating 1420 vs 1500 · uncertainty 0.7 | Win | 0.3869 | **+17.66** |
| `demo-02` · rating 1600 vs 1480 · uncertainty 0.3 | Loss | 0.6661 | **−12.79** |
| `demo-03` · equal ratings 1500 · uncertainty 0.5 | Draw | 0.5000 | **0.00** |

These numbers show the behavior of this **toy model**, not real player outcomes or a game's hidden matchmaking or ranking process.

## Run

The runtime uses the Python standard library. Editable installation is optional for running from the repository root but useful for consistent environments.

```bash
python -m pip install -e .
python -m ranklens.cli data/sample_matches.json
python -m ranklens.cli data/sample_matches.json --output report.json
python -m unittest discover -s tests -v
```

The default CLI writes formatted JSON to **stdout**. `--output` optionally writes a report safely to a file. It refuses to overwrite its input path or existing hard-link alias, serializes the entire report first, and stages a temporary file next to the output before replacement. This does not provide concurrency control or guarantee durability after power failure.

## Inputs and mathematical model

Pass a JSON **array**; each record must be an object with:

- `player_id`: non-empty string
- `rating_before`, `opponent_rating`: finite numbers (negative values are allowed for this abstract model)
- `result`: exactly `win`, `draw`, or `loss`
- `uncertainty`: finite numeric value in **[0, 1]**

The model uses a logistic expected score and the illustrative update:

```text
expected = 1 / (1 + 10^((opponent_rating - rating_before) / 400))
actual   = 1.0 for win, 0.5 for draw, 0.0 for loss
change   = round(24 * (0.5 + uncertainty) * (actual - expected), 2)
after    = round(rating_before + change, 2)
```

For numerical safety, the exponential argument is clipped to **[−20, 20]**, and the difference is computed without overflow for extreme finite inputs. Changes are rounded to two decimal places. The fixed `24` factor, clipping range, uncertainty multiplier and rounding are project design assumptions, not claims about a proprietary algorithm.

## Validation and boundaries

The test suite covers score symmetry and monotonicity, win/loss/draw direction, uncertainty bounds, invalid record types, numerical overflow, deterministic output, golden-fixture equality, and real CLI subprocess behavior. GitHub Actions is configured for **Python 3.10, 3.11, 3.12 on Windows and Ubuntu**; see the [validation record](evidence/validation.md) for confirmed run results.

The model does not account for teammate ratings, role differences, queue context, hidden rating uncertainty estimation, placement policy, streaks, season boundaries, anti-abuse logic or match quality. It should not be used to reverse-engineer, estimate, or make claims about any game's proprietary ranking system.

MIT-compatible license information was not present in the source repository; no license is asserted by this README.
