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

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "fixture_player_statistics.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Fixture player statistics JSON not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        data: List[dict] = json.load(f)

    return data


def insert_fixture_player_statistics(data: List[dict]) -> None:
    """Insert only new fixture player statistics, skipping existing ones."""

    client = get_client()

    try:
        query_result = client.query("SELECT id FROM fact_fixture_player_statistics")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for stat in data:
        record_id = stat.get("id")
        if record_id is None:
            continue

        record_id = int(record_id)

        # Skip if already exists
        if record_id in existing_ids:
            continue

        fixture_id = int(stat.get("fixture_id") or 0)
        team_id = int(stat.get("team_id") or 0)
        player_id = int(stat.get("player_id") or 0)
        minutes_played = int(stat.get("minutes_played") or 0)
        rating = parse_rating(stat.get("rating"))
        substitute = bool(stat.get("substitute"))
        shots = int(stat.get("shots") or 0)
        goals = int(stat.get("goals") or 0)
        assists = int(stat.get("assists") or 0)
        saves = int(stat.get("saves") or 0)
        passes_total = int(stat.get("passes_total") or 0)
        passes_accuracy = int(stat.get("passes_accuracy") or 0)
        dribbles = int(stat.get("dribbles") or 0)
        fouls_drawn = int(stat.get("fouls_drawn") or 0)
        fouls_commited = int(stat.get("fouls_commited") or 0)
        yellow_card = int(stat.get("yellow_card") or 0)
        red_card = int(stat.get("red_card") or 0)

        insert_rows.append((
            record_id,
            fixture_id,
            team_id,
            player_id,
            minutes_played,
            rating,
            substitute,
            shots,
            goals,
            assists,
            saves,
            passes_total,
            passes_accuracy,
            dribbles,
            fouls_drawn,
            fouls_commited,
            yellow_card,
            red_card
        ))

    if insert_rows:
        client.insert(
            "fact_fixture_player_statistics",
            insert_rows,
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
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")


def main() -> None:

    data = load_fixture_player_statistics_json()
    insert_fixture_player_statistics(data)


if __name__ == "__main__":
    main()