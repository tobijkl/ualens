"""Favorite OPC UA servers persistence."""

import json
from pathlib import Path

try:
    import platformdirs
    _CONFIG_DIR = Path(platformdirs.user_config_dir("ualens", "ualens"))
except ImportError:
    _CONFIG_DIR = Path.home() / ".config" / "ualens"


def _favorites_path() -> Path:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return _CONFIG_DIR / "favorites.json"


def load_favorites() -> list[dict]:
    """Load favorites from disk. Returns list of {url, label?, username?}."""
    path = _favorites_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def save_favorites(favorites: list[dict]) -> None:
    """Save favorites to disk."""
    path = _favorites_path()
    path.write_text(json.dumps(favorites, indent=2))


def add_favorite(url: str, label: str | None = None, username: str | None = None) -> None:
    """Add a favorite. Does not store password."""
    favorites = load_favorites()
    entry = {"url": url, "label": label or url, "username": username}
    if not any(f.get("url") == url for f in favorites):
        favorites.append(entry)
        save_favorites(favorites)
