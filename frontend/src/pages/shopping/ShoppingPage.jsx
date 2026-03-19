import { useState, useEffect, useCallback } from 'react'
import { Plus, ShoppingCart, Check, Trash2, Store, GripVertical, ChevronDown } from 'lucide-react'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'
import { shoppingApi } from '../../api/shopping'
import { storesApi } from '../../api/stores'
import { useAuthStore } from '../../store/authStore'
import { useShoppingWS } from '../../ws/useShoppingWS'
import Modal from '../../components/shared/Modal'
import ProductSearch from '../../components/shared/ProductSearch'
import ConfirmDialog from '../../components/shared/ConfirmDialog'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import BarcodeScanner from '../../components/shared/BarcodeScanner'
import { productsApi } from '../../api/products'
import toast from 'react-hot-toast'

function ShoppingItemRow({ item, dragHandleProps, onCheck, onUncheck, onDelete, onEdit }) {
  return (
    <div className={`flex items-center gap-2 py-3 border-b border-gray-100 last:border-0 ${item.checked ? 'opacity-50' : ''}`}>
      {dragHandleProps ? (
        <div {...dragHandleProps} className="text-gray-200 cursor-grab active:cursor-grabbing flex-shrink-0 touch-none px-0.5">
          <GripVertical size={15} />
        </div>
      ) : <div className="w-4 flex-shrink-0" />}

      <button
        onClick={() => item.checked ? onUncheck(item) : onCheck(item)}
        className={`w-6 h-6 rounded-full border-2 flex-shrink-0 flex items-center justify-center transition-colors ${
          item.checked ? 'bg-primary-600 border-primary-600' : 'border-gray-300 hover:border-primary-400'
        }`}
      >
        {item.checked && <Check size={12} className="text-white" strokeWidth={3} />}
      </button>

      <div className="flex-1 min-w-0" onClick={() => onEdit(item)} role="button">
        <p className={`text-sm font-medium ${item.checked ? 'line-through text-gray-400' : 'text-gray-900'}`}>
          {item.product_name}
        </p>
        <div className="flex items-center gap-2 text-xs text-gray-400 flex-wrap">
          {item.quantity && <span>{item.quantity} {item.unit_abbr || ''}</span>}
          {item.note && <span>· {item.note}</span>}
          {item.added_automatically && <span className="badge bg-blue-50 text-blue-600">Auto</span>}
        </div>
      </div>

      <button
        onClick={() => onDelete(item)}
        className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg flex-shrink-0"
      >
        <Trash2 size={15} />
      </button>
    </div>
  )
}

const CATEGORY_ICONS = {
  supermarket: '🛒',
  pharmacy: '💊',
  butcher: '🥩',
  fishmonger: '🐟',
  bakery: '🍞',
  market: '🥦',
  other: '🏪',
}

/**
 * Raggruppa gli item per negozio, poi per corsia.
 * Include TUTTI i negozi da storesList anche se vuoti.
 * Ordine: negozi con item (alpha) → gruppo senza negozio → negozi vuoti (alpha).
 */
function groupByStore(items, storesList) {
  const storeMap = Object.fromEntries(storesList.map((s) => [s.id, s]))

  // Inizializza tutti i negozi noti (anche vuoti)
  const groups = {}
  storesList.forEach((store) => {
    groups[store.id] = {
      storeId: store.id,
      storeName: store.name,
      storeIcon: CATEGORY_ICONS[store.store_category] || '🏪',
      aisleGroups: {},
      itemCount: 0,
    }
  })

  // Distribuisce gli item per negozio + corsia
  items.forEach((item) => {
    const storeKey = item.store || '__none__'
    if (!groups[storeKey]) {
      const storeObj = storeMap[storeKey]
      groups[storeKey] = {
        storeId: storeKey,
        storeName: item.store_name || 'Da assegnare',
        storeIcon: storeObj ? (CATEGORY_ICONS[storeObj.store_category] || '🏪') : '📋',
        aisleGroups: {},
        itemCount: 0,
      }
    }
    const aisleKey = item.store_aisle || '__no_aisle__'
    if (!groups[storeKey].aisleGroups[aisleKey]) {
      groups[storeKey].aisleGroups[aisleKey] = {
        aisleId: aisleKey,
        aisleName: item.aisle_name || null,
        aisleOrder: item.aisle_order ?? Infinity,  // null → in fondo
        items: [],
      }
    }
    groups[storeKey].aisleGroups[aisleKey].items.push(item)
    groups[storeKey].itemCount++
  })

  return Object.values(groups)
    .map((group) => ({
      ...group,
      // Ordina le corsie per il campo order impostato nel negozio; items senza corsia in fondo
      aisleGroups: Object.values(group.aisleGroups).sort((a, b) => {
        if (a.aisleId === '__no_aisle__') return 1
        if (b.aisleId === '__no_aisle__') return -1
        return a.aisleOrder - b.aisleOrder
      }),
    }))
    .sort((a, b) => {
      // "Da assegnare" sempre in cima (se ha item)
      if (a.storeId === '__none__' && a.itemCount > 0) return -1
      if (b.storeId === '__none__' && b.itemCount > 0) return 1
      // Negozi con item prima, vuoti in fondo
      const aHas = a.itemCount > 0
      const bHas = b.itemCount > 0
      if (aHas && !bHas) return -1
      if (!aHas && bHas) return 1
      return a.storeName.localeCompare(b.storeName, 'it')
    })
}

