function Modal({ children, open, title }) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4">
      <div className="w-full max-w-lg rounded-lg border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        {title ? <h2 className="text-lg font-semibold text-white">{title}</h2> : null}
        <div className={title ? 'mt-4' : ''}>{children}</div>
      </div>
    </div>
  );
}

export default Modal;
