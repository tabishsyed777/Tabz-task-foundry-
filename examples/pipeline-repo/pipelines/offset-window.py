from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    parse=lambda x: datetime.fromisoformat(x.replace('Z','+00:00')).replace(tzinfo=None)
    start,end=parse(data['start']),parse(data['end'])
    return [e['id'] for e in data['events'] if start<=parse(e['timestamp'])<end]
