import { useState, useEffect, useCallback } from 'react'
import { ArrowLeft, Copy, RefreshCw, Crown, Trash2, UserPlus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { familiesApi } from '../../api/families'
import { useAuthStore } from '../../store/authStore'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import ConfirmDialog from '../../components/shared/ConfirmDialog'
import toast from 'react-hot-toast'

export default function FamilySettingsPage() {
  const navigate = useNavigate()
  const { family, user, setFamily, logout } = useAuthStore()
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showLeave, setShowLeave] = useState(false)
  const [removeMemberId, setRemoveMemberId] = useState(null)
  const [regenLoading, setRegenLoading] = useState(false)

  const loadMembers = useCallback(async () => {
    if (!family) return
    try {
      const { data } = await familiesApi.listMembers(family.id)
      setMembers(data.results || data)
    } catch { toast.error('Errore') }
    finally { setLoading(false) }
  }, [family])

  useEffect(() => { loadMembers() }, [loadMembers])

  const myMember = members.find((m) => m.user === user?.id)
  const isAdmin = myMember?.role === 'admin'

  async function handleRegenInvite() {
    setRegenLoading(true)
    try {
      const { data } = await familiesApi.regenerateInvite(family.id)
      setFamily({ ...family, invite_code: data.invite_code })
      toast.success('Codice invito rigenerato!')
    } catch { toast.error('Errore') }
    finally { setRegenLoading(false) }
  }

  function copyCode() {
    navigator.clipboard.writeText(family?.invite_code || '')
    toast.success('Codice copiato!')
  }

  async function handleRemoveMember() {
    try {
      await familiesApi.removeMember(family.id, removeMemberId)
      setRemoveMemberId(null)
      loadMembers()
      toast.success('Membro rimosso')
    } catch (err) { toast.error(err.response?.data?.error || 'Errore') }
  }

  async function handleLeave() {
    try {
      await familiesApi.leave(family.id)
      setFamily(null)
      navigate('/family/setup', { replace: true })
      toast.success('Hai lasciato la famiglia')
    } catch (err) { toast.error(err.response?.data?.error || 'Errore') }
  }

  async function handleTransferAdmin(memberId) {
    try {
      await familiesApi.transferAdmin(family.id, memberId)
      loadMembers()
      toast.success('Ruolo admin trasferito')
    } catch { toast.error('Errore') }
  }

  return (
    <div className="p-4 space-y-4 pb-8">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-1.5 rounded-lg hover:bg-gray-100">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-xl font-bold text-gray-900">Impostazioni famiglia</h1>
      </div>

      {/* Family info */}
      <div className="card p-4 space-y-3">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold">Famiglia</p>
          <p className="text-lg font-bold text-gray-900">{family?.name}</p>
        </div>

        {/* Invite code */}
        <div>
          <p className="text-xs text-gray-500 mb-1">Codice invito</p>
          <div className="flex items-center gap-2">
            <code className="flex-1 text-center font-mono text-xl tracking-widest bg-gray-100 rounded-xl py-2 text-primary-700">
              {family?.invite_code}
            </code>
            <button onClick={copyCode} className="btn-secondary px-3 py-2">
              <Copy size={16} />
            </button>
            {isAdmin && (
              <button onClick={handleRegenInvite} className="btn-secondary px-3 py-2" disabled={regenLoading}>
                <RefreshCw size={16} className={regenLoading ? 'animate-spin' : ''} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Members */}
      <div className="card divide-y divide-gray-100">
        <div className="px-4 pt-3 pb-2 flex items-center justify-between">
          <p className="text-sm font-semibold text-gray-700">Membri ({members.length})</p>
        </div>
        {loading ? (
          <div className="flex justify-center py-6"><LoadingSpinner size="sm" /></div>
        ) : (
          members.map((m) => (
            <div key={m.id} className="flex items-center gap-3 px-4 py-3">
              <div className="w-9 h-9 rounded-full bg-primary-100 flex items-center justify-center font-bold text-primary-600 text-sm flex-shrink-0">
                {(m.name || m.user_name || '?')[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {m.name || m.user_name}
                  {m.user === user?.id && <span className="text-gray-400 font-normal"> (tu)</span>}
                </p>
                <p className="text-xs text-gray-400">
                  {m.role === 'admin' ? '👑 Admin' : 'Membro'}
                  {!m.is_registered && ' · Senza account'}
                </p>
              </div>
              {isAdmin && m.user !== user?.id && (
                <div className="flex gap-1">
                  {m.role !== 'admin' && (
                    <button
                      onClick={() => handleTransferAdmin(m.id)}
                      className="p-1.5 text-amber-500 hover:bg-amber-50 rounded"
                      title="Rendi admin"
                    >
                      <Crown size={14} />
                    </button>
                  )}
                  <button
                    onClick={() => setRemoveMemberId(m.id)}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Leave family */}
      <button onClick={() => setShowLeave(true)} className="btn-danger w-full">
        Lascia famiglia
      </button>

      <ConfirmDialog
        open={!!removeMemberId}
        onClose={() => setRemoveMemberId(null)}
        onConfirm={handleRemoveMember}
        title="Rimuovi membro"
        message="Sei sicuro di voler rimuovere questo membro dalla famiglia?"
      />
      <ConfirmDialog
        open={showLeave}
        onClose={() => setShowLeave(false)}
        onConfirm={handleLeave}
        title="Lascia famiglia"
        message="Sei sicuro di voler lasciare questa famiglia? Perderai l'accesso a tutti i dati condivisi."
        confirmLabel="Lascia"
      />
    </div>
  )
}
