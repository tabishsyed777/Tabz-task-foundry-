"""Curated task specifications. Expected fixtures are authored independently of fixes.

The fixture builders never execute or import the reference implementation.
"""
from dataclasses import dataclass
import random
import textwrap


@dataclass
class Spec:
    slug: str
    family: str
    title: str
    contract: str
    source: str
    broken: str
    fixture: object
    difficulty: str = 'medium'


HEADER = '''from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict

'''
SPECS=[]


def add(slug,family,title,contract,body,old,new,fixture):
    source=HEADER+textwrap.dedent(body).lstrip()
    assert old in source,slug
    SPECS.append(Spec(slug,family,title,contract,source,source.replace(old,new,1),fixture))


def fixtures(spec):
    results=[]
    for seed in [7,19,101,103,107,109,113,127,131,137]:
        data,expected=spec.fixture(random.Random(seed))
        results.append(dict(id=f'case-{seed}',visibility='visible' if seed in (7,19) else 'heldout',input=data,expected=expected))
    return results


add('latest-record','deduplication','Keep the latest customer update',
    'Input rows contain id, integer version, and value. Return one row per id: greatest version wins; the last input row wins equal-version ties. Sort output by id.',
    '''
    def transform(data):
        found={}
        for row in data['rows']:
            if row['id'] not in found or row['version'] >= found[row['id']]['version']:
                found[row['id']]=row
        return [found[k] for k in sorted(found)]
    ''',"row['version'] >= found[row['id']]['version']","row['version'] < found[row['id']]['version']",
    lambda r: latest_fixture(r))
def latest_fixture(r):
    n=r.randrange(10,90);rows=[dict(id='a',version=3,value=n),dict(id='a',version=1,value=0),dict(id='b',version=2,value=n+1),dict(id='a',version=3,value=n+2)]
    return dict(rows=rows),[rows[-1],rows[2]]

add('stable-first','deduplication','Preserve the first event per ID',
    'Return the first row for each id, preserving the order in which distinct IDs first appeared. Later duplicate rows must not replace the first.',
    '''
    def transform(data):
        found={}
        for row in data['rows']:
            if row['id'] not in found: found[row['id']]=row
        return list(found.values())
    ''',"if row['id'] not in found: found[row['id']]=row","if True: found[row['id']]=row",
    lambda r: (dict(rows=[dict(id='b',v=r.randrange(10,90)),dict(id='a',v=4),dict(id='b',v=-1)]),None))
# Explicitly author expected rows; do not call the solution to generate labels.
def stable_fixture(r):
    n=r.randrange(10,90);a=dict(id='b',v=n);b=dict(id='a',v=4)
    return dict(rows=[a,b,dict(id='b',v=-1)]),[a,b]
SPECS[-1].fixture=stable_fixture

add('event-idempotency','deduplication','Do not double-count retried purchases',
    'Events contain event_id, customer, and integer cents. An event_id may repeat with an identical payload. Count it once globally. Return a mapping of customer to total cents.',
    '''
    def transform(data):
        totals=defaultdict(int);seen=set()
        for row in data['events']:
            if row['event_id'] in seen: continue
            seen.add(row['event_id']);totals[row['customer']]+=row['cents']
        return dict(totals)
    ''',"if row['event_id'] in seen: continue","if False: continue",
    lambda r: event_fixture(r))
def event_fixture(r):
    n=r.randrange(1,1000);e=dict(event_id='x',customer='a',cents=n);f=dict(event_id='y',customer='a',cents=17)
    return dict(events=[e,f,e]),dict(a=n+17)

add('composite-identity','deduplication','Deduplicate within each tenant',
    'Rows contain tenant, id, and value. The pair (tenant,id) is the identity. Keep the last row for each pair and return rows sorted by tenant, then id.',
    '''
    def transform(data):
        found={}
        for row in data['rows']: found[(row['tenant'],row['id'])]=row
        return sorted(found.values(),key=lambda row:(row['tenant'],row['id']))
    ''',"found[(row['tenant'],row['id'])]=row","found[row['id']]=row",
    lambda r: composite_fixture(r))
