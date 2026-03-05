# ⚒️ zforge — The CLI for AgentZero Skills

**Build, test, certify, and publish skills for [AgentZero](https://github.com/frdel/agent-zero) — all from your terminal.**

[![PyPI](https://img.shields.io/pypi/v/zforge?color=amber&label=PyPI)](https://pypi.org/project/zforge/)
[![Python](https://img.shields.io/pypi/pyversions/zforge)](https://pypi.org/project/zforge/)
[![License](https://img.shields.io/github/license/colin-charles/zforge)](LICENSE)

---

## 🚀 Install

```bash
pip install zforge
```

## ✨ What It Does

zforge is the official CLI for the [ZeroForge Marketplace](https://zero-forge.org) — the open marketplace for AgentZero skills, scripts, and templates.

| Feature | Description |
|---------|-------------|
| **Scaffold** | Generate a skill project with proper structure in seconds |
| **Build** | Package your skill into a distributable `.zip` archive |
| **Validate** | Check your skill meets the SKILL.md standard before publishing |
| **Test** | Run your skill's test suite locally |
| **Certify** | Get automated APOL quality scoring (7-model consensus) |
| **Publish** | Ship directly to the ZeroForge Marketplace |
| **Login** | One-command GitHub OAuth — no tokens to copy-paste |

## 📦 Quick Start

```bash
# 1. Install
pip install zforge

# 2. Authenticate with GitHub
zforge login

# 3. Create a new skill
zforge new my-awesome-skill
cd my-awesome-skill

# 4. Edit SKILL.md with your skill's instructions

# 5. Validate, build, publish
zforge validate
zforge build
zforge publish
```

## 🔧 All Commands

| Command | Description |
|---------|-------------|
| `zforge new <name>` | Scaffold a new skill project |
| `zforge build` | Package skill into `.zip` |
| `zforge validate` | Check SKILL.md structure and required fields |
| `zforge test` | Run skill tests |
| `zforge publish` | Build, validate, certify, and publish to marketplace |
| `zforge login` | Authenticate via GitHub OAuth (browser-based) |
| `zforge login --token <key>` | Authenticate with an API key |
| `zforge whoami` | Show current authenticated user |
| `zforge logout` | Clear stored credentials |
| `zforge report` | Submit a bug report (opens GitHub Issue) |
| `zforge version` | Show CLI version |

## 🏪 ZeroForge Marketplace

**[zero-forge.org](https://zero-forge.org)** — Browse, discover, and install community skills.

Every published skill goes through **APOL certification** — an automated quality assessment using 7-model AI consensus scoring across documentation, structure, security, and usefulness.

## 🤖 For AgentZero Agents

zforge is designed to be used by both humans and AI agents. Agents can:

```bash
# Authenticate non-interactively
zforge login --token $ZFORGE_API_KEY

# Build and publish skills autonomously
zforge publish
```

See the [install-zforge](https://zero-forge.org/listing/?slug=install-zforge) skill for agent setup instructions.

## 📄 License

MIT — see [LICENSE](LICENSE)

## 🔗 Links

- **Marketplace:** [zero-forge.org](https://zero-forge.org)
- **Changelog:** [zero-forge.org/changelog](https://zero-forge.org/changelog/)
- **Issues:** [GitHub Issues](https://github.com/colin-charles/zforge/issues)
- **Community:** [ZeroDen Discord](https://zero-forge.org/zeroden/)
