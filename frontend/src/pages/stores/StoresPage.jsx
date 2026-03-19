import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Store, ChevronRight, Trash2, ShoppingBag, Copy } from 'lucide-react'
import { storesApi } from '../../api/stores'
import { useAuthStore } from '../../store/authStore'
import Modal from '../../components/shared/Modal'
import ConfirmDialog from '../../components/shared/ConfirmDialog'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import toast from 'react-hot-toast'

const CATEGORY_ICONS = {
  supermarket: '🛒',
  pharmacy: '💊',
  butcher: '🥩',
  fishmonger: '🐟',
  bakery: '🍞',
  market: '🥦',
  other: '🏪',
}

export default function StoresPage() {
  const navigate = useNavigate()
  const { family } = useAuthStore()
  const [stores, setStores] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [duplicating, setDuplicating] = useState(null)  // store id in corso di duplicazione
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ name: '', store_category: '', is_default: false })

  const load = useCallback(async () => {
    if (!family) return
    try {
      const [storesRes, catsRes] = await Promise.all([
        storesApi.list(family.id),
        storesApi.categories(),
      ])
      setStores(storesRes.data)
      setCategories(catsRes.data)
    } catch {
      toast.error('Errore nel caricamento negozi')
    } finally {
      setLoading(false)
    }
  }, [family])

  useEffect(() => { load() }, [load])

  async function handleCreate() {
    if (!form.name.trim() || !form.store_category) {
      toast.error('Nome e categoria obbligatori')
      return
    }
    setSaving(true)
    try {
      await storesApi.create(family.id, form)
      toast.success('Negozio aggiunto')
      setShowAdd(false)
      setForm({ name: '', store_category: '', is_default: false })
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore nel salvataggio')
    } finally {
      setSaving(false)
    }
  }

  async function handleDuplicate(store) {
    setDuplicating(store.id)
    try {
      await storesApi.duplicate(family.id, store.id)
      toast.success(`"${store.name}" duplicato`)
      load()
    } catch {
      toast.error('Errore nella duplicazione')
    } finally {
      setDuplicating(null)
    }
  }

  async function handleDelete() {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await storesApi.delete(family.id, deleteTarget.id)
      toast.success('Negozio eliminato')
      setDeleteTarget(null)
      load()
    } catch {
      toast.error('Errore nell\'eliminazione')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <ShoppingBag size={22} className="text-primary-600" /> Negozi
        </h1>
        <button onClick={() => setShowAdd(true)} className="btn-primary text-xs px-3 py-1.5">
          <Plus size={14} /> Aggiungi
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><LoadingSpinner /></div>
      ) : stores.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-gray-400">
          <Store size={48} className="mb-3 opacity-30" />
          <p className="text-sm text-center">Nessun negozio.<br />Aggiungine uno per organizzare la spesa per corsia.</p>
        </div>
      ) : (
        <div className="card divide-y divide-gray-100">
          {stores.map((store) => (
            <div key={store.id} className="flex items-center gap-3 px-4 py-3">
              <span className="text-2xl">
                {CATEGORY_ICONS[store.store_category] || '🏪'}
              </span>
              <button
                onClick={() => navigate(`/stores/${store.id}`)}
                className="flex-1 text-left min-w-0"
              >
                <p className="text-sm font-medium text-gray-900 truncate">{store.name}</p>
                <p className="text-xs text-gray-400">
                  {store.store_category_name}
                  {store.aisles_count > 0 && ` · ${store.aisles_count} cors${store.aisles_count === 1 ? 'ia' : 'ie'}`}
                  {store.is_default && <span className="ml-1 text-primary-600">· Predefinito</span>}
                </p>
              </button>
              <button
                onClick={() => navigate(`/stores/${store.id}`)}
                className="text-gray-300 hover:text-gray-500 p-1"
              >
                <ChevronRight size={16} />
              </button>
              <button
                onClick={() => handleDuplicate(store)}
                disabled={duplicating === store.id}
                title="Duplica negozio"
                className="text-gray-300 hover:text-primary-500 hover:bg-primary-50 p-1.5 rounded-lg disabled:opacity-40"
              >
                {duplicating === store.id
                  ? <span className="text-[10px] text-primary-400">...</span>
                  : <Copy size={15} />}
              </button>
              <button
                onClick={() => setDeleteTarget(store)}
                className="text-gray-300 hover:text-red-500 hover:bg-red-50 p-1.5 rounded-lg"
              >
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add store modal */}
      <Modal open={showAdd} onClose={() => { setShowAdd(false); setForm({ name: '', store_category: '', is_default: false }) }} title="Nuovo negozio">
        <div className="space-y-4">
          <div>
            <label className="label">Nome negozio</label>
            <input
              className="input"
              placeholder="Es. Lidl Via Roma"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              autoFocus
            />
          </div>
          <div>
            <label className="label">Tipo</label>
            <select
              className="input"
              value={form.store_category}
              onChange={(e) => setForm({ ...form, store_category: e.target.value })}
            >
              <option value="">Seleziona tipo...</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {CATEGORY_ICONS[cat.name] || '🏪'} {cat.name_display}
                </option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_default}
              onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
              className="rounded text-primary-600"
            />
            Negozio predefinito
          </label>
          <button className="btn-primary w-full" onClick={handleCreate} disabled={saving}>
            {saving ? 'Salvataggio...' : 'Aggiungi negozio'}
          </button>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Elimina negozio"
        message={`Eliminare "${deleteTarget?.name}"? Verranno rimosse anche tutte le corsie associate.`}
        confirmLabel="Elimina"
        loading={deleting}
      />
    </div>
  )
}
