from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from jobscraper.config import ConfigError
from jobscraper.matching.brief import find_row, render_brief
from jobscraper.matching.calibrate import agreement_report, read_labels, select_for_labeling, write_label_sheet
from jobscraper.matching.filters import JobFilters
from jobscraper.matching.scorer import Scorer, years_asked
from jobscraper.matching.settings import FilterSettings, SalaryFloor, load_profile, load_scoring
from jobscraper.matching.skills import SkillExtractor
from jobscraper.models import MatchTier
from jobscraper.pipeline import persist, process_jobs
from jobscraper.storage.sqlite import SQLiteStorage
from tests.helpers import T0, make_job

CONFIG = Path(__file__).parent.parent / "config"
TODAY = date(2026, 10, 1)


@pytest.fixture(scope="module")
def profile():
    return load_profile(CONFIG / "profile.example.yaml")


@pytest.fixture(scope="module")
def scoring():
    return load_scoring(CONFIG / "scoring.example.yaml")


@pytest.fixture
def scorer(profile, scoring):
    return Scorer(profile, scoring, TODAY)


@pytest.fixture
def filters(scoring):
    return JobFilters(scoring.filters, TODAY)


def job(**kw):
    base = dict(job_id="j", source="x", source_job_id="1", job_url="https://x.com/1", description_excerpt="",
                scoring_text="", work_type="unknown", location=None, date_posted=TODAY, title="Customer Support Agent")
    base.update(kw)
    return make_job(**base)


def factor(scored, name):
    return scored.match_breakdown["factors"][name]["points"]


# ---- golden tests: the worked examples in doc 06 ---------------------------------------------

def test_golden_example_a_top_match(scorer):
    scored = scorer.score(job(
        title="Customer Support Specialist", company="SaaS Co", location="Remote - Africa",
        salary_min=800, salary_max=1200, salary_currency="USD", date_posted=date(2026, 9, 29),
        scoring_text="Requirements: Zendesk, Freshdesk, ticketing, English. Nice to have: CRM, live chat. "
                     "3+ years of experience.",
    ))
    f = lambda n: factor(scored, n)  # noqa: E731
    assert (f("title"), f("skills"), f("location"), f("experience"), f("salary"), f("freshness"), f("industry")) \
        == (25, 17.5, 20, 10, 5, 5, 3)
    assert scored.match_score == 85.5 and scored.match_tier is MatchTier.TOP
    assert set(scored.skills_missing) == {"freshdesk", "live chat"}
    assert scored.recommended_action.startswith("Tailor CV to matched skills")
    assert "freshdesk" in scored.recommended_action.lower()
    assert scored.checklist.startswith("Deadline: none listed")


def test_golden_example_b_bank_onsite(scorer):
    scored = scorer.score(job(
        title="Customer Care Representative", company="Nairobi Bank", location="Nairobi, Kenya",
        date_posted=date(2026, 9, 26), application_deadline=date(2026, 10, 13),
        scoring_text="Requirements: complaint handling, CRM, Swahili, customer service. 2 years of experience.",
    ))
    assert (factor(scored, "title"), factor(scored, "skills"), factor(scored, "location")) == (25, 25, 20)
    assert (factor(scored, "experience"), factor(scored, "salary"), factor(scored, "freshness")) == (8, 5, 4)
    assert scored.match_score == 90 and scored.match_tier is MatchTier.TOP


def test_golden_example_c_us_only_is_excluded(filters):
    verdict = filters.check(job(title="Customer Support Agent", scoring_text="Customer support role. US residents only."))
    assert verdict is not None and verdict.reason == "region_restricted"
    assert "US residents only" in verdict.detail


def test_golden_example_d_technical_support_potential(scorer):
    scored = scorer.score(job(
        title="Technical Support Engineer", location="Remote, Worldwide", date_posted=date(2026, 9, 30),
        scoring_text="Requirements: Linux, scripting, networking, ticketing. 3+ years of experience.",
    ))
    assert factor(scored, "title") == 10
    assert round(factor(scored, "skills"), 1) == 9.4
    assert (factor(scored, "location"), factor(scored, "experience")) == (20, 10)
    assert scored.match_score == 62.4 and scored.match_tier is MatchTier.POTENTIAL
    assert set(scored.skills_missing) == {"linux", "scripting"}
    assert scored.recommended_action.startswith("Review gaps")
    assert scored.checklist == ""


