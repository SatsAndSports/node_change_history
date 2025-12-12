#!/usr/bin/env python3
"""Show top user agents before and after BASE_TIME."""

import duckdb
import os

base_time = os.environ['BASE_TIME']

conn = duckdb.connect()
conn.execute('INSTALL sqlite; LOAD sqlite;')


def top_agents(op, label):
    df = conn.execute(f'''
        WITH latest AS (
            SELECT address, port, user_agent,
                   ROW_NUMBER() OVER (PARTITION BY address, port ORDER BY timestamp DESC) as rn
            FROM sqlite_scan("nodes_history.sqlite", "nodes")
            WHERE timestamp {op} {base_time} AND user_agent IS NOT NULL
        )
        SELECT user_agent, COUNT(*) as count
        FROM latest WHERE rn = 1
        GROUP BY user_agent
        ORDER BY count DESC
        LIMIT 20
    ''').fetchdf()
    print(f'{label}')
    print('=' * 60)
    print(df.to_string(index=False))
    print()


top_agents('<', 'BEFORE')
top_agents('>=', 'AFTER')
