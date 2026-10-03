.PHONY: configure build up down validate-collector test
configure:
	./tools/configure.sh
build: configure
	./tools/compose.sh build credential-init
up: build
	./tools/compose.sh up -d
	./tools/compose.sh wait storage-init
down:
	./tools/compose.sh down
validate-collector:
	./tools/compose.sh run --rm --no-deps otel-gateway validate --config=/etc/otelcol-contrib/config.yaml
test:
	./tools/test-foundation.sh
