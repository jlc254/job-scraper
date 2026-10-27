"""Language and region filters for the community profile (added 2026-10-26).

The community profile rejects ads that require a language other than English or Swahili. The
support profile must not change, so the code default is an empty list and only the community
scoring file populates it.

The region cases are the real `Headquarters:` strings from the 26 Oct 2026 run
(`output/jobs-community-20261026-120651.csv`). On WeWorkRemotely that field is the company's HQ,
not the role location, so bare cities and states must NOT be treated as restrictions.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from jobscraper.matching.filters import JobFilters
from jobscraper.matching.settings import load_scoring
from tests.helpers import make_job

COMMUNITY = Path("config/profiles/community/scoring.yaml")
# The live support scoring file, not the example template: support could gain language
# exclusions in `config/scoring.yaml` while this test still passed on the copy.
SUPPORT = Path("config/scoring.yaml")
TODAY = date(2026, 10, 1)


@pytest.fixture(scope="module")
def community() -> JobFilters:
    return JobFilters(load_scoring(COMMUNITY).filters, TODAY)


def job(**kw: Any) -> Any:
    base: dict[str, Any] = dict(
        job_id="j",
        source="weworkremotely",
        source_job_id="1",
        job_url="https://x.com/1",
        location="Anywhere in the World",
        title="Customer Support Agent",
        scoring_text="",
        date_posted=TODAY,
    )
    base.update(kw)
    return make_job(**base)


# ---- language filter -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("title", "body", "snippet"),
    [
        (
            "Customer Success Manager — Japanese & Korean Speaking (Remote)",
            "Own the post-sale strategy for the region.",
            "Japanese & Korean Speaking",
        ),
        (
            "Japanese Speaking Customer Service Agent",
            "Freelance role supporting Netflix viewers.",
            "Japanese Speaking",
        ),
        (
            "Social Media Content Specialist - Bilingual French / English",
            "Description de poste.",
            "Bilingual French",
        ),
        ("Customer Support Agent", "You must be fluent in German.", "fluent in German"),
        ("Customer Support Agent", "French is required for this role.", "French is required"),
        ("Customer Support Agent", "Portuguese (mandatory).", "Portuguese (mandatory"),
        ("Customer Support Agent", "Must be able to speak Spanish.", "speak Spanish"),
        (
            "Customer Support Agent",
            "You will be Japanese and English speaking.",
            "Japanese and English speaking",
        ),
        (
            "Customer Support Agent",
            "Bilingual Bengali candidates welcome.",
            "Bilingual Bengali",
        ),
        # An optional sentence must not shield a later required one in the same ad.
        (
            "Customer Support Agent",
            "French is a plus. Korean is required for Seoul.",
            "Korean is required",
        ),
    ],
)
def test_a_required_other_language_is_excluded(
    community: JobFilters, title: str, body: str, snippet: str
) -> None:
    verdict = community.check(job(title=title, scoring_text=body, description_excerpt=body))
    assert verdict is not None and verdict.reason == "language_required"
    assert snippet.lower() in verdict.detail.lower()


@pytest.mark.parametrize(
    "body",
    [
        "French is a plus, not required.",
        "Native Korean speaker preferred.",
        "We have offices in France and Germany.",
        "Our clients include teams across Japan and Korea.",
        "English and Swahili are required for this role.",
        "Learn Spanish with our language benefit.",
        "Translation from English into French is handled by a vendor.",
        "English-speaking candidates only.",
        # Optional sentence is skipped; there is no requirement word in it.
        "French and English speaking is a nice to have.",
        # Only the sentence around each hit decides: this one is purely optional.
        "French speaking is a plus. We also work across Japan.",
    ],
)
def test_optional_or_unrelated_language_mentions_are_kept(community: JobFilters, body: str) -> None:
    assert community.check(job(scoring_text=body, description_excerpt=body)) is None


def test_support_profile_leaves_the_language_list_empty() -> None:
    scoring = load_scoring(SUPPORT)
    assert scoring.filters.language_required_patterns == []
    assert "language_required_patterns" not in scoring.filters.model_fields_set


def test_community_profile_populates_the_language_list() -> None:
    assert load_scoring(COMMUNITY).filters.language_required_patterns


# ---- region filter: the real strings from the 26 Oct run -------------------------------------
# On real WWR feeds the `<region>` tag is the top line ("Anywhere in the World") and the
# `Headquarters:` text lives in the description, so these reach the filter through
# scoring_text with a worldwide location, exactly as the filter sees them in production.


@pytest.mark.parametrize(
    "headquarters",
    [
        "Headquarters: San Francisco, CA, New York, NY, Portland, OR, or Remote within United States",
        "Headquarters: Remote - Australia",
        "Headquarters: Remote - Japan",
        "Headquarters: Austria (remote); UK (remote)",
        "Headquarters: United States, Remote",
        "Headquarters: Argentina Remote",
        "Headquarters: Remote (US)",
        "Headquarters: San Francisco, CA, or Remote within Canada or United States",
    ],
)
def test_real_region_restrictions_are_excluded(community: JobFilters, headquarters: str) -> None:
    verdict = community.check(job(scoring_text=headquarters, description_excerpt=headquarters))
    assert verdict is not None and verdict.reason == "region_restricted"


@pytest.mark.parametrize(
    "headquarters",
    [
        "Headquarters: London",
        "Headquarters: California",
        "Headquarters: Delaware",
        "Headquarters: Zurich, Switzerland",
    ],
)
def test_a_company_headquarters_is_not_a_role_restriction(
    community: JobFilters, headquarters: str
) -> None:
    assert community.check(job(scoring_text=headquarters, description_excerpt=headquarters)) is None
