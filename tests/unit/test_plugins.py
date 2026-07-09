"""Tests for the plugin system."""

from __future__ import annotations

import tempfile
from pathlib import Path

from starlette.requests import Request
from starlette.responses import Response

from app.plugins.base import GatewayPlugin
from app.plugins.loader import discover_plugins, load_plugins


class ExamplePlugin(GatewayPlugin):
    name = "example"
    order = 10

    async def process_request(self, request: Request) -> Request:
        request.state.plugin_seen = True
        return request

    async def process_response(self, request: Request, response: Response) -> Response:
        response.headers["X-Plugin"] = self.name
        return response


def test_discover_plugins_from_temp_directory() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_file = Path(tmpdir) / "my_plugin.py"
        plugin_file.write_text(
            "from app.plugins.base import GatewayPlugin\n"
            "class MyPlugin(GatewayPlugin):\n"
            "    name = 'my-plugin'\n"
            "    order = 5\n"
            "    async def process_request(self, request):\n"
            "        return request\n"
            "    async def process_response(self, request, response):\n"
            "        return response\n"
        )
        plugins = discover_plugins(tmpdir)
        assert len(plugins) == 1
        assert plugins[0].name == "my-plugin"


def test_load_plugins_instantiates() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_file = Path(tmpdir) / "my_plugin.py"
        plugin_file.write_text(
            "from app.plugins.base import GatewayPlugin\n"
            "class MyPlugin(GatewayPlugin):\n"
            "    name = 'my-plugin'\n"
            "    async def process_request(self, request):\n"
            "        return request\n"
            "    async def process_response(self, request, response):\n"
            "        return response\n"
        )
        plugins = load_plugins(tmpdir)
        assert len(plugins) == 1
        assert plugins[0].name == "my-plugin"


def test_missing_plugin_directory_returns_empty() -> None:
    assert discover_plugins("/nonexistent/path") == []
