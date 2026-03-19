import { useState, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuthStore } from '../../store/authStore'
import { authApi } from '../../api/auth'
import { User, Users, LogOut, ChevronRight, Bell, Trash2, ShoppingBag, Camera, Share2 } from 'lucide-react'
import ConfirmDialog from '../../components/shared/ConfirmDialog'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const navigate = useNavigate()
  const { user, family, logout, updateUser } = useAuthStore()
  const [editing, setEditing] = useState(false)
  const [showDeleteAccount, setShowDeleteAccount] = useState(false)
  const [avatarPreview, setAvatarPreview] = useState(user?.avatar || null)
  const avatarInputRef = useRef(null)
  const { register, handleSubmit, formState: { isSubmitting } } = useForm({
    defaultValues: { name: user?.name || '' }
  })

  async function onSubmit({ name }) {
    try {
      const { data } = await authApi.updateMe({ name })
      updateUser(data)
      setEditing(false)
      toast.success('Profilo aggiornato')
    } catch {
      toast.error('Errore nel salvataggio')
    }
  }

  async function handleAvatarChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const localUrl = URL.createObjectURL(file)
    setAvatarPreview(localUrl)
    try {
      const fd = new FormData()
      fd.append('avatar', file)
      const { data } = await authApi.updateMe(fd)
      updateUser(data)
      toast.success('Avatar aggiornato')
    } catch {
      setAvatarPreview(user?.avatar || null)
      toast.error('Errore nel caricamento avatar')
    }
    e.target.value = ''
  }

  async function handleDeleteAccount() {
    try {
      await authApi.deleteMe()
      logout()
      toast.success('Account eliminato')
    } catch { toast.error('Errore') }
  }

  async function handleLogout() {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold text-gray-900">Profilo</h1>

      {/* User card */}
      <div className="card p-4">
        <div className="flex items-center gap-3 mb-4">
          <div
            className="w-14 h-14 rounded-full bg-primary-100 flex items-center justify-center relative cursor-pointer overflow-hidden group flex-shrink-0"
            onClick={() => avatarInputRef.current?.click()}
          >
            {avatarPreview
              ? <img src={avatarPreview} alt="Avatar" className="w-full h-full object-cover" />
              : <User size={28} className="text-primary-600" />
            }
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded-full">
              <Camera size={16} className="text-white" />
            </div>
            <input ref={avatarInputRef} type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} />
          </div>
          <div>
            <p className="font-semibold text-gray-900">{user?.name}</p>
            <p className="text-sm text-gray-400">{user?.email}</p>
          </div>
        </div>

        {editing ? (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
            <div>
              <label className="label">Nome</label>
              <input className="input" {...register('name', { required: true })} />
            </div>
            <div className="flex gap-2">
              <button type="button" className="btn-secondary flex-1" onClick={() => setEditing(false)}>
                Annulla
              </button>
              <button type="submit" className="btn-primary flex-1" disabled={isSubmitting}>
                {isSubmitting ? 'Salvataggio...' : 'Salva'}
              </button>
            </div>
          </form>
        ) : (
          <button className="btn-secondary w-full text-sm" onClick={() => setEditing(true)}>
            Modifica profilo
          </button>
        )}
      </div>

      {/* Family */}
      {family && (
        <div className="card divide-y divide-gray-100">
          <Link to="/family/settings" className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              <Users size={18} className="text-primary-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Famiglia</p>
                <p className="text-xs text-gray-400">{family.name}</p>
              </div>
            </div>
            <ChevronRight size={16} className="text-gray-400" />
          </Link>
        </div>
      )}

      {/* Other settings */}
      <div className="card divide-y divide-gray-100">
        <Link to="/stores" className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <ShoppingBag size={18} className="text-primary-600" />
            <p className="text-sm font-medium text-gray-900">Negozi e corsie</p>
          </div>
          <ChevronRight size={16} className="text-gray-400" />
        </Link>
        <Link to="/notifications/settings" className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Bell size={18} className="text-gray-500" />
            <p className="text-sm font-medium text-gray-900">Notifiche</p>
          </div>
          <ChevronRight size={16} className="text-gray-400" />
        </Link>
        <Link to="/sharing" className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Share2 size={18} className="text-primary-600" />
            <p className="text-sm font-medium text-gray-900">Condivisioni</p>
          </div>
          <ChevronRight size={16} className="text-gray-400" />
        </Link>
      </div>

      {/* Danger zone */}
      <div className="card divide-y divide-gray-100">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 w-full text-left"
        >
          <LogOut size={18} className="text-gray-500" />
          <p className="text-sm font-medium text-gray-900">Logout</p>
        </button>
        <button
          onClick={() => setShowDeleteAccount(true)}
          className="flex items-center gap-3 px-4 py-3 w-full text-left"
        >
          <Trash2 size={18} className="text-red-500" />
          <p className="text-sm font-medium text-red-500">Elimina account</p>
        </button>
      </div>

      <p className="text-center text-xs text-gray-400">MealMate v0.1.0</p>

      <ConfirmDialog
        open={showDeleteAccount}
        onClose={() => setShowDeleteAccount(false)}
        onConfirm={handleDeleteAccount}
        title="Elimina account"
        message="Sei sicuro? Tutti i tuoi dati verranno eliminati permanentemente."
        confirmLabel="Elimina account"
      />
    </div>
  )
}
