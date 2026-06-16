from __future__ import annotations

from pathlib import Path
from typing import List
import json

from clickhouse_client import get_client


def load_lineup_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "lineups.json"

    if not path.exists():
        raise FileNotFoundError(f"Lineups JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        lineups: List[dict] = json.load(f)

    return lineups


def insert_lineups(data: List[dict]) -> None:
    """Insert only new lineup records into fact_lineups, skipping existing ones."""

    client = get_client()

    try:
        query_result = client.query("SELECT id FROM fact_lineups")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for lineup in data:
        lineup_id = lineup.get("id")
        if lineup_id is None:
            continue

        lineup_id = int(lineup_id)

        # Skip if already exists
        if lineup_id in existing_ids:
            continue

        fixture_id = int(lineup.get("fixture_id") or 0)
        team_id = int(lineup.get("team_id") or 0)
        coach_id = int(lineup.get("coach_id") or 0)
        formation = lineup.get("formation") or "Unknown"

        insert_rows.append((
            lineup_id,
            fixture_id,
            team_id,
            coach_id,
            formation
        ))

    if insert_rows:
        client.insert(
            "fact_lineups",
            insert_rows,
            column_names=[
                "id",
                "fixture_id",
                "team_id",
                "coach_id",
                "formation"
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")


def main() -> None:

    lineups = load_lineup_json()
    insert_lineups(lineups)


if __name__ == "__main__":
    main()