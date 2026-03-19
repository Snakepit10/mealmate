import { useEffect } from 'react'
import { useWS } from './useWS'
import { useNotificationStore } from '../store/notificationStore'
import toast from 'react-hot-toast'

export function useNotificationsWS() {
  const addNotification = useNotificationStore((s) => s.addNotification)

  useWS('/ws/notifications/', {
    'notification.new': (msg) => {
      if (msg.data) {
        addNotification(msg.data)
        toast(msg.data.title || 'Nuova notifica', {
          icon: '🔔',
          duration: 4000,
        })
      }
    },
  })
}
