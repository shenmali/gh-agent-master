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


from agent_equip.agents.cursor import CursorAdapter


def test_cursor_detect_against_cwd(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    ad = CursorAdapter(home=tmp_path, cwd=proj)
    assert ad.detect() is False
    (proj / ".cursor").mkdir()
    assert ad.detect() is True


def test_cursor_renders_mdc_with_own_frontmatter(tmp_path):
    proj = tmp_path / "proj"
    (proj / ".cursor").mkdir(parents=True)
    ch = make_channel(tmp_path)
    ad = CursorAdapter(home=tmp_path, cwd=proj)
    result = ad.install_skill(ch)
    assert result.path == proj / ".cursor" / "rules" / "fake.mdc"
    text = result.path.read_text(encoding="utf-8")
    assert text.startswith("---\ndescription: fake channel\nalwaysApply: false\n---\n")
    assert "# Fake skill" in text
    assert "name: fake" not in text  # original frontmatter stripped


from agent_equip.agents.windsurf import WindsurfAdapter


def test_windsurf_detect_and_target(tmp_path):
    proj = tmp_path / "proj"
    (proj / ".windsurf").mkdir(parents=True)
    ch = make_channel(tmp_path)
    ad = WindsurfAdapter(home=tmp_path, cwd=proj)
    assert ad.detect() is True
    result = ad.install_skill(ch)
    assert result.path == proj / ".windsurf" / "rules" / "fake.md"
    text = result.path.read_text(encoding="utf-8")
    assert text.startswith("# Fake skill")  # frontmatter stripped, plain markdown


from agent_equip.agents.generic import GenericAdapter


def _generic(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir(exist_ok=True)
    return GenericAdapter(home=tmp_path, cwd=proj), proj


def test_generic_is_opt_in_but_detects_true():
    assert GenericAdapter.auto is False
    assert GenericAdapter(home=Path("/x"), cwd=Path("/y")).detect() is True


def test_generic_creates_agents_md_with_marked_block(tmp_path):
    ch = make_channel(tmp_path)
    ad, proj = _generic(tmp_path)
    result = ad.install_skill(ch)
    assert result.action == "installed"
    text = (proj / "AGENTS.md").read_text(encoding="utf-8")
    assert text.startswith("<!-- agent-equip:fake:start -->")
    assert "# Fake skill" in text
    assert text.rstrip().endswith("<!-- agent-equip:fake:end -->")


def test_generic_appends_to_existing_agents_md(tmp_path):
    ch = make_channel(tmp_path)
    ad, proj = _generic(tmp_path)
    (proj / "AGENTS.md").write_text("# My project notes\n", encoding="utf-8")
    result = ad.install_skill(ch)
    assert result.action == "installed"
    text = (proj / "AGENTS.md").read_text(encoding="utf-8")
    assert text.startswith("# My project notes")
    assert "<!-- agent-equip:fake:start -->" in text


def test_generic_replaces_existing_block_idempotently(tmp_path):
    ch = make_channel(tmp_path)
    ad, proj = _generic(tmp_path)
    ad.install_skill(ch)
    assert ad.install_skill(ch).action == "skipped"
    ch.skill_source().write_text("---\nname: fake\n---\n\n# Updated body\n", encoding="utf-8")
    assert ad.install_skill(ch).action == "updated"
    text = (proj / "AGENTS.md").read_text(encoding="utf-8")
    assert "# Updated body" in text
    assert text.count("<!-- agent-equip:fake:start -->") == 1


def test_generic_uninstall_removes_only_the_block(tmp_path):
    ch = make_channel(tmp_path)
    ad, proj = _generic(tmp_path)
    (proj / "AGENTS.md").write_text("# Keep me\n", encoding="utf-8")
    ad.install_skill(ch)
    ad.uninstall_skill(ch)
    text = (proj / "AGENTS.md").read_text(encoding="utf-8")
    assert "Keep me" in text
    assert "agent-equip:fake" not in text


def test_generic_uninstall_deletes_file_if_block_was_everything(tmp_path):
    ch = make_channel(tmp_path)
    ad, proj = _generic(tmp_path)
    ad.install_skill(ch)
    ad.uninstall_skill(ch)
    assert not (proj / "AGENTS.md").exists()


def test_adapter_subclass_requires_name_and_scope():
    with pytest.raises(TypeError, match="scope"):

        class BadScope(AgentAdapter):
            name = "bad"
            scope = "machine"  # invalid

            def detect(self):
                return True

            def skill_target(self, channel):
                return Path("x")
