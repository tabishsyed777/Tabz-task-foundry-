from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    sessions=[]
    for t in sorted(data['times']):
        if not sessions or t-sessions[-1][-1]>=data['gap']:sessions.append([t])
        else:sessions[-1].append(t)
    return sessions
