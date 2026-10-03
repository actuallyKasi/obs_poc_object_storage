FROM python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    AWS_EC2_METADATA_DISABLED=true
WORKDIR /app
COPY tools/foundation/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir -r requirements.lock && pip check
# Install at build time; runtime loading and downloading are disabled in the probe.
RUN python -c "import duckdb; c=duckdb.connect(config={'extension_directory':'/opt/duckdb/extensions'}); c.execute(\"INSTALL httpfs FROM 'https://extensions.duckdb.org'\"); c.execute('LOAD httpfs')"
COPY tools/foundation/storage.py /app/storage.py
COPY tests/integration/foundation.py /app/foundation.py
ENTRYPOINT ["python"]
CMD ["foundation.py"]
