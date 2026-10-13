const enc = new TextEncoder();

/** Constant-time string comparison (length is folded into the result, not an early exit). */
export function safeEqual(a: string | undefined, b: string | undefined): boolean {
  if (a === undefined || b === undefined) return false;
  const ea = enc.encode(a);
  const eb = enc.encode(b);
  let diff = ea.length ^ eb.length;
  const n = Math.max(ea.length, eb.length);
  for (let i = 0; i < n; i++) diff |= (ea[i] ?? 0) ^ (eb[i] ?? 0);
  return diff === 0;
}

/** Checks an Authorization header against the configured credentials. Fails closed if either is unset. */
export function checkBasicAuth(
  header: string | null,
  user: string | undefined,
  pass: string | undefined,
): boolean {
  if (!user || !pass) return false;
  if (!header) return false;
  const [scheme, encoded] = header.split(" ");
  if (scheme !== "Basic" || !encoded) return false;
  let decoded: string;
  try {
    const bytes = Uint8Array.from(atob(encoded), (c) => c.charCodeAt(0));
    decoded = new TextDecoder().decode(bytes);
  } catch {
    return false;
  }
  const i = decoded.indexOf(":");
  if (i < 0) return false;
  const userOk = safeEqual(decoded.slice(0, i), user);
  const passOk = safeEqual(decoded.slice(i + 1), pass);
  return userOk && passOk;
}
