from pathlib import Path
from typing import Dict

from api_client import ApiFootballClient
from config import LEAGUE_ID, OUTPUT_DIR, SEASON
from utils import ensure_output_dir, write_json_array


def extract_fixtures() -> Dict:
    client = ApiFootballClient()

    print("Starting fixtures extraction")

    response = client.request(
        "/fixtures",
        params={
            "league": LEAGUE_ID,
            "season": SEASON
        }
    )

    print("Fixtures extraction complete")

    return response


def save_fixtures(response: Dict) -> Path:
    ensure_output_dir(OUTPUT_DIR)

    output_path = OUTPUT_DIR / "fixtures.json"

    payload = {
        "source": "api-football",
        "endpoint": f"/fixtures?league={LEAGUE_ID}&season={SEASON}",
        "data": response
    }

    write_json_array(output_path, [payload])

    print(f"Saved {output_path}")

    return output_path


if __name__ == "__main__":
    response = extract_fixtures()
    save_fixtures(response)