import { Activity, BrainCircuit, FileText, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';

const foundations = [
  {
    title: 'FastAPI Backend',
    description: 'Clean architecture API shell with SQLite startup wiring.',
    icon: Activity,
  },
  {
    title: 'React Frontend',
    description: 'Vite, Tailwind CSS, routing, services, and context folders.',
    icon: ShieldAlert,
  },
  {
    title: 'AI Ready',
    description: 'Dependencies prepared for threat classification workflows.',
    icon: BrainCircuit,
  },
  {
    title: 'Reports Ready',
    description: 'Project structure prepared for PDF generation outputs.',
    icon: FileText,
  },
];

function HomePage() {
  return (
    <section className="space-y-8">
      <div className="max-w-3xl">
        <p className="text-sm font-medium uppercase tracking-wide text-teal-300">
          MVP Foundation
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-normal text-white sm:text-5xl">
          SentinelAI
        </h1>
        <p className="mt-4 text-lg leading-8 text-slate-300">
          AI-Powered Cybersecurity Threat Intelligence Platform
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/login"
            className="rounded-md bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400"
          >
            Sign in
          </Link>
          <Link
            to="/threats"
            className="rounded-md border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-100 hover:border-slate-500"
          >
            View threats
          </Link>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {foundations.map((item) => {
          const Icon = item.icon;
          return (
            <article
              key={item.title}
              className="rounded-lg border border-slate-800 bg-slate-900 p-5"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md bg-slate-800 text-teal-300">
                <Icon size={22} aria-hidden="true" />
              </div>
              <h2 className="text-base font-semibold text-white">
                {item.title}
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                {item.description}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default HomePage;
