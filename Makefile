.PHONY: uv help install test coverage lint ruff-check format-check typecheck run check

COVERAGE_COMPARE_BRANCH ?= origin/main
uv:  ## Install uv if it's not present.
	@command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/$(cat .uv-version)/install.sh | sh

help:  ## Show this help message
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  help - Show this help message"
	@echo "  install - Install dependencies"
	@echo "  run - Run the project"
	@echo "  lint - Run all linters and type checks"
	@echo "  ruff-check - Run ruff lint checks"
	@echo "  format-check - Check formatting without modifying files"
	@echo "  typecheck - Run mypy type checks"
	@echo "  test - Run all tests"
	@echo "  coverage - Enforce >80% coverage on code changed vs main"

run:  ## Run the project
	uv run manapool

check:
	uv run manapool --check-only

install: uv ## Install dependencies
	uv sync --frozen

test:  ## Run tests
	uv run pytest tests/ --cov=manapool

coverage:  ## Enforce >80% coverage on code changed vs main
	uv run pytest tests/ --cov=manapool --cov-report=xml --cov-report=term-missing
	uv run diff-cover coverage.xml --compare-branch=$(COVERAGE_COMPARE_BRANCH) --fail-under=80

ruff-check:  ## Run ruff lint checks
	uv run ruff check

format-check:  ## Check formatting without modifying files
	uv run ruff format --check

typecheck:  ## Run mypy type checks
	uv run mypy

lint: ruff-check format-check typecheck  ## Run all linters and type checks
