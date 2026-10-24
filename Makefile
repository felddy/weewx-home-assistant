VERSION := $(shell sed -n 's/^version = "\(.*\)"$$/\1/p' pyproject.toml)

# GitHub repository and the directory of branch/tag rulesets managed as code.
# Ruleset IDs are resolved at run time by name, so they are not hardcoded.
# See .github/rulesets/README.md for what the JSON contains (and a decoder
# for the GitHub App IDs it references).
REPO := felddy/weewx-home-assistant
RULESET_DIR := .github/rulesets

.PHONY: apply-ruleset build docs docs-check export-ruleset guard-gh guard-jq guard-version help test version

## help: print this list of targets.
help:
	@grep -E '^## ' Makefile | sed 's/^## //'

## guard-version: fail loudly if the version source is missing or empty.
guard-version:
	@test -n "$(VERSION)" || { echo "ERROR: no version found in pyproject.toml" >&2; exit 1; }

## guard-gh: fail loudly if the GitHub CLI is unavailable.
guard-gh:
	@command -v gh >/dev/null 2>&1 || { echo "ERROR: gh (GitHub CLI) is required" >&2; exit 1; }

## guard-jq: fail loudly if jq is unavailable.
guard-jq:
	@command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required" >&2; exit 1; }

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

## apply-ruleset: create or update every ruleset in RULESET_DIR (IDs resolved by name).
apply-ruleset: guard-gh guard-jq
	@test -n "$$(ls $(RULESET_DIR)/*.json 2>/dev/null)" || { echo "ERROR: no ruleset files in $(RULESET_DIR)" >&2; exit 1; }
	@set -e; \
	for f in $(RULESET_DIR)/*.json; do \
	  name=$$(jq -r '.name' "$$f"); \
	  id=$$(gh api "repos/$(REPO)/rulesets" --jq "[.[] | select(.name == \"$$name\") | .id][0] // empty"); \
	  if [ -n "$$id" ]; then \
	    echo "Updating ruleset '$$name' (id $$id) in $(REPO)"; \
	    gh api --method PUT "repos/$(REPO)/rulesets/$$id" --input "$$f" >/dev/null; \
	  else \
	    echo "Creating ruleset '$$name' in $(REPO)"; \
	    gh api --method POST "repos/$(REPO)/rulesets" --input "$$f" >/dev/null; \
	  fi; \
	done; \
	echo "Done."

## export-ruleset: overwrite each file in RULESET_DIR from its live ruleset.
export-ruleset: guard-gh guard-jq
	@test -n "$$(ls $(RULESET_DIR)/*.json 2>/dev/null)" || { echo "ERROR: no ruleset files in $(RULESET_DIR)" >&2; exit 1; }
	@set -e; \
	for f in $(RULESET_DIR)/*.json; do \
	  name=$$(jq -r '.name' "$$f"); \
	  id=$$(gh api "repos/$(REPO)/rulesets" --jq "[.[] | select(.name == \"$$name\") | .id][0] // empty"); \
	  if [ -z "$$id" ]; then echo "ERROR: no ruleset named '$$name' in $(REPO)" >&2; exit 1; fi; \
	  raw=$$(gh api "repos/$(REPO)/rulesets/$$id"); \
	  printf '%s\n' "$$raw" | jq '{name, target, enforcement, conditions, bypass_actors, rules}' > "$$f.tmp"; \
	  mv "$$f.tmp" "$$f"; \
	  echo "Wrote $$f from ruleset '$$name' (id $$id)"; \
	done
