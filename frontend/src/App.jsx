import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from './store/authStore'
import AppShell from './components/Layout/AppShell'
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import FamilySetupPage from './pages/family/FamilySetupPage'
import PantryPage from './pages/pantry/PantryPage'
import ShoppingPage from './pages/shopping/ShoppingPage'
import RecipesPage from './pages/recipes/RecipesPage'
import RecipeDetailPage from './pages/recipes/RecipeDetailPage'
import RecipeCreatePage from './pages/recipes/RecipeCreatePage'
import CalendarPage from './pages/calendar/CalendarPage'
import NotificationsPage from './pages/notifications/NotificationsPage'
import NotificationSettingsPage from './pages/notifications/NotificationSettingsPage'
import SettingsPage from './pages/settings/SettingsPage'
import FamilySettingsPage from './pages/family/FamilySettingsPage'
import StoresPage from './pages/stores/StoresPage'
import StoreDetailPage from './pages/stores/StoreDetailPage'
import SharingPage from './pages/sharing/SharingPage'
import LoadingSpinner from './components/shared/LoadingSpinner'

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuthStore()
  if (loading) return <div className="flex items-center justify-center h-screen"><LoadingSpinner /></div>
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuthStore()
  if (loading) return <div className="flex items-center justify-center h-screen"><LoadingSpinner /></div>
  return isAuthenticated ? <Navigate to="/pantry" replace /> : children
}

function FamilyGuard({ children }) {
  const { family } = useAuthStore()
  if (!family) return <Navigate to="/family/setup" replace />
  return children
}

export default function App() {
  const { init } = useAuthStore()

  useEffect(() => {
    init()
  }, [init])

  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />

        {/* Family setup (authenticated but no family) */}
        <Route path="/family/setup" element={<PrivateRoute><FamilySetupPage /></PrivateRoute>} />

        {/* App shell with bottom nav */}
        <Route path="/" element={<PrivateRoute><FamilyGuard><AppShell /></FamilyGuard></PrivateRoute>}>
          <Route index element={<Navigate to="/pantry" replace />} />
          <Route path="pantry" element={<PantryPage />} />
          <Route path="shopping" element={<ShoppingPage />} />
          <Route path="recipes" element={<RecipesPage />} />
          <Route path="recipes/new" element={<RecipeCreatePage />} />
          <Route path="recipes/:id" element={<RecipeDetailPage />} />
          <Route path="recipes/:id/edit" element={<RecipeCreatePage />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="notifications/settings" element={<NotificationSettingsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="family/settings" element={<FamilySettingsPage />} />
          <Route path="stores" element={<StoresPage />} />
          <Route path="stores/:storeId" element={<StoreDetailPage />} />
          <Route path="sharing" element={<SharingPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/pantry" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
