import { neon } from "@neondatabase/serverless";

type Sql = ReturnType<typeof neon>;
let client: Sql | undefined;

function getClient(): Sql {
  if (client) return client;
  const url = process.env.DATABASE_URL;
  if (!url) throw new Error("DATABASE_URL is not set");
  client = neon(url);
  return client;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/**
 * Runs one parameterised query with the reader role. Retries once, because the first request after
 * idle time can hit a compute that is still waking from scale-to-zero. Errors are rethrown as a
 * generic message so SQL text and connection details never reach the page.
 */
export async function query<T>(text: string, params: unknown[] = []): Promise<T[]> {
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const rows = await getClient().query(text, params);
      return rows as T[];
    } catch (err) {
      if (attempt === 1) {
        console.error("db query failed", err instanceof Error ? err.name : "unknown");
        throw new Error("Database query failed");
      }
      await sleep(600);
    }
  }
  throw new Error("Database query failed");
}
