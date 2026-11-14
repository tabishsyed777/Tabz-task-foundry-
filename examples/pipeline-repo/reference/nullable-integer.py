from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    return [None if v is None or (isinstance(v,str) and not v.strip()) else int(v) for v in data['values']]
