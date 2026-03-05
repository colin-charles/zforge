"""Shared Rich console helpers used across multiple CLI modules."""
import re

try:
    from rich.console import Console
    from rich.rule import Rule
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None  # type: ignore[assignment]

_TAG_RE = re.compile(r"\[/?[a-zA-Z_ #/]+\]")


def _print(msg: str, style: str = "") -> None:
    """Print *msg* using Rich when available, stripping markup tags otherwise."""
    if HAS_RICH and console is not None:
        console.print(msg, style=style or None)
    else:
        print(_TAG_RE.sub("", msg))


def _rule(title: str) -> None:
    """Print a horizontal rule with *title* centred."""
    if HAS_RICH and console is not None:
        console.print(Rule(title))
    else:
        print(f"\n{'-' * 60} {title} {'-' * 60}")
