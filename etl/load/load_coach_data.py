from __future__ import annotations

from pathlib import Path
from typing import List
import json

from clickhouse_client import get_client


def load_coach_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "coaches.json"

    if not path.exists():
        raise FileNotFoundError(f"Coaches JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        coaches: List[dict] = json.load(f)

    return coaches


def insert_coaches(data: List[dict]) -> None:
    """Insert coach records into dim_coaches, skipping existing ones."""

    client = get_client()

    try:
        query_result = client.query("SELECT id FROM dim_coaches")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for coach in data:
        coach_id = int(coach.get("id") or 0)
        if coach_id == 0:
            continue

        if coach_id in existing_ids:
            continue

        name = coach.get("name") or "Unknown Coach"
        photo_url = coach.get("photo") or ""

        insert_rows.append((
            coach_id,
            name,
            photo_url
        ))

    if insert_rows:
        client.insert(
            "dim_coaches",
            insert_rows,
            column_names=[
                "id",
                "name",
                "photo_url"
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")


def main() -> None:
    coaches = load_coach_json()
    insert_coaches(coaches)


if __name__ == "__main__":
    main()