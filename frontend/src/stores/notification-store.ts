"use client";
import { create } from "zustand";
import type { Notification, NotificationSeverity } from "@/lib/types";

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  severityFilter: NotificationSeverity | "all";
  showArchived: boolean;
  setNotifications: (items: Notification[]) => void;
  addNotification: (item: Notification) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  archive: (id: string) => void;
  setSeverityFilter: (filter: NotificationSeverity | "all") => void;
  setShowArchived: (show: boolean) => void;
  filtered: () => Notification[];
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  severityFilter: "all",
  showArchived: false,

  setNotifications: (items) =>
    set({
      notifications: items,
      unreadCount: items.filter((n) => !n.read).length,
    }),

  addNotification: (item) => {
    const updated = [item, ...get().notifications];
    set({
      notifications: updated,
      unreadCount: updated.filter((n) => !n.read).length,
    });
  },

  markRead: (id) => {
    const updated = get().notifications.map((n) =>
      n.notification_id === id ? { ...n, read: true } : n
    );
    set({
      notifications: updated,
      unreadCount: updated.filter((n) => !n.read).length,
    });
  },

  markAllRead: () => {
    const updated = get().notifications.map((n) => ({ ...n, read: true }));
    set({
      notifications: updated,
      unreadCount: 0,
    });
  },

  archive: (id) => {
    const updated = get().notifications.map((n) =>
      n.notification_id === id ? { ...n, archived: true, read: true } : n
    );
    set({
      notifications: updated,
      unreadCount: updated.filter((n) => !n.read).length,
    });
  },

  setSeverityFilter: (filter) => set({ severityFilter: filter }),
  setShowArchived: (show) => set({ showArchived: show }),

  filtered: () => {
    const { notifications, severityFilter, showArchived } = get();
    return notifications.filter((n) => {
      if (!showArchived && n.archived) return false;
      if (severityFilter !== "all" && n.severity !== severityFilter) return false;
      return true;
    });
  },
}));
