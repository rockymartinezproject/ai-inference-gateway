"""Plugin loader for user-provided gateway middleware."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import TypeVar

from app.plugins.base import GatewayPlugin

PluginT = TypeVar("PluginT", bound=GatewayPlugin)


def discover_plugins(plugin_dir: str | None = None) -> list[type[GatewayPlugin]]:
    """Discover plugin classes from the configured plugin directory."""
    plugin_path = Path(plugin_dir or os.environ.get("GATEWAY_PLUGIN_DIR", "plugins"))
    if not plugin_path.exists():
        return []

    plugins: list[type[GatewayPlugin]] = []
    for file_path in plugin_path.glob("*.py"):
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, GatewayPlugin)
                and attr is not GatewayPlugin
            ):
                plugins.append(attr)

    return sorted(plugins, key=lambda cls: getattr(cls, "order", 0))


def load_plugins(plugin_dir: str | None = None) -> list[GatewayPlugin]:
    """Instantiate discovered plugins."""
    return [cls() for cls in discover_plugins(plugin_dir)]
