from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

def transform(data):
    result=[]
    for user in data['users']:
        address=user.get('address',{});country=address.get('country')
        result.append(dict(id=user['id'],country=country if country is not None else 'UNKNOWN'))
    return result
