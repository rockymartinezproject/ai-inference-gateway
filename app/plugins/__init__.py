"""Plugin system for custom gateway middleware."""

from app.plugins.base import GatewayPlugin
from app.plugins.loader import discover_plugins, load_plugins

__all__ = ["GatewayPlugin", "discover_plugins", "load_plugins"]
