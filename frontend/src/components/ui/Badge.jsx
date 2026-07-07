const variants = {
  amber: 'bg-amber-500/15 text-amber-200 ring-amber-400/30',
  cyan: 'bg-cyan-500/15 text-cyan-200 ring-cyan-400/30',
  green: 'bg-emerald-500/15 text-emerald-200 ring-emerald-400/30',
  red: 'bg-red-500/15 text-red-200 ring-red-400/30',
  slate: 'bg-slate-700/60 text-slate-200 ring-slate-500/30',
};

function Badge({ children, variant = 'cyan' }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${variants[variant]}`}>
      {children}
    </span>
  );
}

export default Badge;
