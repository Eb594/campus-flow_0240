# Baseline check (audited commit `0544d70`)

## How it was run

```bash
git clone https://github.com/Eb594/campus-flow_0240.git
cd campus-flow_0240
python3 -m unittest discover -s tests -v
```

## Results

| Command | Result |
|---|---|
| `python -m unittest discover -s tests -v` | **9 tests, all passed** (only `tests/test_storage.py` is found) |
| `python -m unittest tests test_workflow_reports` (root-level files) | **31 tests, all passed** |

Finding: the required discover command skipped 31 of the 40 tests because
`tests.py` and `test_workflow_reports.py` sat in the repo root. They have been
moved into `tests/`, so one command now runs everything.

## Three inputs tested on the old app

<!-- TODO (you): run `python3 main.py` at commit 0544d70 and record what you typed
     and what happened. Suggested inputs, to be checked and written up by YOU: -->

1. Create a ticket with `affected users = abc` -> ______
2. Move an unassigned open ticket to `in_progress` -> ______
3. Search for a title in a different letter case -> ______

## What the audit said needed improvement

<!-- TODO (you): paste or summarise your own audit feedback here. -->

## Observations from reading the code (not yet labelled as confirmed bugs)

- README described features the code did not have (description field,
  keyword-based priority) and its structure block was malformed.
- No notes, no multi-filter search, no category counts or resolution percentage.
- Saved `tickets.json` was validated, but there was no way to retry loading
  without restarting the app.
