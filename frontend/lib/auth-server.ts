import "server-only";
import { headers } from "next/headers";
import { checkBasicAuth } from "./auth";

/**
 * Second line of defence. Middleware is the first gate, but every page also checks, so a
 * middleware bypass bug can never expose data. Call before any database query.
 */
export async function assertAuth(): Promise<void> {
  const h = await headers();
  if (!checkBasicAuth(h.get("authorization"), process.env.DASH_USER, process.env.DASH_PASS)) {
    throw new Error("Unauthorized");
  }
}