export default function ShoppingPage() {
  const { family } = useAuthStore()
  const [items, setItems] = useState([])
  const [stores, setStores] = useState([])
  const [loading, setLoading] = useState(true)
  const [collapsedStores, setCollapsedStores] = useState(new Set())
  const [quickAddStoreId, setQuickAddStoreId] = useState(null)
  const [quickAddSaving, setQuickAddSaving] = useState(false)
  const [showAdd, setShowAdd] = useState(false)
  const [showScanner, setShowScanner] = useState(false)
  const [showComplete, setShowComplete] = useState(false)
  const [addProduct, setAddProduct] = useState(null)
  const [addCategory, setAddCategory] = useState('')
  const [quantity, setQuantity] = useState('')
  const [note, setNote] = useState('')
  const [selectedStore, setSelectedStore] = useState('')
  const [saving, setSaving] = useState(false)
  const [completing, setCompleting] = useState(false)
  const [categories, setCategories] = useState([])
  const [editItem, setEditItem] = useState(null)
  const [editProductName, setEditProductName] = useState('')
  const [editCategory, setEditCategory] = useState('')
  const [editQuantity, setEditQuantity] = useState('')
  const [editNote, setEditNote] = useState('')
  const [editStore, setEditStore] = useState('')
  const [editDefaultStore, setEditDefaultStore] = useState('')
  const [editSaving, setEditSaving] = useState(false)

  const load = useCallback(async () => {
    if (!family) return
    try {
      const [itemsRes, storesRes] = await Promise.all([
        shoppingApi.list(family.id),
        storesApi.list(family.id),
      ])
      setItems(itemsRes.data.results || itemsRes.data)
      setStores(storesRes.data)
    } catch {
      toast.error('Errore nel caricamento lista')
    } finally {
      setLoading(false)
    }
  }, [family])

  useEffect(() => { load() }, [load])
  useShoppingWS(family?.id, { onUpdate: load })

  useEffect(() => {
    productsApi.categories()
      .then(({ data }) => setCategories(data))
      .catch(() => {})
  }, [])

  function toggleStore(storeId) {
    setCollapsedStores((prev) => {
      const next = new Set(prev)
      if (next.has(storeId)) next.delete(storeId)
      else next.add(storeId)
      return next
    })
  }

  async function handleQuickAddToStore(product, storeId) {
    setQuickAddSaving(true)
    const storeParam = (storeId && storeId !== '__none__') ? storeId : null
    try {
      await shoppingApi.quickAdd(family.id, { name: product.name, store: storeParam })
      toast.success(`${product.name} aggiunto`)
      setQuickAddStoreId(null)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Prodotto già in lista')
    } finally {
      setQuickAddSaving(false)
    }
  }

  async function handleCheck(item) {
    try {
      await shoppingApi.check(family.id, item.id)
      toast.success(`${item.product_name} aggiunto in dispensa`)
      load()
    } catch { toast.error('Errore') }
  }

  async function handleUncheck(item) {
    try {
      await shoppingApi.uncheck(family.id, item.id)
      load()
    } catch { toast.error('Errore') }
  }

  async function handleDelete(item) {
    try {
      await shoppingApi.delete(family.id, item.id)
      load()
    } catch { toast.error('Errore') }
  }

  // Drag & drop tra negozi
  async function handleDragEnd(result) {
    const { draggableId, source, destination } = result
    if (!destination || source.droppableId === destination.droppableId) return

    const newStoreId = destination.droppableId === '__none__' ? null : destination.droppableId
    const draggedItem = items.find((i) => i.id === draggableId)
    if (!draggedItem) return

    const newStoreName = newStoreId
      ? (stores.find((s) => s.id === newStoreId)?.name || null)
      : null

    // Aggiornamento ottimistico
    setItems((prev) => prev.map((i) =>
      i.id === draggableId
        ? { ...i, store: newStoreId, store_name: newStoreName, store_aisle: null, aisle_name: null }
        : i
    ))

    try {
      const { data } = await shoppingApi.update(family.id, draggableId, { store: newStoreId })
      setItems((prev) => prev.map((i) => i.id === draggableId ? { ...i, ...data } : i))
    } catch {
      toast.error('Errore nello spostamento')
      load()
    }
  }

  function openEdit(item) {
    setEditItem(item)
    setEditProductName(item.product_name || '')
    setEditCategory(item.product_category ? String(item.product_category) : '')
    setEditQuantity(item.quantity || '')
    setEditNote(item.note || '')
    setEditStore(item.store || '')
    setEditDefaultStore(item.product_default_store ? String(item.product_default_store) : '')
  }

  function closeEdit() {
    setEditItem(null)
    setEditProductName('')
    setEditCategory('')
    setEditQuantity('')
    setEditNote('')
    setEditStore('')
    setEditDefaultStore('')
  }

  async function handleEditSave() {
    if (!editItem) return
    if (!editProductName.trim()) return toast.error('Il nome prodotto non può essere vuoto')
    setEditSaving(true)
    try {
      const saves = [
        shoppingApi.update(family.id, editItem.id, {
          quantity: editQuantity || null,
          note: editNote || '',
          store: editStore || null,
        }),
      ]
      const origCat = editItem.product_category ? String(editItem.product_category) : ''
      const origDefaultStore = editItem.product_default_store ? String(editItem.product_default_store) : ''
      const productPatch = {}
      if (editProductName.trim() !== editItem.product_name)
        productPatch.name = editProductName.trim()
      if (editCategory !== origCat)
        productPatch.category = editCategory || null
      if (editDefaultStore !== origDefaultStore)
        productPatch.default_store = editDefaultStore || null
      if (Object.keys(productPatch).length > 0)
        saves.push(productsApi.update(editItem.product, productPatch))
      await Promise.all(saves)
      toast.success('Modifiche salvate')
      closeEdit()
      load()
    } catch { toast.error('Errore nel salvataggio') } finally { setEditSaving(false) }
  }

  function resetAddForm() {
    setAddProduct(null)
    setAddCategory('')
    setQuantity('')
    setNote('')
    setSelectedStore('')
  }

  async function handleAddProduct() {
    if (!addProduct) return
    if (!addProduct.id && !addCategory) {
      return toast.error('Seleziona una categoria per il prodotto')
    }
    setSaving(true)
    try {
      if (!addProduct.id) {
        await shoppingApi.quickAdd(family.id, {
          name: addProduct.name,
          category: addCategory || null,
          quantity: quantity || null,
          note: note || '',
          store: selectedStore || null,
        })
      } else {
        await shoppingApi.create(family.id, {
          product: addProduct.id,
          quantity: quantity || null,
          note: note || '',
          store: selectedStore || null,
        })
      }
      toast.success(`${addProduct.name} aggiunto alla lista`)
      setShowAdd(false)
      resetAddForm()
      load()
    } catch (err) {
      const data = err.response?.data
      const msg =
        data?.product?.[0] ||
        data?.non_field_errors?.[0] ||
        data?.detail ||
        data?.error ||
        (typeof data === 'string' ? data : null) ||
        'Errore nell\'aggiunta'
      toast.error(msg)
    } finally {
      setSaving(false)
    }
  }

  function handleQuickCreate(name) {
    setAddProduct({ id: null, name })
  }

  async function handleComplete() {
    setCompleting(true)
    try {
      await shoppingApi.complete(family.id)
      toast.success('Spesa completata!')
      setShowComplete(false)
      load()
    } catch { toast.error('Errore') } finally {
      setCompleting(false)
    }
  }

  async function handleBarcodeScan(barcode) {
    setShowScanner(false)
    try {
      const { data } = await productsApi.scan(barcode)
      if (data.found === false) {
        toast.error('Prodotto non trovato')
      } else {
        setAddProduct(data)
        setShowAdd(true)
      }
    } catch { toast.error('Errore nella scansione') }
  }

  const unchecked = items.filter((i) => !i.checked)
  const checked = items.filter((i) => i.checked)
  const progress = items.length > 0 ? Math.round((checked.length / items.length) * 100) : 0
  const uncheckedGroups = groupByStore(unchecked, stores)
  const listIsEmpty = unchecked.length === 0 && checked.length === 0

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <ShoppingCart size={22} className="text-primary-600" /> Lista spesa
        </h1>
        <div className="flex gap-1">
          <button onClick={() => setShowScanner(true)} className="btn-secondary text-xs px-3 py-1.5">📷</button>
          <button onClick={() => setShowAdd(true)} className="btn-primary text-xs px-3 py-1.5">
            <Plus size={14} /> Aggiungi
          </button>
        </div>
      </div>

      {/* Progress bar */}
      {items.length > 0 && (
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>{checked.length} / {items.length} prodotti</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12"><LoadingSpinner /></div>
      ) : listIsEmpty ? (
        <div className="flex flex-col items-center py-16 text-gray-400">
          <ShoppingCart size={48} className="mb-3 opacity-30" />
          <p className="text-sm">Lista vuota. Aggiungi prodotti!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Unchecked — raggruppati per negozio + corsia, drag & drop tra negozi */}
          <DragDropContext onDragEnd={handleDragEnd}>
            {uncheckedGroups.map((group) => {
              const isCollapsed = collapsedStores.has(group.storeId)
              const isEmpty = group.itemCount === 0

              // Costruisce lista piatta con header corsia intercalati,
              // mantenendo indici Draggable sequenziali
              let draggableIdx = 0
              const flatRows = []
              group.aisleGroups.forEach((aisle) => {
                if (aisle.aisleName) {
                  flatRows.push({ type: 'header', key: `hdr-${aisle.aisleId}`, aisleName: aisle.aisleName })
                }
                aisle.items.forEach((item) => {
                  flatRows.push({ type: 'item', key: item.id, item, idx: draggableIdx++ })
                })
              })

              return (
                <div key={group.storeId} className="card overflow-hidden">
                  {/* Header negozio — clic per espandere/collassare */}
                  <div
                    className={`px-4 py-3 flex items-center gap-2 ${!isEmpty ? 'cursor-pointer select-none hover:bg-gray-50 active:bg-gray-100' : ''}`}
                    onClick={() => !isEmpty && toggleStore(group.storeId)}
                  >
                    <span className="text-base leading-none">{group.storeIcon}</span>
                    <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide flex-1 truncate">
                      {group.storeName}
                    </p>
                    {isEmpty ? (
                      <span className="text-[10px] text-gray-300 font-normal">vuoto</span>
                    ) : (
                      <>
                        <span className="text-xs text-gray-400 font-normal">{group.itemCount}</span>
                        <ChevronDown
                          size={15}
                          className={`text-gray-400 transition-transform duration-200 flex-shrink-0 ${isCollapsed ? '-rotate-90' : ''}`}
                        />
                      </>
                    )}
                    {/* Bottone aggiunta rapida per questo negozio */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setQuickAddStoreId(quickAddStoreId === group.storeId ? null : group.storeId)
                      }}
                      disabled={quickAddSaving}
                      className={`p-1 rounded-lg flex-shrink-0 transition-colors ${
                        quickAddStoreId === group.storeId
                          ? 'text-primary-600 bg-primary-100'
                          : 'text-gray-300 hover:text-primary-600 hover:bg-primary-50'
                      }`}
                      title="Aggiungi prodotto a questo negozio"
                    >
                      <Plus size={14} />
                    </button>
                  </div>

                  {/* Pannello aggiunta rapida inline */}
                  {quickAddStoreId === group.storeId && (
                    <div className="px-4 py-2 bg-primary-50 border-b border-primary-100 space-y-1.5">
                      <ProductSearch
                        onSelect={(p) => handleQuickAddToStore(p, group.storeId)}
                        onCreateNew={(name) => handleQuickAddToStore({ name }, group.storeId)}
                        placeholder="Cerca o crea prodotto..."
                        autoFocus
                      />
                      <button
                        onClick={() => setQuickAddStoreId(null)}
                        className="text-xs text-gray-400 hover:text-gray-600"
                      >
                        Annulla
                      </button>
                    </div>
                  )}

                  {/* Area droppable — sempre in DOM per il DnD */}
                  <Droppable droppableId={group.storeId}>
                    {(provided, snapshot) => {
                      // Determina stile del contenitore in base allo stato
                      let containerClass = 'transition-colors'
                      if (isEmpty) {
                        // Negozio vuoto: zona drop con bordo tratteggiato
                        containerClass += ` mx-4 mb-3 rounded-xl border border-dashed flex items-center justify-center min-h-[36px] ${
                          snapshot.isDraggingOver
                            ? 'border-primary-400 bg-primary-50'
                            : 'border-gray-200'
                        }`
                      } else if (isCollapsed && !snapshot.isDraggingOver) {
                        // Collassato senza hover: strip sottile per DnD detection
                        containerClass += ' h-1.5'
                      } else if (isCollapsed && snapshot.isDraggingOver) {
                        // Collassato con hover: zona drop visibile
                        containerClass += ' px-4 py-4 flex items-center justify-center bg-primary-50'
                      } else {
                        // Espanso
                        containerClass += ` px-4 pb-2 min-h-[40px] ${snapshot.isDraggingOver ? 'bg-primary-50' : ''}`
                      }

                      return (
                        <div
                          ref={provided.innerRef}
                          {...provided.droppableProps}
                          className={containerClass}
                        >
                          {/* Messaggio zona drop per negozio vuoto */}
                          {isEmpty && (
                            <span className={`text-[10px] select-none pointer-events-none ${snapshot.isDraggingOver ? 'text-primary-400' : 'text-gray-300'}`}>
                              {snapshot.isDraggingOver ? 'Trascina qui' : 'nessun prodotto'}
                            </span>
                          )}

                          {/* Messaggio zona drop per negozio collassato */}
                          {!isEmpty && isCollapsed && snapshot.isDraggingOver && (
                            <span className="text-xs text-primary-400 select-none pointer-events-none">
                              Trascina qui per spostare
                            </span>
                          )}

                          {/* Items espansi con sezioni corsia */}
                          {!isEmpty && !isCollapsed && flatRows.map((row) =>
                            row.type === 'header' ? (
                              /* Separatore corsia */
                              <div key={row.key} className="flex items-center gap-3 py-2 -mx-0">
                                <div className="flex-1 h-px bg-gray-100" />
                                <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide shrink-0">
                                  {row.aisleName}
                                </span>
                                <div className="flex-1 h-px bg-gray-100" />
                              </div>
                            ) : (
                              <Draggable key={row.key} draggableId={row.item.id} index={row.idx}>
                                {(dp, ds) => (
                                  <div
                                    ref={dp.innerRef}
                                    {...dp.draggableProps}
                                    className={ds.isDragging ? 'shadow-lg rounded-xl bg-white opacity-95' : ''}
                                  >
                                    <ShoppingItemRow
                                      item={row.item}
                                      dragHandleProps={dp.dragHandleProps}
                                      onCheck={handleCheck}
                                      onUncheck={handleUncheck}
                                      onDelete={handleDelete}
                                      onEdit={openEdit}
                                    />
                                  </div>
                                )}
                              </Draggable>
                            )
                          )}

                          {provided.placeholder}
                        </div>
                      )
                    }}
                  </Droppable>
                </div>
              )
            })}
          </DragDropContext>

          {/* Già presi */}
          {checked.length > 0 && (
            <div className="card overflow-hidden">
              <div className="px-4 pt-3 pb-0">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                  Già presi ({checked.length})
                </p>
              </div>
              <div className="px-4 pb-2">
                {checked.map((item) => (
                  <ShoppingItemRow
                    key={item.id}
                    item={item}
                    onCheck={handleCheck}
                    onUncheck={handleUncheck}
                    onDelete={handleDelete}
                    onEdit={openEdit}
                  />
                ))}
              </div>
            </div>
          )}

          {checked.length > 0 && (
            <button className="btn-primary w-full" onClick={() => setShowComplete(true)}>
              <Check size={16} /> Completa spesa
            </button>
          )}
        </div>
      )}

      {/* Modal aggiunta prodotto */}
      <Modal
        open={showAdd}
        onClose={() => { setShowAdd(false); resetAddForm() }}
        title="Aggiungi alla lista"
      >
        <div className="space-y-4">
          {!addProduct ? (
            <ProductSearch onSelect={setAddProduct} onCreateNew={handleQuickCreate} autoFocus />
          ) : (
            <>
              <div className="flex items-center gap-3 p-3 bg-primary-50 rounded-xl">
                {addProduct.image_url && (
                  <img src={addProduct.image_url} alt="" className="w-8 h-8 rounded-lg object-cover flex-shrink-0" />
                )}
                <p className="font-medium text-gray-900 flex-1">{addProduct.name}</p>
                <button onClick={() => setAddProduct(null)} className="text-xs text-gray-400 underline">
                  Cambia
                </button>
              </div>

              {!addProduct.id && (
                <div>
                  <label className="label">
                    Categoria <span className="text-red-500">*</span>
                  </label>
                  <select
                    className="input"
                    value={addCategory}
                    onChange={(e) => setAddCategory(e.target.value)}
                  >
                    <option value="">— Seleziona categoria —</option>
                    {categories
                      .slice()
                      .sort((a, b) => a.name.localeCompare(b.name, 'it'))
                      .map((c) => (
                        <option key={c.id} value={c.id}>{c.icon} {c.name}</option>
                      ))}
                  </select>
                </div>
              )}

              <div>
                <label className="label">Quantità (opzionale)</label>
                <input className="input" placeholder="Es. 2, 500g, 1 litro" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
              </div>

              {stores.length > 0 && (
                <div>
                  <label className="label flex items-center gap-1">
                    <Store size={13} className="text-gray-400" /> Negozio (opzionale)
                  </label>
                  <select
                    className="input"
                    value={selectedStore}
                    onChange={(e) => setSelectedStore(e.target.value)}
                  >
                    <option value="">Nessun negozio</option>
                    {stores.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="label">Note (opzionale)</label>
                <input className="input" placeholder="Es. senza lattosio" value={note} onChange={(e) => setNote(e.target.value)} />
              </div>
              <button className="btn-primary w-full" onClick={handleAddProduct} disabled={saving}>
                {saving ? 'Aggiunta...' : 'Aggiungi alla lista'}
              </button>
            </>
          )}
        </div>
      </Modal>

      <ConfirmDialog
        open={showComplete}
        onClose={() => setShowComplete(false)}
        onConfirm={handleComplete}
        title="Completa spesa"
        message={`Archivia i ${checked.length} prodotti spuntati? Verranno rimossi dalla lista, quelli non spuntati rimarranno.`}
        confirmLabel="Completa"
        danger={false}
        loading={completing}
      />

      {showScanner && (
        <BarcodeScanner onResult={handleBarcodeScan} onClose={() => setShowScanner(false)} />
      )}

      {/* Modal modifica prodotto */}
      <Modal open={!!editItem} onClose={closeEdit} title="Modifica prodotto">
        <div className="space-y-4">
          <div>
            <label className="label">Nome prodotto</label>
            <input className="input" placeholder="Nome prodotto" value={editProductName} onChange={(e) => setEditProductName(e.target.value)} />
          </div>

          <div>
            <label className="label">Categoria</label>
            <select
              className="input"
              value={editCategory}
              onChange={(e) => setEditCategory(e.target.value)}
            >
              <option value="">— Nessuna categoria —</option>
              {categories
                .slice()
                .sort((a, b) => a.name.localeCompare(b.name, 'it'))
                .map((c) => (
                  <option key={c.id} value={c.id}>{c.icon} {c.name}</option>
                ))}
            </select>
          </div>

          <div>
            <label className="label">Quantità (opzionale)</label>
            <input className="input" placeholder="Es. 2, 500g, 1 litro" value={editQuantity} onChange={(e) => setEditQuantity(e.target.value)} />
          </div>

          {stores.length > 0 && (
            <div>
              <label className="label flex items-center gap-1">
                <Store size={13} className="text-gray-400" /> Negozio (opzionale)
              </label>
              <select
                className="input"
                value={editStore}
                onChange={(e) => setEditStore(e.target.value)}
              >
                <option value="">Nessun negozio</option>
                {stores.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
          )}

          {stores.length > 0 && (
            <div>
              <label className="label flex items-center gap-1">
                <Store size={13} className="text-gray-400" /> Negozio preferito prodotto (opzionale)
              </label>
              <select
                className="input"
                value={editDefaultStore}
                onChange={(e) => setEditDefaultStore(e.target.value)}
              >
                <option value="">Nessun negozio preferito</option>
                {stores.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
          )}

          <div>
            <label className="label">Note (opzionale)</label>
            <input className="input" placeholder="Es. senza lattosio" value={editNote} onChange={(e) => setEditNote(e.target.value)} />
          </div>

          <button className="btn-primary w-full" onClick={handleEditSave} disabled={editSaving}>
            {editSaving ? 'Salvataggio...' : 'Salva modifiche'}
          </button>
        </div>
      </Modal>
    </div>
  )
}
