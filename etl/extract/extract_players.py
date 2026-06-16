from pathlib import Path
from typing import List
import json
import time

from api_client import ApiFootballClient
from config import OUTPUT_DIR, SEASON
from utils import ensure_output_dir, load_json_array, write_json_array, append_json_array


def load_team_ids():
    with open("C:/Users/7610/OneDrive/Dokumen/HQTCSDL/etl/extract/output/teams.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    team_ids = [36,39,40,41,42,45,46,47,48,49,50,51,52,55,63]

    # for item in raw:
    #     response = item["data"].get("response", [])

    #     for team_obj in response:
    #         team = team_obj.get("team")
    #         if team and "id" in team:
    #             team_ids.append(team["id"])

    if not team_ids:
        raise ValueError("No team IDs were found in teams.json")

    return team_ids


def extract_players() -> None:
    ensure_output_dir(OUTPUT_DIR)
    client = ApiFootballClient()
    team_ids = load_team_ids()
    output_path = "C:/Users/7610/OneDrive/Dokumen/HQTCSDL/etl/extract/output/players.json"
    print(f"Starting players extraction for {len(team_ids)} teams")

    delay_seconds = 6
    request_count = 0

    for team_id in team_ids:
        endpoint = "/players"
        params = {"team": team_id, "season": SEASON}
        page = 1
        total_pages = 1
        
        while page <= total_pages:
            response = client.request(
                endpoint,
                params={**params, "page": page}
            )
            # print(response)
            
            if response.get("errors"):
                print(
                    f"Skipped players page {page} for team {team_id}: "
                    f"{response['errors']}"
                )
            else:
                payload = {
                    "source": "api-football",
                    "endpoint": f"/players?team={team_id}&season={SEASON}&page={page}",
                    "data": response,
                }
                
                append_json_array(output_path, payload)
                print(f"Captured players page {page} for team {team_id}")
                
                # Update total_pages from paging info
                paging = response.get("paging", {})
                total_pages = paging.get("total", 1)
            
            page += 1
            request_count += 1
            
            # Add delay between requests (but not after the last one)
            if page <= total_pages:
                print(
                    f"Waiting {delay_seconds}s "
                    f"(rate limit: 10 req/min)..."
                )
                time.sleep(delay_seconds)

    print(f"Players extraction complete. Output saved to {output_path}")



if __name__ == "__main__":
    extract_players()
