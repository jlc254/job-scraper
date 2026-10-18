/** Adds or replaces the `profile` query parameter on an internal href.
 *
 *  Internal links are relative, like "/?tier=top" or "/jobs/abc?back=...". Anything
 *  with a scheme (https://, mailto:) or protocol-relative ("//host") is external and is
 *  returned untouched: apply links point at job boards and must never be rewritten.
 *  Pure string handling; no imports, so it is trivially unit tested.
 */
export function withProfile(href: string, profile: string): string {
  if (!href.startsWith("/") || href.startsWith("//")) return href;
  const hashIndex = href.indexOf("#");
  const hash = hashIndex === -1 ? "" : href.slice(hashIndex);
  const base = hashIndex === -1 ? href : href.slice(0, hashIndex);
  const queryIndex = base.indexOf("?");
  const path = queryIndex === -1 ? base : base.slice(0, queryIndex);
  const params = new URLSearchParams(queryIndex === -1 ? "" : base.slice(queryIndex + 1));
  params.set("profile", profile);
  return `${path}?${params.toString()}${hash}`;
}
