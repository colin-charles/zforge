import re
"""zforge -- ZeroForge Skill Development CLI."""
import sys
import threading
import urllib.request
import urllib.error
import json as _json
from pathlib import Path
from typing import Optional

import typer

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

app = typer.Typer(
    name="zforge",
    help="ZeroForge Skill Development CLI -- build, test, validate, and publish skills.",
    add_completion=False,
    rich_markup_mode="rich" if HAS_RICH else None,
)

try:
    from importlib.metadata import version as _pkg_version
    VERSION = _pkg_version("zforge")
except Exception:
    VERSION = "2.1.12"  # fallback only

def _check_for_update() -> bool:
    """Check PyPI for a newer version — synchronous. Returns True if upgraded."""
    import subprocess, time, pathlib, os
    try:
        # --- 5-min cooldown via cache file ---
        _cache = pathlib.Path.home() / ".zforge_update_check"
        now = time.time()
        if _cache.exists() and (now - _cache.stat().st_mtime) < 60:
            return False  # checked recently, skip
        _cache.touch()  # update timestamp before network call

        def _ver(v): return tuple(int(x) for x in v.split("."))

        req = urllib.request.Request(
            "https://pypi.org/pypi/zforge/json",
            headers={"User-Agent": f"zforge/{VERSION}"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            latest = _json.loads(resp.read())["info"]["version"]

        if _ver(latest) <= _ver(VERSION):
            return False  # already on latest

        print(f"⚡ zforge v{VERSION} → v{latest} found. Auto-upgrading...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "zforge",
             "--quiet", "--disable-pip-version-check"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            # pip succeeded — restart immediately with new code.
            # Do NOT gate on importlib.metadata (it caches stale version in the
            # same process and causes os.execv to be skipped on some envs).
            print(f"✅ Upgraded to zforge v{latest} — restarting...\n")
            return True
        else:
            print(f"⚠️  Auto-upgrade failed. Run: pip install --upgrade zforge\n")
            return False
    except Exception:
        return False  # Never crash the CLI over an update check


def _run_update_check() -> None:
    """Run upgrade check synchronously BEFORE command dispatch.
    If a new version was installed, re-exec this process so the new code runs the command.
    """
    import os
    upgraded = _check_for_update()
    if upgraded:
        # Replace current process with fresh one running the new version
        os.execv(sys.executable, [sys.executable] + sys.argv)


# Public read-only Supabase credentials (anon key — safe to embed)
_PUBLIC_SUPABASE_URL  = "https://turwttpspnqmhszjwjgs.supabase.co"
_PUBLIC_SUPABASE_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR1cnd0dHBzcG5xbWhzemp3amdzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIyMDM3NzAsImV4cCI6MjA4Nzc3OTc3MH0.fBajcHIJZs1lYwfEJRtnHvZdjqZ2u7YGIuPnhyAg85g"


@app.callback(invoke_without_command=True)
def _main(ctx: typer.Context) -> None:
    """ZeroForge Skill Development CLI -- build, test, validate, and publish skills."""
    _run_update_check()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())

ASCII_ART = r"""
 ______           ___  __
|__  / ___ _ __ / _ \/ _| ___  _ __ __ _ ___
  / / / _ \ '__| | | | |_ / _ \| '__/ _` / _ \
 / /_|  __/ |  | |_| |  _| (_) | | | (_| |  __/
/____|\___|_|   \___/|_|  \___/|_|  \__, |\___|
                                      |___/
"""


@app.command()
def hello():
    """New here? Start with this — shows what to do next."""
    if HAS_RICH:
        from rich.padding import Padding
        console.print()
        console.print(Panel(
            f"[bold cyan]{ASCII_ART}[/bold cyan]",
            border_style="cyan",
            padding=(0, 2)
        ))
        console.print(Panel(
            "[bold green]✓ ZeroForge CLI is installed and working![/bold green]\n\n"
            "[bold]Here's what to do next:[/bold]\n\n"
            "  [bold cyan]STEP 1[/bold cyan]  Browse skills at [underline]https://zero-forge.org/listings/[/underline]\n"
            "  [bold cyan]STEP 2[/bold cyan]  Install a skill:     [yellow]zforge install install-zforge[/yellow]\n"
            "  [bold cyan]STEP 3[/bold cyan]  Run it:              [yellow]zforge run install-zforge[/yellow]\n\n"
            "  [bold cyan]FORGE[/bold cyan]   Build your own:      [yellow]zforge build my-skill-name[/yellow]\n\n"
            "[dim]Full guide -> https://zero-forge.org/start/[/dim]",
            title="[bold]// WELCOME TO ZEROFORGE[/bold]",
            border_style="green",
            padding=(1, 2)
        ))
        console.print()
    else:
        print()
        print(ASCII_ART)
        print("✓ ZeroForge CLI is installed and working!")
        print()
        print("What to do next:")
        print("  STEP 1  Browse skills:       https://zero-forge.org/listings/")
        print("  STEP 2  Install a skill:     zforge install install-zforge")
        print("  STEP 3  Run it:              zforge run install-zforge")
        print("  FORGE   Build your own:      zforge build my-skill-name")
        print()
        print("Full guide: https://zero-forge.org/start/")
        print()


@app.command()
def info():
    """Show ZeroForge CLI info, version, and available commands."""
    if HAS_RICH:
        commands_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        commands_table.add_column("Command", style="bold yellow")
        commands_table.add_column("Description")
        commands_table.add_row("zforge build <name>",     "🚀 Full pipeline: scaffold → APOL → validate → publish")
        commands_table.add_row("zforge new <name>",       "Scaffold a new skill directory")
        commands_table.add_row("zforge dev",              "Run APOL experiment pipeline")
        commands_table.add_row("zforge validate",         "Validate skill structure and quality")
        commands_table.add_row("zforge test",             "Run SkillTest.md test suite")
        commands_table.add_row("zforge publish",          "Package and publish to marketplace")
        commands_table.add_row("zforge list",             "Browse approved marketplace skills")
        commands_table.add_row("zforge search <query>",   "Search skills by keyword")
        commands_table.add_row("zforge install <slug>",   "Download & install a skill locally")
        commands_table.add_row("zforge hello",            "🆕 New here? Start with this")
        commands_table.add_row("zforge info",             "Show this info panel")

        panel_content = (
            f"[bold cyan]{ASCII_ART}[/bold cyan]"
            f"[bold]Version:[/bold] {VERSION}\n"
            f"[bold]Mission:[/bold] Build, test & publish quality skills for the AgentZero ecosystem\n\n"
        )
        console.print(Panel(panel_content, title="[bold magenta]ZeroForge[/]", border_style="magenta"))
        console.print(commands_table)
        console.print()
        console.print("[dim]Docs: https://zeroforge.dev  |  GitHub: github.com/colin-charles/zeroforge[/dim]")
    else:
        print(ASCII_ART)
        print(f"ZeroForge CLI v{VERSION}")
        print("Commands: new | dev | validate | test | publish | info")
        print("Docs: https://zeroforge.dev")


@app.command()
def new(
    skill_name: str = typer.Argument(..., help="Name of the new skill to scaffold"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Parent directory (default: cwd)"),
):
    """Scaffold a new skill directory with all boilerplate files."""
    from cli.scaffold import scaffold_skill, print_success
    out = Path(output_dir) if output_dir else None
    target = scaffold_skill(skill_name, out)
    print_success(skill_name, target)


@app.command()
def dev(
    goal: str = typer.Option("GOAL.md", "--goal", "-g", help="Path to GOAL.md"),
    cycles: int = typer.Option(3, "--cycles", "-c", help="Number of APOL cycles"),
    model: str = typer.Option("openrouter/anthropic/claude-sonnet-4-5", "--model", "-m", help="LLM model to use"),
    skill: Optional[str] = typer.Option(None, "--skill", "-s", help="Skill directory (default: cwd)"),
):
    """Run the APOL experiment pipeline to generate and refine SKILL.md."""
    from cli.runner import run_dev
    skill_dir = Path(skill).resolve() if skill else Path.cwd()
    exit_code = run_dev(goal=goal, cycles=cycles, model=model, skill_dir=skill_dir)
    raise typer.Exit(code=exit_code)


@app.command()
def validate(
    skill: str = typer.Argument(".", help="Skill name or path to validate (default: cwd)"),
):
    """Validate a skill directory against ZeroForge quality standards."""
    from cli.validator import run_validate
    # Accept skill name (looks up in cwd) or full path
    skill_path = Path(skill)
    if not skill_path.is_absolute() and not skill_path.is_dir():
        # Try treating it as a skill name relative to cwd
        candidate = Path.cwd() / skill
        if candidate.is_dir():
            skill_path = candidate
    exit_code = run_validate(skill_dir=skill_path.resolve())
    raise typer.Exit(code=exit_code)


@app.command()
def test(
    skill: str = typer.Option(".", "--skill", "-s", help="Skill directory to test (default: cwd)"),
):
    """Run SkillTest.md test suite against a skill directory."""
    from cli.tester import run_test
    exit_code = run_test(skill_dir=Path(skill).resolve())
    raise typer.Exit(code=exit_code)


@app.command()
def publish(
    skill_dir: Path = typer.Argument(Path("."), help="Skill directory to publish (default: cwd)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate and package only, do not submit to marketplace"),
):
    """Validate, package and publish skill to zero-forge.org marketplace."""
    from cli.publisher import publish_skill
    publish_skill(skill_dir, dry_run=dry_run)


@app.command()
def build(
    skill_name: str = typer.Argument(..., help="Name of the new skill (snake_case)"),
    desc: str = typer.Option(..., "--desc", "-d", help="What the skill does (1-2 sentences)"),
    author: str = typer.Option("colin-charles", "--author", "-a", help="Your ZeroForge handle"),
    tags: str = typer.Option("utilities", "--tags", "-t", help="Comma-separated tags e.g. pdf,text,web"),
    category: str = typer.Option("utilities", "--category", "-c", help="Skill category"),
    price: str = typer.Option("free", "--price", "-p", help="Price: free or USD amount e.g. 4.99"),
    cycles: int = typer.Option(2, "--cycles", help="APOL improvement cycles (2 recommended)"),
    model: str = typer.Option("openrouter/anthropic/claude-sonnet-4-5", "--model", "-m", help="LLM model"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Parent directory (default: cwd)"),
    publish: bool = typer.Option(False, "--publish", help="Auto-publish after build"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Package only, don't submit"),
):
    """🚀 Full automated pipeline: scaffold → GOAL.md → APOL → validate → test → publish."""
    from cli.builder import build as run_build
    tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    out = Path(output_dir).resolve() if output_dir else Path.cwd()
    run_build(
        skill_name=skill_name,
        description=desc,
        author=author,
        tags=tags_list,
        category=category,
        price=price,
        cycles=cycles,
        model=model,
        output_dir=out,
        publish=publish,
        dry_run=dry_run,
    )


@app.command(name="list")
def list_skills(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    limit: int = typer.Option(20, "--limit", "-n", help="Max results to show"),
):
    """Browse approved skills on the ZeroForge marketplace."""
    import json, urllib.request, urllib.parse, os
    supabase_url = (os.environ.get("SUPABASE_URL") or _PUBLIC_SUPABASE_URL).rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY") or _PUBLIC_SUPABASE_ANON

    params = f"status=eq.approved&order=created_at.desc&limit={limit}"
    if category:
        params += f"&category=eq.{category}"
    url = f"{supabase_url}/rest/v1/listings?select=id,title,description,creator_name,apol_certified,price,tags&{params}"
    req = urllib.request.Request(url, headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            listings = json.loads(resp.read())
    except Exception as e:
        print(f"ERROR fetching marketplace: {e}")
        raise typer.Exit(1)

    if not listings:
        print('No listings found. Be the first — run: zforge build <name> --desc "..."')
        return

    # Filter by tag client-side
    if tag:
        listings = [l for l in listings if tag.lower() in [t.lower() for t in (l.get("tags") or [])]]

    if HAS_RICH:
        table = Table(title=f"ZeroForge Marketplace ({len(listings)} skills)", box=box.ROUNDED, header_style="bold cyan")
        table.add_column("Slug", style="bold yellow", no_wrap=True)
        table.add_column("Title", style="white")
        table.add_column("Author", style="cyan")
        table.add_column("APOL", justify="right", style="green")
        table.add_column("Price", justify="right", style="magenta")
        table.add_column("Tags", style="dim")
        for l in listings:
            score = "APOL✓" if l.get('apol_certified') else "—"
            tags_str = ", ".join((l.get("tags") or [])[:3])
            price = l.get("price") or "free"
            table.add_row(
                l.get("id", "-")[:8] + "...",
                l.get("title", "-"),
                l.get("creator_name", "-"),
                score,
                price,
                tags_str
            )
        console.print(table)
        console.print("\n[dim]Install any skill: [bold]zforge install <title>[/bold][/dim]")
    else:
        print(f"{'Slug':<30} {'Author':<20} {'APOL':<8} {'Price':<8}")
        print("-" * 70)
        for l in listings:
            score = "APOL✓" if l.get('apol_certified') else "—"
            print(f"{l.get('title',''):<30} {l.get('creator_name',''):<20} {score:<8} {l.get('price','free'):<8}")
        print("\nInstall: zforge install <slug>")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search term — matches title, description, or tags"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
):
    """Search the ZeroForge marketplace by keyword."""
    import json, urllib.request, urllib.parse, os
    supabase_url = (os.environ.get("SUPABASE_URL") or _PUBLIC_SUPABASE_URL).rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY") or _PUBLIC_SUPABASE_ANON

    # Search title and description via ilike
    import urllib.parse
    q = urllib.parse.quote(f"%{query}%")
    url = (
        f"{supabase_url}/rest/v1/listings"
        f"?select=id,title,description,creator_name,apol_certified,price,tags"
        f"&status=eq.approved"
        f"&or=(title.ilike.{q},description.ilike.{q})"
        f"&limit={limit}"
    )
    req = urllib.request.Request(url, headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read())
    except Exception as e:
        print(f"ERROR: {e}")
        raise typer.Exit(1)

    if not results:
        print(f"No results for '{query}'. Try: zforge list")
        return

    if HAS_RICH:
        console.print(f"\n[bold cyan]Search results for '{query}'[/bold cyan] — {len(results)} found\n")
        for l in results:
            score = "APOL✓" if l.get('apol_certified') else "—"
            tags_str = ", ".join((l.get("tags") or [])[:4])
            console.print(f"  [bold yellow]{l.get('title')}[/bold yellow]  [dim]by {l.get('creator_name')}[/dim]  APOL: [green]{score}[/green]  [{tags_str}]")
            console.print(f"  [white]{l.get('description', '')[:100]}[/white]")
            console.print(f"  [dim]→ zforge install {l.get('title')}[/dim]")
    else:
        for l in results:
            print(f"  {l.get('title')} — {l.get('description', '')[:80]}")
            print(f"  Install: zforge install {l.get('title')}")


@app.command()
def install(
    slug: str = typer.Argument(..., help="Skill slug from the marketplace (e.g. system-health-report)"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Parent directory (default: ./skills/)"),
    skip_install_sh: bool = typer.Option(False, "--skip-install", help="Skip running install.sh after clone"),
):
    """Download and install a skill from the ZeroForge marketplace."""
    import json, urllib.request, os, subprocess
    supabase_url = (os.environ.get("SUPABASE_URL") or _PUBLIC_SUPABASE_URL).rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY") or _PUBLIC_SUPABASE_ANON

    # 1. Fetch listing — try exact title, then fuzzy slug-to-title match
    import urllib.parse as _up

    def _fetch(query_param: str):
        req = urllib.request.Request(
            f"{supabase_url}/rest/v1/listings?{query_param}&status=eq.approved&select=*&limit=1",
            headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    rows = []
    try:
        # First: exact title match (case-insensitive)
        rows = _fetch(f"title=ilike.{_up.quote(slug)}")
        if not rows:
            # Second: convert slug dashes/underscores to wildcard pattern
            fuzzy = '%' + '%'.join(re.split(r'[\-_\s]+', slug.lower())) + '%'
            rows = _fetch(f"title=ilike.{_up.quote(fuzzy)}")
    except Exception as e:
        print(f"ERROR fetching listing: {e}")
        raise typer.Exit(1)

    if not rows:
        print(f"Skill '{slug}' not found. Try: zforge list  or  zforge search <keyword>")
        raise typer.Exit(1)

    listing = rows[0]
    title = listing.get("title", slug)
    repo_url = (listing.get("url") or "").strip()
    author = listing.get("creator_name", "unknown")
    score = listing.get("apol_certified")
    score_str = f"{float(score):.3f}" if score else "N/A"

    if HAS_RICH:
        console.print(f"\n[bold magenta]Installing:[/bold magenta] [bold yellow]{title}[/bold yellow]")
        console.print(f"  Author: [cyan]{author}[/cyan]  |  APOL: [green]{score_str}[/green]")
        console.print(f"  {listing.get('description', '')[:100]}")
    else:
        print(f"Installing: {title} (by {author}, APOL: {score_str})")

    # 2. Determine target directory
    if output_dir:
        parent = Path(output_dir).resolve()
    else:
        # Auto-detect Agent Zero environment — install to /a0/skills/ if it exists
        _a0_skills = Path("/a0/skills")
        parent = _a0_skills if _a0_skills.exists() else Path.cwd() / "skills"
    parent.mkdir(parents=True, exist_ok=True)
    # Use sanitized title as directory name
    dir_name = re.sub(r'[^\w]+', '_', title.lower()).strip('_')
    target = parent / dir_name

    if target.exists():
        print(f"WARNING: {target} already exists. Delete it first to reinstall.")
        raise typer.Exit(1)

    # 3. Resolve URLs — storage_url (zip) takes priority over source_url (git)
    storage_url = (listing.get("storage_url") or "").strip()
    source_url   = (listing.get("source_url")  or listing.get("url") or "").strip()

    if storage_url and storage_url.startswith("http"):
        # ── Path A: Download zip from Supabase Storage ──────────────────────
        import tempfile, zipfile as _zf
        if HAS_RICH:
            console.print(f"  [dim]Downloading from ZeroForge Storage...[/dim]")
        else:
            print("  Downloading skill zip from ZeroForge...")
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp_path = tmp.name
            req = urllib.request.Request(
                storage_url,
                headers={"User-Agent": "zforge-cli/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_path, "wb") as out:
                out.write(resp.read())
            # Extract zip → target directory
            target.mkdir(parents=True, exist_ok=True)
            with _zf.ZipFile(tmp_path, "r") as zf:
                # Strip top-level folder if zip has one
                members = zf.namelist()
                prefix = members[0] if (members and members[0].endswith("/") and
                                         all(m.startswith(members[0]) for m in members[1:])) else None
                for member in members:
                    member_path = member[len(prefix):] if prefix else member
                    if not member_path:  # skip the root folder entry itself
                        continue
                    dest = target / member_path
                    if member.endswith("/"):
                        dest.mkdir(parents=True, exist_ok=True)
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(dest, "wb") as dst:
                            dst.write(src.read())
            import os as _os
            _os.unlink(tmp_path)
            if HAS_RICH:
                console.print(f"  [green]✓ Downloaded and extracted[/green]")
            else:
                print("  Download complete.")
        except Exception as e:
            print(f"ERROR: Download failed: {e}")
            raise typer.Exit(1)

    elif source_url and source_url.startswith("http"):
        # ── Path B: Git clone from creator repo (open-source skills) ─────────
        if HAS_RICH:
            console.print(f"  [dim]Cloning source from {source_url}...[/dim]")
            console.print(f"  [dim yellow](Tip: this skill links to its public GitHub repo)[/dim yellow]")
        else:
            print(f"  Cloning {source_url}...")
        result = subprocess.run(["git", "clone", source_url, str(target)])
        if result.returncode != 0:
            print("ERROR: git clone failed. Check the repository URL.")
            raise typer.Exit(1)

    else:
        # ── Path C: No download URL ──────────────────────────────────────────
        listing_url = f"https://zero-forge.org/listing/?id={listing.get('id', '')}"
        if HAS_RICH:
            console.print(f"[yellow]  No download URL available for this skill.[/yellow]")
            console.print(f"  Visit: [bold]{listing_url}[/bold] for manual download instructions.")
        else:
            print(f"  No download URL. Visit: {listing_url}")
        raise typer.Exit(0)

    # 4. Run install.sh
    install_sh = target / "install.sh"
    if install_sh.exists() and not skip_install_sh:
        if HAS_RICH:
            console.print("  [dim]Running install.sh...[/dim]")
        else:
            print("  Running install.sh...")
        subprocess.run(["bash", str(install_sh)], cwd=str(target))

    # 5. Done
    _a0_note = "  [dim]Agent Zero: reload skills or use skills_tool to access it.[/dim]" if str(target).startswith("/a0/skills") else ""
    _a0_note_plain = "  Agent Zero: reload skills or use skills_tool to access it." if str(target).startswith("/a0/skills") else ""
    if HAS_RICH:
        console.print(f"\n[bold green]✓ Installed:[/bold green] [bold yellow]{slug}[/bold yellow] → {target}")
        console.print(f"  [dim]Run it: python {target}/scripts/main.py[/dim]")
        if _a0_note:
            console.print(_a0_note)
    else:
        print(f"\n✓ Installed {slug} → {target}")
        print(f"  Run: python {target}/scripts/main.py")
        if _a0_note_plain:
            print(_a0_note_plain)




def main():
    app()


if __name__ == "__main__":
    main()


@app.command()
def setup():
    """First-time setup wizard — configure your API key in plain English."""
    import os
    from pathlib import Path

    env_path = Path("/a0/usr/workdir/ZeroForge/.env")

    if HAS_RICH:
        console.print()
        console.print(Panel(
            "[bold cyan]Welcome to ZeroForge![/bold cyan]\n\n"
            "This wizard sets up your API key so you can [bold]create skills[/bold].\n"
            "You do NOT need an API key to install or run skills.",
            title="[bold magenta]ZeroForge Setup[/]",
            border_style="magenta"
        ))
        console.print()
    else:
        print("\n=== ZeroForge Setup Wizard ===")
        print("This configures your API key for building skills.")
        print()

    # Check existing config
    existing_key = ""
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                existing_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

    if existing_key and not existing_key.startswith("your_") and len(existing_key) > 10:
        if HAS_RICH:
            console.print(f"[green]Already configured![/green] Key ends in ...{existing_key[-6:]}")
            console.print()
            console.print("[bold]You are ready! Try:[/bold]")
            console.print("  [cyan]zforge list[/cyan]")
            console.print("  [cyan]zforge run install-zforge[/cyan]")
            console.print("  [cyan]zforge build my-skill --desc 'what it does'[/cyan]")
        else:
            print(f"Already configured (ends in ...{existing_key[-6:]})")
        return

    if HAS_RICH:
        console.print("[bold yellow]Step 1 of 2 — Get a free API key[/bold yellow]")
        console.print()
        console.print("  ZeroForge uses OpenRouter to power skill creation.")
        console.print("  Sign up free at: [bold cyan]https://openrouter.ai/keys[/bold cyan]")
        console.print("  Click Create Key and copy it — starts with sk-or-...")
        console.print()
        api_key = console.input("[bold yellow]Paste your OpenRouter API key: [/bold yellow]").strip()
    else:
        print("Step 1: Get a free OpenRouter API key")
        print("  Visit: https://openrouter.ai/keys")
        api_key = input("Paste your key: ").strip()

    if not api_key or len(api_key) < 10:
        if HAS_RICH:
            console.print("[red]No key entered. Run zforge setup again when ready.[/red]")
        else:
            print("No key entered. Run zforge setup again when ready.")
        return

    # Save to .env
    env_path.parent.mkdir(parents=True, exist_ok=True)
    if env_path.exists():
        import re as _re
        content = env_path.read_text()
        if "OPENROUTER_API_KEY=" in content:
            content = _re.sub(r"OPENROUTER_API_KEY=.*", f"OPENROUTER_API_KEY={api_key}", content)
        else:
            content += f"\nOPENROUTER_API_KEY={api_key}\n"
        env_path.write_text(content)
    else:
        env_path.write_text(f"OPENROUTER_API_KEY={api_key}\n")

    os.environ["OPENROUTER_API_KEY"] = api_key

    if HAS_RICH:
        console.print()
        console.print("[green]API key saved![/green]")
        console.print()
        console.print("[bold yellow]Step 2 of 2 — You are ready![/bold yellow]")
        console.print()
        console.print("Try these commands:")
        console.print("  [cyan]zforge list[/cyan]")
        console.print("  [cyan]zforge run install-zforge[/cyan]")
        console.print("  [cyan]zforge build my-skill --desc 'what it does'[/cyan]")
    else:
        print("API key saved! Try: zforge list")


@app.command(name="run")
def run_skill(
    slug: str = typer.Argument(..., help="Skill name to install and run"),
    skill_args: Optional[str] = typer.Option(None, "--args", help="Arguments to pass to the skill"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Where to install"),
    keep: bool = typer.Option(False, "--keep", help="Keep installed files after running"),
):
    """Install a skill AND run it in one command. No terminal knowledge needed."""
    import subprocess, shutil, json, urllib.request, re as _re
    import os, tempfile, zipfile as _zf, urllib.parse as _up
    from pathlib import Path

    env_path = Path("/a0/usr/workdir/ZeroForge/.env")
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if (not supabase_url or not anon_key) and env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("SUPABASE_URL="):
                supabase_url = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("SUPABASE_ANON_KEY="):
                anon_key = line.split("=", 1)[1].strip().strip('"')

    if HAS_RICH:
        console.print()
        console.print(f"[bold magenta]zforge run[/bold magenta] -> [bold yellow]{slug}[/bold yellow]")
        console.print()

    def fetch_listing(param):
        req = urllib.request.Request(
            f"{supabase_url}/rest/v1/listings?{param}&status=eq.approved&select=*&limit=1",
            headers={"apikey": anon_key, "Authorization": f"Bearer {anon_key}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    rows = []
    try:
        rows = fetch_listing(f"title=ilike.{_up.quote(slug)}")
        if not rows:
            fuzzy = "%" + "%".join(_re.split(r"[\-_\s]+", slug.lower())) + "%"
            rows = fetch_listing(f"title=ilike.{_up.quote(fuzzy)}")
    except Exception as e:
        if HAS_RICH:
            console.print(f"[red]Could not reach marketplace: {e}[/red]")
        raise typer.Exit(1)

    if not rows:
        if HAS_RICH:
            console.print(f"[red]Skill '{slug}' not found.[/red]")
            console.print("  Try: [cyan]zforge list[/cyan] to see all available skills.")
        raise typer.Exit(1)

    listing = rows[0]
    title = listing.get("title", slug)
    storage_url = (listing.get("storage_url") or "").strip()

    if HAS_RICH:
        console.print(f"  [green]Found:[/green] [bold]{title}[/bold]")
        console.print(f"  [dim]{listing.get('description', '')[:80]}[/dim]")
        console.print()

    base_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="zf_run_"))
    dir_name = _re.sub(r"[^\w]+", "_", title.lower()).strip("_")
    skill_dir = base_dir / dir_name

    if not skill_dir.exists():
        if not storage_url.startswith("http"):
            if HAS_RICH:
                console.print("[red]No download URL for this skill.[/red]")
            raise typer.Exit(1)

        if HAS_RICH:
            console.print("  [dim]Downloading...[/dim]")
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                tmp_path = tmp.name
            req = urllib.request.Request(storage_url, headers={"User-Agent": "zforge-cli/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_path, "wb") as out:
                out.write(resp.read())
            skill_dir.mkdir(parents=True, exist_ok=True)
            with _zf.ZipFile(tmp_path, "r") as zf:
                members = zf.namelist()
                prefix = (members[0] if members and members[0].endswith("/")
                          and all(m.startswith(members[0]) for m in members[1:]) else None)
                for member in members:
                    rel = member[len(prefix):] if prefix else member
                    if not rel:
                        continue
                    dest = skill_dir / rel
                    if member.endswith("/"):
                        dest.mkdir(parents=True, exist_ok=True)
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(dest, "wb") as dst:
                            dst.write(src.read())
            os.unlink(tmp_path)
            if HAS_RICH:
                console.print("  [green]Downloaded[/green]")
        except Exception as e:
            if HAS_RICH:
                console.print(f"[red]Download failed: {e}[/red]")
            raise typer.Exit(1)

    # Unwrap double-nested zip (e.g. skill_dir/skill_name/scripts/ -> skill_dir/scripts/)
    _contents = list(skill_dir.iterdir())
    if len(_contents) == 1 and _contents[0].is_dir():
        skill_dir = _contents[0]

    main_script = None
    for candidate in [
        skill_dir / "scripts" / "main.py",
        skill_dir / "main.py",
        skill_dir / "scripts" / "run.py"
    ]:
        if candidate.exists():
            main_script = candidate
            break
    if not main_script:
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists():
            py_files = list(scripts_dir.glob("*.py"))
            if py_files:
                main_script = py_files[0]

    if not main_script:
        if HAS_RICH:
            console.print(f"[red]No runnable script found. Skill at: {skill_dir}[/red]")
        raise typer.Exit(1)

    req_file = skill_dir / "requirements.txt"
    if req_file.exists() and req_file.stat().st_size > 0:
        if HAS_RICH:
            console.print("  [dim]Installing dependencies...[/dim]")
        subprocess.run(["pip", "install", "-q", "-r", str(req_file)], capture_output=True)

    if HAS_RICH:
        console.print(f"  [green]Running:[/green] [bold]{title}[/bold]")
        console.print("  " + "=" * 50)
        console.print()

    cmd = ["python", str(main_script)]
    if skill_args:
        cmd += skill_args.split()
    result = subprocess.run(cmd, cwd=str(skill_dir))

    if HAS_RICH:
        console.print()
        console.print("  " + "=" * 50)
        if result.returncode == 0:
            console.print("[green]Done![/green]")
        else:
            console.print(f"[yellow]Skill exited with code {result.returncode}[/yellow]")

    if not keep and not output_dir:
        shutil.rmtree(str(base_dir), ignore_errors=True)

    raise typer.Exit(code=result.returncode)

