## [1.0.3] - 2026-03-02

## [2.0.0] - 2026-03-02
### Added
- Self-update checker: zforge now notifies you when a newer version is available on PyPI
- Runs silently in background thread — never blocks your command
- Shows upgrade prompt: ⚡ zforge v2.0.0 → vX.X.X available! Run: pip install --upgrade zforge

### Fixed
- VERSION constant in main.py synced with pyproject.toml (was mismatched)

## [1.0.9] - 2026-03-02
### Fixed
- `zforge publish` no longer requires SUPABASE_URL or SUPABASE_ANON_KEY env vars
- publisher.py now falls back to hardcoded public credentials (same pattern as main.py)
- Creators can run `zforge publish` out of the box with no environment configuration
- Service key (SUPABASE_SERVICE_KEY) remains env-only — it is admin-only and never embedded


## [1.0.8] - 2026-03-02
### Fixed
- `zforge validate` now checks the correct **nested** `skill.json` structure (`metadata.*` and `description.*` blocks) — previous validator checked non-existent top-level fields
- Added `description.short` length constraint: must be <=120 chars (matches publisher.py)
- Added `description.description_for_agent` word count constraint: must be >=10 words (matches publisher.py)
- Added `metadata.category` validity check against known categories
- Added `description.long` warning when missing
- Validate now catches all errors that `zforge publish` would reject — no more surprises at publish time

## [1.0.7] - 2026-03-02

### Fixed
- `zforge validate <name>` now accepts skill name/path as a **positional argument** — no more `--skill` flag required
- Validator is now fully **self-contained** — no longer depends on missing external `04_validate_skill.py` script
- Validator runs inline checks: SKILL.md, skill.json required fields, required sections, and optional recommendations

### Improved
- Clear ✅ / ⚠️ / ❌ output with pass/fail summary
- Handles skill name resolution (looks up `./skill_name/` relative to cwd)

### Fixed
- publisher.py now includes `apol_certified` and `apol_cert` fields in Supabase payload so certified skills display the ZFORGE VERIFIED badge on the marketplace
## [1.0.5] - 2026-03-02
### Changed
- Added comprehensive PyPI metadata: author, homepage, repository, classifiers, keywords
- Improved package discoverability and legitimacy signals on PyPI
- README: clarified pip install as primary installation method


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
