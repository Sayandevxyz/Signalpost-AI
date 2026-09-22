install:
	python -m pip install -r requirements.txt
dev:
	uvicorn signalpost.app.main:app --reload
test:
	pytest -q
lint:
	ruff check signalpost scripts tests
format:
	ruff format signalpost scripts tests
validate:
	python scripts/validate_dataset.py
benchmark:
	python scripts/benchmark.py
docker:
	docker compose up --build
