.PHONY: install ingest score validate report all test verify-prod probe-start probe-summary

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

webdata:
	python3 -m hotelareascore.cli webdata --city $(CITY) --release $(RELEASE)

cost:
	python3 scripts/cost_bot.py

# Read-only checks against the LIVE deployed site (staycontext.com by
# default) -- noindex/robots.txt/sitemap-exposure/HTTPS/HSTS/canonicals/
# 404/redirects. GET requests only, no auth, no state change. Override the
# target with BASE_URL=... for a staging check.
BASE_URL ?= https://staycontext.com
verify-prod:
	python3 scripts/verify_prod.py --base-url $(BASE_URL)

# Incident probe (docs/reports/incident-2026-09-09-cloudflare-pages/):
# every 30s, 4 fixed URLs, logs status+cf-ray, no state change. Run
# probe-start in the background (it never exits on its own -- Ctrl+C or
# kill the process to stop); probe-summary regenerates probe-summary.md
# from whatever's in probe.log so far.
probe-start:
	bash scripts/prod_probe_loop.sh

probe-summary:
	python3 scripts/prod_probe_summary.py

# Phase 2 product-proof site (web/) — static Astro build, no live backend.
web-install:
	npm --prefix web install

web-build: webdata
	npm --prefix web run build

web-dev: webdata
	npm --prefix web run dev

# Full Phase 1 pipeline: Overture release -> scores -> QA -> Data Proof Report.
all: ingest score validate report

test:
	pytest -q

# Explicit manual production upload; never called by CI or by a git push.
.PHONY: deploy
deploy:
	node web/scripts/deploy-pages.mjs
