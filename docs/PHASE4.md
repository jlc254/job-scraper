# Phase 4 notes: matching and scoring

New: `matching/` (settings, filters, skills, scorer, explain, brief, calibrate), Excluded-tab support in
storage, `process_jobs` in pipeline.py, CLI commands `brief` and `calibrate`, example configs
`config/profile.example.yaml` and `config/scoring.example.yaml`.
Removed: `prefilter.py` (the interim off-topic filter). Its job is now the `off_topic` hard filter,
and filtered jobs are logged to the Excluded tab with a reason instead of vanishing.

Setup (once):

    cp config/profile.example.yaml config/profile.yaml     # then edit to your real profile
    cp config/scoring.example.yaml config/scoring.yaml
    # create a tab named Excluded in the Sheet (headers are added for you)
    pytest
    python main.py run --storage sqlite --no-notify        # twice: second run adds 0 and logs 0 excluded
    python main.py brief <job_id or prefix> --storage sqlite
    python main.py calibrate --export output/labels.csv --storage sqlite
    # fill the label column (apply/maybe/skip) by reading each posting, then:
    python main.py calibrate --labels output/labels.csv --storage sqlite

Pipeline order: normalize, hard filters, dedupe, score new jobs, store. Excluded jobs go to the
Excluded tab once (reruns skip them). A stored job that later fails a filter is left alone.

IMPORTANT: your real profile.yaml and scoring.yaml were never shared with me, so the schema here is mine.
Point values default to doc 06 and the golden tests reproduce doc 06 examples A, B, C and D against the
example files. If your own files use different keys, paste them and I will reconcile the loader.

Decisions to confirm:
1. Experience: a title containing "manager" scores 2 (doc 06), except "customer success manager" (configurable
   in scoring.yaml: experience.manager_exceptions).
2. Location: "Kenya" without a city scores 16 (other Kenyan city). Unknown location and remote-with-no-region
   both score 10 and carry the "eligibility unconfirmed" flag. The "EAT-compatible timezone" rule (16) exists
   but nothing sets timezone_limited yet, so it is dormant.
3. Freshness: if the posting date is unknown, the discovery date is used (so it scores as fresh).
4. Region filter: besides phrase patterns, any job whose source lists specific countries without Kenya or
   Africa (Himalayas locationRestrictions, Jobicy jobGeo, WWR region) is excluded as region_restricted.
   EMEA is left "unclear" and scored, not excluded.
5. Recommended action: one main action by rule, then advisories that must not be hidden
   (eligibility check, missing common tool such as Freshdesk).
6. Existing rows are never rescored (the full posting text is not stored, only a 1000-char excerpt). Changing
   scoring_version affects new jobs only. Say if you want a rescore-from-excerpt command.
7. Salary is neutral (5) until you set salary_floor after calibration (D11).

Not in this phase: Telegram digest and follow-up reminders (Phase 5), retention of Excluded rows (Phase 7).
