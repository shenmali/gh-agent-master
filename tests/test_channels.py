import pytest

from agent_equip.channels.base import Channel, CheckResult


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
