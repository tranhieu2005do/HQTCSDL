from pathlib import Path
from typing import List
import time
import json

from api_client import ApiFootballClient
from config import OUTPUT_DIR
from utils import ensure_output_dir, load_json_array, write_json_array


def load_fixture_ids():
    with open("D:/HQTCSDL/HQTCSDL/output/fixtures.json", "r", encoding="utf-8") as f:
        fixtures = json.load(f)

    # tất cả fixture id từ fixtures.json
    all_fixture_ids = set()

    for item in fixtures:
        response = item["data"].get("response", [])

        for obj in response:
            fixture = obj.get("fixture")
            if fixture and "id" in fixture:
                all_fixture_ids.add(str(fixture["id"]))

    # đã có trong events.json
    events_file = Path("D:/HQTCSDL/HQTCSDL/output/events.json")

    existing_ids = set()

    if events_file.exists():
        with open(events_file, "r", encoding="utf-8") as f:
            events = json.load(f)

        for e in events:
            endpoint = e.get("endpoint", "")
            if "fixture=" in endpoint:
                existing_ids.add(endpoint.split("fixture=")[1].split("&")[0])

    # chỉ lấy fixture chưa crawl
    remaining = list(all_fixture_ids - existing_ids)

    return remaining

# APPEND JSON FILE (NO OVERWRITE)
def append_json(path: Path, new_data: list):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            try:
                old_data = json.load(f)
            except json.JSONDecodeError:
                old_data = []
    else:
        old_data = []

    old_data.extend(new_data)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(old_data, f, ensure_ascii=False, indent=2)


# MAIN Extract
def extract_events():
    ensure_output_dir(OUTPUT_DIR)
    client = ApiFootballClient()

    fixture_ids = load_fixture_ids()
    output_path = OUTPUT_DIR / "events.json"

    print(f"Need to process {len(fixture_ids)} new fixtures")

    payloads = []
    max_requests = 100

    for idx, fixture_id in enumerate(fixture_ids[:max_requests]):

        endpoint = "/fixtures/events"

        try:
            response = client.request(endpoint, params={"fixture": fixture_id})

            payloads.append({
                "source": "api-football",
                "endpoint": f"/fixtures/events?fixture={fixture_id}",
                "data": response,
            })

            print(f"[{idx+1}] OK fixture {fixture_id}")
            print(response)

        except Exception as exc:
            print(f"FAILED fixture {fixture_id}: {exc}")

        time.sleep(6)  # 10 req/min

    # append thay vì overwrite
    append_json(output_path, payloads)

    print(f"Done. Appended {len(payloads)} records to {output_path}")


if __name__ == "__main__":
    extract_events()