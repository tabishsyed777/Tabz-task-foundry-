from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    totals=defaultdict(int)
    for row in data['transactions']:totals[row['account']]+=abs(row['cents'])
    return dict(totals)
