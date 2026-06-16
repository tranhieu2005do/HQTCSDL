from __future__ import annotations

from pathlib import Path
from typing import List
import json

from clickhouse_client import get_client


def load_player_statistics_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "players_statistic_season.json"

    if not path.exists():
        raise FileNotFoundError(
            f"Player statistics JSON not found: {path}"
        )

    with path.open("r", encoding="utf-8") as f:
        statistics: List[dict] = json.load(f)

    return statistics


def insert_player_statistics(data: List[dict]) -> None:
    client = get_client()

    try:
        query_result = client.query("SELECT team_id, player_id FROM fact_player_statistic")
        existing_keys = {(row[0], row[1]) for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing keys, assuming empty table: {e}")
        existing_keys = set()

    insert_rows = []

    for stat in data:
        player_id = stat.get("player_id")
        team_id = stat.get("team_id")

        if player_id is None or team_id is None:
            continue

        player_id = int(player_id)
        team_id = int(team_id)

        key = (team_id, player_id)

        # Skip if already exists
        if key in existing_keys:
            continue

        position = stat.get("position") or ""
        appearences = int(stat.get("appearances") or 0)
        lineups = int(stat.get("lineups") or 0)
        minutes = int(stat.get("minutes") or 0)
        total_shots = int(stat.get("total_shots") or 0)
        total_goals = int(stat.get("total_goals") or 0)
        total_assists = int(stat.get("total_assists") or 0)
        total_saves = int(stat.get("total_saves") or 0)
        total_passes = int(stat.get("total_passes") or 0)
        yellow_cards = int(stat.get("yellow_cards") or 0)
        yellowred_cards = int(stat.get("yellowred_cards") or 0)
        red_cards = int(stat.get("red_cards") or 0)

        insert_rows.append((
            player_id,
            team_id,
            position,
            appearences,
            lineups,
            minutes,
            total_shots,
            total_goals,
            total_assists,
            total_saves,
            total_passes,
            yellow_cards,
            yellowred_cards,
            red_cards
        ))

    if insert_rows:
        client.insert(
            table="fact_player_statistic",
            data=insert_rows,
            column_names=[
                "player_id",
                "team_id",
                "position",
                "appearences",
                "lineups",
                "minutes",
                "total_shots",
                "total_goals",
                "total_assists",
                "total_saves",
                "total_passes",
                "yellow_cards",
                "yellowred_cards",
                "red_cards"
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")


def main() -> None:
    statistics = load_player_statistics_json()
    insert_player_statistics(statistics)


if __name__ == "__main__":
    main()