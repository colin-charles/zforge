# SkillTest — [skill_name]
version: 1.0
author: [handle]

<!--
  SkillTest.md — ZeroForge Declarative Test Format v1.0
  =====================================================
  Each test is a markdown H3 section (### test_name) with
  bullet-list key-value pairs parsed by test_runner.py.

  Supported test types:
  ─────────────────────
  shell         Run a shell command; check exit code and/or stdout.
  apol_metric   Run programmatic_metric() on a .md file; check score.
  file_exists   Assert one or more files exist relative to skill root.
  python_import Try importing a Python module; assert no ImportError.

  Field reference by type:
  ─────────────────────────────────────────────────────────────────────
  ALL TYPES
    - type: <shell|apol_metric|file_exists|python_import>  (required)
    - timeout: <seconds>    (optional, default 30 — applies to shell)

  shell
    - command: <shell command string>              (required)
    - expect_exit: <int>                           (optional, default 0)
    - expect_output_contains: "<substring>"        (optional)
    - expect_output_not_contains: "<substring>"    (optional)
    - working_dir: <relative path from skill root> (optional, default: skill root)

  apol_metric
    - file: <relative path to .md file>  (required)
    - expect_score_gte: <float 0.0–1.0>  (required)

  file_exists
    - files:           (required — YAML list, one path per line)
      - path/to/file
      - another/file

  python_import
    - module: <importable module name>  (required)
-->

## Tests

### test_install
- type: shell
- command: bash install.sh
- expect_exit: 0
- expect_output_contains: "complete"
- timeout: 60

### test_apol_metric
- type: apol_metric
- file: SKILL.md
- expect_score_gte: 0.70

### test_script_runs
- type: shell
- command: python scripts/main.py --help
- expect_exit: 0
- timeout: 30

### test_required_files
- type: file_exists
- files:
  - SKILL.md
  - install.sh
  - requirements.txt

### test_python_import
- type: python_import
- module: requests
