.PHONY: help install setup run clean test

help:
	@echo "Agentic Documentation Generator - Available Commands"
	@echo "===================================================="
	@echo "make install    - Install dependencies"
	@echo "make setup      - Setup virtual environment and install dependencies"
	@echo "make run        - Run with example repository (set REPO variable)"
	@echo "make clean      - Clean up generated files and cache"
	@echo "make test       - Run tests (when implemented)"
	@echo ""
	@echo "Example usage:"
	@echo "  make setup"
	@echo "  make run REPO=openshift/installer LIMIT=5"

install:
	pip install -r requirements.txt

setup:
	python3 -m venv venv
	@echo "Virtual environment created. Activate with:"
	@echo "  source venv/bin/activate  # On Linux/Mac"
	@echo "  venv\\Scripts\\activate     # On Windows"
	@echo ""
	@echo "Then run: make install"

run:
	@if [ -z "$(REPO)" ]; then \
		echo "Error: REPO variable not set"; \
		echo "Usage: make run REPO=owner/repo [LIMIT=10]"; \
		exit 1; \
	fi
	python main.py --repo $(REPO) $(if $(LIMIT),--limit $(LIMIT),)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .coverage htmlcov/
	@echo "Cleaned up generated files and cache"

test:
	@echo "Tests not yet implemented"
	@echo "Add tests in tests/ directory and run with pytest"
