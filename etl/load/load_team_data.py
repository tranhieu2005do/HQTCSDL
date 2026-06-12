from __future__ import annotations

from pathlib import Path
from typing import List
import json

from clickhouse_client import get_client

def load_team_json() -> List[dict]:

    base_dir = Path(__file__).resolve().parent.parent.parent
    path = base_dir / "database" / "teams.json"

    if not path.exists():
        raise FileNotFoundError(f"Teams JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    teams: List[dict] = []

    # Support two common shapes: a list of API payloads (each with data.response)
    # or a direct list of team dicts.
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "data" in item:
                response = item["data"].get("response", [])
                for entry in response:
                    team_obj = entry.get("team") if isinstance(entry, dict) else entry
                    if team_obj:
                        teams.append(team_obj)
            else:
                # assume item itself is a team dict
                if isinstance(item, dict):
                    teams.append(item)
    elif isinstance(data, dict):
        response = data.get("response", [])
        for entry in response:
            team_obj = entry.get("team") if isinstance(entry, dict) else entry
            if team_obj:
                teams.append(team_obj)

    return teams


def insert_teams(data: List[dict]) -> None:
    """Insert team records into dim_team."""

    client = get_client()

    rows = []

    for t in data:
        team = t.get("team") if "team" in t else t

        team_id = team.get("id")
        if team_id is None:
            continue

        rows.append((
            int(team_id),
            str(team.get("name") or ""),
            team.get("code") or None,
            int(team["founded"]) if team.get("founded") else None,
            team.get("logo") or team.get("logo_url") or ""
        ))

    if not rows:
        print("No rows to insert")
        return

    client.insert(
        "dim_team",
        rows,
        column_names=[
            "id",
            "name",
            "code",
            "founded",
            "logo_url"
        ]
    )

    print(f"Inserted {len(rows)} rows")


def main() -> None:
    teams = load_team_json()
    insert_teams(teams)


if __name__ == "__main__":
    main()
