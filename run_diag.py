from app import app

# Diagnostic script kept silent to avoid exposing server chatter in the app output.
app.testing = True
client = app.test_client()

paths = ['/', '/generate', '/huzaifa-admin']
for p in paths:
    try:
        client.get(p)
    except Exception:
        pass