def composite_fixture(r):
    n=r.randrange(1,100);a=dict(tenant='east',id='1',value=n);b=dict(tenant='west',id='1',value=n+1)
    return dict(rows=[dict(a,value=0),b,a]),[a,b]

add('utc-day','timezones','Aggregate events by UTC calendar day',
    'Each event has an ISO-8601 timestamp with an explicit offset and integer value. Sum values by UTC date and return a date-to-total mapping. Z means UTC.',
    '''
    def transform(data):
        out=defaultdict(int)
        for event in data['events']:
            stamp=datetime.fromisoformat(event['timestamp'].replace('Z','+00:00'))
            day=stamp.astimezone(timezone.utc).date().isoformat()
            out[day]+=event['value']
        return dict(out)
    ''',"stamp.astimezone(timezone.utc).date().isoformat()","stamp.date().isoformat()",
    lambda r: (dict(events=[dict(timestamp='2025-01-02T00:30:00+05:30',value=(n:=r.randrange(1,100))),dict(timestamp='2025-01-01T23:00:00Z',value=2)]),{'2025-01-01':n+2}))

add('elapsed-time','timezones','Calculate elapsed seconds across offsets',
    'Return integer elapsed seconds from start to end, respecting each timestamp offset. Inputs have whole seconds and explicit offsets; signed results are allowed.',
    '''
    def transform(data):
        start=datetime.fromisoformat(data['start'].replace('Z','+00:00'))
        end=datetime.fromisoformat(data['end'].replace('Z','+00:00'))
        return int((end-start).total_seconds())
    ''',"(end-start).total_seconds()","(end.replace(tzinfo=None)-start.replace(tzinfo=None)).total_seconds()",
    lambda r: (dict(start='2025-01-01T10:00:00+05:30',end=f"2025-01-01T05:{(m:=r.randrange(0,60)):02}:00Z"),1800+60*m))

add('instant-sort','timezones','Sort events by actual instant',
    'Sort events by their ISO timestamp interpreted as an instant, breaking ties by id. Return only event IDs. Every timestamp includes an offset.',
    '''
    def transform(data):
        return [e['id'] for e in sorted(data['events'],key=lambda e:(datetime.fromisoformat(e['timestamp'].replace('Z','+00:00')),e['id']))]
    ''',"datetime.fromisoformat(e['timestamp'].replace('Z','+00:00'))","e['timestamp']",
    lambda r: (dict(events=[dict(id=f'a{(n:=r.randrange(100))}',timestamp='2025-01-02T00:00:00+05:30'),dict(id=f'b{n}',timestamp='2025-01-01T23:00:00Z')]),[f'a{n}',f'b{n}']))

add('offset-window','timezones','Filter a UTC time window',
    'Return IDs, in input order, whose offset-aware timestamps are in [start,end). Start and end also have explicit offsets.',
    '''
    def transform(data):
        parse=lambda x: datetime.fromisoformat(x.replace('Z','+00:00'))
        start,end=parse(data['start']),parse(data['end'])
        return [e['id'] for e in data['events'] if start<=parse(e['timestamp'])<end]
    ''',"datetime.fromisoformat(x.replace('Z','+00:00'))","datetime.fromisoformat(x.replace('Z','+00:00')).replace(tzinfo=None)",
    lambda r: (dict(start='2025-01-01T00:00:00Z',end='2025-01-01T01:00:00Z',events=[dict(id=(n:=str(r.randrange(100))),timestamp='2025-01-01T05:45:00+05:30'),dict(id='outside',timestamp='2025-01-01T00:30:00-02:00')]),[n]))

add('line-rounding','money','Round each invoice line correctly',
    'Input prices are nonnegative decimal strings. Round each price to cents using ROUND_HALF_UP, then sum the integer cents. Do not round only the final sum.',
    '''
    def transform(data):
        return sum(int((Decimal(p)*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)) for p in data['prices'])
    ''',"int((Decimal(p)*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))","int(Decimal(p)*100)",
    lambda r: (dict(prices=[f'{(n:=r.randrange(1,100))}.005','0.005']),100*n+2))

