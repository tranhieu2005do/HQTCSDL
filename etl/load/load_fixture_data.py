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

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "fixtures.json"

    if not path.exists():
        raise FileNotFoundError(f"Fixtures JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        fixtures: List[dict] = json.load(f)

    return fixtures


def insert_fixtures(data: List[dict]) -> None:
    """Insert fixture records into fact_fixture, skipping existing ones."""

    client = get_client()

    try:
        query_result = client.query("SELECT id FROM fact_fixture")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for fixture in data:
        fixture_id = fixture.get("id")
        if fixture_id is None:
            continue

        fixture_id = int(fixture_id)
        if fixture_id in existing_ids:
            continue

        referee = fixture.get("referee") or None
        f_date = parse_date(fixture.get("date"))
        venue_id = int(fixture.get("venue_id") or 0)
        round_val = int(fixture.get("round") or 0)
        home_id = int(fixture.get("home_id") or 0)
        away_id = int(fixture.get("away_id") or 0)
        home_goals = int(fixture.get("home_goals") or 0)
        away_goals = int(fixture.get("away_goals") or 0)

        insert_rows.append((
            fixture_id,
            referee,
            f_date,
            venue_id,
            round_val,
            home_id,
            away_id,
            home_goals,
            away_goals
        ))

    if insert_rows:
        client.insert(
            "fact_fixture",
            insert_rows,
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
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")


def main() -> None:
    fixtures = load_fixture_json()
    insert_fixtures(fixtures)


if __name__ == "__main__":
    main()