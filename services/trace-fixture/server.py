"""GH-2 only: deterministic canonical response, no storage/query implementation."""
import copy
import json
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs

with open('/app/trace.json') as f:
    TRACE = json.load(f)

def unix_nano(value):
    match = re.fullmatch(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})', value)
    if not match:
        raise ValueError('Expected RFC3339')
    whole, fraction, zone = match.groups()
    delta = datetime.fromisoformat(whole + zone.replace('Z', '+00:00')) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 1_000_000_000 + int((fraction or '').ljust(9, '0'))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == '/healthz':
            return self.reply(200, {'status': 'fixture'})
        trace_id = url.path.removeprefix('/api/v1/traces/')
        if not url.path.startswith('/api/v1/traces/') or not re.fullmatch('[0-9a-f]{32}', trace_id):
            return self.error(400, 'INVALID_REQUEST', 'Expected a lowercase 32-hex trace ID')
        args = parse_qs(url.query, keep_blank_values=True)
        result = copy.deepcopy(TRACE)
        if args:
            try:
                if set(args) != {'start', 'end'} or any(len(v) != 1 for v in args.values()):
                    raise ValueError()
                start, end = (unix_nano(args[k][0]) for k in ('start', 'end'))
                if start < 0 or not 0 < end-start <= 86400 * 1_000_000_000:
                    raise ValueError()
            except ValueError:
                return self.error(400, 'INVALID_RANGE', 'Supply paired RFC3339 bounds, increasing and at most 24 hours')
            result['meta'].update(lookupScope='time_range', requestedRange={k:v[0] for k,v in args.items()})
            # The fixture models one immutable block's overlap; never trim its spans.
            if end <= min(int(s['startTimeUnixNano']) for s in TRACE['spans']) or start > max(int(s['endTimeUnixNano']) for s in TRACE['spans']):
                return self.error(404, 'NOT_FOUND', 'Not found in selected time range; explicitly choose All retained data to widen')
        if trace_id == 'abcdef0123456789abcdef0123456789':
            span = copy.deepcopy(TRACE['spans'][0])
            span.update(traceId=trace_id, spanId='3333333333333333', name='payment attempt', serviceName='payments')
            result.update(traceId=trace_id, spans=[span])
        elif trace_id != TRACE['traceId']:
            return self.error(404, 'NOT_FOUND', 'Trace not found in the fixture dataset')
        self.reply(200, result)

    def error(self, status, code, message):
        self.reply(status, {'error': {'code':code,'message':message,'retryable':False},'requestId':'fixture'})

    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        self.wfile.write(data)

ThreadingHTTPServer(('0.0.0.0',8080), Handler).serve_forever()
