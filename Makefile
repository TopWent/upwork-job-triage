.PHONY: install test lint typecheck clean

VENV ?= .venv
PY   := $(VENV)/bin/python

install:
	python -m venv $(VENV)
	$(PY) -m pip install -e ".[dev]"

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check src tests

typecheck:
	$(PY) -m mypy src

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache build dist *.egg-info
