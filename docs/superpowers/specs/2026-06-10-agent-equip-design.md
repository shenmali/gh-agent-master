# agent-equip — Design Spec

**Date:** 2026-06-10
**Status:** Approved (pending user review of this document)
**Repo:** github.com/shenmali/agent-equip (public, MIT)

## One-liner

Set up GitHub superpowers for any AI coding agent in one command.

## Purpose

`agent-equip` is an installer CLI that makes an AI coding agent (Claude Code, Cursor, Windsurf, others) ready to work with GitHub:

1. Checks that the official `gh` CLI is installed and authenticated; guides the user through fixing gaps.
2. Installs a GitHub usage skill (SKILL.md) into each detected agent's skill/rules directory, so the agent knows which `gh` commands to run for which user request.
3. Reports channel and agent status via a read-only `doctor` command.
4. Gets out of the way: after setup, the agent calls `gh` directly. agent-equip is scaffolding, not a wrapper.

**Project goals:** portfolio piece, community tool (easy install, English docs), learning project. Not primarily for the author's daily use.

## Non-goals (v1)

- No channels other than GitHub (architecture is ready for more; none ship in v1).
- No MCP server, no API wrapper commands, no proxy/cookie infrastructure.
- No credential storage of any kind — auth lives entirely in `gh`'s own secure store.
- No auto-update mechanism, no config file. The only state is the install manifest.

## Architecture: two pluggable axes

Every feature is one file. Two extension axes:

- **Channels** (`channels/`) — platforms an agent can be equipped for. v1 ships `github.py` only.
- **Agent adapters** (`agents/`) — coding agents that can receive skills. v1 ships `claude_code.py`, `cursor.py`, `windsurf.py`, `generic.py`.

Registration is an explicit list in `registry.py` — no entry-point magic, no dynamic discovery.

```
agent-equip/
├── pyproject.toml              # packaging; console script: agent-equip
├── README.md                   # English; quickstart, agent table, security posture
├── LICENSE                     # MIT — Copyright (c) 2026 shenmali (or real name; decided at implementation)
├── CHANGELOG.md
├── .github/workflows/ci.yml    # lint + test matrix
├── src/agent_equip/
│   ├── __init__.py             # __version__
│   ├── cli.py                  # Typer app: install / doctor / uninstall / list
│   ├── registry.py             # CHANNELS = [...], AGENTS = [...]
│   ├── manifest.py             # read/write ~/.agent-equip/manifest.json
│   ├── channels/
│   │   ├── base.py             # Channel interface, CheckResult
│   │   └── github.py
│   ├── agents/
│   │   ├── base.py             # AgentAdapter interface, InstallResult
│   │   ├── claude_code.py      # global scope → ~/.claude/skills/github/SKILL.md
│   │   ├── cursor.py           # project scope → <cwd>/.cursor/rules/github.mdc
│   │   ├── windsurf.py         # project scope → <cwd>/.windsurf/rules/github.md
│   │   └── generic.py          # opt-in only → appends marked block to <cwd>/AGENTS.md
│   └── skills/
│       └── github/SKILL.md     # the content delivered to agents
└── tests/
    ├── test_channels.py
    ├── test_agents.py
    ├── test_manifest.py
    └── test_cli.py
```

## Interfaces

```python
@dataclass
class CheckResult:
    status: Literal["ok", "warn", "fail"]
    message: str
    fix_hint: str | None = None

class Channel(ABC):
    name: str                          # "github"
    description: str
    def check(self) -> CheckResult: ...
    def skill_source(self) -> Path:    # path to bundled SKILL.md

@dataclass
class InstallResult:
    agent: str
    path: Path
    action: Literal["installed", "updated", "skipped"]

class AgentAdapter(ABC):
    name: str                          # "claude-code"
    scope: Literal["global", "project"]  # where skills land: home dir vs. cwd
    def detect(self) -> bool: ...      # is this agent present on the machine / in this project?
    def install_skill(self, channel: Channel) -> InstallResult: ...
    def uninstall_skill(self, channel: Channel) -> None: ...
```

