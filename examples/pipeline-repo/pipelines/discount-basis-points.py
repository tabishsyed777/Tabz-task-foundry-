from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    value=Decimal(data['subtotal_cents'])*(10000-data['discount_bps'])/10000
    return int(value)
