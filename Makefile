export BASE_TIME := 1765277892

.PHONY: help venv sync_data analyze check top_agents

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

top_agents: .venv
	.venv/bin/python -c "\
import duckdb, os; \
base_time = os.environ['BASE_TIME']; \
conn = duckdb.connect(); \
conn.execute('INSTALL sqlite; LOAD sqlite;'); \
df = conn.execute(f''' \
    WITH latest AS ( \
        SELECT address, port, user_agent, \
               ROW_NUMBER() OVER (PARTITION BY address, port ORDER BY timestamp DESC) as rn \
        FROM sqlite_scan(\"nodes_history.sqlite\", \"nodes\") \
        WHERE timestamp < {base_time} AND user_agent IS NOT NULL \
    ) \
    SELECT user_agent, COUNT(*) as count \
    FROM latest WHERE rn = 1 \
    GROUP BY user_agent \
    ORDER BY count DESC \
    LIMIT 20 \
''').fetchdf(); \
print(df.to_string(index=False))"

