from __future__ import annotations

from pathlib import Path
from typing import List
import json
from datetime import date

from clickhouse_client import get_client


def parse_date(value: str | None) -> date | None:

    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def load_fixture_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent
    path = base_dir / "database" / "fixtures.json"

    if not path.exists():
        raise FileNotFoundError(f"Fixtures JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        fixtures: List[dict] = json.load(f)

    return fixtures


def insert_fixtures(data: List[dict]) -> None:
    """Insert fixture records into fact_fixtures."""

    client = get_client()

    rows = []

    for fixture in data:

        fixture_id = fixture.get("id")

        if fixture_id is None:
            continue

        rows.append((
            int(fixture_id),

            fixture.get("referee") or None,

            parse_date(fixture.get("date")),

            int(fixture.get("venue_id") or 0),

            int(fixture.get("round") or 0),

            int(fixture.get("home_id") or 0),
            int(fixture.get("away_id") or 0),

            int(fixture.get("home_goals") or 0),
            int(fixture.get("away_goals") or 0)
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "fact_fixture",
        rows,
        column_names=[
            "id",

            "referee",
            "date",

            "venue_id",
            "round",

            "home_id",
            "away_id",

            "home_goals",
            "away_goals"
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:
    fixtures = load_fixture_json()
    insert_fixtures(fixtures)


if __name__ == "__main__":
    main()