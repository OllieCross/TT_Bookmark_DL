.PHONY: install install-dev lint format type-check run docker-build docker-run clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

lint:
	flake8 downloader.py
	black --check downloader.py
	isort --check-only downloader.py

format:
	black downloader.py
	isort downloader.py

type-check:
	mypy downloader.py

check: lint type-check

run:
	python downloader.py

docker-build:
	docker compose build

docker-run:
	docker compose run --rm downloader

clean:
	rm -rf __pycache__ .mypy_cache .ruff_cache
	find . -name "*.pyc" -delete
