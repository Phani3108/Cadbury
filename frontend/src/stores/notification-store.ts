"use client";
import { create } from "zustand";
import type { Notification } from "@/lib/types";

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  setNotifications: (items: Notification[]) => void;
  addNotification: (item: Notification) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,

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
}));
