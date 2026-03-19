import { useEffect } from 'react'
import { Bell, Check, Trash2, Settings } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useNotificationStore } from '../../store/notificationStore'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import { format, parseISO } from 'date-fns'
import { it } from 'date-fns/locale'
import toast from 'react-hot-toast'

const TYPE_ICONS = {
  expiry: '⏰',
  missing_ingredient: '🛒',
  shopping_updated: '📝',
  menu_today: '🍽️',
  member_joined: '👋',
  recipe_rated: '⭐',
  recipe_shared: '🔗',
}

export default function NotificationsPage() {
  const { notifications, loading, unreadCount, load, markRead, markAllRead, remove } = useNotificationStore()

  useEffect(() => { load() }, [load])

  async function handleMarkAllRead() {
    try {
      await markAllRead()
      toast.success('Tutte le notifiche lette')
    } catch { toast.error('Errore') }
  }

  async function handleDelete(id) {
    try {
      await remove(id)
    } catch { toast.error('Errore') }
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Bell size={22} className="text-primary-600" /> Notifiche
        </h1>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <button onClick={handleMarkAllRead} className="text-xs text-primary-600 font-medium flex items-center gap-1">
              <Check size={13} /> Segna tutte lette
            </button>
          )}
          <Link to="/notifications/settings" className="p-2 rounded-lg text-gray-500 hover:bg-gray-100">
            <Settings size={18} />
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><LoadingSpinner /></div>
      ) : notifications.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-gray-400">
          <Bell size={48} className="mb-3 opacity-30" />
          <p className="text-sm">Nessuna notifica</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={`card p-3 flex items-start gap-3 cursor-pointer hover:shadow-md transition-shadow ${!n.read ? 'border-l-4 border-l-primary-500' : ''}`}
              onClick={() => !n.read && markRead(n.id)}
            >
              <span className="text-xl flex-shrink-0 mt-0.5">{TYPE_ICONS[n.type] || '🔔'}</span>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${n.read ? 'text-gray-600' : 'text-gray-900'}`}>{n.title}</p>
                <p className="text-xs text-gray-500 mt-0.5 leading-snug">{n.message}</p>
                <p className="text-xs text-gray-300 mt-1">
                  {format(parseISO(n.created_at), 'd MMM, HH:mm', { locale: it })}
                </p>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); handleDelete(n.id) }}
                className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded flex-shrink-0"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
