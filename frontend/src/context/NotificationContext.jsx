import { createContext, useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { useAuth } from './AuthContext.jsx';
import { useToast } from '../hooks/useToast.js';
import { dashboardService } from '../services/dashboardService.js';
import { threatService } from '../services/threatService.js';

export const NotificationContext = createContext(null);

const storageKey = 'sentinelai_notifications';
const pollIntervalMs = 20000;
const maxNotifications = 60;

function createNotificationId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function readStoredNotifications() {
  try {
    const raw = localStorage.getItem(storageKey);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function persistNotifications(notifications) {
  localStorage.setItem(storageKey, JSON.stringify(notifications.slice(0, maxNotifications)));
}

function threatTimestamp(threat) {
  return threat?.updated_at || threat?.last_analyzed || threat?.detected_at || '';
}

function isAiCompleted(threat) {
  return Boolean(threat?.last_analyzed && threat?.ai_summary);
}

function isAiFailed(threat) {
  return Boolean(threat?.source === 'Endpoint Agent' && !threat?.last_analyzed);
}

function getNotificationStyle(type, severity) {
  if (severity === 'CRITICAL') {
    return { toastType: 'error', title: 'Critical Threat Detected' };
  }

  if (type === 'ai_completed') {
    return { toastType: 'success', title: 'AI Analysis Completed' };
  }

  if (type === 'sync_completed') {
    return { toastType: 'success', title: 'Threat Intelligence Sync Completed' };
  }

  if (type === 'threat_updated') {
    return { toastType: 'warning', title: 'Threat Updated' };
  }

  return { toastType: 'warning', title: 'New Threat Detected' };
}

export function NotificationProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const { showToast } = useToast();
  const [notifications, setNotifications] = useState(() => readStoredNotifications());
  const [refreshVersion, setRefreshVersion] = useState(0);
  const knownThreatsRef = useRef(new Map());
  const initializedRef = useRef(false);
  const pollingRef = useRef(false);

  const unreadCount = useMemo(
    () => notifications.filter((notification) => notification.status === 'unread').length,
    [notifications],
  );

  const storeNotifications = useCallback((updater) => {
    setNotifications((current) => {
      const next = typeof updater === 'function' ? updater(current) : updater;
      const limited = next.slice(0, maxNotifications);
      persistNotifications(limited);
      return limited;
    });
  }, []);

  const createNotification = useCallback(
    ({ message, severity = 'INFO', threatId, title, type }) => {
      const notification = {
        id: createNotificationId(),
        message,
        severity,
        status: 'unread',
        threatId,
        timestamp: new Date().toISOString(),
        title,
        type,
      };

      storeNotifications((current) => [notification, ...current]);
      const style = getNotificationStyle(type, severity);
      showToast({
        message,
        title: title || style.title,
        type: style.toastType,
      });

      console.info('notification created', notification);

      if (severity === 'CRITICAL') {
        console.warn('critical alert generated', notification);
      }

      return notification;
    },
    [showToast, storeNotifications],
  );

  const markRead = useCallback(
    (id) => {
      storeNotifications((current) =>
        current.map((notification) =>
          notification.id === id ? { ...notification, status: 'read' } : notification,
        ),
      );
      console.info('notification read', { id });
    },
    [storeNotifications],
  );

  const markAllRead = useCallback(() => {
    storeNotifications((current) =>
      current.map((notification) => ({ ...notification, status: 'read' })),
    );
    console.info('notification read', { scope: 'all' });
  }, [storeNotifications]);

  const dismissNotification = useCallback(
    (id) => {
      storeNotifications((current) => current.filter((notification) => notification.id !== id));
    },
    [storeNotifications],
  );

  const notifyThreatChange = useCallback(
    (threat, previous) => {
      const severity = threat.severity || 'INFO';

      if (!previous) {
        createNotification({
          message: `${threat.title} from ${threat.source || 'unknown source'}`,
          severity,
          threatId: threat.id,
          title: severity === 'CRITICAL' ? 'Critical Threat Detected' : 'New Threat Detected',
          type: 'new_threat',
        });
        return;
      }

      if (!previous.aiCompleted && isAiCompleted(threat)) {
        createNotification({
          message: `${threat.title} analysis is ready.`,
          severity,
          threatId: threat.id,
          title: 'AI Analysis Completed',
          type: 'ai_completed',
        });
        return;
      }

      if (previous.timestamp !== threatTimestamp(threat)) {
        createNotification({
          message: `${threat.title} was updated.`,
          severity,
          threatId: threat.id,
          title: severity === 'CRITICAL' ? 'Critical Threat Updated' : 'Threat Updated',
          type: 'threat_updated',
        });
      }
    },
    [createNotification],
  );

  const pollLiveState = useCallback(async () => {
    if (!isAuthenticated || pollingRef.current) {
      return;
    }

    pollingRef.current = true;
    try {
      const [threatResponse] = await Promise.all([
        threatService.list({ page: 1, pageSize: 20 }),
        dashboardService.summary(),
      ]);
      const threats = threatResponse.items || [];
      const nextKnownThreats = new Map(knownThreatsRef.current);

      threats.forEach((threat) => {
        const previous = knownThreatsRef.current.get(threat.id);
        if (initializedRef.current) {
          notifyThreatChange(threat, previous);
        }
        nextKnownThreats.set(threat.id, {
          aiCompleted: isAiCompleted(threat),
          aiFailed: isAiFailed(threat),
          severity: threat.severity,
          timestamp: threatTimestamp(threat),
        });
      });

      knownThreatsRef.current = nextKnownThreats;
      initializedRef.current = true;
      setRefreshVersion((current) => {
        const next = current + 1;
        console.info('dashboard refresh', { refreshVersion: next });
        return next;
      });
    } catch (error) {
      if (error.response?.status !== 401) {
        console.warn('Live notification polling failed', error);
      }
    } finally {
      pollingRef.current = false;
    }
  }, [isAuthenticated, notifyThreatChange]);

  useEffect(() => {
    if (!isAuthenticated) {
      initializedRef.current = false;
      knownThreatsRef.current = new Map();
      return undefined;
    }

    pollLiveState();
    const interval = window.setInterval(pollLiveState, pollIntervalMs);

    return () => window.clearInterval(interval);
  }, [isAuthenticated, pollLiveState]);

  const notifyThreatIntelligenceSync = useCallback(
    (result) => {
      createNotification({
        message: `${result.imported} imported, ${result.updated} updated, ${result.analyzed} analyzed.`,
        severity: 'INFO',
        title: 'Threat Intelligence Sync Completed',
        type: 'sync_completed',
      });
      setRefreshVersion((current) => current + 1);
    },
    [createNotification],
  );

  const notifyAiCompleted = useCallback(
    (threatTitle, threatId) => {
      const previous = knownThreatsRef.current.get(threatId) || {};
      knownThreatsRef.current.set(threatId, {
        ...previous,
        aiCompleted: true,
        timestamp: new Date().toISOString(),
      });
      createNotification({
        message: `${threatTitle} analysis is ready.`,
        severity: 'INFO',
        threatId,
        title: 'AI Analysis Completed',
        type: 'ai_completed',
      });
      setRefreshVersion((current) => current + 1);
    },
    [createNotification],
  );

  const value = useMemo(
    () => ({
      createNotification,
      dismissNotification,
      markAllRead,
      markRead,
      notifications,
      notifyAiCompleted,
      notifyThreatIntelligenceSync,
      refreshVersion,
      unreadCount,
    }),
    [
      createNotification,
      dismissNotification,
      markAllRead,
      markRead,
      notifications,
      notifyAiCompleted,
      notifyThreatIntelligenceSync,
      refreshVersion,
      unreadCount,
    ],
  );

  return <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>;
}
