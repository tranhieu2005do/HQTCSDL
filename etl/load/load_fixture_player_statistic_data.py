from __future__ import annotations

from pathlib import Path
from typing import List
import json
from decimal import Decimal

from clickhouse_client import get_client


def parse_rating(value: str | None) -> Decimal:

    if not value:
        return Decimal("0.0")

    try:
        return Decimal(value)
    except:
        return Decimal("0.0")


def load_fixture_player_statistics_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent
    path = base_dir / "database" / "fixture_player_statistics.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Fixture player statistics JSON not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data: List[dict] = json.load(f)

    return data


def insert_fixture_player_statistics(data: List[dict]) -> None:
    """Insert fixture player statistics."""

    client = get_client()

    rows = []

    for stat in data:

        record_id = stat.get("id")

        if record_id is None:
            continue

        rows.append((
            int(record_id),

            int(stat.get("fixture_id") or 0),
            int(stat.get("team_id") or 0),
            int(stat.get("player_id") or 0),

            int(stat.get("minutes_played") or 0),

            parse_rating(stat.get("rating")),

            bool(stat.get("substitute")),

            int(stat.get("shots") or 0),
            int(stat.get("goals") or 0),
            int(stat.get("assists") or 0),
            int(stat.get("saves") or 0),

            int(stat.get("passes_total") or 0),
            int(stat.get("passes_accuracy") or 0),

            int(stat.get("dribbles") or 0),

            int(stat.get("fouls_drawn") or 0),
            int(stat.get("fouls_commited") or 0),

            int(stat.get("yellow_card") or 0),
            int(stat.get("red_card") or 0)
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "fact_fixture_player_statistics",
        rows,
        column_names=[
            "id",

            "fixture_id",
            "team_id",
            "player_id",

            "minutes_played",

            "rating",

            "substitute",

            "shots",
            "goals",
            "assists",
            "saves",

            "passes_total",
            "passes_accuracy",

            "dribbles",

            "fouls_drawn",
            "fouls_commited",

            "yellow_card",
            "red_card"
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:

    data = load_fixture_player_statistics_json()
    insert_fixture_player_statistics(data)


if __name__ == "__main__":
    main()