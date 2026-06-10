import pytest
from pathlib import Path

from agent_equip.agents.base import AgentAdapter, InstallResult, strip_frontmatter
from agent_equip.channels.base import Channel, CheckResult


class FakeChannel(Channel):
    name = "fake"
    description = "fake channel"

    def __init__(self, skill_path: Path):
        self._skill_path = skill_path

    def check(self) -> CheckResult:
        return CheckResult("ok", "fine")

    def skill_source(self) -> Path:
        return self._skill_path


class DummyAdapter(AgentAdapter):
    name = "dummy"
    scope = "project"

    def detect(self) -> bool:
        return True

    def skill_target(self, channel: Channel) -> Path:
        return self.cwd / "rules" / f"{channel.name}.md"


def make_channel(tmp_path: Path, body: str = "---\nname: fake\n---\n\n# Fake skill\n") -> FakeChannel:
    skill = tmp_path / "SKILL.md"
    skill.write_text(body, encoding="utf-8")
    return FakeChannel(skill)


def test_strip_frontmatter_removes_yaml_block():
    text = "---\nname: x\ndescription: y\n---\n\n# Body\n"
    assert strip_frontmatter(text) == "# Body\n"


def test_strip_frontmatter_passthrough_without_block():
    assert strip_frontmatter("# Just body\n") == "# Just body\n"


def test_install_skill_fresh_install(tmp_path):
    ch = make_channel(tmp_path)
    ad = DummyAdapter(home=tmp_path, cwd=tmp_path / "proj")
    result = ad.install_skill(ch)
    assert result == InstallResult("dummy", tmp_path / "proj" / "rules" / "fake.md", "installed")
    assert result.path.read_text(encoding="utf-8").startswith("---\nname: fake")


def test_install_skill_is_idempotent_skip(tmp_path):
    ch = make_channel(tmp_path)
    ad = DummyAdapter(home=tmp_path, cwd=tmp_path / "proj")
    ad.install_skill(ch)
    assert ad.install_skill(ch).action == "skipped"


def test_install_skill_updates_changed_content(tmp_path):
    ch = make_channel(tmp_path)
    ad = DummyAdapter(home=tmp_path, cwd=tmp_path / "proj")
    ad.install_skill(ch)
    ch.skill_source().write_text("---\nname: fake\n---\n\n# New body\n", encoding="utf-8")
    result = ad.install_skill(ch)
    assert result.action == "updated"
    assert "# New body" in result.path.read_text(encoding="utf-8")


def test_uninstall_skill_removes_file(tmp_path):
    ch = make_channel(tmp_path)
    ad = DummyAdapter(home=tmp_path, cwd=tmp_path / "proj")
    result = ad.install_skill(ch)
    ad.uninstall_skill(ch)
    assert not result.path.exists()


def test_uninstall_skill_tolerates_missing_file(tmp_path):
    ch = make_channel(tmp_path)
    ad = DummyAdapter(home=tmp_path, cwd=tmp_path / "proj")
    ad.uninstall_skill(ch)  # must not raise


from agent_equip.agents.claude_code import ClaudeCodeAdapter


def test_claude_code_detect(tmp_path):
    ad = ClaudeCodeAdapter(home=tmp_path, cwd=tmp_path)
    assert ad.detect() is False
    (tmp_path / ".claude").mkdir()
    assert ad.detect() is True


def test_claude_code_is_global_scope_and_auto():
    assert ClaudeCodeAdapter.scope == "global"
    assert ClaudeCodeAdapter.auto is True


def test_claude_code_install_target_and_content(tmp_path):
    (tmp_path / ".claude").mkdir()
    ch = make_channel(tmp_path)
    ad = ClaudeCodeAdapter(home=tmp_path, cwd=tmp_path)
    result = ad.install_skill(ch)
    assert result.path == tmp_path / ".claude" / "skills" / "fake" / "SKILL.md"
    # Claude Code keeps the original frontmatter
    assert result.path.read_text(encoding="utf-8").startswith("---\nname: fake")


def test_adapter_subclass_requires_name_and_scope():
    with pytest.raises(TypeError, match="scope"):

        class BadScope(AgentAdapter):
            name = "bad"
            scope = "machine"  # invalid

            def detect(self):
                return True

            def skill_target(self, channel):
                return Path("x")
