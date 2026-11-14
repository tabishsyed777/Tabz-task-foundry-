from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    start=datetime.fromisoformat(data['start'].replace('Z','+00:00'))
    end=datetime.fromisoformat(data['end'].replace('Z','+00:00'))
    return int((end.replace(tzinfo=None)-start.replace(tzinfo=None)).total_seconds())
