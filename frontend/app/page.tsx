import Link from "next/link";
import FilterPanel from "@/components/FilterPanel";
import JobCard from "@/components/JobCard";
import OverviewStrip from "@/components/OverviewStrip";
import Pagination from "@/components/Pagination";
import { parseFilters, toQueryString, type RawParams } from "@/lib/filters";
import { todayInNairobi } from "@/lib/format";
import { filterOptions, listJobs, overview } from "@/lib/queries";

export const dynamic = "force-dynamic";

export default async function Home({ searchParams }: { searchParams: Promise<RawParams> }) {
  const filters = parseFilters(await searchParams);
  const [list, stats, options] = await Promise.all([listJobs(filters), overview(), filterOptions()]);
  const today = todayInNairobi();
  const back = toQueryString(filters);
  const includeWeak = filters.tiers.includes("weak");
  const pageOneQuery = toQueryString(filters, { page: 1 });
  const pageOneHref = pageOneQuery ? `/?${pageOneQuery}` : "/";

  return (
    <main className="shell">
      <header className="masthead">
        <h1>Job matches</h1>
        <p className="muted">Read-only. Change status and notes in the Google Sheet.</p>
      </header>

      <OverviewStrip overview={stats} shown={list.total} />

      <div className="layout">
        <aside className="rail">
          <FilterPanel filters={filters} options={options} />
        </aside>

        <section aria-label="Jobs">
          {list.jobs.length === 0 ? (
            <div className="empty">
              <h2>{list.total > 0 ? "No jobs on this page" : "No jobs match these filters"}</h2>
              <p>
                {list.total > 0
                  ? "Go back to the first page to see them."
                  : includeWeak
                    ? "Try a lower minimum score or clear a filter."
                    : "Weak matches are hidden by default. Tick Weak in the tier filter, or clear a filter."}
              </p>
              {list.total > 0 ? (
                <Link href={pageOneHref} className="link-button">
                  Go to page 1
                </Link>
              ) : (
                <Link href="/" className="link-button">
                  Clear all filters
                </Link>
              )}
            </div>
          ) : (
            <>
              <div className="list">
                {list.jobs.map((job) => (
                  <JobCard key={job.job_id} job={job} back={back} today={today} />
                ))}
              </div>
              <Pagination filters={filters} page={list.page} pages={list.pages} />
            </>
          )}
        </section>
      </div>
    </main>
  );
}
