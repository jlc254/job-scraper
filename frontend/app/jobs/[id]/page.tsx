import Link from "next/link";
import { notFound } from "next/navigation";
import ScoreBadge from "@/components/ScoreBadge";
import ScoreBar from "@/components/ScoreBar";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import SkillChips from "@/components/SkillChips";
import { assertAuth } from "@/lib/auth-server";
import { parseBreakdown } from "@/lib/breakdown";
import { sanitizeBack, type RawParams } from "@/lib/filters";
import {
  deadlineNote,
  eligibilityLabel,
  formatDate,
  formatDateTime,
  humanize,
  safeHttpUrl,
  todayInNairobi,
  workTypeLabel,
} from "@/lib/format";
import { getJob } from "@/lib/queries";

export const dynamic = "force-dynamic";

const ID_RE = /^[A-Za-z0-9_-]{1,64}$/;

export default async function JobPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<RawParams>;
}) {
  await assertAuth();
  const { id } = await params;
  if (!ID_RE.test(id)) notFound();
  const job = await getJob(id);
  if (!job) notFound();

  const back = sanitizeBack((await searchParams).back);
  const backHref = back ? `/?${back}` : "/";
  const breakdown = parseBreakdown(job.match_breakdown);
  const applyUrl = safeHttpUrl(job.job_url);
  const deadline = deadlineNote(job.application_deadline, todayInNairobi());

  return (
    <main className="shell detail">
      <p>
        <Link href={backHref} className="back">
          Back to the list
        </Link>
      </p>

      <header className="detail-head">
        <ScoreBadge score={job.match_score} tier={job.match_tier} large />
        <div>
          <h1>{job.title}</h1>
          <p className="company">{job.company}</p>
          <ul className="facts">
            {job.location ? <li>{job.location}</li> : null}
            <li>{workTypeLabel(job.work_type)}</li>
            <li className={job.remote_eligibility === "unclear" ? "fact-warn" : undefined}>
              {eligibilityLabel(job.remote_eligibility)}
            </li>
            {job.employment_type !== "unknown" ? <li>{humanize(job.employment_type)}</li> : null}
            {job.salary ? <li>{job.salary}</li> : null}
          </ul>
          <ul className="chips">
            {job.application_status !== "New" ? <li className="chip chip-status">Status: {job.application_status}</li> : null}
            {job.is_repost ? <li className="chip chip-status">Repost</li> : null}
          </ul>
        </div>
        <div className="job-side">
          {applyUrl ? (
            <a className="button" href={applyUrl} target="_blank" rel="noopener noreferrer">
              Apply
            </a>
          ) : (
            <span className="muted small">No valid link</span>
          )}
          <span className="source">via {humanize(job.source)}</span>
        </div>
      </header>

      <ScoreBar breakdown={breakdown} score={job.match_score} />
      <p className="note">Eligibility comes from the source listing. Read the posting before applying.</p>

      <section>
        <h2>Why this score</h2>
        {breakdown ? (
          <ScoreBreakdown breakdown={breakdown} score={job.match_score} />
        ) : (
          <p className="muted">No score breakdown was stored for this job.</p>
        )}
      </section>

      <section>
        <h2>Skills</h2>
        <SkillChips
          matched={job.skills_matched}
          partial={breakdown?.skills.partial ?? []}
          missing={job.skills_missing}
        />
      </section>

      {job.recommended_action ? (
        <section>
          <h2>Recommended action</h2>
          <p>{job.recommended_action}</p>
        </section>
      ) : null}

      {job.checklist ? (
        <section>
          <h2>Checklist</h2>
          <p className="prewrap">{job.checklist}</p>
        </section>
      ) : null}

      <section>
        <h2>Excerpt</h2>
        <p className="prewrap">{job.description_excerpt || "No excerpt stored."}</p>
        {applyUrl ? (
          <p>
            <a href={applyUrl} target="_blank" rel="noopener noreferrer">
              Read the full posting
            </a>
          </p>
        ) : null}
      </section>

      <section>
        <h2>Dates</h2>
        <dl className="dates-list">
          <dt>Posted</dt>
          <dd>{formatDate(job.date_posted)}</dd>
          <dt>Deadline</dt>
          <dd>{job.application_deadline ? `${formatDate(job.application_deadline)}${deadline.text ? `, ${deadline.text.toLowerCase()}` : ""}` : "None listed"}</dd>
          <dt>First found</dt>
          <dd>{formatDateTime(job.first_seen)}</dd>
          <dt>Last seen</dt>
          <dd>{formatDateTime(job.last_seen)}</dd>
          <dt>Source</dt>
          <dd>{humanize(job.source)}</dd>
        </dl>
      </section>
    </main>
  );
}
