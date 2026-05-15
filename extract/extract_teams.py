from pathlib import Path
from typing import Dict, List

from api_client import ApiFootballClient
from config import LEAGUE_ID, OUTPUT_DIR, SEASON
from utils import ensure_output_dir, write_json_array


def extract_teams() -> Dict:
    client = ApiFootballClient()

    print("Starting teams extraction")

    response = client.get(
        "/teams",
        params={
            "league": LEAGUE_ID,
            "season": SEASON
        }
    )

    print("Teams extraction complete")

    return response


def save_teams(response: Dict) -> Path:
    ensure_output_dir(OUTPUT_DIR)

    output_path = OUTPUT_DIR / "teams.json"

    payload = {
        "source": "api-football",
        "endpoint": f"/teams?league={LEAGUE_ID}&season={SEASON}",
        "data": response
    }

    write_json_array(output_path, [payload])

    print(f"Saved {output_path}")

    return output_path


if __name__ == "__main__":
    response = extract_teams()
    save_teams(response)