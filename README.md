# alawconnect-ChicagoCrashes-1

Fetch and explore Chicago traffic crash data from the
[City of Chicago Data Portal](https://data.cityofchicago.org/Transportation/Traffic-Crashes-Crashes/85ca-t3if)
using Python and the `requests` library.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Run the sample script to print a few crash records:

```bash
python crashes.py
```

Or import the `fetch_crashes` function in your own code:

```python
from crashes import fetch_crashes

# Fetch the first 50 crashes from 2023
records = fetch_crashes(limit=50, where="crash_year='2023'")
for record in records:
    print(record["rd_no"], record["crash_date"])
```

### `fetch_crashes` parameters

| Parameter | Type  | Default | Description                                       |
|-----------|-------|---------|---------------------------------------------------|
| `limit`   | `int` | `100`   | Maximum number of records to return               |
| `offset`  | `int` | `0`     | Number of records to skip (for pagination)        |
| `where`   | `str` | `None`  | Optional [SoQL](https://dev.socrata.com/docs/queries/) WHERE clause |