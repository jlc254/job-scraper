"""Diagnostics for the community profile's skill matching (doc 15, D36).

skills.py was not reviewed when the profile was written, so these tests ask the real extractor
whether ordinary words trigger skills. If one fails, the extractor matches loosely: fix skills.py
(whole-word matching) rather than weakening the test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jobscraper.matching.settings import load_scoring
from jobscraper.matching.skills import SkillExtractor

SCORING = Path("config/profiles/community/scoring.yaml")


def found(text: str) -> set[str]:
    skills = SkillExtractor(load_scoring(SCORING).skill_dictionary).extract(text)
    return set(skills.required) | set(skills.preferred)


@pytest.mark.parametrize(
    "text, wrong",
    [
        ("We want people who excel in a fast-paced team.", "microsoft excel"),
        ("Plan the launch with a project plan.", "project coordination"),
        ("Shipping containers arrive weekly.", "docker"),
        ("Strong word of mouth growth.", "microsoft office"),
        ("Speaking at community events.", "public speaking"),
        ("A lighthouse stands on the coast.", "lighthouse ci"),
        ("Buffer the queue before the demo.", "buffer app"),
        ("Our golf caddy carried the bag.", "caddy server"),
        ("We use Canvas LMS for onboarding courses.", "canva"),
        ("We slack off on Friday afternoons.", "slack workspace"),
    ],
)
def test_ordinary_words_do_not_trigger_skills(text, wrong):
    assert wrong not in found(text)


def test_real_phrases_still_match():
    assert "microsoft excel" in found("Requirements: advanced MS Excel and pivot tables.")
    assert "community management" in found("Requirements: community building experience.")
    assert "event management" in found("Requirements: event planning and logistics.")


@pytest.mark.parametrize(
    "text, skill",
    [
        ("Requirements: Buffer app scheduling.", "buffer app"),
        ("Requirements: Canva designs for social posts.", "canva"),
        ("Requirements: Slack workspace administration.", "slack workspace"),
        ("Requirements: Caddy web server in front of the app.", "caddy server"),
        ("Requirements: developer relations and community building.", "developer relations"),
        ("Requirements: run Lighthouse CI on every pull request.", "lighthouse ci"),
    ],
)
def test_new_tools_match_on_their_full_phrase(text, skill):
    assert skill in found(text)
