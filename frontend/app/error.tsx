"use client";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const showDetails = process.env.NODE_ENV !== "production";

  return (
    <main className="shell">
      <div className="empty">
        <h1>Something went wrong</h1>
        <p>The page could not be loaded. Try again in a moment. If this keeps failing, check the server logs.</p>
        {showDetails && error.message ? (
          <p className="muted small">Development detail: {error.message}</p>
        ) : null}
        {error.digest ? <p className="muted small">Reference: {error.digest}</p> : null}
        <button type="button" className="button" onClick={reset}>
          Try again
        </button>
      </div>
    </main>
  );
}
