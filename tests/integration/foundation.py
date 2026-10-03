"""Real S3 and DuckDB compatibility checks, executed inside the tools image."""
import hashlib
import http.client
import http.server
import json
import os
import platform
import sys
import tempfile
import threading
import urllib.request
import urllib.parse
import uuid

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import ClientError

from storage import client

BUCKET = os.environ['S3_BUCKET']
SENTINEL = 'compatibility/persistence.bin'
PAYLOAD = bytes(range(256)) * 4096


class RangeRecorder(http.server.BaseHTTPRequestHandler):
    """Forward S3 requests unchanged; retain only method/range/status evidence."""

    def log_message(self, *_args):
        pass  # Never log signed request headers or URLs.

    def forward(self):
        endpoint = urllib.parse.urlsplit(os.environ['S3_ENDPOINT'])
        upstream = http.client.HTTPConnection(endpoint.hostname, endpoint.port, timeout=10)
        try:
            upstream.request(self.command, self.path, headers=dict(self.headers))
            response = upstream.getresponse()
            data = response.read()
            self.server.observed.append((self.command, self.headers.get('Range'), response.status))
            self.send_response(response.status)
            for name, value in response.getheaders():
                if name.lower() not in ('connection', 'transfer-encoding'):
                    self.send_header(name, value)
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(data)
        finally:
            upstream.close()

    do_GET = forward
    do_HEAD = forward


def read_body(response):
    with response['Body'] as body:
        return body.read()


def persistence(mode):
    s3 = client()
    if mode == 'seed':
        s3.put_object(Bucket=BUCKET, Key=SENTINEL, Body=PAYLOAD)
    assert read_body(s3.get_object(Bucket=BUCKET, Key=SENTINEL)) == PAYLOAD
    print(f'PASS persistence {mode}: sha256={hashlib.sha256(PAYLOAD).hexdigest()}')


def rejected(s3, key, label):
    operations = [
        lambda: s3.get_object(Bucket=BUCKET, Key=key),
        lambda: s3.head_object(Bucket=BUCKET, Key=key),
        lambda: s3.list_objects_v2(Bucket=BUCKET),
        lambda: s3.put_object(Bucket=BUCKET, Key=key, Body=b'unauthorized'),
    ]
    for operation in operations:
        try:
            operation()
        except ClientError as error:
            assert error.response['ResponseMetadata']['HTTPStatusCode'] == 403
        else:
            raise AssertionError(f'{label} request unexpectedly authorized')
    print(f'PASS auth: {label} GET/HEAD/LIST/PUT denied')


