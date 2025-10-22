# KuCoin AI Multi-Bot (Paper Scaffold)

Minimal paper-first trading scaffold with modular strategies and Streamlit dashboard.

## Setup

1. Install Python 3.11.
2. Create and activate a virtual environment (`python -m venv .venv && source .venv/bin/activate`).
3. Install dependencies: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env.local` and set secrets. Keep `ENV=paper` for dry-run mode.

## Running the bot

- Smoke test indicators: `ENV=paper python -m src.main --smoke`
- Single iteration: `ENV=paper python -m src.main --once`
- Continuous loop (paper): `ENV=paper python -m src.main`

## Dashboard

Launch the Streamlit UI with:

```bash
streamlit run dashboard_app.py
```

Buttons trigger the bash runner for smoke, single iteration, and loop start/stop (paper mode).

## CI

GitHub Actions workflow **Trader** (manual dispatch) installs dependencies and runs the smoke test in paper mode.
