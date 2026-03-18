.PHONY: help install install-dev lint format type-check test test-unit test-integration setup-db run-backtest run-paper run-live dashboard health clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install all dependencies including dev tools
	pip install -r requirements-dev.txt
	pre-commit install

lint:  ## Run linter (ruff)
	ruff check src/ tests/ main.py

format:  ## Auto-format code
	ruff format src/ tests/ main.py
	ruff check --fix src/ tests/ main.py

type-check:  ## Run type checker (mypy)
	mypy src/ main.py

test:  ## Run all tests
	pytest

test-unit:  ## Run unit tests only
	pytest -m unit

test-integration:  ## Run integration tests only
	pytest -m integration

setup-db:  ## Initialize the SQLite database
	python scripts/setup_db.py

run-backtest:  ## Run backtesting
	python main.py --mode backtest

run-paper:  ## Run paper trading
	python main.py --mode paper-trade

run-live:  ## Run live trading (requires passing all gates)
	python main.py --mode live

dashboard:  ## Show performance dashboard
	python main.py --mode dashboard

health:  ## Run system health check
	python scripts/health_check.py

clean:  ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage dist build *.egg-info