add('discount-basis-points','money','Apply a discount without integer truncation',
    'Input subtotal_cents and discount_bps are integers; 10000 bps is 100%. Return final cents after discount, rounded half up once. Nonnegative subtotal, bps in 0..10000.',
    '''
    def transform(data):
        value=Decimal(data['subtotal_cents'])*(10000-data['discount_bps'])/10000
        return int(value.quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    ''',"int(value.quantize(Decimal('1'),rounding=ROUND_HALF_UP))","int(value)",
    lambda r: (dict(subtotal_cents=2*(n:=r.randrange(10,500))+1,discount_bps=5000),n+1))

add('cent-allocation','money','Allocate cents without losing the remainder',
    'Split nonnegative total_cents equally among positive count recipients. Return an integer list. Give any remainder one cent at a time to the earliest recipients.',
    '''
    def transform(data):
        base,extra=divmod(data['total_cents'],data['count'])
        return [base+int(i<extra) for i in range(data['count'])]
    ''',"base+int(i<extra)","base",
    lambda r: (dict(total_cents=3*(n:=r.randrange(1,200))+2,count=3),[n+1,n+1,n]))

add('signed-refunds','money','Preserve the sign of refund transactions',
    'Transactions have account and signed integer cents. Positive entries are charges and negative entries are refunds. Return net cents for every account seen, including net zero.',
    '''
    def transform(data):
        totals=defaultdict(int)
        for row in data['transactions']:totals[row['account']]+=row['cents']
        return dict(totals)
    ''',"+=row['cents']","+=abs(row['cents'])",
    lambda r: (dict(transactions=[dict(account='a',cents=(n:=r.randrange(100,500))),dict(account='a',cents=-20),dict(account='b',cents=0)]),dict(a=n-20,b=0)))

add('left-enrichment','joins','Keep orders whose customer is unknown',
    'Customers have unique id and name. Orders have id, customer_id, cents. Return every order in input order with customer_name added; use null for an unknown customer.',
    '''
    def transform(data):
        customers={r['id']:r['name'] for r in data['customers']}
        return [dict(o,customer_name=customers.get(o['customer_id'])) for o in data['orders']]
    ''',"for o in data['orders']]","for o in data['orders'] if o['customer_id'] in customers]",
    lambda r: left_fixture(r))
def left_fixture(r):
    n=r.randrange(1,100);a=dict(id='x',customer_id='known',cents=n);b=dict(id='y',customer_id='missing',cents=9)
    return dict(customers=[dict(id='known',name='Ada')],orders=[a,b]),[dict(a,customer_name='Ada'),dict(b,customer_name=None)]

add('latest-dimension','joins','Join against the newest dimension version',
    'Customer rows have id, integer version, and segment; the greatest version is authoritative. Versions per id are unique. Return order IDs and their customer segment in order; unknowns get null.',
    '''
    def transform(data):
        customers={}
        for c in sorted(data['customers'],key=lambda c:c['version']):customers[c['id']]=c['segment']
        return [dict(id=o['id'],segment=customers.get(o['customer_id'])) for o in data['orders']]
    ''',"sorted(data['customers'],key=lambda c:c['version'])","data['customers']",
    lambda r: (dict(customers=[dict(id='c',version=4,segment=(s:='premium'+str(r.randrange(100)))),dict(id='c',version=1,segment='old')],orders=[dict(id='o',customer_id='c')]),[dict(id='o',segment=s)]))

add('join-multiplication','joins','Avoid counting order revenue once per item',
    'Orders have unique id and total_cents. Items have order_id. Return revenue_cents summed once per order, and item_count for items whose order exists. Ignore orphan items.',
    '''
    def transform(data):
        orders={o['id']:o['total_cents'] for o in data['orders']}
        return dict(revenue_cents=sum(orders.values()),item_count=sum(i['order_id'] in orders for i in data['items']))
    ''',"sum(orders.values())","sum(orders.get(i['order_id'],0) for i in data['items'])",
    lambda r: (dict(orders=[dict(id='a',total_cents=(n:=r.randrange(100,900))),dict(id='b',total_cents=40)],items=[dict(order_id='a'),dict(order_id='a'),dict(order_id='orphan')]),dict(revenue_cents=n+40,item_count=2)))

