# RankLens — Validation record

**Upgrade branch:** `improve/ranklens-reliability-ci-case-study`  
**Baseline commit:** [`38c2fe7b88fe0613bfadb0b147158c87a7e8fb26`](https://github.com/Preciouscrazy/RankLens/commit/38c2fe7b88fe0613bfadb0b147158c87a7e8fb26)  
**Earlier sample report PR:** [#2](https://github.com/Preciouscrazy/RankLens/pull/2)

## Baseline

The original RankLens repository had **three small unit tests** and one Ubuntu Python 3.11 job; [baseline run #43105245590](https://github.com/Preciouscrazy/RankLens/actions/runs/43105245590) completed successfully. The existing open sample-report PR included a synthetic [golden JSON report](sample-report.json), retained in this proposed upgrade.

## Expanded verification

The upgrade defines **34 algorithm unit tests and 14 subprocess CLI tests** (**48 methods**) and configures six GitHub Actions combinations:

| Runner | Python 3.10 | Python 3.11 | Python 3.12 |
| --- | --- | --- | --- |
| Ubuntu 24.04 | Pending | Pending | Pending |
| Windows latest | Pending | Pending | Pending |

Tests cover the expected-score math, extreme finite ratings and overflow, input schema and type safety, uncertainty, outcome validation, result ordering, deterministic synthetic report comparison, CLI stdout, optional file output, hard-link safety, preserving prior reports on error, and status codes.

**A defined matrix is not verification by itself.** This document will record successful hosted runs for the exact source commit after GitHub Actions checks finish.

## Reproduce

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m ranklens.cli data/sample_matches.json
python -m ranklens.cli data/sample_matches.json --output report.json
```

The canonical [sample report](sample-report.json) is versioned; generated `report.json` is gitignored. All inputs are fictional. CI results demonstrate the tested implementation on specified Python versions and operating systems; they do not measure real-world ranking correctness or claim a proprietary model.
