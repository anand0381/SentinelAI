import { Inbox } from 'lucide-react';

function EmptyState({ action, description, title }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/60 px-6 py-10 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-slate-800 text-cyan-300">
        <Inbox size={24} aria-hidden="true" />
      </div>
      <h2 className="mt-4 text-base font-semibold text-white">{title}</h2>
      {description ? <p className="mt-2 text-sm text-slate-400">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export default EmptyState;
