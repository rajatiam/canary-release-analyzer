import csv, hashlib, io, json, math, re
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import Request, urlopen

def now(): return datetime.now(timezone.utc).isoformat()

def validate(data, records):
    if not isinstance(data,dict): raise ValueError('JSON object required')
    row = {}
    for key,example in CONFIG['example'].items():
        value = data.get(key)
        if isinstance(example,bool):
            if not isinstance(value,bool): raise ValueError(key+' must be boolean')
        elif isinstance(example,(int,float)):
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0: raise ValueError(key+' must be finite and nonnegative')
            if isinstance(example,int) and not isinstance(value,int): raise ValueError(key+' must be an integer')
        elif not isinstance(value,str) or not value.strip() or len(value)>2000: raise ValueError(key+' requires text, up to 2000 characters')
        row[key] = value.strip() if isinstance(value,str) else value
    return initialize(row,records)

def http_url(value):
    url = urlparse(value)
    if url.scheme not in ['http','https'] or not url.hostname or url.username or url.password: raise ValueError('HTTP(S) URL without credentials required')

def unique(rows,row,fields):
    if any(all(r[f]==row[f] for f in fields) for r in rows): raise ValueError('Duplicate '+', '.join(fields))

def initialize(row,records):
    if row['requests']==0 or row['errors']>row['requests']: raise ValueError('Requests must be positive and errors cannot exceed requests')
    if row['baseline_latency_ms']==0 or row['max_latency_ratio']==0: raise ValueError('Baseline latency and latency ratio must be positive')
    if row['max_error_percent']>100: raise ValueError('Error percentage must be at most 100')
    return dict(row,decision='pending',error_percent=None,latency_ratio=None,reasons=[])
def summary(rows): return {'canaries':len(rows),'promote':sum(r['decision']=='promote' for r in rows),'rollback':sum(r['decision']=='rollback' for r in rows)}
def transition(row,action):
    if action!='analyze': raise ValueError('Unsupported action')
    error_percent=row['errors']/row['requests']*100; ratio=row['canary_latency_ms']/row['baseline_latency_ms']; reasons=[]
    if error_percent>row['max_error_percent']: reasons.append('Error rate exceeds threshold')
    if ratio>row['max_latency_ratio']: reasons.append('Latency ratio exceeds threshold')
    return dict(row,decision='rollback' if reasons else 'promote',error_percent=round(error_percent,3),latency_ratio=round(ratio,3),reasons=reasons)
