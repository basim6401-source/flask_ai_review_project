from app import app

# Diagnostic helpers intentionally kept silent in production usage.
app.testing = True
client = app.test_client()

paths = ['/', '/generate', '/huzaifa-admin']
for p in paths:
    try:
        client.get(p)
    except Exception:
        pass
