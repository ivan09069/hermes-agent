"""Regression tests for the Hermes Agentic Trader repair safety boundary."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest
import yaml


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path, monkeypatch):
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.delenv("HERMES_TRADER_KILL_SWITCH", raising=False)
    yield hermes_home


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_plugin():
    plugin_dir = _repo_root() / "plugins" / "hermes-agentic-trader"
    if "hermes_plugins" not in sys.modules:
        ns = types.ModuleType("hermes_plugins")
        ns.__path__ = []
        sys.modules["hermes_plugins"] = ns
    spec = importlib.util.spec_from_file_location(
        "hermes_plugins.hermes_agentic_trader",
        plugin_dir / "__init__.py",
        submodule_search_locations=[str(plugin_dir)],
    )
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "hermes_plugins.hermes_agentic_trader"
    mod.__path__ = [str(plugin_dir)]
    sys.modules["hermes_plugins.hermes_agentic_trader"] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_config(home: Path, trader):
    (home / "config.yaml").write_text(
        yaml.safe_dump({"trader": trader}),
        encoding="utf-8",
    )


class TestWriteQuarantine:
    @pytest.mark.parametrize("tool_name", ["execute_swap", "submit_gasless_swap"])
    def test_paper_mode_blocks_raw_write_tools(self, _isolate_env, tool_name):
        _write_config(_isolate_env, {"mode": "paper"})
        mod = _load_plugin()
        out = mod._on_pre_tool_call(tool_name=tool_name, args={"quoteData": {}})
        assert out == {
            "action": "block",
            "message": "Hermes Agentic Trader is in paper mode. Live MCP write tools are blocked.",
        }

    @pytest.mark.parametrize("tool_name", ["execute_swap", "submit_gasless_swap"])
    def test_live_mode_is_still_quarantined_during_repair(self, _isolate_env, tool_name):
        _write_config(_isolate_env, {"mode": "live"})
        mod = _load_plugin()
        out = mod._on_pre_tool_call(tool_name=tool_name, args={"quoteData": {"chainId": 8453}})
        assert out["action"] == "block"
        assert "quarantined" in out["message"]
        assert "quote-bound risk gate" in out["message"]

    def test_kill_switch_wins_over_live_mode(self, _isolate_env, monkeypatch):
        _write_config(_isolate_env, {"mode": "live"})
        monkeypatch.setenv("HERMES_TRADER_KILL_SWITCH", "1")
        mod = _load_plugin()
        out = mod._on_pre_tool_call(tool_name="execute_swap", args={"quoteData": {}})
        assert out["action"] == "block"
        assert "kill switch" in out["message"].lower()

    def test_unrelated_read_tool_passes(self, _isolate_env):
        _write_config(_isolate_env, {"mode": "paper"})
        mod = _load_plugin()
        assert mod._on_pre_tool_call(
            tool_name="get_swap_quote",
            args={"chainId": 8453},
        ) is None

    def test_malformed_trader_config_fails_safe_to_paper(self, _isolate_env):
        (_isolate_env / "config.yaml").write_text(
            yaml.safe_dump({"trader": "not-a-mapping"}),
            encoding="utf-8",
        )
        mod = _load_plugin()
        out = mod._on_pre_tool_call(tool_name="execute_swap", args={"quoteData": {}})
        assert out["action"] == "block"
        assert "paper mode" in out["message"].lower()


class TestMcpManifest:
    def _manifest(self):
        path = _repo_root() / "optional-mcps" / "defi-trading" / "manifest.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_exact_mcp_version_is_pinned(self):
        manifest = self._manifest()
        assert "defi-trading-mcp@2.1.3" in manifest["transport"]["args"]

    def test_raw_write_tools_are_not_default_enabled(self):
        manifest = self._manifest()
        enabled = set(manifest["tools"]["default_enabled"])
        assert "execute_swap" not in enabled
        assert "submit_gasless_swap" not in enabled

    def test_base_specific_trending_tool_is_default_enabled(self):
        manifest = self._manifest()
        assert "get_trending_pools_by_network" in manifest["tools"]["default_enabled"]

    def test_private_key_is_optional_in_paper_mode(self):
        manifest = self._manifest()
        env = {item["name"]: item for item in manifest["auth"]["env"]}
        assert env["USER_PRIVATE_KEY"]["required"] is False


class TestPluginRegistration:
    def test_registers_pre_tool_hook(self):
        mod = _load_plugin()
        calls = []

        class Ctx:
            def register_hook(self, name, fn):
                calls.append((name, fn))

        mod.register(Ctx())
        assert len(calls) == 1
        assert calls[0][0] == "pre_tool_call"
        assert calls[0][1] is mod._on_pre_tool_call
