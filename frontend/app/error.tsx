"use client";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="shell">
      <div className="empty">
        <h1>The jobs could not be loaded</h1>
        <p>The database did not answer. Try again in a moment. If it keeps failing, check the Neon project and the Vercel logs.</p>
        {error.digest ? <p className="muted small">Reference: {error.digest}</p> : null}
        <button type="button" className="button" onClick={reset}>
          Try again
        </button>
      </div>
    </main>
  );
}
