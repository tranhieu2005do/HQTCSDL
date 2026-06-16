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


def load_head_to_head_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "head_to_head.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Head to head JSON not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data: List[dict] = json.load(f)

    return data


def insert_head_to_head(data: List[dict]) -> None:

    client = get_client()

    try:
        query_result = client.query("SELECT id FROM head_to_head")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for match in data:
        match_id = match.get("id")
        if match_id is None:
            continue

        match_id = int(match_id)

        # Skip if already exists
        if match_id in existing_ids:
            continue

        home_team_id = int(match.get("home_team_id") or 0)
        home_team_name = match.get("home_team_name") or None
        away_team_id = int(match.get("away_team_id") or 0)
        away_team_name = match.get("away_team_name") or None
        league_name = match.get("league_name") or None
        home_goals = int(match.get("home_goals") or 0)
        away_goals = int(match.get("away_goals") or 0)
        match_date = parse_date(match.get("date"))

        insert_rows.append((
            match_id,
            home_team_id,
            home_team_name,
            away_team_id,
            away_team_name,
            league_name,
            home_goals,
            away_goals,
            match_date
        ))

    if insert_rows:
        client.insert(
            "head_to_head",
            insert_rows,
            column_names=[
                "id",
                "home_team_id",
                "home_team_name",
                "away_team_id",
                "away_team_name",
                "league_name",
                "home_goals",
                "away_goals",
                "match_date"
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")


def main() -> None:

    data = load_head_to_head_json()

    insert_head_to_head(data)


if __name__ == "__main__":
    main()