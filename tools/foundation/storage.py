"""Small container-only storage bootstrap; credentials are never logged."""
import json
import os
import sys
import time
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, EndpointConnectionError, ConnectionClosedError


def client(**overrides):
    options = dict(
        endpoint_url=os.environ['S3_ENDPOINT'],
        region_name=os.environ['AWS_DEFAULT_REGION'],
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'},
                      connect_timeout=3, read_timeout=10, retries={'max_attempts': 2}),
    )
    options.update(overrides)
    return boto3.client('s3', **options)


def credentials():
    path = Path('/credentials/s3.json')
    path.write_text(json.dumps({'identities': [{
        'name': 'local-foundation',
        'credentials': [{'accessKey': os.environ['AWS_ACCESS_KEY_ID'],
                         'secretKey': os.environ['AWS_SECRET_ACCESS_KEY']}],
        'actions': ['Admin', 'Read', 'Write', 'List', 'Tagging'],
    }]}))
    # The pinned SeaweedFS image drops privileges to uid/gid 1000.
    os.chown(path, 1000, 1000)
    path.chmod(0o600)
    print('S3 credential configuration ready')


def initialize():
    s3 = client()
    bucket = os.environ['S3_BUCKET']
    for attempt in range(60):
        try:
            s3.list_buckets()
            break
        except (EndpointConnectionError, ConnectionClosedError):
            time.sleep(1)
    else:
        raise RuntimeError('S3 did not become available within startup budget')
    try:
        s3.head_bucket(Bucket=bucket)
        print('Bucket already exists')
    except ClientError as error:
        if error.response['ResponseMetadata']['HTTPStatusCode'] != 404:
            raise
        s3.create_bucket(Bucket=bucket)
        print('Bucket created')
    s3.head_bucket(Bucket=bucket)
    print('Bucket readiness PASS')


if __name__ == '__main__':
    {'credentials': credentials, 'init': initialize}[sys.argv[1]]()
