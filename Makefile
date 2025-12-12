.PHONY: help venv sync_data analyze

help:
	@echo "make venv    - create virtualenv and install dependencies"
	@echo "make analyze - run analysis"
	@echo "make sync    - fetch latest data from Pi"

.venv:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

venv: .venv

analyze: .venv
	.venv/bin/python analyze.py

sync_data:
	# to copy the latest database from my Bitcoin node:
	bash sync_data.bash

