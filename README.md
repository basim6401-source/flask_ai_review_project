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

- This repo includes `requirements.txt`, `Procfile`, and `render.yaml` for deployment.
- Render uses the included `render.yaml` configuration with the production start command.
- Heroku uses the `Procfile` automatically.

## Notes
- `app.py` respects the `PORT` and `FLASK_DEBUG` environment variables for production.
- `FLASK_ENV=production` and a generated `SECRET_KEY` are recommended for hosted deployment.
- For quick sharing you can use `ngrok` to tunnel your local port.

