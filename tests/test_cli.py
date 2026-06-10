from pathlib import Path

from typer.testing import CliRunner

from agent_equip import registry
from agent_equip.channels.base import Channel, CheckResult
from agent_equip.cli import app

runner = CliRunner()


class StubChannel(Channel):
    name = "github"
    description = "stub github channel"

    def __init__(self, status="ok", skill_path: Path | None = None):
        self._status = status
        self._skill_path = skill_path

    def check(self) -> CheckResult:
        hints = {"warn": "run `gh auth login`", "fail": "brew install gh"}
        return CheckResult(self._status, f"status is {self._status}", hints.get(self._status))

    def skill_source(self) -> Path:
        return self._skill_path


def use_stub(monkeypatch, tmp_path, status="ok"):
    """Point the CLI at a stub channel and an isolated home/cwd under tmp_path."""
    skill = tmp_path / "SKILL.md"
    skill.write_text("---\nname: github\n---\n\n# GitHub skill\n", encoding="utf-8")
    stub = StubChannel(status=status, skill_path=skill)
    monkeypatch.setattr(registry, "CHANNELS", {"github": stub})
    home = tmp_path / "home"
    cwd = tmp_path / "proj"
    home.mkdir(exist_ok=True)
    cwd.mkdir(exist_ok=True)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(Path, "cwd", classmethod(lambda cls: cwd))
    return home, cwd


def test_list_shows_channels_and_agents(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    for expected in ["github", "claude-code", "cursor", "windsurf", "generic", "opt-in"]:
        assert expected in result.output


def test_doctor_ok_exit_zero(monkeypatch, tmp_path):
    home, _ = use_stub(monkeypatch, tmp_path, status="ok")
    (home / ".claude").mkdir()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "[ok] github" in result.output
    assert "claude-code" in result.output


def test_doctor_warn_exit_one(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path, status="warn")
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "[!] github" in result.output
    assert "gh auth login" in result.output


def test_doctor_fail_exit_two(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path, status="fail")
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 2
    assert "[x] github" in result.output


def test_install_into_detected_agents(monkeypatch, tmp_path):
    home, cwd = use_stub(monkeypatch, tmp_path, status="ok")
    (home / ".claude").mkdir()
    (cwd / ".cursor").mkdir()
    result = runner.invoke(app, ["install", "github"])
    assert result.exit_code == 0
    assert (home / ".claude" / "skills" / "github" / "SKILL.md").is_file()
    assert (cwd / ".cursor" / "rules" / "github.mdc").is_file()
    # windsurf not detected -> not installed
    assert not (cwd / ".windsurf").exists()
    # manifest recorded under home
    assert (home / ".agent-equip" / "manifest.json").is_file()
    assert "installed" in result.output


def test_install_unknown_channel_exits_two(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["install", "nope"])
    assert result.exit_code == 2
    assert "unknown channel" in result.output


def test_install_fail_status_prints_hint_and_exits_two(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path, status="fail")
    result = runner.invoke(app, ["install", "github"])
    assert result.exit_code == 2
    assert "brew install gh" in result.output


def test_install_warn_status_still_installs(monkeypatch, tmp_path):
    home, _ = use_stub(monkeypatch, tmp_path, status="warn")
    (home / ".claude").mkdir()
    result = runner.invoke(app, ["install", "github"])
    assert result.exit_code == 0
    assert (home / ".claude" / "skills" / "github" / "SKILL.md").is_file()
    assert "gh auth login" in result.output


def test_install_no_agents_detected_exits_one(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["install", "github"])
    assert result.exit_code == 1
    assert "No agents detected" in result.output


def test_install_specific_agent_generic(monkeypatch, tmp_path):
    _, cwd = use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["install", "github", "--agent", "generic"])
    assert result.exit_code == 0
    assert (cwd / "AGENTS.md").is_file()


def test_install_specific_agent_unknown_exits_two(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)
    result = runner.invoke(app, ["install", "github", "--agent", "nope"])
    assert result.exit_code == 2
    assert "unknown agent" in result.output


def test_install_specific_agent_undetected_exits_two(monkeypatch, tmp_path):
    use_stub(monkeypatch, tmp_path)  # no .claude dir created
    result = runner.invoke(app, ["install", "github", "--agent", "claude-code"])
    assert result.exit_code == 2
    assert "not detected" in result.output
