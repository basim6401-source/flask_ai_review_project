from app import app
import traceback

print('Registered routes:')
for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods))
    print(f"{rule.rule} -> {methods}")

app.testing = True
app.debug = True
client = app.test_client()

paths = ['/', '/generate', '/admin']
for p in paths:
    print('\nREQUEST', p)
    try:
        res = client.get(p)
        print('STATUS', res.status_code)
        data = res.get_data(as_text=True)
        print('LENGTH', len(data))
        print(data[:800])
    except Exception:
        print('EXCEPTION')
        traceback.print_exc()
