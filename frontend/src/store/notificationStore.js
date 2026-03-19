import { create } from 'zustand'
import { notificationsApi } from '../api/notifications'

export const useNotificationStore = create((set, get) => ({
  notifications: [],
  unreadCount: 0,
  loading: false,

  load: async () => {
    set({ loading: true })
    try {
      const { data } = await notificationsApi.list()
      const items = data.results || data
      const unread = items.filter((n) => !n.read).length
      set({ notifications: items, unreadCount: unread })
    } finally {
      set({ loading: false })
    }
  },

  addNotification: (notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: state.unreadCount + 1,
    }))
  },

  markRead: async (id) => {
    await notificationsApi.markRead(id)
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    }))
  },

  markAllRead: async () => {
    await notificationsApi.markAllRead()
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    }))
  },

  remove: async (id) => {
    const n = get().notifications.find((n) => n.id === id)
    await notificationsApi.delete(id)
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
      unreadCount: n && !n.read ? Math.max(0, state.unreadCount - 1) : state.unreadCount,
    }))
  },
}))
