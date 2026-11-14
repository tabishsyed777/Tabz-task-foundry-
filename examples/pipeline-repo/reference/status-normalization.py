from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    mapping={'paid':'paid','settled':'paid','refund':'refunded','refunded':'refunded','pending':'pending'}
    return [mapping.get(v.strip().lower(),'unknown') if isinstance(v,str) else 'unknown' for v in data['statuses']]
