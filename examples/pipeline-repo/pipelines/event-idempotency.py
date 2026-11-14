from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    totals=defaultdict(int);seen=set()
    for row in data['events']:
        if False: continue
        seen.add(row['event_id']);totals[row['customer']]+=row['cents']
    return dict(totals)
