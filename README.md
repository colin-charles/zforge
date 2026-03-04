# zforge

> The official CLI for building, validating, and publishing AgentZero skills to the [ZeroForge](https://zero-forge.org) marketplace.

```
███████╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗
╚══███╔╝██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
  ███╔╝ █████╗  ██║   ██║██████╔╝██║  ███╗█████╗
 ███╔╝  ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
███████╗██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
```

## What is zforge?

`zforge` is a command-line tool for AgentZero skill developers. It helps you:

- 🔐 **Authenticate** via GitHub — one-time browser login
- 🏗️ **Scaffold** new skills from a standard template
- ✅ **Validate** skills against the AgentZero SKILL.md standard
- 📦 **Build** distributable skill packages
- 🚀 **Publish** skills to the ZeroForge marketplace with verified attribution
- 🧪 **Test** skill behaviour before release


## Trust & Safety

`zforge` is fully **open source** (MIT licensed). Every line of code is publicly auditable:

👉 **Source:** [github.com/colin-charles/zforge](https://github.com/colin-charles/zforge)  
👉 **Author:** colin-charles — [hello@zero-forge.org](mailto:hello@zero-forge.org)  
👉 **PyPI:** [pypi.org/project/zforge](https://pypi.org/project/zforge/)

- No telemetry or analytics collected
- API key stored locally in `~/.zforge/config.json` (never transmitted except to ZeroForge's own API)
- All marketplace interactions go through ZeroForge's public API
- Dependencies: `typer` and `rich` only — both widely trusted open-source libraries

## Installation

```bash
pip install zforge
```

Or use the one-liner:

```bash
curl -fsSL https://zero-forge.org/install.sh | bash
```

## Quick Start

```bash
# 1. Authenticate with GitHub (one-time setup)
zforge login

# 2. Create a new skill
zforge new my-skill

# 3. Validate your skill
zforge validate my-skill/

# 4. Build a distributable package
zforge build my-skill/

# 5. Publish to ZeroForge marketplace
zforge publish my-skill/
```

## Commands

| Command | Description |
|---------|-------------|
| `zforge login` | Authenticate via GitHub (browser OAuth) |
| `zforge login --manual` | Authenticate by pasting API key manually |
| `zforge whoami` | Show currently authenticated user |
| `zforge new <name>` | Scaffold a new skill from template |
| `zforge validate <dir>` | Validate skill against SKILL.md standard |
| `zforge build <dir>` | Build a `.zip` skill package |
| `zforge publish <dir>` | Publish skill to ZeroForge marketplace |
| `zforge test <dir>` | Run skill tests |
| `zforge hello` | Verify installation and show usage |

## Authentication

`zforge login` authenticates you via GitHub OAuth — no copy-paste required:

```bash
$ zforge login

  Opening browser for GitHub authentication...
  Waiting for callback on http://localhost:7391...

  [browser opens → click Authorize on GitHub]

  ✔  Authenticated as @your-handle
  ✔  API key saved to ~/.zforge/config.json
```

**Prefer manual setup?** Use the `--manual` flag:

```bash
zforge login --manual
# Prompts you to paste your API key from zero-forge.org/profile/edit/
```

**Check who you're logged in as:**

```bash
$ zforge whoami
  Logged in as @your-handle
```

**For CI/CD or agent environments**, set the env var instead:

```bash
export ZFORGE_API_KEY=your-api-key
zforge publish my-skill/
```

> Authentication is required before publishing. Skills published without a valid API key will be rejected.

## How Certification Works

When you run `zforge publish`, the CLI automatically evaluates your skill quality using the **APOL pipeline** — an LLM-based judge that scores your `SKILL.md` across four dimensions:

| KPI | What is checked | Weight |
|-----|----------------|--------|
| Task Specificity | Are tasks described with precise, actionable detail? | High |
| Example Quality | Are examples concrete, realistic, and complete? | High |
| Scope Accuracy | Does the skill do what it says — no more, no less? | Medium |
| Submission Ready | Is the skill ready for production use? | Gate |

### The publish flow

```
zforge publish my-skill/
  │
  ├── Auth check (API key required)
  │
  ├── Structural validation (required fields/sections)
  │
  ├── APOL quality scoring
  │     └── Score ≥ 0.80  →  CERTIFIED badge ✅  published immediately
  │
  └── Score < 0.80  →  You choose:

        A) Publish now as UNCERTIFIED
        B) Run APOL improvement pipeline

             B → LLM refines documentation (intent preserved)
               → Shows diff before overwriting
               → You confirm [Y/N]
               → Score ≥ 0.80 → CERTIFIED ✅
```

> **Your intent is always protected.** The APOL pipeline only improves *how* your skill is documented — never *what* it does. You review every change before it is saved.

### What CERTIFIED means

A **CERTIFIED** badge means the skill was independently scored at ≥ 0.80 by the APOL LLM judge. It is a quality signal, not just a compliance check.

An **UNCERTIFIED** skill is structurally valid and usable — it just hasn't passed the quality threshold yet.

## Using as an AgentZero Skill

`zforge` ships as an installable AgentZero skill. To install it inside Agent Zero:

```
Install the zforge skill from zero-forge.org/start
```

See [SKILL.md](./SKILL.md) for the full Agent Zero skill instructions.

## Requirements

- Python 3.10+
- `typer >= 0.9.0`
- `rich >= 13.0.0`

## Contributing

PRs welcome. Please validate your changes with `zforge validate` before submitting.

## License

MIT — see [LICENSE](./LICENSE)

## Links

- 🌐 Marketplace: [zero-forge.org](https://zero-forge.org)
- 💬 Community: [zero-forge.org/zeroden](https://zero-forge.org/zeroden)
- 🚀 Get Started: [zero-forge.org/start](https://zero-forge.org/start)