# ---- hard filters ----------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"posting_country_restrictions": ["United States"], "remote_eligibility": "restricted"}, "region_restricted"),
        ({"scoring_text": "Customer support. Must be authorized to work in the UK."}, "region_restricted"),
        ({"application_deadline": TODAY - timedelta(days=1)}, "expired"),
        ({"scoring_text": "Customer support. A small registration fee applies."}, "scam_pattern"),
        ({"scoring_text": "Customer support. Apply only via WhatsApp."}, "scam_pattern"),
        ({"title": "Telemarketer"}, "excluded_title"),
        ({"title": "Backend Engineer", "scoring_text": "Write Go services."}, "off_topic"),
        ({"date_posted": TODAY - timedelta(days=40)}, "too_old"),
    ],
)
def test_filters_exclude(filters, overrides, reason):
    verdict = filters.check(job(**overrides))
    assert verdict is not None and verdict.reason == reason


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"date_posted": TODAY - timedelta(days=40), "application_deadline": TODAY + timedelta(days=5)},
        {"date_posted": None},
        {"title": "Account Specialist", "scoring_text": "You will provide customer support to our clients."},
        {"application_deadline": TODAY},
    ],
)
def test_filters_keep(filters, overrides):
    assert filters.check(job(**overrides)) is None


@pytest.mark.parametrize("text", ["Please email us only if urgent.", "Reach us only on weekdays.", "Join us. Only the best."])
def test_region_patterns_do_not_misfire_on_ordinary_words(filters, text):
    assert filters.check(job(scoring_text=f"Customer support role. {text}")) is None


def test_restriction_in_first_position_wins_over_other_reasons(filters):
    verdict = filters.check(job(title="Telemarketer", scoring_text="US only. registration fee"))
    assert verdict is not None and verdict.reason == "region_restricted"


def test_custom_filter_config_replaces_defaults():
    custom = JobFilters(FilterSettings(scam_patterns=[r"free pizza"], support_keywords=["pizza"]), TODAY)
    assert custom.check(job(title="Pizza taster", scoring_text="free pizza")).reason == "scam_pattern"


# ---- skills extraction ----------------------------------------------------------------------

@pytest.fixture
def extractor(scoring):
    return SkillExtractor(scoring.skill_dictionary)


def test_inline_headings_split_required_and_preferred(extractor):
    got = extractor.extract("Requirements: Zendesk, ticketing. Nice to have: CRM.")
    assert got.required == ["zendesk", "ticketing"] and got.preferred == ["crm"]


def test_no_headings_means_all_required(extractor):
    got = extractor.extract("We use Zendesk and HubSpot every day.")
    assert set(got.required) == {"zendesk", "hubspot"} and got.preferred == []


def test_required_wins_when_skill_appears_in_both(extractor):
    got = extractor.extract("Requirements:\n- CRM\nNice to have:\n- CRM, Excel")
    assert "crm" in got.required and got.preferred == ["excel"]


def test_synonyms_and_word_boundaries(extractor):
    got = extractor.extract("Requirements: Microsoft Excel, a service desk background, sqlite experience")
    assert "excel" in got.required and "ticketing" in got.required and "sql" not in got.required


def test_bonus_in_a_sentence_is_not_a_heading(extractor):
    got = extractor.extract("We offer an annual bonus. You know Zendesk.")
    assert got.required == ["zendesk"] and got.preferred == []


def test_requirement_lines_are_collected_and_capped(extractor):
    text = "Requirements:\n" + "\n".join(f"- item {i}" for i in range(15)) + "\nNice to have:\n- extra"
    got = extractor.extract(text)
    assert len(got.requirements) == 10 and got.requirements[0] == "item 0"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("3+ years of experience", (3, None)),
        ("1-3 years experience required", (1, 3)),
        ("at least 5 years' experience", (5, None)),
        ("we have been in business for 10 years", None),
    ],
)
def test_years_asked(text, expected):
    assert years_asked(text) == expected


# ---- scorer factors ------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("title", "points"),
    [("Customer Support Agent - Remote", 25), ("Customer Support Agent Tier 2", 22),
     ("Billing Support Specialist", 18), ("Technical Support Engineer", 10),
     ("Support Coordinator", 5), ("Warehouse Operator", 0)],
)
def test_title_points(scorer, title, points):
    assert factor(scorer.score(job(title=title)), "title") == points


@pytest.mark.parametrize(
    ("kw", "points"),
    [({"location": "Remote - Kenya"}, 20), ({"location": "Mombasa, Kenya"}, 16), ({"location": "Remote"}, 10),
     ({"location": "Kampala, Uganda"}, 8), ({"location": "Berlin, Germany"}, 4), ({"location": None}, 10),
     ({"location": "Nairobi", "work_type": "hybrid"}, 20)],
)
def test_location_points(scorer, kw, points):
    scored = scorer.score(job(**kw))
    assert factor(scored, "location") == points
    unconfirmed = points == 10
    assert ("eligibility unconfirmed" in scored.match_breakdown["flags"]) == unconfirmed


