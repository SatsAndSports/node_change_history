#!/usr/bin/env python3
"""Analyze Bitcoin node history data."""

import duckdb
import matplotlib.pyplot as plt
from pathlib import Path

DB_PATH = Path(__file__).parent / "nodes_history.sqlite"


def get_connection():
    """Connect to SQLite database via DuckDB."""
    conn = duckdb.connect()
    conn.execute("INSTALL sqlite; LOAD sqlite;")
    return conn


def top_user_agents(conn, limit=20):
    """Get most common user agents."""
    return conn.execute(f"""
        SELECT user_agent, COUNT(*) as count
        FROM sqlite_scan('{DB_PATH}', 'nodes')
        WHERE success = 1 AND user_agent IS NOT NULL
        GROUP BY user_agent
        ORDER BY count DESC
        LIMIT {limit}
    """).fetchdf()


def plot_user_agents(df, output_path="user_agents.png"):
    """Create horizontal bar chart of user agents."""
    fig, ax = plt.subplots(figsize=(12, 8))

    # Reverse for horizontal bar chart (top at top)
    df_plot = df.iloc[::-1]

    bars = ax.barh(df_plot["user_agent"], df_plot["count"], color="#f7931a")
    ax.set_xlabel("Count")
    ax.set_title("Most Common Bitcoin Node User Agents")
    ax.bar_label(bars, padding=3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor="white")
    print(f"Saved: {output_path}")
    plt.close()


def main():
    conn = get_connection()

    # User agent analysis
    print("Top User Agents")
    print("=" * 60)
    df = top_user_agents(conn)
    print(df.to_string(index=False))
    print()

    plot_user_agents(df)


if __name__ == "__main__":
    main()
