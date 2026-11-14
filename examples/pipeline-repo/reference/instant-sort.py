from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    return [e['id'] for e in sorted(data['events'],key=lambda e:(datetime.fromisoformat(e['timestamp'].replace('Z','+00:00')),e['id']))]
