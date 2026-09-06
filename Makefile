.PHONY: install ingest score validate report all test

CITY ?= all
RELEASE ?= latest

install:
	pip install -e ".[dev]"

ingest:
	python3 -m hotelareascore.cli ingest --city $(CITY) --release $(RELEASE)

score:
	python3 -m hotelareascore.cli score --city $(CITY) --release $(RELEASE)

validate:
	python3 -m hotelareascore.cli validate --city $(CITY) --release $(RELEASE)

report:
	python3 -m hotelareascore.cli report --city $(CITY) --release $(RELEASE)

# Full Phase 1 pipeline: Overture release -> scores -> QA -> Data Proof Report.
all: ingest score validate report

test:
	pytest -q
