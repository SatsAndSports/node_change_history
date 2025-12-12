.PHONY: help venv sync_data analyze check

help:
	@echo "make venv    - create virtualenv and install dependencies"
	@echo "make analyze - run analysis"
	@echo "make sync    - fetch latest data from Pi"
	@echo "make check   - check database integrity"

.venv:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

venv: .venv

analyze: .venv
	.venv/bin/python analyze.py

sync_data:
	# to copy the latest database from my Bitcoin node:
	bash sync_data.bash
	$(MAKE) check

check:
	sqlite3 nodes_history.sqlite "PRAGMA integrity_check;"

