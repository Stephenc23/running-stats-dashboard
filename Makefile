SHELL := /bin/sh

.PHONY: up down logs rebuild api-shell db-shell frontend

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=150

rebuild:
	docker compose build --no-cache

api-shell:
	docker compose exec api sh

db-shell:
	docker compose exec db psql -U postgres -d running_stats

frontend:
	npm --prefix frontend install
	npm --prefix frontend run dev
