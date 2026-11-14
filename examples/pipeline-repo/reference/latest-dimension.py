from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    customers={}
    for c in sorted(data['customers'],key=lambda c:c['version']):customers[c['id']]=c['segment']
    return [dict(id=o['id'],segment=customers.get(o['customer_id'])) for o in data['orders']]
