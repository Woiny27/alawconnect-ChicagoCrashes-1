"""Fetch Chicago traffic crash data from the City of Chicago Data Portal (Socrata)."""

import requests

# Chicago Traffic Crashes – Crashes dataset (Socrata resource ID)
BASE_URL = "https://data.cityofchicago.org/resource/85ca-t3if.json"


def fetch_crashes(limit: int = 100, offset: int = 0, where: str | None = None) -> list[dict]:
    """Return a list of crash records from the Chicago Data Portal.

    Args:
        limit:  Maximum number of records to return (default 100).
        offset: Number of records to skip (useful for pagination).
        where:  Optional SoQL WHERE clause, e.g. ``"crash_year='2023'"``

    Returns:
        A list of crash record dicts as returned by the API.

    Raises:
        requests.HTTPError: If the API returns a non-2xx status code.
    """
    params: dict[str, str | int] = {
        "$limit": limit,
        "$offset": offset,
    }
    if where:
        params["$where"] = where

    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    """Print a sample of crash records to stdout."""
    print("Fetching Chicago crash records …")
    records = fetch_crashes(limit=5)
    for i, record in enumerate(records, start=1):
        crash_date = record.get("crash_date", "N/A")
        crash_type = record.get("first_crash_type", "N/A")
        injuries = record.get("injuries_total", "0")
        rd_no = record.get("rd_no", "N/A")
        print(f"{i}. [{rd_no}] {crash_date}  type={crash_type}  injuries={injuries}")


if __name__ == "__main__":
    main()
