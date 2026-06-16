from __future__ import annotations

from pathlib import Path
from typing import List
import json
import random

from clickhouse_client import get_client


def load_goal_event_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "goal_events.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Goal events JSON not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data: List[dict] = json.load(f)

    return data


def parse_minute(value) -> int:

    try:
        minute = int(value)

        if 1 <= minute <= 100:
            return minute

    except:
        pass

    return random.randint(1, 90)


def insert_goal_events(data: List[dict]) -> None:
    """Insert only new goal events into fact_goal_events, skipping existing ones."""

    client = get_client()

    try:
        query_result = client.query("SELECT event_id FROM fact_goal_events")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for event in data:
        event_id = event.get("event_id")
        fixture_id = event.get("fixture_id")
        team_id = event.get("team_id")
        player_score_id = event.get("player_score_id")

        if None in (
            event_id,
            fixture_id,
            team_id,
            player_score_id
        ):
            continue

        event_id = int(event_id)

        # Skip if already exists
        if event_id in existing_ids:
            continue

        fixture_id = int(fixture_id)
        team_id = int(team_id)
        player_score_id = int(player_score_id)
        player_score_name = event.get("player_score_name") or ""
        player_assist_id = (
            int(event["player_assist_id"])
            if event.get("player_assist_id") is not None
            else None
        )
        player_assist_name = event.get("player_assist_name")
        minute = parse_minute(event.get("minute"))
        detail = event.get("detail") or ""

        insert_rows.append((
            event_id,
            fixture_id,
            team_id,
            player_score_id,
            player_score_name,
            player_assist_id,
            player_assist_name,
            minute,
            detail
        ))

    if insert_rows:
        client.insert(
            "fact_goal_events",
            insert_rows,
            column_names=[
                "event_id",
                "fixture_id",
                "team_id",
                "player_score_id",
                "player_score_name",
                "player_assist_id",
                "player_assist_name",
                "minute",
                "detail"
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")


def main() -> None:

    data = load_goal_event_json()
    insert_goal_events(data)


if __name__ == "__main__":
    main()