@pytest.mark.parametrize(
    ("kw", "points"),
    [({"scoring_text": "5 years of experience"}, 10), ({"scoring_text": "2 years experience"}, 8),
     ({"scoring_text": "12 years of experience"}, 6), ({}, 7), ({"title": "Senior Support Agent"}, 6),
     ({"title": "Support Manager"}, 2), ({"title": "Customer Success Manager"}, 7),
     ({"title": "Junior Support Agent"}, 8)],
)
def test_experience_points(scorer, kw, points):
    assert factor(scorer.score(job(**kw)), "experience") == points


@pytest.mark.parametrize(("days", "points"), [(0, 5), (3, 5), (7, 4), (14, 3), (30, 1), (31, 0)])
def test_freshness_points(scorer, days, points):
    assert factor(scorer.score(job(date_posted=TODAY - timedelta(days=days))), "freshness") == points


def test_salary_floor_comparison(profile, scoring):
    floored = profile.model_copy(update={"salary_floor": SalaryFloor(amount=800, currency="USD", period="month")})
    s = Scorer(floored, scoring, TODAY)
    ok = dict(salary_min=900, salary_max=1000, salary_currency="USD", salary_period="month")
    low = dict(salary_min=300, salary_max=400, salary_currency="USD", salary_period="month")
    yearly = dict(salary_min=12000, salary_max=14400, salary_currency="USD", salary_period="year")
    other = dict(salary_min=900, salary_max=1000, salary_currency="KES", salary_period="month")
    assert [factor(s.score(job(**x)), "salary") for x in (ok, low, yearly, other, {})] == [10, 2, 10, 5, 5]


def test_industry_preferred_and_avoided(profile, scoring):
    p = profile.model_copy(update={"preferred_industries": ["banking"], "avoided_industries": ["bpo"]})
    s = Scorer(p, scoring, TODAY)
    assert factor(s.score(job(company="Kenya Bank")), "industry") == 5
    assert factor(s.score(job(scoring_text="a call centre outsourcing company")), "industry") == 0
    assert factor(s.score(job()), "industry") == 3


def test_skills_not_listed_is_neutral(scorer):
    scored = scorer.score(job(scoring_text="Join our friendly team."))
    assert factor(scored, "skills") == 12 and "skills not listed" in scored.match_breakdown["flags"]


def test_tier_boundaries(scorer):
    assert [scorer._tier(x) for x in (85, 84.9, 75, 74.9, 50, 49.9)] == [  # noqa: SLF001
        MatchTier.TOP, MatchTier.STRONG, MatchTier.STRONG, MatchTier.POTENTIAL, MatchTier.POTENTIAL, MatchTier.WEAK]


def test_breakdown_is_json_serialisable_and_versioned(scorer):
    scored = scorer.score(job())
    data = json.loads(json.dumps(scored.match_breakdown))
    assert data["version"] == 1 and set(data["factors"]) == {
        "title", "skills", "location", "experience", "salary", "freshness", "industry"}
    assert sum(f["points"] for f in data["factors"].values()) == pytest.approx(data["total"], abs=0.1)


def test_action_apply_now_when_deadline_close(scorer):
    scored = scorer.score(job(
        title="Customer Support Specialist", location="Remote - Africa",
        scoring_text="Requirements: Zendesk, ticketing, English. 3+ years of experience.",
        application_deadline=TODAY + timedelta(days=2),
    ))
    assert scored.match_tier in (MatchTier.TOP, MatchTier.STRONG) and scored.recommended_action.startswith("Apply now")


def test_unconfirmed_eligibility_advisory_not_hidden_by_main_action(scorer):
    scored = scorer.score(job(title="Customer Support Specialist", location="Remote",
                              scoring_text="Requirements: Zendesk, ticketing, English. 3+ years of experience."))
    assert "Check country eligibility" in scored.recommended_action


def test_transferable_strengths(scorer):
    scored = scorer.score(job(title="Billing Support Specialist", scoring_text="You will handle collections and invoicing."))
    assert any("Payment follow-up" in t for t in scored.transferable)


def test_weak_jobs_have_no_action(scorer):
    scored = scorer.score(job(title="Warehouse Operator", location="Berlin, Germany", scoring_text="Lift boxes.",
                              date_posted=TODAY - timedelta(days=25)))
    assert scored.match_tier is MatchTier.WEAK and scored.recommended_action == ""


