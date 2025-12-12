# Bitcoin Node History

Tracking Bitcoin node user agents over time, with analysis of version migrations.

## Node Migration Data

Transition matrix showing how nodes changed between categories before/after the release of BIP-110 signaling (Dec 9, 2025):

```
                Core30  Core28-29  OlderCore      Knots    BIP-110      Other       Gone
Core30            1767          3          ·          ·          ·          ·         40
Core28-29           22       4962          ·          3          ·          ·        152
OlderCore            2         10       3399          ·          ·          ·         84
Knots                ·          ·          1       3863          8          ·        112
Other                ·          ·          ·          ·          ·          1          ·
New                342        793        420        562          3          ·          ·
```

- Rows = category before, Columns = category after
- **8** Knots nodes upgraded to BIP-110 signaling
- **3** new BIP-110 nodes appeared
- **New** = nodes discovered after the cutoff date
- **Gone** = nodes not seen after the cutoff date

## Setup

```bash
make venv      # create virtualenv and install dependencies
```

## Usage

```bash
make analyze      # basic user agent analysis
make top_agents   # top agents before/after comparison
make migrations   # migration matrix and visualizations
make check        # verify database integrity
make sync_data    # fetch latest data from Pi
```

## Data Collection

Data is collected by `nodes_history.py` running on a Raspberry Pi, which probes Bitcoin nodes via Tor and records their user agents and capabilities.
