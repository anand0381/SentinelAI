import { Bell, CheckCheck, Trash2, X } from 'lucide-react';

import Badge from '../ui/Badge.jsx';
import Button from '../ui/Button.jsx';
import { useNotifications } from '../../hooks/useNotifications.js';
import { formatDateTime } from '../../utils/formatters.js';

const severityVariant = {
  CRITICAL: 'red',
  HIGH: 'amber',
  INFO: 'cyan',
  LOW: 'green',
  MEDIUM: 'cyan',
};

function NotificationCenter({ onClose }) {
  const {
    dismissNotification,
    markAllRead,
    markRead,
    notifications,
    unreadCount,
  } = useNotifications();

  return (
    <div className="absolute right-0 mt-2 w-[min(28rem,calc(100vw-2rem))] rounded-lg border border-slate-800 bg-slate-900 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <div>
          <p className="text-sm font-semibold text-white">Notifications</p>
          <p className="text-xs text-slate-500">{unreadCount} unread alerts</p>
        </div>
        <div className="flex items-center gap-2">
          <Button className="px-2 py-1" onClick={markAllRead} variant="ghost">
            <CheckCheck size={15} aria-hidden="true" />
          </Button>
          <button
            aria-label="Close notifications"
            className="rounded-md p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
            onClick={onClose}
            type="button"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      </div>

      <div className="max-h-[28rem] overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-6 py-10 text-center">
            <Bell className="text-slate-600" size={28} aria-hidden="true" />
            <p className="mt-3 text-sm font-medium text-white">No notifications yet</p>
            <p className="mt-1 text-xs text-slate-500">Live SOC alerts will appear here.</p>
          </div>
        ) : (
          notifications.map((notification) => (
            <div
              className={`border-b border-slate-800 px-4 py-3 ${
                notification.status === 'unread' ? 'bg-cyan-400/5' : 'bg-transparent'
              } ${
                notification.severity === 'CRITICAL' ? 'border-l-4 border-l-red-500' : ''
              }`}
              key={notification.id}
            >
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-white">{notification.title}</p>
                    <Badge variant={severityVariant[notification.severity] || 'cyan'}>
                      {notification.severity}
                    </Badge>
                    {notification.status === 'unread' ? (
                      <span className="h-2 w-2 rounded-full bg-cyan-300" aria-label="Unread" />
                    ) : null}
                  </div>
                  <p className="mt-1 text-sm leading-5 text-slate-300">{notification.message}</p>
                  <p className="mt-2 text-xs text-slate-500">
                    {notification.type} | {formatDateTime(notification.timestamp)}
                  </p>
                </div>
                <div className="flex shrink-0 gap-1">
                  {notification.status === 'unread' ? (
                    <button
                      aria-label="Mark notification read"
                      className="rounded-md p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
                      onClick={() => markRead(notification.id)}
                      type="button"
                    >
                      <CheckCheck size={15} aria-hidden="true" />
                    </button>
                  ) : null}
                  <button
                    aria-label="Dismiss notification"
                    className="rounded-md p-1 text-slate-400 hover:bg-slate-800 hover:text-red-200"
                    onClick={() => dismissNotification(notification.id)}
                    type="button"
                  >
                    <Trash2 size={15} aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default NotificationCenter;
