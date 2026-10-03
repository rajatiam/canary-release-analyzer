import csv, hashlib, io, json, math, re
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from .validation import validate_input, http_url, unique

def now(): return datetime.now(timezone.utc).isoformat()
def validate(data,records): return initialize(validate_input(data,CONFIG['example']),records)

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