add('tenant-join','joins','Join customers using tenant and customer ID',
    'Customers are unique by (tenant,id). Orders contain tenant and customer_id. Return customer names in order, using null if the pair does not exist.',
    '''
    def transform(data):
        customers={(c['tenant'],c['id']):c['name'] for c in data['customers']}
        return [customers.get((o['tenant'],o['customer_id'])) for o in data['orders']]
    ''',"return [customers.get((o['tenant'],o['customer_id'])) for o in data['orders']]","return [{c['id']:c['name'] for c in data['customers']}.get(o['customer_id']) for o in data['orders']]",
    lambda r: (dict(customers=[dict(tenant='a',id='1',name=(s:='Ada'+str(r.randrange(100)))),dict(tenant='b',id='1',name='Ben')],orders=[dict(tenant='a',customer_id='1'),dict(tenant='c',customer_id='1')]),[s,None]))

add('half-open','windows','Use half-open numeric reporting windows',
    'Given integer start/end and records with integer t and id, return IDs in input order for start <= t < end. Empty windows return an empty list.',
    '''
    def transform(data):
        return [r['id'] for r in data['records'] if data['start']<=r['t']<data['end']]
    ''',"r['t']<data['end']","r['t']<=data['end']",
    lambda r: (dict(start=(n:=r.randrange(1,100)),end=n+10,records=[dict(id='start',t=n),dict(id='end',t=n+10),dict(id='before',t=n-1)]),['start']))

add('session-gap','windows','Start a session only after the idle gap is exceeded',
    'Sort integer event times. Return a list of sessions, each a list of times. A new session starts only when the gap from the preceding time is strictly greater than gap. Equal times stay together.',
    '''
    def transform(data):
        sessions=[]
        for t in sorted(data['times']):
            if not sessions or t-sessions[-1][-1]>data['gap']:sessions.append([t])
            else:sessions[-1].append(t)
        return sessions
    ''',"t-sessions[-1][-1]>data['gap']","t-sessions[-1][-1]>=data['gap']",
    lambda r: (dict(times=[(n:=r.randrange(1,100))+5,n,n+11],gap=5),[[n,n+5],[n+11]]))

add('calendar-seven-day','windows','Compute a seven-calendar-day total',
    'Given an ISO date as_of and dated integer-value records, sum values on the seven calendar dates ending at as_of, inclusive. Ignore future and older records; duplicate dates all contribute.',
    '''
    def transform(data):
        end=datetime.fromisoformat(data['as_of']).date();start=end-timedelta(days=6)
        return sum(r['value'] for r in data['records'] if start<=datetime.fromisoformat(r['date']).date()<=end)
    ''',"timedelta(days=6)","timedelta(days=7)",
    lambda r: (dict(as_of='2025-01-10',records=[dict(date='2025-01-03',value=99),dict(date='2025-01-04',value=(n:=r.randrange(1,100))),dict(date='2025-01-10',value=2),dict(date='2025-01-11',value=50)]),n+2))

add('asof-features','windows','Prevent future information leaking into features',
    'Updates have unique integer t and a value. For each query time, return the value at the greatest update time <= query, or null if none exists. Query order is preserved.',
    '''
    def transform(data):
        result=[]
        for q in data['queries']:
            past=[u for u in data['updates'] if u['t']<=q]
            result.append(max(past,key=lambda u:u['t'])['value'] if past else None)
        return result
    ''',"if u['t']<=q","if True",
    lambda r: (dict(updates=[dict(t=3,value=(n:=r.randrange(10,100))),dict(t=9,value=n+1)],queries=[1,3,5,9]),[None,n,n,n+1]))

add('quantity-alias','schema','Respect an explicit zero in a renamed field',
    'For each record return quantity if the quantity key is present, otherwise qty if present, otherwise 1. Explicit zero and null values must be preserved.',
    '''
    def transform(data):
        return [r['quantity'] if 'quantity' in r else r.get('qty',1) for r in data['rows']]
    ''',"r['quantity'] if 'quantity' in r else r.get('qty',1)","r.get('quantity') or r.get('qty') or 1",
    lambda r: (dict(rows=[dict(quantity=0,qty=9),dict(qty=(n:=r.randrange(2,100))),{},dict(quantity=None)]),[0,n,1,None]))

