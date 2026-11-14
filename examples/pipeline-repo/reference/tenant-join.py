from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    customers={(c['tenant'],c['id']):c['name'] for c in data['customers']}
    return [customers.get((o['tenant'],o['customer_id'])) for o in data['orders']]
