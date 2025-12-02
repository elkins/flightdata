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
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov black ruff mypy

test:
	python -m pytest -v

coverage:
	python -m pytest --cov=. --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

format:
	black *.py --line-length 100

lint:
	ruff check *.py

typecheck:
	mypy adsbexchange.py flight_logger.py config.py

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.pyc
	rm -rf *.csv
	rm -rf *.json
	rm -rf build dist *.egg-info

run:
	python adsbexchange.py

examples:
	python examples.py

config:
	python config.py .flightdata.json
	@echo "Configuration template created!"
	@echo "Edit .flightdata.json to add your API key"
