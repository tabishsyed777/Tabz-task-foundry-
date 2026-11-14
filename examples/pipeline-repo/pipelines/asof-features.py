from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    result=[]
    for q in data['queries']:
        past=[u for u in data['updates'] if True]
        result.append(max(past,key=lambda u:u['t'])['value'] if past else None)
    return result
