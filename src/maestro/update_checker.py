"""Check for new releases on GitHub."""

import urllib.request
from typing import NamedTuple


class UpdateInfo(NamedTuple):
    """Information about an available update."""

    has_update: bool
    latest_version: str | None
    release_url: str | None
    error: str | None


def parse_version(version: str) -> tuple[int, ...]:
    """Parse semantic version string into tuple of ints.

    Args:
        version: Version string like "1.3.0" or "v1.3.0"

    Returns:
        Tuple of version numbers (1, 3, 0)
    """
    # Remove 'v' prefix if present
    version = version.lstrip("v")
    try:
        return tuple(int(x) for x in version.split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def compare_versions(current: str, latest: str) -> bool:
    """Compare two semantic versions.

    Args:
        current: Current version string
        latest: Latest version string

    Returns:
        True if latest > current, False otherwise
    """
    current_tuple = parse_version(current)
    latest_tuple = parse_version(latest)
    return latest_tuple > current_tuple


def check_for_updates(
    current_version: str, repo: str, timeout: int = 5
) -> UpdateInfo:
    """Check GitHub for new releases.

    Args:
        current_version: Current app version (e.g., "1.3.0")
        repo: GitHub repo in format "owner/repo"
        timeout: Request timeout in seconds

    Returns:
        UpdateInfo with update availability and details
    """
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    release_url = f"https://github.com/{repo}/releases/latest"

    try:
        # Make request to GitHub API
        req = urllib.request.Request(
            api_url,
            headers={"Accept": "application/vnd.github.v3+json"},
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return UpdateInfo(
                    has_update=False,
                    latest_version=None,
                    release_url=None,
                    error=f"GitHub API returned status {response.status}",
                )

            # Parse JSON response
            import json

            data = json.loads(response.read().decode("utf-8"))
            latest_version = data.get("tag_name", "").lstrip("v")

            if not latest_version:
                return UpdateInfo(
                    has_update=False,
                    latest_version=None,
                    release_url=None,
                    error="Could not parse version from GitHub response",
                )

            # Compare versions
            has_update = compare_versions(current_version, latest_version)

            return UpdateInfo(
                has_update=has_update,
                latest_version=latest_version,
                release_url=release_url if has_update else None,
                error=None,
            )

    except urllib.error.URLError as e:
        # Network error (no internet, timeout, etc.)
        return UpdateInfo(
            has_update=False,
            latest_version=None,
            release_url=None,
            error=f"Network error: {e.reason}",
        )
    except Exception as e:
        # Other errors (JSON parse, etc.)
        return UpdateInfo(
            has_update=False,
            latest_version=None,
            release_url=None,
            error=f"Unexpected error: {e}",
        )
