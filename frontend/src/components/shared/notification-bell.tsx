"use client";

import { useEffect, useRef, useState } from "react";
import { Bell, CheckCheck, Eye } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatRelativeTime } from "@/lib/utils";
import { useNotificationStore } from "@/stores/notification-store";
import { notifications as notificationsApi } from "@/lib/api";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { notifications, unreadCount, setNotifications, markRead, markAllRead } =
    useNotificationStore();

  // Fetch on mount
  useEffect(() => {
    notificationsApi
      .list(false, 20)
      .then(setNotifications)
      .catch(() => {});
  }, [setNotifications]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  function handleMarkRead(id: string) {
    markRead(id);
    notificationsApi.markRead(id).catch(() => {});
  }

  function handleMarkAllRead() {
    markAllRead();
    notificationsApi.markAllRead().catch(() => {});
  }

  const latest = notifications.slice(0, 5);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell button */}
      <button
        onClick={() => setOpen((prev) => !prev)}
        className={cn(
          "relative p-2 rounded-lg transition-colors",
          "text-slate-400 hover:text-slate-600 hover:bg-slate-100",
          open && "bg-slate-100 text-slate-600"
        )}
        aria-label="Notifications"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white bg-red-500 rounded-full leading-none">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-lg shadow-lg z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
            <h3 className="text-sm font-semibold text-slate-900">Notifications</h3>
            {unreadCount > 0 && (
              <span className="text-[11px] text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded-full">
                {unreadCount} unread
              </span>
            )}
          </div>

          {/* List */}
          {latest.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <Bell className="w-8 h-8 text-slate-200 mx-auto mb-2" />
              <p className="text-xs text-slate-400">No notifications yet</p>
            </div>
          ) : (
            <div className="max-h-80 overflow-y-auto divide-y divide-slate-50">
              {latest.map((n) => (
                <div
                  key={n.notification_id}
                  className={cn(
                    "flex items-start gap-3 px-4 py-3 transition-colors",
                    !n.read && "bg-brand-50/30"
                  )}
                >
                  {/* Unread indicator */}
                  <div className="pt-1.5 flex-shrink-0">
                    {!n.read ? (
                      <div className="w-2 h-2 rounded-full bg-brand-500" />
                    ) : (
                      <div className="w-2 h-2" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 truncate">
                      {n.title}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">
                      {n.body}
                    </p>
                    <p className="text-[10px] text-slate-300 mt-1">
                      {formatRelativeTime(n.created_at)}
                    </p>
                  </div>

                  {/* Mark read */}
                  {!n.read && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleMarkRead(n.notification_id);
                      }}
                      className="flex-shrink-0 p-1 rounded text-slate-300 hover:text-brand-500 hover:bg-slate-50 transition-colors"
                      aria-label="Mark as read"
                      title="Mark as read"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Footer */}
          {notifications.length > 0 && unreadCount > 0 && (
            <div className="border-t border-slate-100 px-4 py-2">
              <button
                onClick={handleMarkAllRead}
                className="flex items-center gap-1.5 text-xs text-brand-500 hover:text-brand-600 font-medium transition-colors w-full justify-center py-1"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                Mark all as read
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
