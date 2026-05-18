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

    base_dir = Path(__file__).resolve().parent.parent
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

    rows = []

    for match in data:

        match_id = match.get("id")

        if match_id is None:
            continue

        rows.append((
            int(match_id),

            int(match.get("home_team_id") or 0),
            match.get("home_team_name") or None,

            int(match.get("away_team_id") or 0),
            match.get("away_team_name") or None,

            match.get("league_name") or None,

            int(match.get("home_goals") or 0),
            int(match.get("away_goals") or 0),

            parse_date(match.get("date"))
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "head_to_head",
        rows,
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
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:

    data = load_head_to_head_json()

    insert_head_to_head(data)


if __name__ == "__main__":
    main()