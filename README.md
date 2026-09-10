# AI Google Review Generator

Simple Flask app that generates short Google-style reviews for demo purposes.

## Run locally

1. Create and activate a virtual environment (Windows PowerShell example):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m flask run
```

2. Open `http://127.0.0.1:5000` in your browser.

## Deploy (Render / Heroku)

- This repo includes `requirements.txt` and a `Procfile` for simple deployment.
- On Render use start command: `gunicorn app:app --bind 0.0.0.0:$PORT`.
- On Heroku the `Procfile` will be used automatically.

## Notes
- `app.py` respects the `PORT` and `FLASK_DEBUG` environment variables for production.
- For quick sharing you can use `ngrok` to tunnel your local port.

