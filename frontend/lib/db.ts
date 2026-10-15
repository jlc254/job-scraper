import { neon } from "@neondatabase/serverless";
import { Pool } from "pg";

type NeonSql = ReturnType<typeof neon>;
let neonClient: NeonSql | undefined;
let postgresPool: Pool | undefined;

class DatabaseConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DatabaseConfigurationError";
  }
}

function getDatabaseUrl(): URL {
  const value = process.env.DATABASE_URL;
  if (!value) throw new DatabaseConfigurationError("DATABASE_URL is not set");

  try {
    const url = new URL(value);
    if (url.protocol !== "postgres:" && url.protocol !== "postgresql:") {
      throw new Error("DATABASE_URL must use postgres:// or postgresql://");
    }
    return url;
  } catch (err) {
    if (err instanceof DatabaseConfigurationError) throw err;
    throw new DatabaseConfigurationError("DATABASE_URL is not a valid PostgreSQL connection URL");
  }
}

async function runQuery(text: string, params: unknown[]): Promise<unknown[]> {
  const url = getDatabaseUrl();
  const connectionString = url.toString();

  // Neon exposes an HTTP SQL endpoint. Local PostgreSQL (including Compose) speaks
  // the regular PostgreSQL protocol, so it must use node-postgres instead.
  if (url.hostname.endsWith(".neon.tech") && !process.env.DB_USE_PG) {
    neonClient ??= neon(connectionString);
    return (await neonClient.query(text, params)) as unknown[];
  }

  postgresPool ??= new Pool({
    connectionString,
    max: 5,
    connectionTimeoutMillis: 5_000,
    idleTimeoutMillis: 30_000,
  });
  const result = await postgresPool.query(text, params);
  return result.rows;
}

function errorProperties(err: unknown): { name: string; message: string; code?: string } {
  if (!(err instanceof Error)) return { name: "UnknownError", message: String(err) };
  const code = "code" in err && typeof err.code === "string" ? err.code : undefined;
  return { name: err.name, message: err.message, ...(code ? { code } : {}) };
}

function isRetryable(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  const code = "code" in err && typeof err.code === "string" ? err.code : "";

  // Retry connection failures and a few transient PostgreSQL conditions. SQL,
  // schema, and permission errors won't improve after waiting.
  const isPostgresConnectionError = code.startsWith("08") ||
    ["40001", "40P01", "53300", "57P01", "57P02", "57P03"].includes(code);
  if (isPostgresConnectionError) {
    return true;
  }
  if (err.name === "NeonDbError" && "sourceError" in err && err.sourceError instanceof Error) {
    return isRetryable(err.sourceError);
  }
  return ["ECONNRESET", "ECONNREFUSED", "ETIMEDOUT", "EHOSTUNREACH", "ENETUNREACH"].includes(code);
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const isProduction = process.env.NODE_ENV === "production";

/**
 * Uses Neon HTTP for Neon URLs and node-postgres for local PostgreSQL URLs.
 * Transient connection failures get one retry. Development/test errors include
 * their database message; production throws a generic error and logs diagnostics
 * only on the server.
 */
export async function query<T>(text: string, params: unknown[] = []): Promise<T[]> {
  let lastError: unknown;
  
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      return (await runQuery(text, params)) as T[];
    } catch (err) {
      lastError = err;
      const retry = attempt === 0 && isRetryable(err);
      if (retry) {
        await sleep(600);
        continue;
      }
      break;
    }
  }

  const details = errorProperties(lastError);
  console.error("[db] query failed", { ...details, attempt: 1 });
  const codePart = details.code ? ` (${details.code})` : "";
  const message = isProduction
    ? "Database query failed"
    : `Database query failed${codePart}: ${details.message}`;
  throw new Error(message, { cause: lastError });
}
