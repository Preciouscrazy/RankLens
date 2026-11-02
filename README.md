# RankLens
A Python portfolio project explaining a **hypothetical** ranked-rating update from synthetic match records. It does not reproduce Riot's proprietary ranking or matchmaking calculations.

Run:
```bash
python -m ranklens.cli data/sample_matches.json
python -m unittest discover -s tests -v
```
Python 3.10+; no third-party dependencies.

Each JSON record has `player_id`, `rating_before`, `opponent_rating`, `result` (`win`, `loss`, `draw`), and `uncertainty` (0–1). The educational model uses a logistic expected score and `K * (0.5 + uncertainty) * (actual - expected)`. Results are illustrative, not predictions of a real game system. Use synthetic or authorized data only.

## Development

Run the unit tests before publishing changes:

```bash
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs the same test suite for pushes and pull requests.

## Scope and limitations

This project demonstrates documented educational analysis with sample data. Its results should not be treated as production monitoring, real-world player ratings, or access to any proprietary game service.
