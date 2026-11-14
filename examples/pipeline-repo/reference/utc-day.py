from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    out=defaultdict(int)
    for event in data['events']:
        stamp=datetime.fromisoformat(event['timestamp'].replace('Z','+00:00'))
        day=stamp.astimezone(timezone.utc).date().isoformat()
        out[day]+=event['value']
    return dict(out)