# ---- pipeline: filters, scoring, excluded log -----------------------------------------------

def test_pipeline_excludes_logs_once_and_scores(filters, scorer, tmp_path):
    good = job(job_id="g", source_job_id="g1", job_url="https://x.com/g", title="Customer Support Specialist",
               location="Remote - Africa", scoring_text="Requirements: Zendesk, ticketing, English. 3+ years of experience.")
    us_only = job(job_id="u", source_job_id="u1", job_url="https://x.com/u", scoring_text="US residents only.")
    backend = job(job_id="b", source_job_id="b1", job_url="https://x.com/b", title="Backend Engineer",
                  scoring_text="Write Go services.")
    storage = SQLiteStorage()

    out1 = process_jobs([good, us_only, backend], storage, T0, [], filters=filters, scorer=scorer)
    persist(storage, out1, tmp_path)
    assert [j.match_tier for j in out1.new_jobs] == [MatchTier.TOP]
    assert dict(out1.excluded_by_reason) == {"region_restricted": 1, "off_topic": 1}
    assert storage.load_excluded_ids() == {"u", "b"} and len(storage.load_index()) == 1
    row = storage.load_rows()[0]
    assert row["match_tier"] == "top" and json.loads(row["match_breakdown"])["version"] == 1
    assert row["skills_missing"] == "" and row["checklist"].startswith("Deadline:")

    out2 = process_jobs([good, us_only, backend], storage, T0, [], filters=filters, scorer=scorer)
    persist(storage, out2, tmp_path)
    assert out2.new_jobs == [] and out2.excluded == []  # nothing re-logged, nothing duplicated
    assert len(storage.load_index()) == 1


def test_stored_job_that_later_fails_a_filter_is_left_alone(filters, scorer, tmp_path):
    storage = SQLiteStorage()
    good = job(job_id="g", title="Customer Support Specialist", location="Remote - Africa",
               scoring_text="Requirements: Zendesk. 3+ years of experience.")
    persist(storage, process_jobs([good], storage, T0, [], filters=filters, scorer=scorer), tmp_path)
    expired = good.model_copy(update={"application_deadline": TODAY - timedelta(days=2)})
    out = process_jobs([expired], storage, T0, [], filters=filters, scorer=scorer)
    assert out.excluded == [] and out.new_jobs == [] and out.updates == []


# ---- brief and calibration -----------------------------------------------------------------

def test_brief_renders_from_stored_row(filters, scorer, tmp_path):
    storage = SQLiteStorage()
    good = job(job_id="abc123", title="Customer Support Specialist", location="Remote - Africa",
               scoring_text="Requirements:\n- Zendesk\n- Freshdesk\nNice to have: CRM")
    persist(storage, process_jobs([good], storage, T0, [], filters=filters, scorer=scorer), tmp_path)
    rows = storage.load_rows()
    row = find_row(rows, "abc")
    assert row is not None
    text = render_brief(row)
    assert "# Customer Support Specialist" in text and "## Why it scored this way" in text
    assert "freshdesk" in text and "Zendesk" in text and "scoring version 1" in text
    assert find_row(rows, "zzz") is None


def test_calibration_export_and_report(tmp_path):
    rows = [{"job_id": f"{t}{i}", "title": f"{t} {i}", "company": "Co", "match_tier": t, "job_url": "u",
             "first_seen": f"2026-10-0{i + 1}"} for t in ("top", "strong", "potential", "weak") for i in range(3)]
    picked = select_for_labeling(rows, limit=8)
    assert len(picked) == 8 and {r["match_tier"] for r in picked} == {"top", "strong", "potential", "weak"}
    sheet = tmp_path / "labels.csv"
    write_label_sheet(picked, sheet)
    assert "tier" not in sheet.read_text().splitlines()[0]
    labels_text = sheet.read_text().replace(",\n", ",apply\n")
    sheet.write_text(labels_text)
    labels = read_labels(sheet)
    assert len(labels) == 8
    report = agreement_report(rows, labels)
    assert "Top/Strong that you labelled apply: 100%" in report


# ---- settings --------------------------------------------------------------------------------

def test_settings_defaults_and_errors(tmp_path, scoring):
    assert scoring.scoring_version == 1 and scoring.title.strong_exact == 25 and scoring.tiers.top == 85
    assert "zendesk" in scoring.skill_dictionary
    with pytest.raises(ConfigError, match="not found"):
        load_scoring(tmp_path / "missing.yaml")
    bad = tmp_path / "bad.yaml"
    bad.write_text("tiers: {top: not-a-number}")
    with pytest.raises(ConfigError, match="invalid config"):
        load_scoring(bad)
