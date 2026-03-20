import { Outlet } from 'react-router-dom'
import { useEffect } from 'react'
import BottomNav from './BottomNav'
import NotificationBell from '../shared/NotificationBell'
import { useAuthStore } from '../../store/authStore'
import { useNotificationStore } from '../../store/notificationStore'
import { useNotificationsWS } from '../../ws/useNotificationsWS'

function GlobalWSListener() {
  useNotificationsWS()
  return null
}

export default function AppShell() {
  const { family, user } = useAuthStore()
  const load = useNotificationStore((s) => s.load)

  useEffect(() => { load() }, [load])

  return (
    <div className="min-h-screen bg-gray-100 flex justify-center">
      <div className="w-full max-w-md bg-gray-50 flex flex-col min-h-screen relative">
        {/* Top header */}
        <header className="sticky top-0 z-20 bg-white border-b border-gray-200 pt-safe">
          <div className="flex items-center justify-between px-4 h-14">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-primary-600 flex items-center justify-center">
                <span className="text-white font-bold text-xs">M</span>
              </div>
              <div>
                <p className="text-xs text-gray-500 leading-none">Famiglia</p>
                <p className="text-sm font-semibold text-gray-900 leading-tight">{family?.name || 'MealMate'}</p>
              </div>
            </div>
            <NotificationBell />
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 pb-20">
          <Outlet />
        </main>

        {/* Bottom navigation */}
        <BottomNav />

        {/* Global WebSocket listener */}
        <GlobalWSListener />
      </div>
    </div>
  )
}
