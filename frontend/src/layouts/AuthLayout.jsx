import { Outlet } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';

function AuthLayout() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="grid min-h-screen lg:grid-cols-[1fr_520px]">
        <section className="hidden bg-slate-900 lg:block">
          <div className="flex h-full flex-col justify-between p-10">
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-md bg-cyan-400/15 text-cyan-300">
                <ShieldCheck size={26} aria-hidden="true" />
              </span>
              <div>
                <p className="font-semibold text-white">SentinelAI</p>
                <p className="text-sm text-slate-400">Threat Intelligence Platform</p>
              </div>
            </div>
            <div className="max-w-xl">
              <p className="text-sm font-medium uppercase tracking-wide text-cyan-300">
                Cybersecurity Operations
              </p>
              <h1 className="mt-4 text-4xl font-semibold text-white">
                Monitor threats, incidents, and response readiness from one workspace.
              </h1>
              <p className="mt-5 text-base leading-7 text-slate-300">
                A focused dashboard foundation for final-year project demonstrations and
                security operations workflows.
              </p>
            </div>
            <p className="text-sm text-slate-500">Secure access powered by JWT authentication.</p>
          </div>
        </section>
        <section className="flex items-center justify-center px-4 py-10">
          <div className="w-full max-w-md">
            <Outlet />
          </div>
        </section>
      </main>
    </div>
  );
}

export default AuthLayout;
