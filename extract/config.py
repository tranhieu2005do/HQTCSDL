import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

API_KEY = "5efcc462c004f02d47c5aa76dbe1ba34"
BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 39
SEASON = 2022
OUTPUT_DIR = PROJECT_ROOT / "output"

if not API_KEY:
    API_KEY = os.getenv("API_KEY", "")

# If no API key is set in the environment, the caller must provide one.
# Do not hardcode secrets into source code in production.
