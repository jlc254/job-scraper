#!/usr/bin/env python3
"""Pin every `uses:` line in .github/workflows to a full commit SHA (doc 08).

Write the version you want as a trailing comment:

    uses: actions/checkout@UNPINNED # v4

then run `python scripts/pin_actions.py`. It looks up the commit behind that tag with
`git ls-remote` (needs network) and rewrites the line as `@<40-hex sha> # v4`.

    --update   re-resolve lines that are already pinned (moves them to the tag's current commit)
    --check    change nothing, exit 1 if any line is unpinned
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

USES = re.compile(
    r"^(?P<prefix>\s*-?\s*uses:\s*)(?P<repo>[\w.-]+/[\w./-]+)@(?P<ref>\S+)"
    r"(?:[ \t]*#[ \t]*(?P<tag>\S+))?[ \t]*$"
)
SHA = re.compile(r"^[0-9a-f]{40}$")
SAFE = re.compile(r"^[\w.\-/]+$")

Resolver = Callable[[str, str], str]


def resolve(repo: str, tag: str) -> str:
    """Commit SHA behind a tag. Annotated tags are peeled to the commit."""
    if not SAFE.fullmatch(repo) or not SAFE.fullmatch(tag):
        raise ValueError(f"refusing odd repo or tag: {repo}@{tag}")
    out = subprocess.run(  # noqa: S603
        [
            "git",
            "ls-remote",
            f"https://github.com/{repo}.git",
            f"refs/tags/{tag}",
            f"refs/tags/{tag}^{{}}",
        ],  # noqa: S607
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout
    found: dict[str, str] = {}
    for line in out.splitlines():
        line_sha, _, ref = line.partition("\t")
        found[ref] = line_sha
    sha: str | None = found.get(f"refs/tags/{tag}^{{}}") or found.get(f"refs/tags/{tag}")
    if not sha or not SHA.fullmatch(sha):
        raise LookupError(f"no tag {tag} found in {repo}")
    return sha


def pin_text(text: str, resolver: Resolver, update: bool = False) -> tuple[str, list[str]]:
    """Return (new text, problems). Local actions and already-pinned lines are left alone."""
    problems: list[str] = []
    lines: list[str] = []
    for number, line in enumerate(text.splitlines(keepends=True), start=1):
        match = USES.match(line.rstrip("\r\n"))
        if not match or match["repo"].startswith("."):
            lines.append(line)
            continue
        ref, tag = match["ref"], match["tag"]
        pinned = bool(SHA.fullmatch(ref)) and ref != "0" * 40
        if pinned and not update:
            lines.append(line)
            continue
        wanted = tag or (None if pinned or ref == "UNPINNED" else ref)
        if not wanted:
            problems.append(
                f"line {number}: add a '# vX' comment naming the version for {match['repo']}"
            )
            lines.append(line)
            continue
        try:
            sha = resolver(match["repo"], wanted)
        except (LookupError, ValueError, subprocess.SubprocessError, OSError) as exc:
            problems.append(f"line {number}: could not resolve {match['repo']}@{wanted}: {exc}")
            lines.append(line)
            continue
        ending = line[len(line.rstrip("\r\n")) :]
        lines.append(f"{match['prefix']}{match['repo']}@{sha} # {wanted}{ending}")
    return "".join(lines), problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dir", type=Path, default=Path(".github/workflows"))
    args = parser.parse_args(argv)

    failures = 0
    for path in sorted(args.dir.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        if args.check:

            def refuse(repo: str, tag: str) -> str:
                raise LookupError("unpinned")

            _, problems = pin_text(text, refuse, update=False)
            failures += len(problems)
            for p in problems:
                print(f"{path}: {p}")
            continue
        new_text, problems = pin_text(text, resolve, update=args.update)
        for p in problems:
            print(f"{path}: {p}", file=sys.stderr)
        failures += len(problems)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            print(f"pinned {path}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
