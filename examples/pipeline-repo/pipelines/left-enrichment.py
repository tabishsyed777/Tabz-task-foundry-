from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    customers={r['id']:r['name'] for r in data['customers']}
    return [dict(o,customer_name=customers.get(o['customer_id'])) for o in data['orders'] if o['customer_id'] in customers]
