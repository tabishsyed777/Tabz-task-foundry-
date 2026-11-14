from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    orders={o['id']:o['total_cents'] for o in data['orders']}
    return dict(revenue_cents=sum(orders.get(i['order_id'],0) for i in data['items']),item_count=sum(i['order_id'] in orders for i in data['items']))
