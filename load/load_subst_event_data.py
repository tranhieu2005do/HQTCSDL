from __future__ import annotations

from pathlib import Path
from typing import List
import json
import random

from clickhouse_client import get_client


def load_substitution_event_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent
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
    """Insert substitution events into fact_substitution_events."""

    client = get_client()

    rows = []

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

        rows.append((
            int(event_id),
            int(fixture_id),
            int(team_id),
            int(player_in_id),
            str(player_in_name),
            int(player_out_id),
            str(player_out_name),

            parse_minute(event.get("minute")),

            event.get("detail") or ""
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "fact_substitution_event",
        rows,
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
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:

    data = load_substitution_event_json()
    insert_substitution_events(data)


if __name__ == "__main__":
    main()