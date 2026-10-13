import Link from "next/link";

export default function NotFound() {
  return (
    <main className="shell">
      <div className="empty">
        <h1>Job not found</h1>
        <p>It may have closed or aged out of the dashboard. The Google Sheet keeps the full history.</p>
        <Link href="/" className="button">
          Back to the list
        </Link>
      </div>
    </main>
  );
}
