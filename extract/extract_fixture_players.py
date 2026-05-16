from pathlib import Path
from typing import List
import json
import time
from api_client import ApiFootballClient
from config import OUTPUT_DIR
from utils import ensure_output_dir, append_json_array


def load_fixture_ids() -> List[str]:
    with open("output/fixtures.json", "r", encoding="utf-8") as f:
        fixtures = json.load(f)

    # tất cả fixture id từ fixtures.json
    all_fixture_ids = set()

    for item in fixtures:
        response = item["data"].get("response", [])

        for obj in response:
            fixture = obj.get("fixture")
            if fixture and "id" in fixture:
                all_fixture_ids.add(str(fixture["id"]))

    # đã có trong fixture_players.json
    players_file = Path("output/fixture_players.json")

    existing_ids = set()

    if players_file.exists():
        with open(players_file, "r", encoding="utf-8") as f:
            players = json.load(f)

        for p in players:
            endpoint = p.get("endpoint", "")
            if "fixture=" in endpoint:
                existing_ids.add(endpoint.split("fixture=")[1].split("&")[0])

    # chỉ lấy fixture chưa crawl
    remaining = list(all_fixture_ids - existing_ids)

    return remaining


def extract_fixture_players() -> None:
    ensure_output_dir(OUTPUT_DIR)
    client = ApiFootballClient()
    fixture_ids = load_fixture_ids()
    output_path = OUTPUT_DIR / "fixture_players.json"

    max_requests = 100
    delay_seconds = 6

    print(
        f"Starting fixture players extraction for "
        f"{min(len(fixture_ids), max_requests)} fixtures"
    )

    for index, fixture_id in enumerate(fixture_ids[:max_requests]):
        endpoint = "/fixtures/players"

        response = client.request(
            endpoint,
            params={"fixture": fixture_id}
        )

        if response.get("errors"):
            print(
                f"Skipped fixture players for fixture "
                f"{fixture_id}: {response.get('errors')}"
            )
        else:
            payload = {
                "source": "api-football",
                "endpoint": (
                    f"/fixtures/players?fixture={fixture_id}"
                ),
                "data": response,
            }

            append_json_array(output_path, payload)

            print(
                f"Captured fixture players for fixture "
                f"{fixture_id}"
            )

        if index < max_requests - 1:
            print(
                f"Waiting {delay_seconds}s "
                f"(rate limit: 10 req/min)..."
            )
            time.sleep(delay_seconds)

    print(
        f"Fixture players extraction complete. "
        f"Output saved to {output_path}"
    )


if __name__ == "__main__":
    extract_fixture_players()