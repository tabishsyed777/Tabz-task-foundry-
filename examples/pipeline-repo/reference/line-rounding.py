from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    return sum(int((Decimal(p)*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)) for p in data['prices'])
