import json
from src.agent import functions

with open('openapi.json') as f:
    spec = json.load(f)
paths = set(spec.get('paths', {}).keys())
missing = []
for fdef in functions:
    path = '/' + fdef['name']
    if path not in paths:
        missing.append(path)
if missing:
    raise SystemExit('Missing paths in spec: ' + ', '.join(missing))
