"""Shipped sources.yaml and profiles.yaml: the community profile needs more than one WWR feed."""

from __future__ import annotations

from pathlib import Path

from jobscraper.config import load_sources
from jobscraper.profiles import load_profiles, validate_profile_sources

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "sources.yaml"
PROFILES = ROOT / "config" / "profiles.yaml"
SUPPORT_FEED = "https://weworkremotely.com/categories/remote-customer-support-jobs.rss"
SITE_WIDE_FEED = "https://weworkremotely.com/remote-jobs.rss"


def test_every_shipped_source_is_enabled_verified_and_documented():
    sources = load_sources(CONFIG)
    expected = {"himalayas", "jobicy", "weworkremotely", "weworkremotely_categories"}
    assert expected <= set(sources)
    for source_id in expected:
        config = sources[source_id]
        assert config.enabled, source_id
        assert config.status == "verified", source_id
        assert config.terms_url, source_id


def test_support_profile_keeps_the_single_support_feed():
    # The support profile's only change is the allowlist below; its fetch set stays identical.
    assert load_sources(CONFIG)["weworkremotely"].feeds == [SUPPORT_FEED]


def test_categories_source_polls_the_widened_feed_set():
    feeds = load_sources(CONFIG)["weworkremotely_categories"].feeds
    assert SUPPORT_FEED in feeds
    assert SITE_WIDE_FEED in feeds
    assert len(feeds) == 8
    assert len(set(feeds)) == len(feeds)
    assert all(feed.startswith("https://weworkremotely.com/") for feed in feeds)


def test_jobicy_asks_for_the_largest_verified_page():
    jobicy = load_sources(CONFIG)["jobicy"]
    assert jobicy.query_params.get("count") == 100


def test_himalayas_pages_deeper_without_changing_the_verified_page_size():
    himalayas = load_sources(CONFIG)["himalayas"]
    assert himalayas.page_size == 20
    assert himalayas.max_pages == 10


def test_profiles_route_the_wider_feeds_to_community_only():
    entries = {entry.id: entry for entry in load_profiles(PROFILES)}
    validate_profile_sources(list(entries.values()), set(load_sources(CONFIG)))

    assert entries["support"].sources == ("himalayas", "jobicy", "weworkremotely")
    assert entries["community"].sources == (
        "himalayas",
        "jobicy",
        "weworkremotely_categories",
    )
