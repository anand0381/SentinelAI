const variants = {
  primary: 'bg-cyan-400 text-slate-950 hover:bg-cyan-300',
  secondary: 'border border-slate-700 bg-slate-900 text-slate-100 hover:border-cyan-400',
  danger: 'bg-red-500 text-white hover:bg-red-400',
  ghost: 'text-slate-300 hover:bg-slate-800 hover:text-white',
};

function Button({
  children,
  className = '',
  disabled = false,
  type = 'button',
  variant = 'primary',
  ...props
}) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      disabled={disabled}
      type={type}
      {...props}
    >
      {children}
    </button>
  );
}

export default Button;
