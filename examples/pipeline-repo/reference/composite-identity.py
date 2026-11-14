from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    found={}
    for row in data['rows']: found[(row['tenant'],row['id'])]=row
    return sorted(found.values(),key=lambda row:(row['tenant'],row['id']))
