import pytest

from agent_equip import registry
from agent_equip.channels.github import GitHubChannel


def test_channels_contains_github():
    assert isinstance(registry.CHANNELS["github"], GitHubChannel)


def test_get_channel_known():
    assert registry.get_channel("github").name == "github"


def test_get_channel_unknown_raises_with_available_list():
    with pytest.raises(KeyError, match="github"):
        registry.get_channel("nope")


def test_make_adapters_returns_all_four(tmp_path):
    adapters = registry.make_adapters(home=tmp_path, cwd=tmp_path)
    names = [a.name for a in adapters]
    assert names == ["claude-code", "cursor", "windsurf", "generic"]
    assert all(a.home == tmp_path for a in adapters)
