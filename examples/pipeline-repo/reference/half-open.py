from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    return [r['id'] for r in data['records'] if data['start']<=r['t']<data['end']]
