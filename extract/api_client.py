import random
import time
from typing import Any, Dict, Generator, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import API_KEY, BASE_URL


class ApiFootballClient:
    def __init__(self) -> None:
        if not API_KEY:
            raise ValueError(
                "API key is required. Set the environment variable API_FOOTBALL_API_KEY."
            )

        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"x-apisports-key": API_KEY})
        self.timeout = (5, 20)
        self.max_retries = 5
        self.backoff_factor = 1.0
        self._mount_retry_adapter()

    def _mount_retry_adapter(self) -> None:
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            backoff_factor=0.5,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _sleep_after_request(self) -> None:
        time.sleep(random.uniform(0.5, 1.0))

    def request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        params = params or {}

        response = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after else self.backoff_factor * attempt
                    print(f"429 rate limit received. Sleeping {wait:.1f}s before retry {attempt}/{self.max_retries}.")
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                payload = response.json()
                self._sleep_after_request()
                return payload

            except requests.exceptions.Timeout:
                if attempt == self.max_retries:
                    raise
                wait = self.backoff_factor * attempt
                print(f"Timeout on {url}. Retrying in {wait:.1f}s ({attempt}/{self.max_retries}).")
                time.sleep(wait)
            except requests.exceptions.RequestException as exc:
                status_code = response.status_code if response is not None else None
                if status_code and status_code >= 500:
                    if attempt == self.max_retries:
                        raise
                    wait = self.backoff_factor * attempt
                    print(f"Server error {status_code} on {url}. Retrying in {wait:.1f}s.")
                    time.sleep(wait)
                    continue
                raise exc

        raise RuntimeError(f"Failed to request {url} after {self.max_retries} attempts.")

    def get_paginated(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Generator[Dict[str, Any], None, None]:
        params = params.copy() if params else {}
        page = 1

        while True:
            params["page"] = page
            response = self.request(endpoint, params=params)
            yield response

            paging = response.get("paging") or {}
            current = paging.get("current")
            total = paging.get("total")
            if not current or not total or current >= total:
                break
            page += 1
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.request(endpoint, params)
