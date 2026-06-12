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
    """Insert coach records into dim_coaches."""

    client = get_client()

    rows = []

    for coach in data:

        coach_id = coach.get("id") or 0

        rows.append((
            int(coach_id),
            coach.get("name") or "Unknown Coach",
            coach.get("photo") or ""
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "dim_coaches",
        rows,
        column_names=[
            "id",
            "name",
            "photo_url"
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:
    coaches = load_coach_json()
    insert_coaches(coaches)


if __name__ == "__main__":
    main()