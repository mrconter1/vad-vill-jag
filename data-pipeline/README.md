# data-pipeline

Fetches Swedish Riksdagen vote data and generates quiz questions using Claude Sonnet.

## Setup

```
pip install anthropic requests
```

Copy `.env.example` to `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-...
```

## Usage

Run from inside this folder:

```
python extract_questions.py 9999 10 --since 2021-09-01
```

Arguments: `N_DOCS WORKERS --since YYYY-MM-DD`

- `N_DOCS` — max number of betänkanden to process (use 9999 for all)
- `WORKERS` — parallel Sonnet calls (default 5)
- `--since` — only process documents voted on after this date

Stats mode (no Sonnet calls, just coverage numbers):

```
python extract_questions.py --stats --since 2021-09-01
```

## Output

- `questions.json` — generated quiz questions with party stances
- `bet-cache.json` — cached betänkande text (auto-populated)
- `extraction-errors.json` — log of documents that failed or were skipped
- `votering-YYYYNN.json` — raw vote data per riksmöte (auto-downloaded)
