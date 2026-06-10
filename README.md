# agent-equip

**Set up GitHub superpowers for any AI coding agent in one command.**

Your AI coding agent (Claude Code, Cursor, Windsurf, ...) can write code — but does it know how to *work GitHub*? `agent-equip` makes sure it does:

1. Checks that the official [`gh` CLI](https://cli.github.com) is installed and authenticated — and tells you exactly how to fix it if not.
2. Installs a battle-ready GitHub skill into every agent it detects on your machine, teaching the agent which `gh` command answers which request.
3. Gets out of the way. After setup your agent talks to GitHub directly through `gh`. No wrapper, no middleman, no new API to learn.

```bash
pipx install git+https://github.com/shenmali/agent-equip
agent-equip install github
```

Then ask your agent things like:

> *"What are the open issues in vercel/next.js?"*
> *"Summarize the diff of PR #42 in our repo."*
> *"Find popular Rust vector databases on GitHub."*

## Supported agents

| Agent | Scope | Skill location |
|---|---|---|
| Claude Code | global | `~/.claude/skills/github/SKILL.md` |
| Cursor | project | `.cursor/rules/github.mdc` |
| Windsurf | project | `.windsurf/rules/github.md` |
| Generic (any agent reading AGENTS.md) | project, opt-in | marked block in `AGENTS.md` |

Project-scoped agents are detected per project: run `agent-equip install github` inside the project. The generic adapter only runs when you explicitly ask: `--agent generic`.

## Commands

| Command | What it does |
|---|---|
| `agent-equip install github` | Check `gh`, detect agents, install the skill |
| `agent-equip install github --agent cursor` | Target a single agent |
| `agent-equip install github --auto` | Also *run* system install commands instead of printing them |
| `agent-equip doctor` | Read-only health report (exit code 0/1/2 = ok/warn/fail) |
| `agent-equip list` | Show channels and agents |
| `agent-equip uninstall` | Remove everything agent-equip installed — exactly that, nothing else |

## Security posture

- **Zero credentials stored.** Authentication is handled entirely by `gh`'s own secure store. agent-equip never sees, stores, or transmits a token.
- **Safe by default.** agent-equip never runs system-modifying commands unless you pass `--auto`. Without it, commands are printed for you to review and run.
- **Surgical uninstall.** Every file written is recorded in `~/.agent-equip/manifest.json`; `uninstall` removes exactly those and nothing else.
- `doctor` is strictly read-only.

## Architecture

Two pluggable axes — every feature is one file:

```
src/agent_equip/
├── channels/        # platforms (v1: github)
│   └── github.py    # health check for the gh CLI
├── agents/          # adapters (claude-code, cursor, windsurf, generic)
└── skills/
    └── github/SKILL.md   # the content agents receive
```

Adding a channel = one file in `channels/` + a `SKILL.md` + one registry line.
Adding an agent = one file in `agents/` + one registry line.

## Contributing

PRs welcome — especially new agent adapters and channels. Each one is a single file with a small interface (see `channels/base.py` and `agents/base.py`); copy an existing one, adjust, add tests.

## License

MIT.

*Architecture philosophy inspired by [Agent-Reach](https://github.com/Panniantong/Agent-Reach); all code written from scratch.*
