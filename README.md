## Local run with jarvis

Activate the existing conda environment from the project root:

```bash
conda activate jarvis
```

Run the Streamlit app:

```bash
streamlit run apps/streamlit_app/app.py
```

Run the command-line scripts:

```bash
python scripts/run_bt.py
python scripts/signals_today.py
```

Refresh/download sample market data:

```bash
python scripts/fetch.py
```

`main.py` is only a small placeholder that prints a hello message. The actual app entry point is `apps/streamlit_app/app.py`. We can regenerate `requirements.txt` later from the working `jarvis` environment.

For full app:

https://backtesting-trading-strategies.streamlit.app/

Note:
If the app appears idle or unresponsive, it is probably just sleeping.
Wait a few seconds and let Streamlit wake up the engine.
