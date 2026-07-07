function Spinner({ label = 'Loading' }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-slate-300">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-cyan-300" />
      {label}
    </span>
  );
}

export default Spinner;
