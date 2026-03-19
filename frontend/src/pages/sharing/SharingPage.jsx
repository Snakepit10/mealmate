import { useState, useEffect, useCallback } from 'react'
import { Share2, Check, X, Trash2, ArrowLeft } from 'lucide-react'
import { sharingApi } from '../../api/sharing'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import toast from 'react-hot-toast'
import { format, parseISO } from 'date-fns'
import { it } from 'date-fns/locale'
import { useNavigate } from 'react-router-dom'

const RESOURCE_ICONS = {
  recipe: '🍽️',
  calendar: '📅',
  shopping: '🛒',
  pantry: '📦',
}

const STATUS_BADGE = {
  pending: { label: 'In attesa', cls: 'bg-yellow-50 text-yellow-700' },
  accepted: { label: 'Accettato', cls: 'bg-green-50 text-green-700' },
  rejected: { label: 'Rifiutato', cls: 'bg-red-50 text-red-500' },
}

function ShareCard({ share, isSent, onAccept, onReject, onRevoke }) {
  const badge = STATUS_BADGE[share.status] || STATUS_BADGE.pending
  const icon = RESOURCE_ICONS[share.resource_type] || '🔗'

  return (
    <div className="card p-3 flex items-start gap-3">
      <span className="text-2xl flex-shrink-0 mt-0.5">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">
          {share.resource_type_display}
        </p>
        <p className="text-xs text-gray-500 mt-0.5">
          {isSent
            ? `A: ${share.shared_with_user_name || share.shared_with_family_name || '—'}`
            : `Da: ${share.shared_by_name}`}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <span className={`badge text-xs ${badge.cls}`}>{badge.label}</span>
          <span className="text-xs text-gray-400">
            {share.permission === 'write' ? '✏️ Scrittura' : '👁️ Lettura'}
          </span>
          <span className="text-xs text-gray-300">
            {format(parseISO(share.created_at), 'd MMM', { locale: it })}
          </span>
        </div>
      </div>

      <div className="flex gap-1 flex-shrink-0">
        {!isSent && share.status === 'pending' && (
          <>
            <button
              onClick={() => onAccept(share.id)}
              className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
              title="Accetta"
            >
              <Check size={16} />
            </button>
            <button
              onClick={() => onReject(share.id)}
              className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
              title="Rifiuta"
            >
              <X size={16} />
            </button>
          </>
        )}
        {isSent && (
          <button
            onClick={() => onRevoke(share.id)}
            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg"
            title="Revoca"
          >
            <Trash2 size={15} />
          </button>
        )}
      </div>
    </div>
  )
}

export default function SharingPage() {
  const navigate = useNavigate()
  const [tab, setTab] = useState('received')
  const [received, setReceived] = useState([])
  const [sent, setSent] = useState([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [recvRes, sentRes] = await Promise.all([
        sharingApi.list({ direction: 'received' }),
        sharingApi.list({ direction: 'sent' }),
      ])
      setReceived(recvRes.data)
      setSent(sentRes.data)
    } catch {
      toast.error('Errore nel caricamento condivisioni')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleAccept(id) {
    try {
      await sharingApi.accept(id)
      toast.success('Condivisione accettata')
      load()
    } catch { toast.error('Errore') }
  }

  async function handleReject(id) {
    try {
      await sharingApi.reject(id)
      toast.success('Condivisione rifiutata')
      load()
    } catch { toast.error('Errore') }
  }

  async function handleRevoke(id) {
    try {
      await sharingApi.delete(id)
      toast.success('Condivisione revocata')
      load()
    } catch { toast.error('Errore') }
  }

  const pending = received.filter((s) => s.status === 'pending')
  const displayed = tab === 'received' ? received : sent

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-1 rounded-lg hover:bg-gray-100">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Share2 size={22} className="text-primary-600" /> Condivisioni
        </h1>
        {pending.length > 0 && (
          <span className="ml-auto badge bg-primary-600 text-white text-xs px-2 py-0.5 rounded-full">
            {pending.length}
          </span>
        )}
      </div>

      <div className="flex bg-gray-100 rounded-xl p-1 gap-1">
        <button
          className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${tab === 'received' ? 'bg-white text-primary-700 shadow-sm' : 'text-gray-500'}`}
          onClick={() => setTab('received')}
        >
          Ricevute ({received.length})
          {pending.length > 0 && <span className="ml-1 text-primary-500">· {pending.length} nuove</span>}
        </button>
        <button
          className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${tab === 'sent' ? 'bg-white text-primary-700 shadow-sm' : 'text-gray-500'}`}
          onClick={() => setTab('sent')}
        >
          Inviate ({sent.length})
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><LoadingSpinner /></div>
      ) : displayed.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-gray-400">
          <Share2 size={48} className="mb-3 opacity-30" />
          <p className="text-sm">
            {tab === 'received' ? 'Nessuna condivisione ricevuta.' : 'Nessuna condivisione inviata.'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {displayed.map((share) => (
            <ShareCard
              key={share.id}
              share={share}
              isSent={tab === 'sent'}
              onAccept={handleAccept}
              onReject={handleReject}
              onRevoke={handleRevoke}
            />
          ))}
        </div>
      )}
    </div>
  )
}
