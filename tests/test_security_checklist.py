"""Machine-checkable items from the doc 08 pre-deployment checklist.

Items that need a human (repository is private, Sheet sharing, secrets actually set, gitleaks on the
full history) are in PHASE7.md. Everything here runs offline.
"""

from __future__ import annotations

import ast
import io
import logging
import re
from pathlib import Path
from typing import Any

import pytest
import respx

from jobscraper.notifications.telegram import TelegramNotifier
from jobscraper.utils.errors import FetchError
from jobscraper.utils.logging import JsonFormatter, RedactionFilter

ROOT = Path(__file__).parent.parent
SRC = sorted((ROOT / "src").rglob("*.py"))


def test_gitignore_covers_secrets_and_runtime_output() -> None:
    lines = {x.strip() for x in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()}
    assert {".env", "output/", "logs/"} <= lines
    assert any("service-account" in x and x.endswith(".json") for x in lines)
    assert any(("credentials" in x or "key" in x) and x.endswith(".json") for x in lines)


def test_env_example_holds_placeholders_only() -> None:
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            name, _, value = line.partition("=")
            assert name.isupper() and value == "", f"{name} must have no value in .env.example"


def test_every_secret_in_doc_09_reaches_the_workflow() -> None:
    text = (ROOT / ".github" / "workflows" / "daily.yml").read_text(encoding="utf-8")
    for name in (
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID_JULIET",
        "GOOGLE_SERVICE_ACCOUNT_JSON_B64",
        "GOOGLE_SHEET_ID_JULIET",
        "ADZUNA_APP_ID",
        "ADZUNA_APP_KEY",
        "JOOBLE_API_KEY",
        "CAREERJET_AFFID",
        "RELIEFWEB_APPNAME",
        "HEALTHCHECK_URL",
    ):
        assert f"secrets.{name}" in text, name


def test_no_dangerous_constructs_in_source() -> None:
    banned = re.compile(r"\b(eval|exec)\(|shell\s*=\s*True|pickle\.load|yaml\.load\(")
    for path in SRC:
        assert not banned.search(path.read_text(encoding="utf-8")), path.name


def test_print_is_only_used_by_the_cli() -> None:
    for path in SRC:
        if path.name == "cli.py":
            continue
        assert not re.search(r"^\s*print\(", path.read_text(encoding="utf-8"), re.MULTILINE), (
            path.name
        )


def test_no_bare_except_and_every_http_client_has_a_timeout() -> None:
    for path in SRC:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                assert node.type is not None, f"bare except in {path.name}:{node.lineno}"
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "Client"
            ):
                assert any(k.arg == "timeout" for k in node.keywords), (
                    f"no timeout in {path.name}:{node.lineno}"
                )


def capture_logs(secrets: list[str]):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactionFilter(secrets))
    root = logging.getLogger()
    previous_level = root.level
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)

    def stop() -> str:
        root.removeHandler(handler)
        root.setLevel(previous_level)
        return stream.getvalue()

    return stop


@respx.mock
def test_a_fake_api_key_never_appears_in_logs_or_errors(make_client: Any) -> None:
    key = "FAKEKEY-9f8e7d6c5b4a"
    respx.get("https://api.example.com/jobs").respond(500)
    stop = capture_logs([key])
    with pytest.raises(FetchError) as caught:
        make_client({"api.example.com"}).get(
            "https://api.example.com/jobs", params={"app_key": key}
        )
    logs = stop()
    assert key not in logs and key not in str(caught.value) and "retrying" in logs


@respx.mock
def test_a_fake_telegram_token_never_appears_in_logs_or_errors() -> None:
    token = "123456789:" + "Z" * 35
    respx.post(f"https://api.telegram.org/bot{token}/sendMessage").respond(500)
    stop = capture_logs([token])
    result = TelegramNotifier(token, "42", sleep=lambda s: None, clock=lambda: 0.0).send(["hello"])
    logs = stop()
    assert (
        result.sent == 0
        and token not in logs
        and token not in (result.error or "")
        and "telegram send failed" in logs
    )


def test_redaction_catches_a_token_pasted_into_a_message() -> None:
    stop = capture_logs([])
    logging.getLogger("t").error(
        "failed calling https://api.telegram.org/bot123456789:%s/sendMessage?x=1", "Q" * 35
    )
    assert "Q" * 35 not in stop()
