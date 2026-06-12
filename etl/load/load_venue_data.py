from __future__ import annotations

from pathlib import Path
from typing import List
import json

from clickhouse_client import get_client


def load_venue_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "venues.json"

    if not path.exists():
        raise FileNotFoundError(f"Venues JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        venues: List[dict] = json.load(f)

    return venues


def insert_venues(data: List[dict]) -> None:
    """Insert venue records into dim_venue."""

    client = get_client()

    rows = []

    for venue in data:

        venue_id = venue.get("id")

        if venue_id is None:
            continue

        rows.append((
            int(venue_id),
            str(venue.get("name") or ""),
            venue.get("address") or None,
            venue.get("city") or None,
            int(venue["capacity"]) if venue.get("capacity") else None,
            venue.get("image_url") or ""
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "dim_venue",
        rows,
        column_names=[
            "id",
            "name",
            "address",
            "city",
            "capacity",
            "image_url"
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:
    venues = load_venue_json()
    insert_venues(venues)


if __name__ == "__main__":
    main()