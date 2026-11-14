from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    found={}
    for row in data['rows']:
        if row['id'] not in found: found[row['id']]=row
    return list(found.values())
