import FilterDisclosure from "./FilterDisclosure";
import { FOUND_OPTIONS, TIERS, WORK_TYPES, activeFilterCount, type Filters } from "@/lib/filters";
import { eligibilityLabel, humanize, tierLabel, workTypeLabel } from "@/lib/format";
import type { FilterOptions } from "@/lib/types";

interface Opt {
  value: string;
  label: string;
}

function Select({ name, label, value, options, anyLabel = "Any" }: { name: string; label: string; value: string | undefined; options: Opt[]; anyLabel?: string }) {
  // Keep a selected value visible even if it is no longer present in the data.
  const withCurrent = value && !options.some((o) => o.value === value) ? [...options, { value, label: value }] : options;
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <select id={name} name={name} defaultValue={value ?? ""}>
        <option value="">{anyLabel}</option>
        {withCurrent.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function FilterPanel({ filters, options }: { filters: Filters; options: FilterOptions }) {
  const workTypes = WORK_TYPES.filter((w) => options.workTypes.includes(w) || w === filters.workType);
  const skillOptions = options.skills.map((s) => ({ value: s.skill, label: `${s.skill} (${s.n})` }));

  return (
    <FilterDisclosure activeCount={activeFilterCount(filters)}>
      <form method="get" action="/" className="filter-form">
        <div className="field">
          <label htmlFor="q">Search</label>
          <input id="q" name="q" type="search" defaultValue={filters.q ?? ""} placeholder="Title, company or text" maxLength={120} />
        </div>

        <fieldset className="field">
          <legend>Match tier</legend>
          {TIERS.map((t) => (
            <label key={t} className="check">
              <input type="checkbox" name="tier" value={t} defaultChecked={filters.tiers.includes(t)} />
              {tierLabel(t)}
            </label>
          ))}
        </fieldset>

        <div className="field">
          <label htmlFor="min_score">Minimum score</label>
          <input id="min_score" name="min_score" type="number" min={0} max={100} inputMode="numeric" defaultValue={filters.minScore || ""} />
        </div>

        <Select name="source" label="Source" value={filters.source} options={options.sources.map((s) => ({ value: s, label: humanize(s) }))} />
        <Select name="work_type" label="Work type" value={filters.workType} options={workTypes.map((w) => ({ value: w, label: workTypeLabel(w) }))} />
        <Select name="eligibility" label="Eligibility" value={filters.eligibility} options={options.eligibility.map((e) => ({ value: e, label: eligibilityLabel(e) }))} />
        <Select name="employment_type" label="Employment type" value={filters.employmentType} options={options.employmentTypes.map((e) => ({ value: e, label: humanize(e) }))} />
        <Select name="status" label="Application status" value={filters.status} options={options.statuses.map((s) => ({ value: s, label: s }))} />
        <Select
          name="found"
          label="Found"
          value={filters.foundDays ? String(filters.foundDays) : undefined}
          anyLabel="Any time"
          options={FOUND_OPTIONS.map((d) => ({ value: String(d), label: d === 1 ? "Last 24 hours" : `Last ${d} days` }))}
        />
        <Select name="skill" label="Skill you have" value={filters.skill} options={skillOptions} />

        <div className="field">
          <label htmlFor="sort">Sort by</label>
          <select id="sort" name="sort" defaultValue={filters.sort}>
            <option value="score">Best score</option>
            <option value="newest">Newest found</option>
            <option value="oldest">Oldest found</option>
            <option value="deadline">Closing soonest</option>
          </select>
        </div>

        <div className="filter-actions">
          <button type="submit" className="button">
            Apply filters
          </button>
          <a href="/" className="link-button">
            Clear
          </a>
        </div>
      </form>
    </FilterDisclosure>
  );
}
