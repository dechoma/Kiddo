.PHONY: help sync sync-gmail test test-integration clean

help:
	@echo "Available commands:"
	@echo "  make sync         - Install base + dev dependencies (uv sync)"
	@echo "  make sync-gmail   - Install with Gmail dependencies"
	@echo "  make test         - Run tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make clean        - Clean up generated files"

sync:
	uv sync

sync-gmail:
	uv sync --extra gmail

test:
	uv run pytest

test-integration:
	uv run pytest tests/integration -m integration

clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov

