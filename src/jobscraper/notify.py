"""Send a planned digest and mark what was delivered, so nothing is sent twice (doc 07)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime

from jobscraper.models import JobUpdate
from jobscraper.notifications.base import Notifier
from jobscraper.notifications.digest import Digest
from jobscraper.storage.base import Storage
from jobscraper.utils.errors import StorageError

log = logging.getLogger(__name__)


@dataclass
class Delivery:
    sent: int = 0
    total: int = 0
    error: str | None = None
    jobs_marked: int = 0
    follow_ups_marked: int = 0
    mark_error: str | None = None


def deliver_digest(
    digest: Digest, notifier: Notifier, storage: Storage, now: datetime, today: date
) -> Delivery:
    """Send one message at a time and mark its rows straight after it is delivered.

    If a send fails, delivery stops. Rows in later messages stay unmarked and are picked up
    by the next run. If marking fails after a send, the owner may see a job twice, so that
    is reported loudly rather than hidden.
    """
    result = Delivery(total=len(digest.batches))
    for batch in digest.batches:
        outcome = notifier.send([batch.text])
        if outcome.sent < 1:
            result.error = outcome.error or "send failed"
            break
        result.sent += 1
        updates = [JobUpdate(job_id=j, fields={"notified_at": now.isoformat()}) for j in batch.job_ids]
        updates += [
            JobUpdate(job_id=j, fields={"follow_up_reminded_on": today.isoformat()})
            for j in batch.follow_up_ids
        ]
        if not updates:
            continue
        for attempt in (1, 2):
            try:
                storage.update_jobs(updates)
                result.jobs_marked += len(batch.job_ids)
                result.follow_ups_marked += len(batch.follow_up_ids)
                break
            except StorageError as exc:
                log.warning("could not mark notified", extra={"ctx": {"attempt": attempt}})
                result.mark_error = str(exc)
    return result
