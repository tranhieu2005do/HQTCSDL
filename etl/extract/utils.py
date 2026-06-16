import json
from pathlib import Path
from typing import Any, Dict, List


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json_array(path: Path, values: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(values, handle, indent=2, ensure_ascii=False)


def append_json_array(path, value: Dict[str, Any]) -> None:
    path = Path(path)
    if path.exists():
        items = load_json_array(path)
    else:
        items = []

    items.append(value)
    write_json_array(path, items)


def load_json_array(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array in {path}")
    return data
