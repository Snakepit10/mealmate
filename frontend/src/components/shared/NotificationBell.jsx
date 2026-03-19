import { Bell } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useNotificationStore } from '../../store/notificationStore'

export default function NotificationBell() {
  const unreadCount = useNotificationStore((s) => s.unreadCount)
  return (
    <Link to="/notifications" className="relative p-2 rounded-lg text-gray-600 hover:bg-gray-100">
      <Bell size={20} />
      {unreadCount > 0 && (
        <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold leading-none">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </Link>
  )
}
