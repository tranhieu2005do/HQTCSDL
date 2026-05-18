from __future__ import annotations

from pathlib import Path
from typing import List
import json

from clickhouse_client import get_client


def load_lineup_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent
    path = base_dir / "database" / "lineups.json"

    if not path.exists():
        raise FileNotFoundError(f"Lineups JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        lineups: List[dict] = json.load(f)

    return lineups


def insert_lineups(data: List[dict]) -> None:
    """Insert lineup records into fact_lineups."""

    client = get_client()

    rows = []

    for lineup in data:

        lineup_id = lineup.get("id")

        if lineup_id is None:
            continue

        rows.append((
            int(lineup_id),

            int(lineup.get("fixture_id") or 0),
            int(lineup.get("team_id") or 0),

            int(lineup.get("coach_id") or 0),

            lineup.get("formation") or "Unknown"
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "fact_lineups",
        rows,
        column_names=[
            "id",

            "fixture_id",
            "team_id",

            "coach_id",

            "formation"
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:

    lineups = load_lineup_json()
    insert_lineups(lineups)


if __name__ == "__main__":
    main()