from pathlib import Path
from typing import List
from itertools import combinations
import json
import time

from api_client import ApiFootballClient
from config import OUTPUT_DIR
from utils import ensure_output_dir, append_json_array


# def load_team_ids() -> List[str]:
#     with open("output/teams.json", "r", encoding="utf-8") as f:
#         teams = json.load(f)

#     all_team_ids = set()

#     response = teams["data"]["response"]

#     for team in response:
#         if team and "id" in team:
#             all_team_ids.add(str(team["id"]))

#     return list(all_team_ids)

def load_team_ids() -> List[str]:
    with open("output/teams.json", "r", encoding="utf-8") as f:
        teams = json.load(f)

    all_team_ids = set()

    for item in teams:

        response = item["data"].get("response", [])

        for team_data in response:

            team = team_data.get("team")

            if team and "id" in team:
                all_team_ids.add(str(team["id"]))

    return sorted(all_team_ids, key=int)

def normalize_pair(pair: str) -> str:
    a, b = pair.split("-")
    return "-".join(sorted([a, b], key=int))

def generate_team_pairs() -> List[str]:
    team_ids = load_team_ids()
    pairs = [
        normalize_pair(f"{a}-{b}")
        for a, b in combinations(team_ids, 2)
    ]
    return pairs


def load_remaining_pairs() -> List[str]:
    all_pairs = set(generate_team_pairs())
    output_file = Path("output/fixture_headtohead.json")
    existing_pairs = set()

    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            items = json.load(f)

        for item in items:
            pair = item["data"]["parameters"]["h2h"]

            existing_pairs.add(
                normalize_pair(pair)
            )

    remaining = list(all_pairs - existing_pairs)
    # print("exisiting pair: ", existing_pairs)
    # print("remaining pair: ", remaining)
    return remaining


def extract_fixture_headtohead() -> None:
    ensure_output_dir(OUTPUT_DIR)
    client = ApiFootballClient()
    pair_ids = load_remaining_pairs()
    output_path = OUTPUT_DIR / "fixture_headtohead.json"

    max_requests = 32
    delay_seconds = 6

    print(
        f"Starting fixture headtohead extraction for "
        f"{min(len(pair_ids), max_requests)} pairs"
    )

    for index, pair_id in enumerate(pair_ids[:max_requests]):
        endpoint = "/fixtures/headtohead"

        response = client.request(
            endpoint,
            params={"h2h": pair_id}
        )

        if response.get("errors"):
            print(
                f"Skipped fixture headtohead for pair "
                f"{pair_id}: {response.get('errors')}"
            )
        else:
            payload = {
                "source": "api-football",
                "endpoint": (
                    f"/fixtures/headtohead?h2h={pair_id}"
                ),
                "data": response,
            }

            append_json_array(output_path, payload)

            print(
                f"Captured fixture headtohead for pair "
                f"{pair_id}"
            )

        if index < max_requests - 1:
            print(
                f"Waiting {delay_seconds}s "
                f"(rate limit: 10 req/min)..."
            )
            time.sleep(delay_seconds)

    print(
        f"Fixture headtohead extraction complete. "
        f"Output saved to {output_path}"
    )


if __name__ == "__main__":
    extract_fixture_headtohead()
