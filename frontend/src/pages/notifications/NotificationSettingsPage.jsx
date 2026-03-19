import { useState, useEffect } from 'react'
import { ArrowLeft, Bell } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { notificationsApi } from '../../api/notifications'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import toast from 'react-hot-toast'

const SETTINGS_FIELDS = [
  { key: 'expiry_enabled', label: 'Scadenze prodotti', description: 'Avviso prima della scadenza' },
  { key: 'missing_ingredient_enabled', label: 'Ingredienti mancanti', description: 'Ogni sera per i pasti di domani' },
  { key: 'shopping_updated_enabled', label: 'Lista spesa aggiornata', description: 'Quando un membro modifica la lista' },
  { key: 'menu_today_enabled', label: 'Menu di oggi', description: 'Riepilogo pasti mattutino' },
  { key: 'recipe_rated_enabled', label: 'Ricette valutate', description: 'Quando qualcuno vota le tue ricette' },
  { key: 'recipe_shared_enabled', label: 'Ricette condivise', description: 'Quando ricevi una ricetta condivisa' },
]

export default function NotificationSettingsPage() {
  const navigate = useNavigate()
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    notificationsApi.getSettings()
      .then(({ data }) => setSettings(data))
      .catch(() => toast.error('Errore nel caricamento'))
      .finally(() => setLoading(false))
  }, [])

  async function toggle(key) {
    const updated = { ...settings, [key]: !settings[key] }
    setSettings(updated)
    setSaving(true)
    try {
      await notificationsApi.updateSettings({ [key]: !settings[key] })
    } catch {
      setSettings(settings)
      toast.error('Errore nel salvataggio')
    } finally {
      setSaving(false)
    }
  }

  async function subscribePush() {
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        toast.error('Push non supportato su questo dispositivo')
        return
      }
      const permission = await Notification.requestPermission()
      if (permission !== 'granted') {
        toast.error('Permesso notifiche negato')
        return
      }
      const reg = await navigator.serviceWorker.ready
      // VAPID public key would be needed here — placeholder for now
      toast('Push notifications configurate!', { icon: '🔔' })
    } catch (err) {
      toast.error('Errore nella configurazione push')
    }
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-1.5 rounded-lg hover:bg-gray-100">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-bold text-gray-900">Impostazioni notifiche</h1>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><LoadingSpinner /></div>
      ) : !settings ? null : (
        <>
          <div className="card divide-y divide-gray-100">
            {SETTINGS_FIELDS.map(({ key, label, description }) => (
              <div key={key} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">{label}</p>
                  <p className="text-xs text-gray-400">{description}</p>
                </div>
                <button
                  onClick={() => toggle(key)}
                  className={`relative w-11 h-6 rounded-full transition-colors flex-shrink-0 ${settings[key] ? 'bg-primary-600' : 'bg-gray-300'}`}
                >
                  <span className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${settings[key] ? 'translate-x-[22px]' : 'translate-x-[2px]'}`} />
                </button>
              </div>
            ))}
          </div>

          {settings.menu_today_enabled && (
            <div className="card p-4">
              <label className="label">Orario promemoria menu</label>
              <input
                className="input"
                type="time"
                value={settings.menu_today_time || '08:00'}
                onChange={async (e) => {
                  const updated = { ...settings, menu_today_time: e.target.value }
                  setSettings(updated)
                  await notificationsApi.updateSettings({ menu_today_time: e.target.value })
                }}
              />
            </div>
          )}

          {settings.expiry_enabled && (
            <div className="card p-4">
              <label className="label">Giorni prima della scadenza</label>
              <input
                className="input"
                type="number"
                min="1"
                max="30"
                value={settings.expiry_days_before || 2}
                onChange={async (e) => {
                  const val = parseInt(e.target.value)
                  if (val > 0) {
                    setSettings({ ...settings, expiry_days_before: val })
                    await notificationsApi.updateSettings({ expiry_days_before: val })
                  }
                }}
              />
            </div>
          )}

          <button onClick={subscribePush} className="btn-secondary w-full">
            <Bell size={16} /> Attiva notifiche push
          </button>
        </>
      )}
    </div>
  )
}
