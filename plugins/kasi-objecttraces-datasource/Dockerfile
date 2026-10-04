FROM node:22.14.0-bookworm-slim@sha256:1c18d9ab3af4585870b92e4dbc5cac5a0dc77dd13df1a5905cea89fc720eb05b AS build
WORKDIR /plugin
COPY plugins/kasi-objecttraces-datasource/package*.json ./
RUN npm ci --no-audit --no-fund
COPY plugins/kasi-objecttraces-datasource/ ./
COPY tests/fixtures/trace.json ./trace.json
RUN npm test && npm run build && cp plugin.json dist/ && mkdir -p dist/img && cp logo.svg dist/img/logo.svg
FROM grafana/grafana:12.2.0@sha256:74144189b38447facf737dfd0f3906e42e0776212bf575dc3334c3609183adf7
COPY --from=build /plugin/dist /var/lib/grafana/plugins/kasi-objecttraces-datasource
