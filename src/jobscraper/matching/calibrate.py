"""Calibration helpers (doc 06): label about 30 real jobs, then compare with the tiers.

Target: at least 80% agreement between Top/Strong and 'apply'.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

LABELS = ("apply", "maybe", "skip")
TIERS = ("top", "strong", "potential", "weak")
TARGET = 0.80


def select_for_labeling(rows: list[dict[str, str]], limit: int = 30) -> list[dict[str, str]]:
    """Newest first, spread across tiers so every tier gets looked at."""
    by_tier: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sorted(rows, key=lambda r: r.get("first_seen", ""), reverse=True):
        by_tier[row.get("match_tier") or "unscored"].append(row)
    picked: list[dict[str, str]] = []
    while len(picked) < limit and any(by_tier.values()):
        for tier in (*TIERS, "unscored"):
            if by_tier[tier] and len(picked) < limit:
                picked.append(by_tier[tier].pop(0))
    return picked


def write_label_sheet(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        # Tier and score are left out on purpose, so your label comes from your own reading.
        writer.writerow(["job_id", "title", "company", "job_url", "label"])
        for r in rows:
            writer.writerow([r.get("job_id"), r.get("title"), r.get("company"), r.get("job_url"), ""])


def read_labels(path: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            label = (row.get("label") or "").strip().lower()
            if label in LABELS and row.get("job_id"):
                labels[row["job_id"]] = label
    return labels


def agreement_report(rows: list[dict[str, str]], labels: dict[str, str]) -> str:
    tiers = {r["job_id"]: (r.get("match_tier") or "unscored") for r in rows if r.get("job_id")}
    titles = {r["job_id"]: f"{r.get('title')} at {r.get('company')}" for r in rows if r.get("job_id")}
    joined = {j: (tiers[j], lab) for j, lab in labels.items() if j in tiers}
    if not joined:
        return "No labelled jobs matched stored rows."
    matrix: Counter[tuple[str, str]] = Counter(joined.values())
    lines = [f"Labelled jobs: {len(joined)}", "", "tier        apply  maybe  skip"]
    for tier in (*TIERS, "unscored"):
        counts = [matrix[(tier, lab)] for lab in LABELS]
        if any(counts):
            lines.append(f"{tier:<10}  {counts[0]:>5}  {counts[1]:>5}  {counts[2]:>4}")
    high = [(t, lab) for t, lab in joined.values() if t in ("top", "strong")]
    apply_ = [(t, lab) for t, lab in joined.values() if lab == "apply"]
    lines.append("")
    if high:
        precision = sum(1 for _, lab in high if lab == "apply") / len(high)
        lines.append(f"Top/Strong that you labelled apply: {precision:.0%} (target {TARGET:.0%})")
    if apply_:
        recall = sum(1 for t, _ in apply_ if t in ("top", "strong")) / len(apply_)
        lines.append(f"Jobs you labelled apply that scored Top/Strong: {recall:.0%}")
    too_high = [titles[j] for j, (t, lab) in joined.items() if t in ("top", "strong") and lab == "skip"]
    too_low = [titles[j] for j, (t, lab) in joined.items() if t in ("potential", "weak") and lab == "apply"]
    if too_high:
        lines += ["", "Scored too high (Top/Strong but skip):", *[f"- {t}" for t in too_high]]
    if too_low:
        lines += ["", "Scored too low (Potential/Weak but apply):", *[f"- {t}" for t in too_low]]
    lines += ["", "Adjust weights only in config/scoring.yaml and increment scoring_version."]
    return "\n".join(lines)
