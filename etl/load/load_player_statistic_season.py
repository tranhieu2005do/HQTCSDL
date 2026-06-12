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

    rows = []

    for stat in data:

        player_id = stat.get("player_id")
        team_id = stat.get("team_id")

        if player_id is None or team_id is None:
            continue

        rows.append((
            # 1
            int(player_id),

            # 2
            int(team_id),

            # 3
            stat.get("position") or "",

            # 4
            int(stat.get("appearances") or 0),

            # 5
            int(stat.get("lineups") or 0),

            # 6
            int(stat.get("minutes") or 0),

            # 7
            int(stat.get("total_shots") or 0),

            # 8
            int(stat.get("total_goals") or 0),

            # 9
            int(stat.get("total_assists") or 0),

            # 10
            int(stat.get("total_saves") or 0),

            # 11
            int(stat.get("total_passes") or 0),

            # 12
            int(stat.get("yellow_cards") or 0),

            # 13
            int(stat.get("yellowred_cards") or 0),

            # 14
            int(stat.get("red_cards") or 0)
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        table="fact_player_statistic",
        data=rows,
        column_names=[
            "player_id",
            "team_id",
            "position",
            "appearences",   # tên column ClickHouse
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
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:
    statistics = load_player_statistics_json()
    insert_player_statistics(statistics)


if __name__ == "__main__":
    main()