"""URL canonicalization and host classification for dedupe (doc 05)."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "ref",
    "source",
    "mc_cid",
    "mc_eid",
    "gh_src",
    "src",
    "trk",
    "ref_src",
    "igshid",
    "lever-source",
    "lever-origin",
}

# Job boards and aggregators: never "the employer's own domain".
AGGREGATOR_HOSTS = {
    "himalayas.app",
    "weworkremotely.com",
    "jobicy.com",
    "remoteok.com",
    "remoteok.io",
    "arbeitnow.com",
    "workingnomads.com",
    "adzuna.com",
    "jooble.org",
    "careerjet.com",
    "reliefweb.int",
    "brightermonday.co.ke",
    "myjobmag.co.ke",
    "fuzu.com",
}
# Employer applicant-tracking boards: better than an aggregator, worse than the employer.
ATS_HOSTS = {
    "boards.greenhouse.io",
    "job-boards.greenhouse.io",
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "apply.workable.com",
    "jobs.smartrecruiters.com",
}


def host_of(url: str) -> str:
    try:
        host = urlsplit(url.strip()).hostname or ""
    except ValueError:
        return ""
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


def _host_in(host: str, group: set[str]) -> bool:
    return any(host == h or host.endswith("." + h) for h in group)


def employer_domain(url: str) -> str | None:
    """Host of the URL if it looks like the employer's own site, else None."""
    host = host_of(url)
    if not host or _host_in(host, AGGREGATOR_HOSTS) or _host_in(host, ATS_HOSTS):
        return None
    return host


def url_rank(url: str) -> int:
    """3 = employer domain, 2 = ATS board, 1 = aggregator or unknown."""
    host = host_of(url)
    if _host_in(host, AGGREGATOR_HOSTS):
        return 1
    if _host_in(host, ATS_HOSTS):
        return 2
    return 3 if host else 0


def canonical_url(url: str) -> str:
    """Comparison key: lowercase host, https, no fragment, no tracking params,
    sorted query, no trailing slash."""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    try:
        port = parts.port
    except ValueError:
        port = None
    netloc = host if port in (None, 80, 443) else f"{host}:{port}"
    query = sorted(
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not (k.lower().startswith("utm_") or k.lower() in _TRACKING_PARAMS)
    )
    scheme = "https" if parts.scheme.lower() in {"http", "https"} else parts.scheme.lower()
    return urlunsplit((scheme, netloc, parts.path.rstrip("/"), urlencode(query), ""))
