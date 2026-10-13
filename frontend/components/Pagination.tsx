import Link from "next/link";
import { toQueryString, type Filters } from "@/lib/filters";

function pageWindow(page: number, count: number): (number | "gap")[] {
  const wanted = new Set([1, count, page - 1, page, page + 1]);
  const pages = [...wanted].filter((p) => p >= 1 && p <= count).sort((a, b) => a - b);
  const out: (number | "gap")[] = [];
  pages.forEach((p, i) => {
    const prev = pages[i - 1];
    if (prev !== undefined && p - prev > 1) out.push("gap");
    out.push(p);
  });
  return out;
}

export default function Pagination({ filters, page, pages }: { filters: Filters; page: number; pages: number }) {
  if (pages <= 1) return null;
  const hrefFor = (p: number): string => {
    const qs = toQueryString(filters, { page: p });
    return qs ? `/?${qs}` : "/";
  };

  return (
    <nav className="pagination" aria-label="Pages">
      {page > 1 ? (
        <Link href={hrefFor(page - 1)} rel="prev">
          Previous
        </Link>
      ) : (
        <span className="disabled">Previous</span>
      )}
      <ul>
        {pageWindow(page, pages).map((p, i) =>
          p === "gap" ? (
            <li key={`gap-${i}`} aria-hidden="true">
              …
            </li>
          ) : (
            <li key={p}>
              {p === page ? (
                <span className="current" aria-current="page">
                  {p}
                </span>
              ) : (
                <Link href={hrefFor(p)}>{p}</Link>
              )}
            </li>
          ),
        )}
      </ul>
      {page < pages ? (
        <Link href={hrefFor(page + 1)} rel="next">
          Next
        </Link>
      ) : (
        <span className="disabled">Next</span>
      )}
    </nav>
  );
}
