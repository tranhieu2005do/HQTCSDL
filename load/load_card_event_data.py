from __future__ import annotations

from pathlib import Path
from typing import List
import json

from clickhouse_client import get_client


def load_card_event_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent
    path = base_dir / "database" / "card_events.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Card events JSON not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data: List[dict] = json.load(f)

    return data


def insert_card_events(data: List[dict]) -> None:
    """Insert card events into fact_card_events."""

    client = get_client()

    rows = []

    for event in data:

        event_id = event.get("event_id")
        minute = int(event.get("minute") or 0)

        if minute > 255:
            print(event)
            continue

        if event_id is None:
            continue

        rows.append((
            int(event_id),

            int(event.get("fixture_id") or 0),
            int(event.get("team_id") or 0),
            int(event.get("player_id") or 0),
            str(event.get("player_name") or ""),
            int(event.get("minute") or 0),

            str(event.get("detail") or "")
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "fact_card_event",
        rows,
        column_names=[
            "event_id",

            "fixture_id",
            "team_id",
            "player_id",
            "player_name",

            "minute",

            "detail"
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:

    data = load_card_event_json()
    insert_card_events(data)


if __name__ == "__main__":
    main()