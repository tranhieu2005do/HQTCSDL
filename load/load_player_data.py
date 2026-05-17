from __future__ import annotations

from pathlib import Path
from typing import List
import json
import re
from datetime import date
from clickhouse_client import get_client


def parse_date(value: str | None) -> date | None:

    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def parse_measurement(value: str | None) -> int | None:

    if not value:
        return None

    match = re.search(r"\d+", value)

    return int(match.group()) if match else None


def load_player_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent
    path = base_dir / "database" / "players.json"

    if not path.exists():
        raise FileNotFoundError(f"Players JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        players: List[dict] = json.load(f)

    return players


def insert_players(data: List[dict]) -> None:
    """Insert player records into dim_player."""

    client = get_client()

    rows = []

    for player in data:

        player_id = player.get("id")

        if player_id is None:
            continue

        rows.append((
            int(player_id),
            str(player.get("name") or ""),
            player.get("firstname") or None,
            player.get("lastname") or None,
            parse_date(player.get("date_birth")),
            player.get("nationality") or None,
            parse_measurement(player.get("height")),
            parse_measurement(player.get("weight")),
            player.get("image_url") or ""
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "dim_player",
        rows,
        column_names=[
            "id",
            "name",
            "first_name",
            "last_name",
            "date_birth",
            "nationality",
            "height_cm",
            "weight_kg",
            "image_url"
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:
    players = load_player_json()
    insert_players(players)


if __name__ == "__main__":
    main()