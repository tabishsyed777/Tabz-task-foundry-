from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    return [r.get('quantity') or r.get('qty') or 1 for r in data['rows']]
