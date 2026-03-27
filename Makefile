:PHONY new-device
new-device:
	mosquitto_pub -t "zigbee2mqtt/bridge/request/permit_join" -m '{"value":true, "time":120}' -p 1889

:PHONY pull
pull:
	docker compose pull

:PHONY build
build:
	docker compose build

:PHONY up
up:
	docker compose up -d

:PHONY down
down:
	docker compose down
	rm -rf kafka/data;
	rm -rf zookeeper/*

:PHONY ps
ps:
	docker compose ps -a

:PHONY migrate
migrate:
	docker compose up -d redis
	docker compose up -d postgres
	docker compose run --rm admin-panel python3 ./manage.py migrate --noinput

:PHONY makemigrations
makemigrations:
	docker compose up -d redis
	docker compose up -d postgres
	docker compose run --rm admin-panel python3 ./manage.py makemigrations --noinput

:PHONY run
run:
	docker compose run --rm ${SRV} bash
