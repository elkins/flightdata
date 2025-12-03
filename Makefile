.PHONY: help install test clean format lint run examples

help:
	@echo "FlightData - ADS-B Exchange API Client"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run test suite"
	@echo "  make coverage   - Run tests with coverage report"
	@echo "  make format     - Format code with black"
	@echo "  make lint       - Run linter (ruff)"
	@echo "  make clean      - Remove generated files"
	@echo "  make run        - Run main example"
	@echo "  make examples   - Run all examples"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

coverage:
	python -m pytest tests/ --cov=src/flightdata --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

format:
	black src/ tests/ examples/ setup.py --line-length 100

lint:
	ruff check src/ tests/ examples/

typecheck:
	mypy src/flightdata/ --ignore-missing-imports

clean:
	rm -rf __pycache__
	rm -rf **/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.pyc
	rm -rf **/*.pyc
	rm -rf *.csv
	rm -rf *.json
	rm -rf build dist *.egg-info
	rm -rf src/*.egg-info

run:
	python -m flightdata.adsbexchange

examples:
	python examples/examples.py

config:
	python -c "from flightdata.config import Config; Config.create_template('.flightdata.json')"
	@echo "Configuration template created!"
	@echo "Edit .flightdata.json to add your API key"
