import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, Plus, LogIn } from 'lucide-react'
import { familiesApi } from '../../api/families'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

export default function FamilySetupPage() {
  const navigate = useNavigate()
  const { setFamily, logout } = useAuthStore()
  const [mode, setMode] = useState(null) // 'create' | 'join'
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleCreate(e) {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      const { data } = await familiesApi.create(name.trim())
      setFamily(data)
      navigate('/pantry', { replace: true })
      toast.success(`Famiglia "${data.name}" creata!`)
    } catch (err) {
      toast.error(err.response?.data?.error || 'Errore nella creazione')
    } finally {
      setLoading(false)
    }
  }

  async function handleJoin(e) {
    e.preventDefault()
    if (!code.trim()) return
    setLoading(true)
    try {
      const { data } = await familiesApi.join(code.trim().toUpperCase())
      setFamily(data.family || data)
      navigate('/pantry', { replace: true })
      toast.success('Sei entrato nella famiglia!')
    } catch (err) {
      toast.error(err.response?.data?.error || 'Codice non valido')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-primary-600 flex items-center justify-center mb-3">
            <Users size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">La tua famiglia</h1>
          <p className="text-sm text-gray-500 mt-1 text-center">
            Crea una nuova famiglia o unisciti a una esistente
          </p>
        </div>

        {!mode && (
          <div className="space-y-3">
            <button
              className="w-full card p-4 flex items-center gap-4 hover:border-primary-300 hover:shadow-md transition-all text-left"
              onClick={() => setMode('create')}
            >
              <div className="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center">
                <Plus size={20} className="text-primary-600" />
              </div>
              <div>
                <p className="font-semibold text-gray-900">Crea famiglia</p>
                <p className="text-xs text-gray-500">Inizia una nuova famiglia</p>
              </div>
            </button>

            <button
              className="w-full card p-4 flex items-center gap-4 hover:border-primary-300 hover:shadow-md transition-all text-left"
              onClick={() => setMode('join')}
            >
              <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                <LogIn size={20} className="text-amber-600" />
              </div>
              <div>
                <p className="font-semibold text-gray-900">Unisciti</p>
                <p className="text-xs text-gray-500">Inserisci il codice invito</p>
              </div>
            </button>
          </div>
        )}

        {mode === 'create' && (
          <form onSubmit={handleCreate} className="card p-6 space-y-4">
            <h2 className="font-semibold text-gray-900">Nuova famiglia</h2>
            <div>
              <label className="label">Nome famiglia</label>
              <input
                className="input"
                placeholder="Es. Famiglia Rossi"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
              />
            </div>
            <div className="flex gap-2">
              <button type="button" className="btn-secondary flex-1" onClick={() => setMode(null)}>
                Indietro
              </button>
              <button type="submit" className="btn-primary flex-1" disabled={loading || !name.trim()}>
                {loading ? 'Creazione...' : 'Crea'}
              </button>
            </div>
          </form>
        )}

        {mode === 'join' && (
          <form onSubmit={handleJoin} className="card p-6 space-y-4">
            <h2 className="font-semibold text-gray-900">Unisciti a una famiglia</h2>
            <div>
              <label className="label">Codice invito</label>
              <input
                className="input uppercase tracking-widest text-center font-mono text-lg"
                placeholder="ABCD1234"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                maxLength={8}
                autoFocus
              />
            </div>
            <div className="flex gap-2">
              <button type="button" className="btn-secondary flex-1" onClick={() => setMode(null)}>
                Indietro
              </button>
              <button type="submit" className="btn-primary flex-1" disabled={loading || code.length < 4}>
                {loading ? 'Unione...' : 'Unisciti'}
              </button>
            </div>
          </form>
        )}

        <button
          onClick={logout}
          className="mt-6 text-xs text-gray-400 hover:text-gray-600 block text-center w-full"
        >
          Logout
        </button>
      </div>
    </div>
  )
}
