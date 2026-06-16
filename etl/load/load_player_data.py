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

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "players.json"

    if not path.exists():
        raise FileNotFoundError(f"Players JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        players: List[dict] = json.load(f)

    return players


# def insert_players(data: List[dict]) -> None:
#     """Insert new player records and update existing ones in dim_players."""

#     client = get_client()

#     # Query all existing IDs from dim_players to determine what to insert vs update
#     try:
#         query_result = client.query("SELECT id FROM dim_players")
#         existing_ids = {row[0] for row in query_result.result_rows}
#     except Exception as e:
#         print(f"Error querying existing IDs, assuming empty table: {e}")
#         existing_ids = set()

#     insert_rows = []
#     update_count = 0

#     for player in data:
#         player_id = player.get("id")
#         if player_id is None:
#             continue

#         player_id = int(player_id)
#         name = str(player.get("name") or "")
#         first_name = player.get("firstname") or None
#         last_name = player.get("lastname") or None
#         date_birth = parse_date(player.get("date_birth"))
#         nationality = player.get("nationality") or None
#         height_cm = parse_measurement(player.get("height"))
#         weight_kg = parse_measurement(player.get("weight"))
#         image_url = player.get("image_url") or ""

#         if player_id in existing_ids:
#             # Perform update (mutation) for existing players
#             update_query = """
#                 ALTER TABLE dim_players UPDATE
#                     name = %(name)s,
#                     first_name = %(first_name)s,
#                     last_name = %(last_name)s,
#                     date_birth = %(date_birth)s,
#                     nationality = %(nationality)s,
#                     height_cm = %(height_cm)s,
#                     weight_kg = %(weight_kg)s,
#                     image_url = %(image_url)s
#                 WHERE id = %(id)s
#             """
#             client.command(
#                 update_query,
#                 parameters={
#                     "id": player_id,
#                     "name": name,
#                     "first_name": first_name,
#                     "last_name": last_name,
#                     "date_birth": date_birth,
#                     "nationality": nationality,
#                     "height_cm": height_cm,
#                     "weight_kg": weight_kg,
#                     "image_url": image_url,
#                 }
#             )
#             update_count += 1
#         else:
#             # Add to insert list
#             insert_rows.append((
#                 player_id,
#                 name,
#                 first_name,
#                 last_name,
#                 date_birth,
#                 nationality,
#                 height_cm,
#                 weight_kg,
#                 image_url
#             ))

#     if insert_rows:
#         client.insert(
#             "dim_players",
#             insert_rows,
#             column_names=[
#                 "id",
#                 "name",
#                 "first_name",
#                 "last_name",
#                 "date_birth",
#                 "nationality",
#                 "height_cm",
#                 "weight_kg",
#                 "image_url"
#             ]
#         )
#         print(f"Inserted {len(insert_rows)} new rows")
#     else:
#         print("No new rows to insert")

#     if update_count > 0:
#         print(f"Updated {update_count} existing rows via ALTER TABLE UPDATE")

def insert_players(data: List[dict]) -> None:
    """Insert only new player records into dim_players, skipping existing ones."""

    client = get_client()

    # Lấy danh sách ID đã tồn tại
    try:
        query_result = client.query("SELECT id FROM dim_players")
        existing_ids = {row[0] for row in query_result.result_rows}
    except Exception as e:
        print(f"Error querying existing IDs, assuming empty table: {e}")
        existing_ids = set()

    insert_rows = []

    for player in data:
        player_id = player.get("id")
        if player_id is None:
            continue

        player_id = int(player_id)

        # Nếu ID đã tồn tại trong ClickHouse thì bỏ qua hoàn toàn
        if player_id in existing_ids:
            continue

        name = str(player.get("name") or "")
        first_name = player.get("firstname") or None
        last_name = player.get("lastname") or None
        date_birth = parse_date(player.get("date_birth"))
        nationality = player.get("nationality") or None
        height_cm = parse_measurement(player.get("height"))
        weight_kg = parse_measurement(player.get("weight"))
        image_url = player.get("image_url") or ""

        # Thêm vào danh sách chờ insert
        insert_rows.append((
            player_id,
            name,
            first_name,
            last_name,
            date_birth,
            nationality,
            height_cm,
            weight_kg,
            image_url
        ))

    if insert_rows:
        print("Inserting rows:", insert_rows)
        client.insert(
            "dim_players",
            insert_rows,
            column_names=[
                "id",
                "name",
                "first_name",
                "last_name",
                "date_birth",
                "nationality",
                "height_cm",
                "weight_kg",
                "image_url",
            ],
            settings={"insert_deduplicate": 0}
        )
        print(f"Inserted {len(insert_rows)} new rows")
    else:
        print("No new rows to insert (all existed)")
def main() -> None:
    players = load_player_json()
    insert_players(players)


if __name__ == "__main__":
    main()