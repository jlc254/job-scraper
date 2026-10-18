import Link from "next/link";
import ScoreBadge from "./ScoreBadge";
import ScoreBar from "./ScoreBar";
import { parseBreakdown } from "@/lib/breakdown";
import {
  deadlineNote,
  eligibilityLabel,
  humanize,
  isoToNairobiDate,
  relativeDay,
  safeHttpUrl,
  workTypeLabel,
} from "@/lib/format";
import { withProfile } from "@/lib/profile-links";
import type { Job } from "@/lib/types";

const SHOWN = 4;

function SkillLine({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  const more = items.length > SHOWN ? `, and ${items.length - SHOWN} more` : "";
  return (
    <p className="skill-line">
      <span className="skill-line-label">{label}</span> {items.slice(0, SHOWN).join(", ")}
      {more}
    </p>
  );
}

export default function JobCard({
  job,
  back,
  today,
  profile,
}: {
  job: Job;
  back: string;
  today: string;
  profile: string;
}) {
  const href = withProfile(
    `/jobs/${encodeURIComponent(job.job_id)}${back ? `?back=${encodeURIComponent(back)}` : ""}`,
    profile,
  );
  const applyUrl = safeHttpUrl(job.job_url);
  const deadline = deadlineNote(job.application_deadline, today);
  const breakdown = parseBreakdown(job.match_breakdown);
  const posted = job.date_posted ? `Posted ${relativeDay(job.date_posted, today)}` : null;

  return (
    <article className="job">
      <div className="job-score">
        <ScoreBadge score={job.match_score} tier={job.match_tier} />
      </div>

      <div className="job-main">
        <h2 className="job-title">
          <Link href={href}>{job.title}</Link>
        </h2>
        <p className="company">{job.company}</p>

        <ul className="facts">
          {job.location ? <li>{job.location}</li> : null}
          <li>{workTypeLabel(job.work_type)}</li>
          <li className={job.remote_eligibility === "unclear" ? "fact-warn" : undefined}>
            {eligibilityLabel(job.remote_eligibility)}
          </li>
          {job.salary ? <li>{job.salary}</li> : null}
        </ul>

        <p className="dates">
          {posted ? <span>{posted}</span> : null}
          <span>Found {relativeDay(isoToNairobiDate(job.first_seen), today)}</span>
          {deadline.urgency !== "none" ? <span className={`deadline deadline-${deadline.urgency}`}>{deadline.text}</span> : null}
        </p>

        {job.application_status !== "New" || job.is_repost ? (
          <ul className="chips">
            {job.application_status !== "New" ? <li className="chip chip-status">Status: {job.application_status}</li> : null}
            {job.is_repost ? <li className="chip chip-status">Repost</li> : null}
          </ul>
        ) : null}

        <SkillLine label="You have" items={job.skills_matched} />
        <SkillLine label="Missing" items={job.skills_missing} />
        <ScoreBar breakdown={breakdown} score={job.match_score} />
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
    </article>
  );
}
