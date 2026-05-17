from __future__ import annotations

from typing import Final
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# ClickHouse connection configuration. Values may be overridden by environment
# variables in production; defaults kept here for local development only.
CLICKHOUSE_HOST = "b0b4djhs9t.ap-southeast-1.aws.clickhouse.cloud"
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = 'ILbo3uSjLqi_W'
CLICKHOUSE_DATABASE = "football"
