import { NavLink } from 'react-router-dom'
import { ShoppingCart, UtensilsCrossed, CalendarDays, Package, Settings } from 'lucide-react'

const items = [
  { to: '/pantry', icon: Package, label: 'Dispensa' },
  { to: '/shopping', icon: ShoppingCart, label: 'Spesa' },
  { to: '/recipes', icon: UtensilsCrossed, label: 'Ricette' },
  { to: '/calendar', icon: CalendarDays, label: 'Calendario' },
  { to: '/settings', icon: Settings, label: 'Profilo' },
]

export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-md bg-white border-t border-gray-200 z-30 pb-safe">
      <div className="flex">
        {items.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors ${
                isActive ? 'text-primary-600' : 'text-gray-500 hover:text-gray-700'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={22} strokeWidth={isActive ? 2.5 : 1.8} />
                <span>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
