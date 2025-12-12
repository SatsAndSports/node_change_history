#!/usr/bin/env python3
"""Analyze user agent migrations before/after BASE_TIME."""

import duckdb
import matplotlib.pyplot as plt
import numpy as np
import os
import plotly.graph_objects as go

base_time = os.environ['BASE_TIME']

CATEGORIZE_SQL = '''
    CASE
        WHEN ua LIKE '%Knots%UASF-BIP110%' THEN 'BIP-110'
        WHEN ua LIKE '%Knots%' THEN 'Knots'
        WHEN ua LIKE '/Satoshi:30.%' THEN 'Core30'
        WHEN ua LIKE '/Satoshi:29.%' OR ua LIKE '/Satoshi:28.%' THEN 'Core28-29'
        WHEN ua LIKE '/Satoshi:%' THEN 'OlderCore'
        ELSE 'Other'
    END
'''


def main():
    conn = duckdb.connect()
    conn.execute('INSTALL sqlite; LOAD sqlite;')

    df = conn.execute(f'''
        WITH before AS (
            SELECT address, port, user_agent as ua,
                   ROW_NUMBER() OVER (PARTITION BY address, port ORDER BY timestamp DESC) as rn
            FROM sqlite_scan("nodes_history.sqlite", "nodes")
            WHERE timestamp < {base_time} AND user_agent IS NOT NULL
        ),
        after AS (
            SELECT address, port, user_agent as ua,
                   ROW_NUMBER() OVER (PARTITION BY address, port ORDER BY timestamp DESC) as rn
            FROM sqlite_scan("nodes_history.sqlite", "nodes")
            WHERE timestamp >= {base_time} AND user_agent IS NOT NULL
        ),
        before_latest AS (
            SELECT address, port, {CATEGORIZE_SQL} as cat FROM before WHERE rn = 1
        ),
        after_latest AS (
            SELECT address, port, {CATEGORIZE_SQL} as cat FROM after WHERE rn = 1
        )

        SELECT COALESCE(b.cat, 'New') as before_cat, COALESCE(a.cat, 'Gone') as after_cat
        FROM before_latest b
        FULL OUTER JOIN after_latest a ON b.address = a.address AND b.port = a.port
    ''').fetchdf()

    # Build transition matrix
    categories = ['Core30', 'Core28-29', 'OlderCore', 'Knots', 'BIP-110', 'Other', 'New', 'Gone']
    before_cats = [c for c in categories if c not in ('Gone', 'BIP-110')]
    after_cats = [c for c in categories if c != 'New']
    matrix = np.zeros((len(before_cats), len(after_cats)), dtype=int)

    for _, row in df.iterrows():
        before_idx = before_cats.index(row['before_cat'])
        after_idx = after_cats.index(row['after_cat'])
        matrix[before_idx, after_idx] += 1

    # Print transition table
    BOLD = "\033[1m"
    RESET = "\033[0m"
    col_width = max(len(c) for c in categories) + 2
    print("Transition matrix (rows=before, cols=after)")
    print("=" * (col_width + col_width * len(after_cats)))
    header_parts = ["".ljust(col_width)]
    for c in after_cats:
        if c == 'BIP-110':
            header_parts.append(f"{BOLD}{c.rjust(col_width)}{RESET}")
        else:
            header_parts.append(c.rjust(col_width))
    print("".join(header_parts))
    for i, cat in enumerate(before_cats):
        row_parts = [cat.ljust(col_width)]
        for j, after in enumerate(after_cats):
            val = matrix[i, j]
            if val == 0:
                cell = "·".rjust(col_width)
            elif after == 'BIP-110':
                cell = f"{BOLD}{str(val).rjust(col_width)}{RESET}"
            else:
                cell = str(val).rjust(col_width)
            row_parts.append(cell)
        print("".join(row_parts))
    print()

    # Plot heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(matrix, cmap='Oranges')

    ax.set_xticks(range(len(after_cats)))
    ax.set_yticks(range(len(before_cats)))
    ax.set_xticklabels(after_cats)
    ax.set_yticklabels(before_cats)
    ax.set_xlabel('After')
    ax.set_ylabel('Before')
    ax.set_title('Node User Agent Migrations')

    # Add counts as text
    for i in range(len(before_cats)):
        for j in range(len(after_cats)):
            val = matrix[i, j]
            if val > 0:
                color = 'white' if val > matrix.max() * 0.6 else 'black'
                ax.text(j, i, str(val), ha='center', va='center', color=color, fontsize=10)

    plt.colorbar(im, ax=ax, label='Count')
    plt.tight_layout()
    plt.savefig('migrations.png', dpi=150, facecolor='white')
    print("Saved: migrations.png")
    plt.close()

    # Sankey diagram
    # Nodes: before categories, after categories (excluding Gone)
    after_cats_no_gone = [c for c in after_cats if c != 'Gone']

    node_labels = ([c for c in before_cats] +
                   [c for c in after_cats_no_gone])

    n_before = len(before_cats)

    # Build links from matrix (skip Gone)
    sources = []
    targets = []
    values = []
    colors = []
    for i, before in enumerate(before_cats):
        for j, after in enumerate(after_cats):
            if matrix[i, j] > 0 and after != 'Gone':
                sources.append(i)
                targets.append(n_before + after_cats_no_gone.index(after))
                # Fade unchanged flows, highlight migrations
                if before == after:
                    colors.append("rgba(200, 200, 200, 0.15)")  # very faint
                else:
                    colors.append("rgba(247, 147, 26, 0.6)")  # orange
                values.append(int(matrix[i, j]))

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=node_labels,
            color="#f7931a"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=colors
        )
    )])

    fig.update_layout(
        title_text="Node User Agent Migrations",
        font_size=12,
        width=1000,
        height=700
    )

    fig.write_image("migrations_sankey.png", scale=2)
    print("Saved: migrations_sankey.png")


if __name__ == '__main__':
    main()
