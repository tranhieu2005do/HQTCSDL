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
    """Insert only new fixture statistics into fact_fixture_statistics, skipping existing ones."""

    client = get_client()

    try:
        query_result = client.query("SELECT id FROM fact_fixture_statistics")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for stat in data:
        stat_id = stat.get("id")
        if stat_id is None:
            continue

        stat_id = int(stat_id)

        # Skip if already exists
        if stat_id in existing_ids:
            continue

        fixture_id = int(stat.get("fixture_id") or 0)
        team_id = int(stat.get("team_id") or 0)
        shots_on_goal = int(stat.get("Shots on Goal") or 0)
        shots_off_goal = int(stat.get("Shots off Goal") or 0)
        total_shots = int(stat.get("Total Shots") or 0)
        blocked_shots = int(stat.get("Blocked Shots") or 0)
        shots_inside_box = int(stat.get("Shots insidebox") or 0)
        shots_outside_box = int(stat.get("Shots outsidebox") or 0)
        fouls = int(stat.get("Fouls") or 0)
        corner_kicks = int(stat.get("Corner Kicks") or 0)
        offsides = int(stat.get("Offsides") or 0)
        possession = parse_percent(stat.get("Ball Possession"))
        yellow_cards = int(stat.get("Yellow Cards") or 0)
        red_cards = int(stat.get("Red Cards") or 0)
        goalkeeper_saves = int(stat.get("Goalkeeper Saves") or 0)
        total_passes = int(stat.get("Total passes") or 0)
        accurate_passes = int(stat.get("Passes accurate") or 0)
        pass_accuracy = parse_percent(stat.get("Passes %"))
        expected_goals = parse_float(stat.get("expected_goals"))

        insert_rows.append((
            stat_id,
            fixture_id,
            team_id,
            shots_on_goal,
            shots_off_goal,
            total_shots,
            blocked_shots,
            shots_inside_box,
            shots_outside_box,
            fouls,
            corner_kicks,
            offsides,
            possession,
            yellow_cards,
            red_cards,
            goalkeeper_saves,
            total_passes,
            accurate_passes,
            pass_accuracy,
            expected_goals
        ))

    if insert_rows:
        client.insert(
            "fact_fixture_statistics",
            insert_rows,
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
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")


def main() -> None:

    data = load_fixture_statistics_json()
    insert_fixture_statistics(data)


if __name__ == "__main__":
    main()