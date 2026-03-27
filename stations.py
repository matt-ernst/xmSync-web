import time
import threading
from typing import Optional
import cloudscraper

_CACHE_TTL = 86400  # 24 hours
_cache: Optional[dict] = None
_cache_time: float = 0
_lock = threading.Lock()


def get_stations():
    """Return {name: deeplink} for all visible stations fetched from xmplaylist.com.

    Results are cached for 24 h. Returns stale cache or empty dict if unreachable.
    """
    global _cache, _cache_time

    now = time.time()
    # Fast path — no lock needed for a fresh cache read
    if _cache is not None and (now - _cache_time) < _CACHE_TTL:
        return _cache

    # Slow path — acquire lock so only one thread/greenlet fetches at a time
    with _lock:
        # Re-check inside the lock (another thread may have populated it)
        now = time.time()
        if _cache is not None and (now - _cache_time) < _CACHE_TTL:
            return _cache

        try:
            scraper = cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "windows", "mobile": False}
            )
            response = scraper.get("https://xmplaylist.com/api/station", timeout=10)
            response.raise_for_status()
            results = response.json().get("results", [])
            fetched = {
                r["name"]: r["deeplink"]
                for r in results
                if r.get("isVisible", True) and r.get("name") and r.get("deeplink")
            }
            if fetched:
                _cache = fetched
                _cache_time = now
                print(f"Stations refreshed from API ({len(fetched)} stations).")
                return _cache
        except Exception as exc:
            print(f"Failed to fetch stations from API: {exc}")

        # Return stale cache if available, otherwise empty (API is required)
        return _cache if _cache is not None else {}