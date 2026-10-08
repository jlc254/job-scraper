from typing import Any
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "pin_actions", Path(__file__).parent.parent / "scripts" / "pin_actions.py"
)
assert SPEC and SPEC.loader
pin = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pin)

SHA_A = "a" * 40
SHA_B = "b" * 40


def fake(repo: str, tag: str) -> str:
    return {("actions/checkout", "v4"): SHA_A, ("actions/setup-python", "v5"): SHA_B}[(repo, tag)]


def test_unpinned_lines_are_pinned_with_the_tag_kept_as_a_comment() -> None:
    text = "steps:\n  - uses: actions/checkout@UNPINNED # v4\n    with:\n      x: 1\n  - run: echo hi\n"
    new, problems = pin.pin_text(text, fake)
    assert problems == []
    assert f"  - uses: actions/checkout@{SHA_A} # v4\n" in new and "run: echo hi" in new


def test_ref_without_a_comment_uses_the_ref_as_the_tag() -> None:
    new, problems = pin.pin_text("      - uses: actions/setup-python@v5\n", fake)
    assert problems == [] and new == f"      - uses: actions/setup-python@{SHA_B} # v5\n"


def test_already_pinned_lines_are_untouched_unless_update_is_requested() -> None:
    line = f"      - uses: actions/checkout@{SHA_B} # v4\n"
    assert pin.pin_text(line, fake) == (line, [])
    new, _ = pin.pin_text(line, fake, update=True)
    assert new == f"      - uses: actions/checkout@{SHA_A} # v4\n"


def test_idempotent() -> None:
    once, _ = pin.pin_text("  - uses: actions/checkout@UNPINNED # v4\n", fake)
    assert pin.pin_text(once, fake) == (once, [])


def test_local_actions_and_other_lines_are_ignored() -> None:
    text = "  - uses: ./.github/actions/thing\n  - name: uses: nothing here\n"
    assert pin.pin_text(text, fake) == (text, [])


def test_placeholder_without_a_version_comment_is_reported() -> None:
    text = "  - uses: actions/checkout@UNPINNED\n"
    new, problems = pin.pin_text(text, fake)
    assert new == text and "add a '# vX' comment" in problems[0]


def test_unknown_tag_is_reported_not_guessed() -> None:
    def missing(repo: str, tag: str) -> str:
        raise LookupError("no tag")

    text = "  - uses: actions/checkout@UNPINNED # v99\n"
    new, problems = pin.pin_text(text, missing)
    assert new == text and "could not resolve" in problems[0]


def test_resolver_rejects_odd_input_and_prefers_the_peeled_commit(monkeypatch: Any) -> None:
    with pytest.raises(ValueError):
        pin.resolve("actions/checkout; rm -rf /", "v4")
    output = f"{SHA_B}\trefs/tags/v4\n{SHA_A}\trefs/tags/v4^{{}}\n"
    monkeypatch.setattr(
        pin.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, output, "")
    )
    assert pin.resolve("actions/checkout", "v4") == SHA_A
    monkeypatch.setattr(
        pin.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, "", "")
    )
    with pytest.raises(LookupError):
        pin.resolve("actions/checkout", "v4")