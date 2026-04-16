"""Fetch public Trailhead profile data via the Trailhead GraphQL API."""
import requests

_GRAPHQL_URL = "https://profile.api.trailhead.com/graphql"

_QUERY = """
query GetProfile($slug: String!) {
  profile(slug: $slug) {
    __typename
    ... on PublicProfile {
      trailheadStats {
        earnedBadgesCount
        earnedPointsSum
        completedTrailCount
        superbadgeCount
        rank { title imageUrl }
      }
      credential {
        certifications { title dateCompleted status { title expired } }
      }
    }
  }
}
"""


def _normalize_username(username):
    """Extract the slug from a full URL or return as-is if already a username."""
    if not username:
        return ""
    username = username.strip().rstrip("/")
    # Handle full URLs like https://www.salesforce.com/trailblazer/architects
    if "/" in username:
        return username.rsplit("/", 1)[-1]
    return username


def fetch_trailhead_profile(username):
    """Fetch Trailhead profile for a given trailblazer username.

    Returns a dict with keys: rank, badges, points, trails, superbadges,
    certifications (list of dicts), rank_image_url.
    Returns None if the profile cannot be fetched.
    """
    username = _normalize_username(username)
    if not username:
        return None
    try:
        resp = requests.post(
            _GRAPHQL_URL,
            json={"query": _QUERY, "variables": {"slug": username}},
            headers={"Content-Type": "application/json"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        profile = data.get("data", {}).get("profile")
        if not profile or profile.get("__typename") != "PublicProfile":
            return None

        stats = profile.get("trailheadStats") or {}
        creds = (profile.get("credential") or {}).get("certifications") or []

        return {
            "rank": (stats.get("rank") or {}).get("title", "Unknown"),
            "rank_image_url": (stats.get("rank") or {}).get("imageUrl", ""),
            "badges": stats.get("earnedBadgesCount", 0),
            "points": stats.get("earnedPointsSum", 0),
            "trails": stats.get("completedTrailCount", 0),
            "superbadges": stats.get("superbadgeCount", 0),
            "certifications": [
                {
                    "title": c.get("title", ""),
                    "date": c.get("dateCompleted", ""),
                    "status": (c.get("status") or {}).get("title", ""),
                    "expired": (c.get("status") or {}).get("expired", False),
                }
                for c in creds
            ],
        }
    except Exception as e:
        print(f"Trailhead API error for {username}: {e}")
        return None
