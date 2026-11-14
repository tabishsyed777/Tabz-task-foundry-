from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    return [r['quantity'] if 'quantity' in r else r.get('qty',1) for r in data['rows']]
