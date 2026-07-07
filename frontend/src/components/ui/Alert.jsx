const styles = {
  error: 'border-red-500/40 bg-red-500/10 text-red-200',
  info: 'border-cyan-500/40 bg-cyan-500/10 text-cyan-100',
  success: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-100',
  warning: 'border-amber-500/40 bg-amber-500/10 text-amber-100',
};

function Alert({ children, type = 'info' }) {
  return (
    <div className={`rounded-md border px-3 py-2 text-sm ${styles[type]}`}>
      {children}
    </div>
  );
}

export default Alert;
