## [1.0.3] - 2026-03-02
### Fixed
- publisher.py now includes `apol_certified` and `apol_cert` fields in Supabase payload so certified skills display the ZFORGE VERIFIED badge on the marketplace

# Changelog

## [1.0.4] - 2026-03-02
### Fixed
- `zforge list`, `zforge search`, `zforge install` now work without any setup
- Public Supabase anon key bundled into CLI (read-only, safe to ship)
- Removed "must be set" credential error for read-only marketplace commands
- Only `zforge publish` requires credentials (GitHub OAuth, unchanged)


## [1.0.1] - 2026-03-02

### Fixed
- Corrected SKILL.md install paths to use `~/.zforge` instead of hardcoded `/a0/usr/workdir/ZeroForge`
- Updated install.sh to clone from `colin-charles/zforge` (new standalone CLI repo)
- Fixed all internal repo URL references from `zeroforge` to `zforge`
- Improved install.sh with better UX and idempotent install check

## [1.0.0] - 2026-03-02

### Added
- `zforge new` — scaffold new skills from template
- `zforge validate` — validate skills against SKILL.md standard
- `zforge build` — build distributable skill packages
- `zforge publish` — publish skills to ZeroForge marketplace
- `zforge test` — run skill tests
- `zforge hello` — verify installation
- AgentZero SKILL.md for use as an installable agent skill
- One-liner install script (`install.sh`)
