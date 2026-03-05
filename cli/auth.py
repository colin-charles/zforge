"""Authentication flows for ZeroForge CLI.

Handles three login modes:
- Token/headless (--token flag, for CI)
- Manual (--manual flag, paste API key)
- Browser OAuth PKCE (default, opens browser for GitHub auth)
"""

import json as _json
import urllib.request
import urllib.error

import typer

from ._config import save_credentials, CONFIG_PATH
from ._console import console, HAS_RICH
from ._constants import _PUBLIC_SUPABASE_URL, _PUBLIC_SUPABASE_ANON

try:
    from rich.panel import Panel
except ImportError:  # pragma: no cover
    Panel = None  # type: ignore

_PORT = 7391
_CALLBACK_URL = f"http://localhost:{_PORT}/callback"
_AUTH_TIMEOUT = 120  # seconds


# ── Shared helpers ───────────────────────────────────────────────────────

def _verify_api_key(api_key: str) -> dict:
    """Verify an API key against Supabase profiles_public.

    Returns profile dict on success, raises typer.Exit(1) on failure.
    """
    try:
        req = urllib.request.Request(
            f"{_PUBLIC_SUPABASE_URL}/rest/v1/profiles_public"
            f"?api_key=eq.{api_key}&select=handle,api_key",
            headers={
                "apikey": _PUBLIC_SUPABASE_ANON,
                "Authorization": f"Bearer {_PUBLIC_SUPABASE_ANON}",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
    except Exception as exc:
        typer.echo(f"❌ Could not verify key: {exc}")
        raise typer.Exit(1)

    if not data:
        typer.echo("❌ Invalid API key.")
        raise typer.Exit(1)

    return data[0]


def _save_and_confirm(api_key: str, handle: str) -> None:
    """Save credentials and print success banner."""
    save_credentials(api_key, handle)
    if HAS_RICH and Panel:
        console.print(Panel(
            f"[bold green]✅ Authenticated as @{handle}[/bold green]\n"
            f"  Key saved to {CONFIG_PATH}\n"
            "  Skills you publish will now be attributed to "
            "your GitHub account.",
            title="[bold green]// LOGIN SUCCESS[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))
    else:
        print(f"\n✅ Authenticated as @{handle}")
        print(f"  Key saved to {CONFIG_PATH}")
        print("  Skills you publish will now be attributed "
              "to your GitHub account.")


# ── Token / headless mode ────────────────────────────────────────────────

def login_with_token(token: str) -> None:
    """Verify a pre-supplied API key and save it (CI / headless use)."""
    token = token.strip()
    if HAS_RICH:
        console.print("  [dim]Verifying token...[/dim]")
    else:
        print("  Verifying token...")

    profile = _verify_api_key(token)
    handle = profile.get("handle", "unknown")
    _save_and_confirm(token, handle)


# ── Manual / paste mode ──────────────────────────────────────────────────

def login_manual() -> None:
    """Prompt the user to paste their API key and verify it."""
    if HAS_RICH and Panel:
        console.print()
        console.print(Panel(
            "Get your API key from "
            "https://zero-forge.org/profile/edit/\n"
            "Sign in with GitHub then scroll to CLI ACCESS KEY",
            title="[bold cyan]// ZEROFORGE LOGIN (MANUAL)[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        ))
    else:
        print("\n// ZEROFORGE LOGIN (MANUAL)")
        print("Get your API key from: "
              "https://zero-forge.org/profile/edit/")

    api_key = typer.prompt("Paste your API key", hide_input=True).strip()
    if not api_key:
        typer.echo("❌ No API key provided.")
        raise typer.Exit(1)

    if HAS_RICH:
        console.print("  [dim]Verifying key...[/dim]")
    else:
        print("  Verifying key...")

    profile = _verify_api_key(api_key)
    handle = profile.get("handle", "unknown")
    _save_and_confirm(api_key, handle)


# ── Browser OAuth PKCE flow ──────────────────────────────────────────────

def login_browser_oauth() -> None:
    """Run full PKCE OAuth flow via local HTTP callback server."""
    import hashlib
    import base64
    import secrets as _secrets
    import threading
    import urllib.parse
    import webbrowser
    from http.server import HTTPServer, BaseHTTPRequestHandler

    done = threading.Event()
    result: dict[str, str] = {}

    # ── PKCE challenge ───────────────────────────────────────────────
    code_verifier = (
        base64.urlsafe_b64encode(_secrets.token_bytes(32))
        .rstrip(b"=")
        .decode()
    )
    code_challenge = (
        base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        )
        .rstrip(b"=")
        .decode()
    )
    state = _secrets.token_hex(16)

    # ── HTML templates ───────────────────────────────────────────────
    _STYLE = (
        "body{background:#0a0a0a;color:#00ff88;font-family:monospace;"
        "display:flex;align-items:center;justify-content:center;"
        "height:100vh;margin:0;}"
        ".box{border:1px solid #00ff88;padding:40px;"
        "text-align:center;max-width:420px;}"
        "h1{font-size:1.2em;margin-bottom:16px;}"
        "p{color:#aaa;font-size:.9em;}"
    )
    _HTML_WAITING = (
        f"<!DOCTYPE html><html><head><meta charset=utf-8>"
        f"<title>ZeroForge Login</title><style>{_STYLE}</style></head>"
        f"<body><div class=box><h1>// AUTHENTICATING...</h1>"
        f"<p>Completing login in your terminal. "
        f"You can close this tab.</p></div></body></html>"
    )
    _HTML_SUCCESS = (
        f"<!DOCTYPE html><html><head><meta charset=utf-8>"
        f"<title>ZeroForge Login</title><style>{_STYLE}</style></head>"
        f"<body><div class=box><h1>✅ Authenticated!</h1>"
        f"<p>You can close this tab and return to your terminal."
        f"</p></div></body></html>"
    )

    # ── Callback handler ─────────────────────────────────────────────
    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args) -> None:
            pass

        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return

            code = params.get("code", [None])[0]
            recv_state = params.get("state", [None])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            if not code or recv_state != state:
                self.wfile.write(_HTML_WAITING.encode())
                return

            self.wfile.write(_HTML_SUCCESS.encode())
            _exchange_code(code, code_verifier, result)
            done.set()

    # ── Start server ─────────────────────────────────────────────────
    try:
        server = HTTPServer(("localhost", _PORT), _Handler)
    except OSError:
        if HAS_RICH:
            console.print(
                f"  [yellow]Port {_PORT} in use "
                f"— use: zforge login --manual[/yellow]"
            )
        else:
            print(f"  Port {_PORT} in use. "
                  f"Try: zforge login --manual")
        raise typer.Exit(1)

    threading.Thread(
        target=server.serve_forever, daemon=True
    ).start()

    oauth_url = _build_oauth_url(code_challenge, state)

    if HAS_RICH and Panel:
        console.print()
        console.print(Panel(
            "Opening browser for GitHub authentication...\n"
            f"If browser doesn’t open, visit:\n{oauth_url}",
            title="[bold cyan]// ZEROFORGE LOGIN[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        ))
        console.print(
            "  [dim]Waiting for GitHub authentication "
            f"(timeout: {_AUTH_TIMEOUT // 60} min)...[/dim]"
        )
    else:
        print("\n// ZEROFORGE LOGIN")
        print(f"Opening browser... "
              f"If it doesn’t open:\n{oauth_url}")
        print("  Waiting for GitHub authentication...")

    webbrowser.open(oauth_url)
    done.wait(timeout=_AUTH_TIMEOUT)
    server.shutdown()

    if not result.get("handle") or not result.get("api_key"):
        if HAS_RICH:
            console.print(
                "  [bold red]❌ Authentication timed out "
                "or API key unavailable.[/bold red]"
            )
            console.print(
                "  Try [bold cyan]zforge login --manual"
                "[/bold cyan] instead."
            )
        else:
            print("  ❌ Authentication timed out. "
                  "Try: zforge login --manual")
        raise typer.Exit(1)

    _save_and_confirm(result["api_key"], result["handle"])


# ── OAuth internal helpers ───────────────────────────────────────────────

def _build_oauth_url(code_challenge: str, state: str) -> str:
    """Construct the Supabase OAuth authorize URL."""
    import urllib.parse

    return (
        f"{_PUBLIC_SUPABASE_URL}/auth/v1/authorize"
        f"?provider=github"
        f"&redirect_to={urllib.parse.quote(_CALLBACK_URL)}"
        f"&flow_type=pkce"
        f"&code_challenge={urllib.parse.quote(code_challenge)}"
        f"&code_challenge_method=S256"
        f"&state={state}"
    )


def _exchange_code(
    code: str,
    code_verifier: str,
    result: dict[str, str],
) -> None:
    """Exchange OAuth auth code for tokens and fetch API key.

    Populates *result* dict with 'handle' and 'api_key' on success.
    Token is scrubbed from memory immediately after use.
    """
    token_url = (
        f"{_PUBLIC_SUPABASE_URL}/auth/v1/token?grant_type=pkce"
    )
    payload = _json.dumps({
        "auth_code": code,
        "code_verifier": code_verifier,
    }).encode()

    access_token = ""
    try:
        req = urllib.request.Request(
            token_url,
            data=payload,
            headers={
                "apikey": _PUBLIC_SUPABASE_ANON,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            token_data = _json.loads(resp.read())

        access_token = token_data.get("access_token", "")
        if not access_token:
            return

        req2 = urllib.request.Request(
            f"{_PUBLIC_SUPABASE_URL}/rest/v1/profiles"
            f"?select=handle,api_key&limit=1",
            headers={
                "apikey": _PUBLIC_SUPABASE_ANON,
                "Authorization": f"Bearer {access_token}",
            },
        )
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            data = _json.loads(resp2.read())

        if data:
            result["handle"] = data[0].get("handle", "")
            result["api_key"] = data[0].get("api_key", "")
    except Exception:
        pass
    finally:
        # Scrub token from memory
        if access_token:
            access_token = "0" * len(access_token)
        del access_token
