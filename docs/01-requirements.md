# 01. Requirements & Acceptance Criteria

This document defines the high-level requirements for the Job Scraper pipeline and the criteria used to determine if the system is functioning correctly.

## 1. Functional Requirements

### 1.1 Data Acquisition
- **Source Diversity**: The system must support multiple source types (RSS, JSON API, HTML scraping) via a pluggable adapter architecture.
- **Isolation**: A failure in one source must not prevent other sources from being processed.
- **Rate Limiting**: The system must honor `robots.txt` and implement exponential backoff for 429 (Too Many Requests) errors.

### 1.2 Processing Pipeline
- **Normalization**: All raw data must be mapped to a common `Job` schema (title, company, URL, location, date).
- **PII Scrubbing**: Personal data (emails, phone numbers) must be removed from scraped content before storage.
- **Deduplication**: The system must identify duplicate jobs across runs and across different sources using content fingerprints.
- **Hard Filtering**: Jobs must be excluded based on region restrictions, scam patterns, and off-topic keywords before scoring.

### 1.3 Matching & Scoring
- **Relevance Scoring**: Jobs must be scored (0-100) based on title relevance, skills overlap, location eligibility, and experience level.
- **Tiering**: Jobs must be categorized into tiers (Top, Strong, Potential, Weak) to prioritize notifications.
- **Explainability**: Every score must be accompanied by a breakdown (e.g., "Matched skills: X, Missing: Y").

### 1.4 Storage & Notification
- **Persistence**: New and updated jobs must be stored in a Google Sheet for the owner's review.
- **Notifications**: A daily Telegram digest must be sent containing only high-match jobs (Top, Strong, Potential).
- **Follow-ups**: The system must track application status and remind the owner of follow-ups 7 days after applying.

## 2. Non-Functional Requirements

- **Reliability**: The system must be resilient to network timeouts and transient API failures.
- **Security**: No secrets (API keys) shall be committed to the repository. All external requests must be HTTPS.
- **Maintainability**: Adding a new source should only require creating a new adapter class and adding a config entry.
- **Efficiency**: The pipeline should complete within 10 minutes on GitHub Actions.

## 3. Acceptance Criteria (Definition of Done)

| Feature | Acceptance Criteria |
|---|---|
| **Scraping** | All enabled sources in `sources.yaml` are contacted and records are parsed. |
| **Filtering** | 100% of jobs containing "US residents only" are excluded for Kenya-based profiles. |
| **Scoring** | Golden examples in `docs/06-matching-and-scoring.md` produce the documented scores. |
| **Storage** | New jobs appear in the Google Sheet; existing jobs have `last_seen` updated. |
| **Notification** | Telegram digest arrives with the correct count of new matching jobs. |
| **Cleanup** | Jobs older than 60 days (and not moved past 'New') are purged from storage. |
| **Health** | Sources with 3+ consecutive failures trigger a Telegram alert. |
