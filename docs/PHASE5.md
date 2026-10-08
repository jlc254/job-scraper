# Phase 5 notes: Telegram digest and follow-up reminders

New: `notifications/` (base, telegram, digest), `notify.py` (send and mark), `utils/dates.py`,
CLI command `notify-test`, and digest sending inside `run`.

Try it (needs the bot token and chat ID you already created):

    export TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=...
    python main.py notify-test                       # one test message to your chat
    python main.py run --storage sqlite --no-notify  # prints the digest preview instead of sending
    python main.py run --storage sqlite              # sends it, then marks rows notified
    python main.py run --storage sqlite              # again: nothing is re-sent

Behaviour:
- The digest is built from STORED rows with an empty notified_at, so jobs from a run whose send failed
  go out on the next run. Each message's jobs are marked notified_at right after that message is delivered.
- Contents: Top and Strong jobs, plus the best 5 Potential jobs first seen within 2 days. Weak jobs are
  never sent. Jobs you have already handled (application_status other than New), inactive and expired
  jobs are skipped. Max 30 jobs per run. 10 jobs per message, each message under 3800 characters.
- Follow-ups: for rows with application_status = Applied, due on your follow_up_date, else applied_on + 7
  days. Computed at digest time and NEVER written into your columns. A new system column,
  follow_up_reminded_on, records that a reminder was sent so it fires once per due date (moving the due
  date later makes it fire again). Dates accept 2026-10-01, 01/10/2026 (day first), 1 Oct 2026, and
  Sheets serial numbers. Unreadable dates are listed in the digest instead of silently ignored.
- RUN line in the last message. A detailed RUN REPORT message is added only when a source is degraded,
  blocked, failed, partial or rate limited. If saving to the Sheet fails, an alert is sent.
- An empty digest ("NO NEW MATCHING JOBS") is sent only on the morning run (before 12:00 EAT) or when
  something is wrong, so quiet afternoon runs stay silent.
- Plain text only (no parse_mode), link previews off. Scraped text has control and direction-override
  characters removed and is length-capped. Non-http links are replaced by "link unavailable".
- Telegram handling: about one message per second, 429 honours retry_after up to 30 s, 5xx and network errors
  retry 3 times with backoff, 400/401/403/404 stop at once. Errors never contain the URL or token.
- Exit codes: 0 ok, 2 config, 3 storage, 4 notification failure.

Decisions to confirm:
1. Added a "Next:" line (recommended action) and a "Deadline:" item to each job, beyond the doc 04 sample.
2. Extra system column follow_up_reminded_on (created automatically). notified_at is now writable by the tool.
3. Potential jobs beyond the 5-per-digest cap, or older than 2 days, are never sent. Say if you want a longer window.
4. Day-first dates: 03/04/2026 reads as 3 April.
5. Not built (Phase 6/7): the workflow's failure alert step, dead-man's-switch ping, three-strikes alert,
   automatic resend of output/unsaved-*.json.

Untested here: nothing in this phase has been run (no network, dependencies not installable in my sandbox).
