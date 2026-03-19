import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Plus, GripVertical, Pencil, Trash2, Check, X, ShoppingCart } from 'lucide-react'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'
import { storesApi } from '../../api/stores'
import { shoppingApi } from '../../api/shopping'
import { productsApi } from '../../api/products'
import { useAuthStore } from '../../store/authStore'
import ConfirmDialog from '../../components/shared/ConfirmDialog'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import ProductSearch from '../../components/shared/ProductSearch'
import toast from 'react-hot-toast'

function AisleRow({ aisle, index, onEdit, onDelete }) {
  return (
    <Draggable draggableId={aisle.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          className={`flex items-center gap-3 py-3 px-4 border-b border-gray-100 last:border-0 bg-white transition-shadow ${snapshot.isDragging ? 'shadow-lg rounded-xl' : ''}`}
        >
          <div {...provided.dragHandleProps} className="text-gray-300 cursor-grab active:cursor-grabbing">
            <GripVertical size={18} />
          </div>
          <span className="text-base leading-none flex-shrink-0">
            {aisle.product_category_icon || '📦'}
          </span>
          <p className="flex-1 text-sm font-medium text-gray-800">{aisle.name}</p>
          <button
            onClick={() => onEdit(aisle)}
            className="p-1.5 text-gray-300 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
          >
            <Pencil size={14} />
          </button>
          <button
            onClick={() => onDelete(aisle)}
            className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg"
          >
            <Trash2 size={14} />
          </button>
        </div>
      )}
    </Draggable>
  )
}

