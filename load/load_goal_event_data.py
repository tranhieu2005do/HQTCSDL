from __future__ import annotations

from pathlib import Path
from typing import List
import json
import random

from clickhouse_client import get_client


def load_goal_event_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent
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
    """Insert goal events into fact_goal_events."""

    client = get_client()

    rows = []

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

        rows.append((
            int(event_id),
            int(fixture_id),
            int(team_id),

            int(player_score_id),
            event.get("player_score_name") or "",

            (
                int(event["player_assist_id"])
                if event.get("player_assist_id") is not None
                else None
            ),

            event.get("player_assist_name"),

            parse_minute(event.get("minute")),

            event.get("detail") or ""
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "fact_goal_events",
        rows,
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
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:

    data = load_goal_event_json()
    insert_goal_events(data)


if __name__ == "__main__":
    main()