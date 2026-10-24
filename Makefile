VERSION := $(shell sed -n 's/^version = "\(.*\)"$$/\1/p' pyproject.toml)

.PHONY: guard-version build docs docs-check help test version

## help: print this list of targets.
help:
	@grep -E '^## ' Makefile | sed 's/^## //'

## guard-version: fail loudly if the version source is missing or empty.
guard-version:
	@test -n "$(VERSION)" || { echo "ERROR: no version found in pyproject.toml" >&2; exit 1; }

## version: print the project version from pyproject.toml.
version: guard-version
	@echo "$(VERSION)"

## docs: render the README and every other document from its template.
docs: guard-version
	python3 tools/render_docs.py --all

## docs-check: verify every rendered document is in sync with its template.
docs-check: guard-version
	python3 tools/render_docs.py --check

## test: run the test suite.
test:
	pytest

## build: build the sdist and wheel.
build:
	python3 -m build
