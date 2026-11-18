.PHONY: help install run test lint format clean docker-build docker-run

PYTHON = .venv/bin/python
PIP = .venv/bin/pip
STREAMLIT = .venv/bin/streamlit
PYTEST = .venv/bin/pytest

help:
	@echo "Available commands:"
	@echo "  make install      Install project dependencies"
	@echo "  make run          Launch the Streamlit travel planner UI"
	@echo "  make test         Execute unit and integration tests"
	@echo "  make clean        Remove cache and build artifacts"
	@echo "  make docker-build Build Docker container"
	@echo "  make docker-run   Run Docker container"

install:
	$(PIP) install -r requirements.txt
	$(PIP) install pytest

run:
	$(STREAMLIT) run app.py

test:
	PYTHONPATH=. $(PYTEST)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache

docker-build:
	docker build -t agentic-travel-planner .

docker-run:
	docker run -p 8501:8501 --env-file .env agentic-travel-planner
