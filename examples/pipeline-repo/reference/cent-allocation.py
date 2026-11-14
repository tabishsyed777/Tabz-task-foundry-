from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    base,extra=divmod(data['total_cents'],data['count'])
    return [base+int(i<extra) for i in range(data['count'])]
