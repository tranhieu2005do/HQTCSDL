from pathlib import Path
from typing import List
import json

from api_client import ApiFootballClient
from config import OUTPUT_DIR, SEASON
from utils import ensure_output_dir, load_json_array, write_json_array


def load_team_ids():
    with open("output/teams.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    team_ids = []

    for item in raw:
        response = item["data"].get("response", [])

        for team_obj in response:
            team = team_obj.get("team")
            if team and "id" in team:
                team_ids.append(team["id"])

    if not team_ids:
        raise ValueError("No team IDs were found in teams.json")

    return team_ids


def extract_players() -> None:
    ensure_output_dir(OUTPUT_DIR)
    client = ApiFootballClient()
    team_ids = load_team_ids()
    output_path = OUTPUT_DIR / "players.json"
    print(f"Starting players extraction for {len(team_ids)} teams")
    payloads = []

    for team_id in team_ids:
        endpoint = "/players"
        params = {"team": team_id, "season": SEASON}
        page = 1
        for response in client.get_paginated(endpoint, params=params):
            payloads.append(
                {
                    "source": "api-football",
                    "endpoint": f"/players?team={team_id}&season={SEASON}&page={page}",
                    "data": response,
                }
            )
            print(f"Captured players page {page} for team {team_id}")
            page += 1

    write_json_array(output_path, payloads)
    print(f"Players extraction complete. Output saved to {output_path}")


if __name__ == "__main__":
    extract_players()