add('nullable-integer','schema','Parse nullable integer fields consistently',
    'Values are null, empty/whitespace strings, integers, or strings containing signed integers. Map null and blank strings to null; convert all other values to integers. Booleans are not inputs.',
    '''
    def transform(data):
        return [None if v is None or (isinstance(v,str) and not v.strip()) else int(v) for v in data['values']]
    ''',"None if v is None or (isinstance(v,str) and not v.strip()) else int(v)","None if not v or (isinstance(v,str) and not v.strip()) else int(v)",
    lambda r: (dict(values=[None,' ',0,'0',f' -{(n:=r.randrange(1,100))} ']),[None,None,0,0,-n]))

add('nested-country','schema','Flatten optional addresses without dropping rows',
    'Return each user id with country from address.country. Missing/null address or missing/null country becomes "UNKNOWN". Preserve user order and non-null country values.',
    '''
    def transform(data):
        result=[]
        for user in data['users']:
            address=user.get('address') or {};country=address.get('country')
            result.append(dict(id=user['id'],country=country if country is not None else 'UNKNOWN'))
        return result
    ''',"address=user.get('address') or {}","address=user.get('address',{})",
    lambda r: (dict(users=[dict(id=(n:=str(r.randrange(100))),address=None),dict(id='b',address=dict(country='IN')),dict(id='c')]),[dict(id=n,country='UNKNOWN'),dict(id='b',country='IN'),dict(id='c',country='UNKNOWN')]))

add('status-normalization','schema','Normalize statuses without accepting unknown categories',
    'Trim and lowercase string statuses. Map paid and settled to paid, refund and refunded to refunded, pending to pending; unknown strings and null map to unknown. Return one output per input.',
    '''
    def transform(data):
        mapping={'paid':'paid','settled':'paid','refund':'refunded','refunded':'refunded','pending':'pending'}
        return [mapping.get(v.strip().lower(),'unknown') if isinstance(v,str) else 'unknown' for v in data['statuses']]
    ''',"v.strip().lower()","v",
    lambda r: (dict(statuses=[' PAID ','Settled',' refund ',None,'pending','mystery'+str(r.randrange(100))]),['paid','paid','refunded','unknown','pending','unknown']))

assert len(SPECS)==24
SPLITS={'deduplication':'train','timezones':'train','money':'train','joins':'validation','windows':'test','schema':'test'}

EMPTY_INPUTS={
'latest-record':({'rows':[]},[]),'stable-first':({'rows':[]},[]),
'event-idempotency':({'events':[]},{}),'composite-identity':({'rows':[]},[]),
'utc-day':({'events':[]},{}),'elapsed-time':({'start':'2025-01-01T00:00:00Z','end':'2025-01-01T00:00:00+00:00'},0),
'instant-sort':({'events':[]},[]),'offset-window':({'start':'2025-01-01T00:00:00Z','end':'2025-01-02T00:00:00Z','events':[]},[]),
'line-rounding':({'prices':[]},0),'discount-basis-points':({'subtotal_cents':0,'discount_bps':10000},0),
'cent-allocation':({'total_cents':0,'count':3},[0,0,0]),'signed-refunds':({'transactions':[]},{}),
'left-enrichment':({'customers':[],'orders':[]},[]),'latest-dimension':({'customers':[],'orders':[{'id':'x','customer_id':'unknown'}]},[{'id':'x','segment':None}]),
'join-multiplication':({'orders':[],'items':[{'order_id':'missing'}]},{'revenue_cents':0,'item_count':0}),
 'tenant-join':({'customers':[],'orders':[]},[]),'half-open':({'start':5,'end':5,'records':[{'id':'a','t':5}]},[]),
'session-gap':({'times':[],'gap':5},[]),'calendar-seven-day':({'as_of':'2025-01-01','records':[]},0),
'asof-features':({'updates':[],'queries':[0,1]},[None,None]),'quantity-alias':({'rows':[]},[]),
'nullable-integer':({'values':[]},[]),'nested-country':({'users':[]},[]),'status-normalization':({'statuses':[]},[])}
_original_fixtures=fixtures

def fixtures(spec):
    data,expected=EMPTY_INPUTS[spec.slug]
    return _original_fixtures(spec)+[dict(id='boundary-empty',visibility='heldout',input=data,expected=expected)]
