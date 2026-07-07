function Input({ className = '', error = '', label, ...props }) {
  return (
    <label className="block">
      {label ? (
        <span className="text-sm font-medium text-slate-200">{label}</span>
      ) : null}
      <input
        className={`mt-2 w-full rounded-md border bg-slate-950 px-3 py-2 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400 ${
          error ? 'border-red-400' : 'border-slate-700'
        } ${className}`}
        {...props}
      />
      {error ? <span className="mt-1 block text-xs text-red-300">{error}</span> : null}
    </label>
  );
}

export default Input;
