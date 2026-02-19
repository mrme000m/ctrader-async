# =============================================================================
# cTrader Async Client — Makefile
# =============================================================================
#
# Quick reference
# ---------------
#   make test                 Run all unit tests (no server required)
#   make integration          Run all integration suites (requires .env)
#   make integration-risk     Run Risk API suite only
#   make integration-history  Run History API suite only
#   make integration-market   Run Market Data suite only
#   make integration-session  Run Session & Assets suite only
#   make integration-events   Run Event Bus suite only
#   make integration-core     Run core connection/trading suite only
#   make integration-list     List all available integration suites
#   make lint                 Run ruff linter
#   make typecheck            Run mypy type checker
#   make clean                Remove __pycache__ and .pytest_cache

PYTHON      ?= python3
PYTEST      ?= $(PYTHON) -m pytest
RUNNER      := tests/run_integration_tests.py

# Pytest flags for unit tests (fast, no server)
UNIT_FLAGS  := --tb=short -q \
	--ignore=tests/test_integration.py \
	--ignore=tests/test_integration_new_features.py \
	--ignore=tests/test_integration_risk_api.py \
	--ignore=tests/test_integration_history_api.py \
	--ignore=tests/test_integration_market_data_extended.py \
	--ignore=tests/test_integration_session_assets.py \
	--ignore=tests/test_integration_events_bus.py \
	--ignore=tests/test_client_auto_enable.py

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

.PHONY: help
help:
	@echo ""
	@echo "  cTrader Async Client — Make targets"
	@echo "  ====================================="
	@echo ""
	@echo "  Unit tests (no server needed)"
	@echo "  ─────────────────────────────"
	@echo "  make test                  Run all unit tests"
	@echo "  make test-v                Run unit tests (verbose)"
	@echo "  make test-file F=tests/test_foo.py   Run single test file"
	@echo ""
	@echo "  Integration tests (requires .env with demo credentials)"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make integration           Run ALL integration suites"
	@echo "  make integration-core      Core: connection, orders, positions"
	@echo "  make integration-market    Market data: candles, ticks, streams"
	@echo "  make integration-risk      Risk API: margin, PnL, leverage"
	@echo "  make integration-history   History API: deals, transactions"
	@echo "  make integration-session   Session & assets: symbols, assets"
	@echo "  make integration-events    Event bus: all typed events"
	@echo "  make integration-new       New features: model bridge, fanout"
	@echo "  make integration-list      List all suites with descriptions"
	@echo "  make integration-fast      All suites, stop on first failure"
	@echo ""
	@echo "  Code quality"
	@echo "  ─────────────"
	@echo "  make lint                  Run ruff linter"
	@echo "  make typecheck             Run mypy"
	@echo "  make clean                 Remove cache directories"
	@echo ""

# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

.PHONY: test
test:
	$(PYTEST) tests/ $(UNIT_FLAGS)

.PHONY: test-v
test-v:
	$(PYTEST) tests/ $(UNIT_FLAGS) -v

.PHONY: test-file
test-file:
	$(PYTEST) $(F) -v --tb=short

# ---------------------------------------------------------------------------
# Integration tests — all suites
# ---------------------------------------------------------------------------

.PHONY: integration
integration:
	$(PYTHON) $(RUNNER)

.PHONY: integration-fast
integration-fast:
	$(PYTHON) $(RUNNER) --fail-fast

# ---------------------------------------------------------------------------
# Integration tests — individual suites
# ---------------------------------------------------------------------------

.PHONY: integration-core
integration-core:
	$(PYTHON) $(RUNNER) --suite core

.PHONY: integration-new
integration-new:
	$(PYTHON) $(RUNNER) --suite new_features

.PHONY: integration-market
integration-market:
	$(PYTHON) $(RUNNER) --suite market

.PHONY: integration-risk
integration-risk:
	$(PYTHON) $(RUNNER) --suite risk

.PHONY: integration-history
integration-history:
	$(PYTHON) $(RUNNER) --suite history

.PHONY: integration-session
integration-session:
	$(PYTHON) $(RUNNER) --suite session

.PHONY: integration-events
integration-events:
	$(PYTHON) $(RUNNER) --suite events

.PHONY: integration-list
integration-list:
	$(PYTHON) $(RUNNER) --list

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------

.PHONY: lint
lint:
	$(PYTHON) -m ruff check src/ tests/ || true

.PHONY: typecheck
typecheck:
	$(PYTHON) -m mypy src/ctc/ --ignore-missing-imports || true

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------

.PHONY: clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache"   -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean done."
