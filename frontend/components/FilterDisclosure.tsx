"use client";

import { useState, type ReactNode } from "react";

/** Only holds the open/closed state for small screens. On wide screens CSS always shows the panel. */
export default function FilterDisclosure({ activeCount, children }: { activeCount: number; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={open ? "filters open" : "filters"}>
      <button
        type="button"
        className="filters-toggle"
        aria-expanded={open}
        aria-controls="filters-body"
        onClick={() => setOpen((o) => !o)}
      >
        {activeCount > 0 ? `Filters, ${activeCount} active` : "Filters"}
      </button>
      <div id="filters-body" className="filters-body">
        {children}
      </div>
    </div>
  );
}
