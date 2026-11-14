from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    found={}
    for row in data['rows']:
        if row['id'] not in found or row['version'] >= found[row['id']]['version']:
            found[row['id']]=row
    return [found[k] for k in sorted(found)]
