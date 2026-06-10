# Changelog

## 0.1.0 — 2026-06-10

Initial release.

- `install github`: checks the gh CLI, detects agents, installs the GitHub skill.
- Adapters: Claude Code (global), Cursor (project), Windsurf (project), generic AGENTS.md block (opt-in).
- `doctor` read-only health report with meaningful exit codes.
- `uninstall` driven by an install manifest — removes exactly what was installed.
- Safe by default: system commands are printed, not run, unless `--auto`.