def compatibility():
    print(f'Python {platform.python_version()}, machine {platform.machine()}, '
          f'DuckDB {duckdb.__version__}, PyArrow {pa.__version__}')
    s3 = client()
    prefix = f'compatibility/{uuid.uuid4().hex}/'
    keys = [f'{prefix}{index:02}.bin' for index in range(7)]
    for key in keys:
        response = s3.put_object(Bucket=BUCKET, Key=key, Body=PAYLOAD,
                                 Metadata={'fixture': 'gh1'})
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
        assert read_body(s3.get_object(Bucket=BUCKET, Key=key)) == PAYLOAD
    head = s3.head_object(Bucket=BUCKET, Key=keys[0])
    assert head['ContentLength'] == len(PAYLOAD)
    assert head['Metadata']['fixture'] == 'gh1'
    ranged = s3.get_object(Bucket=BUCKET, Key=keys[0], Range='bytes=13-1036')
    assert ranged['ResponseMetadata']['HTTPStatusCode'] == 206
    assert ranged['ContentRange'] == f'bytes 13-1036/{len(PAYLOAD)}'
    assert read_body(ranged) == PAYLOAD[13:1037]
    pages = list(s3.get_paginator('list_objects_v2').paginate(
        Bucket=BUCKET, Prefix=prefix, PaginationConfig={'PageSize': 2}))
    assert len(pages) == 4
    assert all(page['IsTruncated'] for page in pages[:-1])
    assert not pages[-1]['IsTruncated']
    assert [item['Key'] for page in pages for item in page['Contents']] == keys
    print('PASS PUT/immediate GET/HEAD/range 206/paginated LIST (7 objects, 4 pages)')
    rejected(client(config=Config(signature_version=UNSIGNED)), keys[0], 'anonymous')
    rejected(client(aws_access_key_id='invalid-fixture-key'), keys[0], 'unknown key')
    rejected(client(aws_secret_access_key='invalid-fixture-secret'), keys[0], 'wrong secret')
    assert read_body(s3.get_object(Bucket=BUCKET, Key=keys[0])) == PAYLOAD

    # An exact INT64 value beyond JavaScript's safe integer range and typed OTLP
    # attributes guard against accidental timestamp/attribute coercion.
    attributes = json.dumps([{'key': 'count', 'value': {'intValue': '9223372036854775807'}},
                             {'key': 'enabled', 'value': {'boolValue': True}}])
    nanos = 1780000000123456789
    table = pa.table({'start_time_ns': pa.array([nanos, nanos + 1], type=pa.int64()),
                      'span_attributes_json': pa.array([attributes, attributes])})
    with tempfile.NamedTemporaryFile(suffix='.parquet') as parquet:
        pq.write_table(table, parquet.name, compression='zstd')
        s3.upload_file(parquet.name, BUCKET, prefix + 'fixture.parquet')
    db = duckdb.connect(config={
        'extension_directory': '/opt/duckdb/extensions',
        'autoinstall_known_extensions': 'false',
        'autoload_known_extensions': 'false',
        'memory_limit': '256MB', 'threads': '2',
    })
    db.execute('LOAD httpfs')
    recorder = http.server.ThreadingHTTPServer(('127.0.0.1', 0), RangeRecorder)
    recorder.observed = []
    thread = threading.Thread(target=recorder.serve_forever, daemon=True)
    thread.start()
    for setting, value in {
        's3_endpoint': f'127.0.0.1:{recorder.server_port}',
        's3_region': os.environ['AWS_DEFAULT_REGION'],
        's3_access_key_id': os.environ['AWS_ACCESS_KEY_ID'],
        's3_secret_access_key': os.environ['AWS_SECRET_ACCESS_KEY'],
        's3_url_style': 'path', 's3_use_ssl': False,
    }.items():
        db.execute(f'SET {setting} = ?', [value])
    try:
        result = db.execute('SELECT * FROM read_parquet(?) ORDER BY start_time_ns',
                            [f's3://{BUCKET}/{prefix}fixture.parquet']).fetchall()
    finally:
        recorder.shutdown()
        recorder.server_close()
        thread.join()
    ranges = [record for record in recorder.observed
              if record[0] == 'GET' and record[1] and record[2] == 206]
    assert ranges, 'DuckDB did not issue a successful S3 byte range request'
    assert result == [(nanos, attributes), (nanos + 1, attributes)]
    extensions = db.execute("SELECT extension_name, installed, loaded FROM duckdb_extensions() WHERE extension_name='httpfs'").fetchall()
    assert extensions == [('httpfs', True, True)]
    print('PASS DuckDB remote S3 Parquet: baked httpfs, downloads disabled, exact INT64/typed attributes')
    print(f'PASS observed DuckDB S3 range requests: {len(ranges)} (HTTP 206)')
    # Only remove this invocation's fixtures. Persistence sentinel stays for restart check.
    for key in keys + [prefix + 'fixture.parquet']:
        s3.delete_object(Bucket=BUCKET, Key=key)


def collector():
    for url in ['http://otel-gateway:13133/', 'http://otel-gateway:8888/metrics']:
        with urllib.request.urlopen(url, timeout=5) as response:
            assert response.status == 200
    print('PASS Collector health and internal metrics endpoints')


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'compatibility'
    if mode in ('seed', 'verify'):
        persistence(mode)
    else:
        {'compatibility': compatibility, 'collector': collector}[mode]()
