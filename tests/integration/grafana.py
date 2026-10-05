"""Run in the fixture container; exercise Grafana's real datasource proxy."""
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = 'http://grafana:3000'
PROXY = '/api/datasources/proxy/uid/object-storage-traces'
TRACE = '/api/v1/traces/0123456789abcdef0123456789abcdef'

def get(path, status=200):
    try:
        response = urlopen(BASE + path, timeout=10)
    except HTTPError as error:
        response = error
    assert response.status == status, (path, response.status)
    return json.load(response)

assert get('/api/health')['version'] == '12.2.0'
source = get('/api/datasources/uid/object-storage-traces')
assert source['access'] == 'proxy' and source['url'] == 'http://querier:8080'
dashboard = get('/api/dashboards/uid/trace-contract')['dashboard']
assert dashboard['panels'][0]['type'] == 'traces'
assert get(PROXY + '/healthz')['status'] == 'fixture'
trace = get(PROXY + TRACE)
assert trace['meta']['lookupScope'] == 'all_retained'
assert trace['meta']['completeness'] == 'unknown'
assert trace['spans'][0]['startTimeUnixNano'] == '1790899200000000123'
assert trace['spans'][1]['durationNano'] == '1500000'
assert trace['spans'][1]['attributes'][0]['value']['boolValue'] is False
assert trace['spans'][1]['events'][0]['name'] == 'exception'
assert trace['spans'][1]['links'][0]['spanId'] == '3333333333333333'
def bounded(start, end, status=200):
    return get(PROXY + TRACE + '?' + urlencode({'start':start, 'end':end}), status)
scoped = bounded('2026-10-02T00:00:00.001Z', '2026-10-02T00:00:00.002Z')
assert scoped['spans'] == trace['spans']  # Block overlap does not trim spans.
assert scoped['meta']['lookupScope'] == 'time_range'
assert scoped['meta']['requestedRange']['start'] == '2026-10-02T00:00:00.001Z'
bounded('2026-10-02T00:00:00.010000123Z', '2026-10-02T00:00:00.010000124Z')
bounded('2026-10-02T00:00:00.010000124Z', '2026-10-02T00:00:00.010000125Z', 404)
bounded('2026-10-02T00:00:00Z', '2026-10-02T00:00:00.000000123Z', 404)
bounded('2026-10-03T00:00:00Z', '2026-10-03T01:00:00Z', 404)
bounded('2026-10-02T00:00:00Z', '2026-10-02T00:00:00Z', 400)
bounded('2026-10-02T00:00:00Z', '2026-10-04T00:00:00Z', 400)
bounded('bad', '2026-10-02T00:00:00Z', 400)
get(PROXY + TRACE + '?start=2026-10-02T00:00:00Z', 400)
get(PROXY + '/api/v1/traces/bad', 400)
get(PROXY + '/api/v1/traces/' + 'f' * 32, 404)
linked = get(PROXY + '/api/v1/traces/abcdef0123456789abcdef0123456789')
assert linked['spans'][0]['spanId'] == '3333333333333333'
print('PASS Grafana version, provisioning, proxy, exact nanoseconds, typed attributes, events, links, paired scope, block boundaries, and HTTP errors')
