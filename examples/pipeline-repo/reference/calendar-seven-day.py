from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    end=datetime.fromisoformat(data['as_of']).date();start=end-timedelta(days=6)
    return sum(r['value'] for r in data['records'] if start<=datetime.fromisoformat(r['date']).date()<=end)
