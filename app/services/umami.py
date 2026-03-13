"""Umami Analytics API integration."""

import requests

from app.config import UMAMI_API_URL, UMAMI_API_TOKEN


def _headers():
    return {"Authorization": f"Bearer {UMAMI_API_TOKEN}", "Content-Type": "application/json"}


def _get(path: str, params: dict = None) -> dict | list | None:
    """Make an authenticated GET request to Umami API."""
    if not UMAMI_API_URL or not UMAMI_API_TOKEN:
        return None
    try:
        resp = requests.get(
            f"{UMAMI_API_URL}/api{path}",
            headers=_headers(),
            params=params or {},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def get_website_stats(umami_site_id: str, start_at: int, end_at: int) -> dict | None:
    """Fetch stats (pageviews, visitors, bounces, totaltime) for a site.

    start_at/end_at are Unix timestamps in milliseconds.
    """
    return _get(f"/websites/{umami_site_id}/stats", {
        "startAt": start_at,
        "endAt": end_at,
    })


def get_website_pageviews(
    umami_site_id: str, start_at: int, end_at: int, unit: str = "day"
) -> dict | None:
    """Fetch pageview timeseries."""
    return _get(f"/websites/{umami_site_id}/pageviews", {
        "startAt": start_at,
        "endAt": end_at,
        "unit": unit,
    })


def get_website_metrics(
    umami_site_id: str, start_at: int, end_at: int, metric_type: str = "url"
) -> list | None:
    """Fetch top pages, referrers, browsers, etc."""
    return _get(f"/websites/{umami_site_id}/metrics", {
        "startAt": start_at,
        "endAt": end_at,
        "type": metric_type,
    })
