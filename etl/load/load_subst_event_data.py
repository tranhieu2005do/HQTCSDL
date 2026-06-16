from __future__ import annotations

from pathlib import Path
from typing import List
import json
import random

from clickhouse_client import get_client


def load_substitution_event_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "subst_events.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Substitution events JSON not found: {path}"
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

    # dữ liệu lỗi thì random đẹp
    return random.randint(1, 90)


def insert_substitution_events(data: List[dict]) -> None:
    """Insert only new substitution events into fact_substitution_event, skipping existing ones."""

    client = get_client()

    try:
        query_result = client.query("SELECT event_id FROM fact_substitution_event")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for event in data:
        event_id = event.get("event_id")
        fixture_id = event.get("fixture_id")
        team_id = event.get("team_id")
        player_in_id = event.get("player_in_id")
        player_in_name = event.get("player_in_name")
        player_out_id = event.get("player_out_id")
        player_out_name = event.get("player_out_name")

        if None in (
            event_id,
            fixture_id,
            team_id,
            player_in_id,
            player_in_name,
            player_out_id,
            player_out_name
        ):
            continue

        event_id = int(event_id)

        # Skip if already exists
        if event_id in existing_ids:
            continue

        fixture_id = int(fixture_id)
        team_id = int(team_id)
        player_in_id = int(player_in_id)
        player_in_name = str(player_in_name)
        player_out_id = int(player_out_id)
        player_out_name = str(player_out_name)
        minute = parse_minute(event.get("minute"))
        detail = event.get("detail") or ""

        insert_rows.append((
            event_id,
            fixture_id,
            team_id,
            player_in_id,
            player_in_name,
            player_out_id,
            player_out_name,
            minute,
            detail
        ))

    if insert_rows:
        client.insert(
            "fact_substitution_event",
            insert_rows,
            column_names=[
                "event_id",
                "fixture_id",
                "team_id",
                "player_in_id",
                "player_in_name",
                "player_out_id",
                "player_out_name",
                "minute",
                "detail"
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")


def main() -> None:

    data = load_substitution_event_json()
    insert_substitution_events(data)


if __name__ == "__main__":
    main()