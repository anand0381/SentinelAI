import { useCallback, useMemo, useState } from 'react';
import { CheckCircle, Info, TriangleAlert, X, XCircle } from 'lucide-react';

import { ToastContext } from './toastStore.js';

const styles = {
  error: {
    icon: XCircle,
    className: 'border-red-500/40 bg-red-500/10 text-red-100',
  },
  info: {
    icon: Info,
    className: 'border-cyan-500/40 bg-cyan-500/10 text-cyan-100',
  },
  success: {
    icon: CheckCircle,
    className: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-100',
  },
  warning: {
    icon: TriangleAlert,
    className: 'border-amber-500/40 bg-amber-500/10 text-amber-100',
  },
};

function createToastId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    ({ message, title, type = 'info' }) => {
      const id = createToastId();
      setToasts((current) => [...current, { id, message, title, type }]);
      window.setTimeout(() => removeToast(id), 4500);
    },
    [removeToast],
  );

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 top-4 z-[60] flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-3">
        {toasts.map((toast) => {
          const style = styles[toast.type] || styles.info;
          const Icon = style.icon;
          return (
            <div
              className={`rounded-lg border px-4 py-3 shadow-2xl backdrop-blur ${style.className}`}
              key={toast.id}
              role="status"
            >
              <div className="flex gap-3">
                <Icon className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
                <div className="min-w-0 flex-1">
                  {toast.title ? <p className="text-sm font-semibold">{toast.title}</p> : null}
                  <p className="text-sm leading-5 opacity-90">{toast.message}</p>
                </div>
                <button
                  aria-label="Dismiss notification"
                  className="rounded-md p-1 opacity-75 transition hover:bg-white/10 hover:opacity-100"
                  onClick={() => removeToast(toast.id)}
                  type="button"
                >
                  <X size={16} aria-hidden="true" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
