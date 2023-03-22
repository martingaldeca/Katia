#!make
include .env
SHELL := /bin/bash
TAIL_LOGS = 50

up:
	docker compose up --force-recreate -d
down:
	docker compose down

down-up: down up

build:
	docker compose build

complete-build: build up

broker-logs:
	docker logs -f --tail ${TAIL_LOGS} broker
sh-broker:
	docker exec -it broker bash

black:
	black . --config pyproject.toml

isort:
	isort .

code-style: black isort

ruff:
	ruff check . --fix

pylint:
	pylint katia/ --fail-under=9

linters: ruff pylint

test:
	pytest -n auto --cov=katia --cov-report html