**Scope semantics:** `global` adapters (Claude Code) detect against the home directory and install once per machine. `project` adapters (Cursor, Windsurf) detect against the current working directory (`.cursor/` or `.windsurf/` exists) and install into that project. `generic` is never auto-selected — it runs only with an explicit `--agent generic`, because implicitly appending to a project's AGENTS.md would be surprising.

Adding a channel touches `channels/<new>.py` + `skills/<new>/SKILL.md` + one registry line. Adding an agent touches `agents/<new>.py` + one registry line. Nothing else.

## CLI commands

| Command | Behavior |
|---|---|
| `agent-equip install github` | Full flow below |
| `agent-equip install github --agent cursor` | Limit to one adapter (error if its `detect()` fails) |
| `agent-equip install github --auto` | Allow running system package commands (default: print them only) |
| `agent-equip doctor` | Read-only status: channel checks, detected agents, installed skills. Exit code 0=ok, 1=warn, 2=fail |
| `agent-equip list` | Available channels and supported agents |
| `agent-equip uninstall` | Remove everything listed in the manifest, then the manifest itself |

### `install github` flow

1. **Channel check:** Is `gh` on PATH? If not, print the OS-appropriate install command (brew / apt / winget). Never run it unless `--auto`.
2. **Auth check:** `gh auth status`. If unauthenticated, print instructions for `gh auth login` (interactive; left to the user).
3. **Agent detection:** Run every adapter's `detect()` (e.g. `~/.claude` exists). Install the skill to each detected agent.
4. **Manifest:** Record every written path in `~/.agent-equip/manifest.json` so `uninstall` is surgical.
5. **Summary table** + a suggested first prompt for the agent.

Install is idempotent: re-running updates skills in place (`action: "updated"`).

## Security posture (stated in README)

- **Zero credentials stored.** Auth is `gh`'s job; agent-equip never sees or writes tokens or cookies.
- **Safe by default.** System-modifying commands are printed, not executed, unless `--auto` is passed. (Inverse of Agent-Reach's default.)
- `doctor` is strictly read-only.
- Only writes: skill files in agent directories + the manifest. `uninstall` removes exactly those.

## GitHub SKILL.md content

English, recipe-style ("when the user asks X, run Y"), covering: repo view/clone/search, code search, issues (list/view/create/comment), PRs (list/view/diff/checkout/review/create), releases, `gh api` for anything else, rate-limit awareness, auth troubleshooting. Frontmatter compatible with Claude Code skill format; adapters may transform format (e.g. `.mdc` for Cursor) but reuse the same body.

## Error handling

- All external commands run via `subprocess.run` with a 5s timeout; failures become `CheckResult("fail"|"warn", ...)`, never uncaught exceptions. `doctor` must not crash on unknown environments — degrade to `warn` with a hint.
- Missing agent directory → adapter `detect()` returns False → silently skipped (explicit error only with `--agent`).
- `generic.py` writes a marked block (`<!-- agent-equip:github:start -->` … `end -->`) into `AGENTS.md` so updates and uninstalls are idempotent and never touch user content.

## Testing & CI

- TDD with pytest. Adapters tested against `tmp_path` fake home dirs (never the real `~/.claude`); `gh` calls mocked for three scenarios: missing, unauthenticated, authenticated.
- CLI tested end-to-end with Typer's `CliRunner`.
- GitHub Actions: Ubuntu + macOS + Windows × Python 3.10–3.12, ruff + pytest. Windows path handling is the expected breakage point; the matrix exists to catch it.

## Publishing plan

1. Public repo `shenmali/agent-equip`, MIT with the author's copyright.
2. English README: value proposition, 30-second quickstart (`pipx install agent-equip && agent-equip install github`), supported-agents table, security posture, contributing guide ("how to add a channel/agent").
3. Attribution line at the bottom of README: *"Architecture philosophy inspired by [Agent-Reach](https://github.com/Panniantong/Agent-Reach); all code written from scratch."*
4. Install via `pipx install git+https://github.com/shenmali/agent-equip` at launch; PyPI release is a separate later step.

## Risks / honest positioning

- The real workhorse is `gh` (GitHub's official CLI). agent-equip's value is the setup automation, the skill content, and the multi-agent adapter layer — the README says this plainly rather than overclaiming.
- Agent rule-directory conventions (Cursor/Windsurf) change over time; adapters are one file each precisely so breakage is cheap to fix.
