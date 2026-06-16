from __future__ import annotations

from pathlib import Path
from typing import List
import json

from clickhouse_client import get_client


def load_card_event_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "card_events.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Card events JSON not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data: List[dict] = json.load(f)

    return data


def insert_card_events(data: List[dict]) -> None:
    """Insert only new card events into fact_card_event, skipping existing ones."""

    client = get_client()

    try:
        query_result = client.query("SELECT event_id FROM fact_card_event")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for event in data:
        event_id = event.get("event_id")
        if event_id is None:
            continue

        event_id = int(event_id)

        # Skip if already exists
        if event_id in existing_ids:
            continue

        minute = int(event.get("minute") or 0)
        if minute > 255:
            print(event)
            continue

        fixture_id = int(event.get("fixture_id") or 0)
        team_id = int(event.get("team_id") or 0)
        player_id = int(event.get("player_id") or 0)
        player_name = str(event.get("player_name") or "")
        detail = str(event.get("detail") or "")

        insert_rows.append((
            event_id,
            fixture_id,
            team_id,
            player_id,
            player_name,
            minute,
            detail
        ))

    if insert_rows:
        client.insert(
            "fact_card_event",
            insert_rows,
            column_names=[
                "event_id",
                "fixture_id",
                "team_id",
                "player_id",
                "player_name",
                "minute",
                "detail"
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")



def main() -> None:

    data = load_card_event_json()
    insert_card_events(data)


if __name__ == "__main__":
    main()