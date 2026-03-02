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

- 🏗️ **Scaffold** new skills from a standard template
- ✅ **Validate** skills against the AgentZero SKILL.md standard
- 📦 **Build** distributable skill packages
- 🚀 **Publish** skills to the ZeroForge marketplace
- 🧪 **Test** skill behaviour before release

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
# Create a new skill
zforge new my-skill

# Validate your skill
zforge validate --skill my-skill/

# Build a distributable package
zforge build --skill my-skill/

# Publish to ZeroForge marketplace
zforge publish my-skill/
```

## Commands

| Command | Description |
|---------|-------------|
| `zforge new <name>` | Scaffold a new skill from template |
| `zforge validate --skill <dir>` | Validate skill against SKILL.md standard |
| `zforge build --skill <dir>` | Build a `.zip` skill package |
| `zforge publish <dir>` | Publish skill to ZeroForge marketplace |
| `zforge test <dir>` | Run skill tests |
| `zforge hello` | Verify installation and show usage |

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
