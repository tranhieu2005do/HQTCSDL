from __future__ import annotations

from pathlib import Path
from typing import List
import json
import re

from clickhouse_client import get_client


def parse_percent(value: str | None) -> int:

    if not value:
        return 0

    match = re.search(r"\d+", str(value))

    return int(match.group()) if match else 0


def parse_float(value: str | None) -> float:

    if not value:
        return 0.0

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def load_fixture_statistics_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "fixture_statistics.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Fixture statistics JSON not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        stats: List[dict] = json.load(f)

    return stats


def insert_fixture_statistics(data: List[dict]) -> None:
    """Insert fixture statistics into fact_fixture_statistics."""

    client = get_client()

    rows = []

    for stat in data:

        stat_id = stat.get("id")

        if stat_id is None:
            continue

        rows.append((
            int(stat_id),

            int(stat.get("fixture_id") or 0),
            int(stat.get("team_id") or 0),

            int(stat.get("Shots on Goal") or 0),
            int(stat.get("Shots off Goal") or 0),
            int(stat.get("Total Shots") or 0),
            int(stat.get("Blocked Shots") or 0),

            int(stat.get("Shots insidebox") or 0),
            int(stat.get("Shots outsidebox") or 0),

            int(stat.get("Fouls") or 0),
            int(stat.get("Corner Kicks") or 0),
            int(stat.get("Offsides") or 0),

            parse_percent(
                stat.get("Ball Possession")
            ),

            int(stat.get("Yellow Cards") or 0),
            int(stat.get("Red Cards") or 0),

            int(stat.get("Goalkeeper Saves") or 0),

            int(stat.get("Total passes") or 0),
            int(stat.get("Passes accurate") or 0),

            parse_percent(
                stat.get("Passes %")
            ),

            parse_float(
                stat.get("expected_goals")
            )
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "fact_fixture_statistics",
        rows,
        column_names=[
            "id",

            "fixture_id",
            "team_id",

            "shots_on_goal",
            "shots_off_goal",
            "total_shots",
            "blocked_shots",

            "shots_inside_box",
            "shots_outside_box",

            "fouls",
            "corner_kicks",
            "offsides",

            "possession",

            "yellow_cards",
            "red_cards",

            "goalkeeper_saves",

            "total_passes",
            "accurate_passes",

            "pass_accuracy",

            "expected_goals"
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:

    data = load_fixture_statistics_json()
    insert_fixture_statistics(data)


if __name__ == "__main__":
    main()