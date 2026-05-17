from __future__ import annotations

from typing import Optional

import clickhouse_connect

from clickhouse_connect_config import (
    CLICKHOUSE_HOST,
    CLICKHOUSE_USER,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_DATABASE,
)


_client: Optional[clickhouse_connect.client.ClickHouseClient] = None


def get_client() -> clickhouse_connect.client.ClickHouseClient:
    """Return a singleton ClickHouse client configured from project config.

    Reads connection constants from `load/clickhouse_connect_config.py`.
    """
    global _client

    if _client is not None:
        return _client

    host = CLICKHOUSE_HOST
    user = CLICKHOUSE_USER
    password = CLICKHOUSE_PASSWORD
    database = CLICKHOUSE_DATABASE

    if not host:
        raise EnvironmentError("CLICKHOUSE_HOST is not set in config")

    _client = clickhouse_connect.get_client(
        host=host,
        port=8443, 
        username=user or None,
        password=password or None,
        database=database or None,
        secure=True
    )

    return _client
