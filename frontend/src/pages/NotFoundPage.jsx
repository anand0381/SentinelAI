import { Link } from 'react-router-dom';

function NotFoundPage() {
  return (
    <section className="max-w-xl">
      <p className="text-sm font-medium uppercase tracking-wide text-teal-300">
        404
      </p>
      <h1 className="mt-3 text-3xl font-semibold text-white">Page not found</h1>
      <p className="mt-3 text-slate-300">
        The requested SentinelAI page does not exist.
      </p>
      <Link
        to="/dashboard"
        className="mt-6 inline-flex rounded-md bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400"
      >
        Return home
      </Link>
    </section>
  );
}

export default NotFoundPage;
