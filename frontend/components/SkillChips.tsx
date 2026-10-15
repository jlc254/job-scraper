function Group({ label, items, kind }: { label: string; items: string[]; kind: "have" | "partial" | "missing" }) {
  if (items.length === 0) return null;
  return (
    <div className="skill-group">
      <h3>{label}</h3>
      <ul className="chips">
        {items.map((s) => (
          <li key={s} className={`chip chip-${kind}`}>
            {s}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function SkillChips({ matched, partial, missing }: { matched: string[]; partial: string[]; missing: string[] }) {
  const partialSet = new Set(partial.map((s) => s.toLowerCase()));
  const fullMatched = matched.filter((s) => !partialSet.has(s.toLowerCase()));

  if (fullMatched.length + partial.length + missing.length === 0) {
    return <p className="muted">No skills were detected in this posting.</p>;
  }
  return (
    <div className="skills">
      <Group label="You have" items={fullMatched} kind="have" />
      <Group label="Partly have" items={partial} kind="partial" />
      <Group label="Missing" items={missing} kind="missing" />
    </div>
  );
}
