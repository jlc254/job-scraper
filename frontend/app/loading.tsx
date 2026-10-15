export default function Loading() {
  return (
    <main className="shell" aria-busy="true">
      <p className="muted" role="status">Loading jobs. The first load after a quiet period can take a few seconds.</p>
      <div className="list">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="job skeleton" aria-hidden="true" />
        ))}
      </div>
    </main>
  );
}