export default function StoreDetailPage() {
  const { storeId } = useParams()
  const navigate = useNavigate()
  const { family } = useAuthStore()
  const [store, setStore] = useState(null)
  const [aisles, setAisles] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [newAisleCategory, setNewAisleCategory] = useState('')
  const [addingAisle, setAddingAisle] = useState(false)
  const [savingAisle, setSavingAisle] = useState(false)
  const [editAisle, setEditAisle] = useState(null)
  const [editCategory, setEditCategory] = useState('')
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [editingStore, setEditingStore] = useState(false)
  const [storeName, setStoreName] = useState('')
  const [shoppingItems, setShoppingItems] = useState([])
  const [showAddShopping, setShowAddShopping] = useState(false)
  const [addingShoppingItem, setAddingShoppingItem] = useState(false)

  const load = useCallback(async () => {
    if (!family) return
    try {
      const [storeRes, aislesRes] = await Promise.all([
        storesApi.get(family.id, storeId),
        storesApi.listAisles(family.id, storeId),
      ])
      setStore(storeRes.data)
      setStoreName(storeRes.data.name)
      setAisles(aislesRes.data)
    } catch {
      toast.error('Errore nel caricamento negozio')
      navigate('/stores')
    } finally {
      setLoading(false)
    }
  }, [family, storeId, navigate])

  useEffect(() => { load() }, [load])

  const loadShopping = useCallback(async () => {
    if (!family) return
    try {
      const { data } = await shoppingApi.list(family.id, { store: storeId, checked: 'false' })
      setShoppingItems(Array.isArray(data) ? data : (data.results || []))
    } catch {}
  }, [family, storeId])

  useEffect(() => { loadShopping() }, [loadShopping])

  async function handleAddToShoppingList(product) {
    setAddingShoppingItem(true)
    try {
      await shoppingApi.quickAdd(family.id, { name: product.name, store: storeId })
      toast.success(`${product.name} aggiunto alla lista`)
      setShowAddShopping(false)
      loadShopping()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Prodotto già in lista')
    } finally {
      setAddingShoppingItem(false)
    }
  }

  async function handleCheckShoppingItem(item) {
    try {
      await shoppingApi.check(family.id, item.id)
      toast.success(`${item.product_name} spuntato ✓`)
      loadShopping()
    } catch {
      toast.error('Errore')
    }
  }

  async function handleRemoveShoppingItem(item) {
    try {
      await shoppingApi.delete(family.id, item.id)
      setShoppingItems((prev) => prev.filter((i) => i.id !== item.id))
    } catch {
      toast.error('Errore')
    }
  }

  // Carica le categorie prodotto una sola volta
  useEffect(() => {
    productsApi.categories()
      .then(({ data }) => setCategories(data.slice().sort((a, b) => a.name.localeCompare(b.name, 'it'))))
      .catch(() => {})
  }, [])

  // Categorie non ancora usate come corsie
  const usedCategoryIds = new Set(aisles.map((a) => a.product_category).filter(Boolean))
  const availableCategories = categories.filter((c) => !usedCategoryIds.has(c.id))

  async function handleAddAisle() {
    if (!newAisleCategory) return toast.error('Seleziona una categoria')
    setSavingAisle(true)
    try {
      const { data } = await storesApi.createAisle(family.id, storeId, {
        product_category: newAisleCategory,
        // name is auto-set by backend from category
      })
      setAisles((prev) => [...prev, data])
      setNewAisleCategory('')
      setAddingAisle(false)
      toast.success('Corsia aggiunta')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore')
    } finally {
      setSavingAisle(false)
    }
  }

  async function handleEditAisle() {
    if (!editCategory) return toast.error('Seleziona una categoria')
    try {
      const cat = categories.find((c) => c.id === editCategory)
      const name = cat ? `${cat.icon} ${cat.name}`.trim() : ''
      const { data } = await storesApi.updateAisle(family.id, storeId, editAisle.id, {
        product_category: editCategory,
        name,
      })
      setAisles((prev) => prev.map((a) => (a.id === data.id ? data : a)))
      setEditAisle(null)
      toast.success('Corsia aggiornata')
    } catch {
      toast.error('Errore nel salvataggio')
    }
  }

  async function handleDeleteAisle() {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await storesApi.deleteAisle(family.id, storeId, deleteTarget.id)
      setAisles((prev) => prev.filter((a) => a.id !== deleteTarget.id))
      setDeleteTarget(null)
      toast.success('Corsia eliminata')
    } catch {
      toast.error('Errore nell\'eliminazione')
    } finally {
      setDeleting(false)
    }
  }

  async function handleSaveStoreName() {
    if (!storeName.trim()) return
    try {
      const { data } = await storesApi.update(family.id, storeId, { name: storeName.trim() })
      setStore(data)
      setEditingStore(false)
      toast.success('Nome aggiornato')
    } catch {
      toast.error('Errore nel salvataggio')
    }
  }

  async function handleDragEnd(result) {
    if (!result.destination) return
    const from = result.source.index
    const to = result.destination.index
    if (from === to) return

    const reordered = Array.from(aisles)
    const [moved] = reordered.splice(from, 1)
    reordered.splice(to, 0, moved)
    setAisles(reordered)

    try {
      await storesApi.reorderAisles(family.id, storeId, reordered.map((a) => a.id))
    } catch {
      toast.error('Errore nel riordinamento')
      load()
    }
  }

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner /></div>

  // Categorie disponibili per l'edit di una corsia (include la categoria corrente della corsia)
  const editAvailableCategories = editAisle
    ? categories.filter((c) => !usedCategoryIds.has(c.id) || c.id === editAisle.product_category)
    : availableCategories

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/stores')} className="p-2 -ml-2 text-gray-500 hover:bg-gray-100 rounded-xl">
          <ArrowLeft size={20} />
        </button>
        {editingStore ? (
          <div className="flex items-center gap-2 flex-1">
            <input
              className="input flex-1 text-base font-bold"
              value={storeName}
              onChange={(e) => setStoreName(e.target.value)}
              autoFocus
              onKeyDown={(e) => { if (e.key === 'Enter') handleSaveStoreName() }}
            />
            <button onClick={handleSaveStoreName} className="p-2 text-primary-600 hover:bg-primary-50 rounded-xl">
              <Check size={18} />
            </button>
            <button onClick={() => { setEditingStore(false); setStoreName(store.name) }} className="p-2 text-gray-400 hover:bg-gray-100 rounded-xl">
              <X size={18} />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2 flex-1">
            <h1 className="text-xl font-bold text-gray-900 flex-1">{store?.name}</h1>
            <button onClick={() => setEditingStore(true)} className="p-2 text-gray-300 hover:text-primary-600 hover:bg-primary-50 rounded-xl">
              <Pencil size={16} />
            </button>
          </div>
        )}
      </div>

      <p className="text-sm text-gray-400">{store?.store_category_name}</p>

      {/* Aisles section */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-semibold text-gray-700">Corsie ({aisles.length})</p>
          {availableCategories.length > 0 && (
            <button
              onClick={() => setAddingAisle(true)}
              className="btn-secondary text-xs px-3 py-1.5"
            >
              <Plus size={13} /> Aggiungi
            </button>
          )}
        </div>

        {addingAisle && (
          <div className="flex items-center gap-2 mb-3 p-3 bg-primary-50 rounded-xl">
            <select
              className="input flex-1 bg-white text-sm"
              value={newAisleCategory}
              onChange={(e) => setNewAisleCategory(e.target.value)}
              autoFocus
            >
              <option value="">— Seleziona categoria —</option>
              {availableCategories.map((c) => (
                <option key={c.id} value={c.id}>{c.icon} {c.name}</option>
              ))}
            </select>
            <button onClick={handleAddAisle} disabled={savingAisle} className="p-2 text-primary-600 hover:bg-primary-100 rounded-xl">
              <Check size={18} />
            </button>
            <button onClick={() => { setAddingAisle(false); setNewAisleCategory('') }} className="p-2 text-gray-400 hover:bg-gray-100 rounded-xl">
              <X size={18} />
            </button>
          </div>
        )}

        {aisles.length === 0 && !addingAisle ? (
          <div className="text-center py-8 text-gray-400">
            <p className="text-sm">Nessuna corsia. Aggiungine una per organizzare i prodotti.</p>
          </div>
        ) : (
          <div className="card overflow-hidden">
            <DragDropContext onDragEnd={handleDragEnd}>
              <Droppable droppableId="aisles">
                {(provided) => (
                  <div ref={provided.innerRef} {...provided.droppableProps}>
                    {aisles.map((aisle, index) => (
                      editAisle?.id === aisle.id ? (
                        <div key={aisle.id} className="flex items-center gap-2 py-3 px-4 border-b border-gray-100 bg-primary-50">
                          <select
                            className="input flex-1 bg-white text-sm"
                            value={editCategory}
                            onChange={(e) => setEditCategory(e.target.value)}
                            autoFocus
                          >
                            <option value="">— Seleziona categoria —</option>
                            {editAvailableCategories.map((c) => (
                              <option key={c.id} value={c.id}>{c.icon} {c.name}</option>
                            ))}
                          </select>
                          <button onClick={handleEditAisle} className="p-1.5 text-primary-600 hover:bg-primary-100 rounded-lg">
                            <Check size={16} />
                          </button>
                          <button onClick={() => setEditAisle(null)} className="p-1.5 text-gray-400 hover:bg-gray-100 rounded-lg">
                            <X size={16} />
                          </button>
                        </div>
                      ) : (
                        <AisleRow
                          key={aisle.id}
                          aisle={aisle}
                          index={index}
                          onEdit={(a) => { setEditAisle(a); setEditCategory(a.product_category || '') }}
                          onDelete={setDeleteTarget}
                        />
                      )
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </DragDropContext>
          </div>
        )}
      </div>

      <p className="text-xs text-gray-400 text-center">
        Trascina le corsie per riordinarle
      </p>

      {/* Lista della spesa per questo negozio */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
            <ShoppingCart size={15} className="text-primary-500" />
            Lista della spesa ({shoppingItems.length})
          </p>
          <button
            onClick={() => setShowAddShopping((v) => !v)}
            disabled={addingShoppingItem}
            className="btn-secondary text-xs px-3 py-1.5 disabled:opacity-50"
          >
            <Plus size={13} /> Aggiungi
          </button>
        </div>

        {showAddShopping && (
          <div className="mb-3 p-3 bg-primary-50 rounded-xl space-y-2">
            <ProductSearch
              onSelect={(product) => handleAddToShoppingList(product)}
              onCreateNew={(name) => handleAddToShoppingList({ name })}
              placeholder="Cerca o crea prodotto..."
              autoFocus
            />
            <button
              onClick={() => setShowAddShopping(false)}
              className="text-xs text-gray-400 hover:text-gray-600"
            >
              Annulla
            </button>
          </div>
        )}

        {shoppingItems.length === 0 && !showAddShopping ? (
          <p className="text-sm text-gray-400 text-center py-4">
            Nessun prodotto in lista per questo negozio.
          </p>
        ) : shoppingItems.length > 0 && (
          <div className="card divide-y divide-gray-100">
            {shoppingItems.map((item) => (
              <div key={item.id} className="flex items-center gap-3 px-4 py-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{item.product_name}</p>
                  {item.aisle_name && (
                    <p className="text-[11px] text-gray-400 truncate">{item.aisle_name}</p>
                  )}
                </div>
                <button
                  onClick={() => handleCheckShoppingItem(item)}
                  className="p-1.5 text-gray-300 hover:text-green-500 hover:bg-green-50 rounded-lg"
                  title="Spunta prodotto"
                >
                  <Check size={15} />
                </button>
                <button
                  onClick={() => handleRemoveShoppingItem(item)}
                  className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg"
                  title="Rimuovi dalla lista"
                >
                  <X size={15} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteAisle}
        title="Elimina corsia"
        message={`Eliminare la corsia "${deleteTarget?.name}"?`}
        confirmLabel="Elimina"
        loading={deleting}
      />
    </div>
  )
}
