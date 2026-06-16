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
    """Insert venue records into dim_venue, skipping existing ones."""

    client = get_client()

    try:
        query_result = client.query("SELECT id FROM dim_venue")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for venue in data:
        venue_id = venue.get("id")
        if venue_id is None:
            continue

        venue_id = int(venue_id)
        if venue_id in existing_ids:
            continue

        name = str(venue.get("name") or "")
        address = venue.get("address") or None
        city = venue.get("city") or None
        capacity = int(venue["capacity"]) if venue.get("capacity") else None
        image_url = venue.get("image_url") or ""

        insert_rows.append((
            venue_id,
            name,
            address,
            city,
            capacity,
            image_url
        ))

    if insert_rows:
        client.insert(
            "dim_venue",
            insert_rows,
            column_names=[
                "id",
                "name",
                "address",
                "city",
                "capacity",
                "image_url"
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")


def main() -> None:
    venues = load_venue_json()
    insert_venues(venues)


if __name__ == "__main__":
    main()