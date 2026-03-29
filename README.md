# Vilket parti tillhör jag?

A Swedish political quiz that matches your views to real Riksdag votes. Questions are sourced directly from Sweden's open parliamentary data — no editorial interpretation, just facts.

## How it works

1. A random set of questions is drawn from ~1800 real parliamentary votes from the last five years.
2. You answer JA, NEJ, or Ingen åsikt for each.
3. Your answers are compared to how each party actually voted, giving you a party alignment breakdown.

## Project structure

```
/                   Next.js web app (this repo root)
data-pipeline/      Python scripts that fetch Riksdag data and generate questions.json
```

## Running the web app

```bash
npm install
npm run dev
```

## Regenerating questions

```bash
cd data-pipeline
pip install anthropic requests
python extract_questions.py 9999 10 --since 2021-09-01
```

See `data-pipeline/README.md` for full pipeline docs.
