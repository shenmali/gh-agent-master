import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_equip.channels.base import Channel, CheckResult
from agent_equip.channels.github import GitHubChannel, gh_install_hint


def test_check_result_defaults():
    res = CheckResult(status="ok", message="all good")
    assert res.status == "ok"
    assert res.message == "all good"
    assert res.fix_hint is None


def test_check_result_with_fix_hint():
    res = CheckResult(status="fail", message="gh missing", fix_hint="brew install gh")
    assert res.fix_hint == "brew install gh"


def test_channel_is_abstract():
    with pytest.raises(TypeError):
        Channel()  # type: ignore[abstract]


def test_channel_subclass_contract(tmp_path):
    class Dummy(Channel):
        name = "dummy"
        description = "a dummy channel"

        def check(self):
            return CheckResult("ok", "fine")

        def skill_source(self):
            return tmp_path / "SKILL.md"

    ch = Dummy()
    assert ch.name == "dummy"
    assert ch.check().status == "ok"
    assert ch.skill_source().name == "SKILL.md"


def test_github_check_fail_when_gh_missing(monkeypatch):
    monkeypatch.setattr("agent_equip.channels.github.shutil.which", lambda _: None)
    res = GitHubChannel().check()
    assert res.status == "fail"
    assert res.fix_hint == gh_install_hint()


def test_github_check_ok_when_authenticated(monkeypatch):
    monkeypatch.setattr("agent_equip.channels.github.shutil.which", lambda _: "/usr/bin/gh")
    monkeypatch.setattr(
        "agent_equip.channels.github.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=0),
    )
    res = GitHubChannel().check()
    assert res.status == "ok"


def test_github_check_warn_when_not_authenticated(monkeypatch):
    monkeypatch.setattr("agent_equip.channels.github.shutil.which", lambda _: "/usr/bin/gh")
    monkeypatch.setattr(
        "agent_equip.channels.github.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=1),
    )
    res = GitHubChannel().check()
    assert res.status == "warn"
    assert "gh auth login" in (res.fix_hint or "")


def test_github_check_warn_on_timeout(monkeypatch):
    def boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="gh", timeout=5)

    monkeypatch.setattr("agent_equip.channels.github.shutil.which", lambda _: "/usr/bin/gh")
    monkeypatch.setattr("agent_equip.channels.github.subprocess.run", boom)
    res = GitHubChannel().check()
    assert res.status == "warn"


def test_github_skill_source_exists():
    src = GitHubChannel().skill_source()
    assert src.is_file()
    assert src.name == "SKILL.md"
    assert "gh " in src.read_text(encoding="utf-8")


def test_channel_subclass_requires_name_and_description():
    with pytest.raises(TypeError, match="name"):

        class NoName(Channel):  # noqa: F811 - intentionally incomplete
            description = "missing name"

            def check(self):
                return CheckResult("ok", "fine")

            def skill_source(self):
                return Path("x")


def test_github_check_warn_on_oserror(monkeypatch):
    def boom(*a, **k):
        raise OSError("permission denied")

    monkeypatch.setattr("agent_equip.channels.github.shutil.which", lambda _: "/usr/bin/gh")
    monkeypatch.setattr("agent_equip.channels.github.subprocess.run", boom)
    res = GitHubChannel().check()
    assert res.status == "warn"
