from app import app

# Route discovery is intentionally silent in production output.
_ = app.url_map.iter_rules()
