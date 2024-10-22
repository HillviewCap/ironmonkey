import json

def from_json(value):
    try:
        return json.loads(value)
    except:
        return None

def json_loads_filter(s):
    if not s:
        return []
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return []
