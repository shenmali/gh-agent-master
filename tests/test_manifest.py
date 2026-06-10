from agent_equip import manifest
from agent_equip.manifest import ManifestEntry


def test_load_returns_empty_when_no_manifest(tmp_path):
    assert manifest.load(root=tmp_path) == []


def test_record_and_load_roundtrip(tmp_path):
    entry = ManifestEntry(agent="claude-code", channel="github", path="/x/SKILL.md")
    manifest.record(entry, root=tmp_path)
    assert manifest.load(root=tmp_path) == [entry]
    assert (tmp_path / ".agent-equip" / "manifest.json").is_file()


def test_record_deduplicates(tmp_path):
    entry = ManifestEntry(agent="cursor", channel="github", path="/y/github.mdc")
    manifest.record(entry, root=tmp_path)
    manifest.record(entry, root=tmp_path)
    assert manifest.load(root=tmp_path) == [entry]


def test_clear_removes_manifest_and_empty_dir(tmp_path):
    manifest.record(
        ManifestEntry(agent="a", channel="c", path="/p"), root=tmp_path
    )
    manifest.clear(root=tmp_path)
    assert not (tmp_path / ".agent-equip").exists()
    assert manifest.load(root=tmp_path) == []
