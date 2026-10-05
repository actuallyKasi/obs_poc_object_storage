FROM python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
WORKDIR /app
COPY services/trace-fixture/server.py /app/server.py
COPY tests/fixtures/trace.json /app/trace.json
USER 65534:65534
CMD ["python", "server.py"]
