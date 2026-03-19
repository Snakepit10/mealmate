import { useState, useEffect, useCallback } from 'react'
import { Plus, Package, Calendar, Trash2, CheckCircle, Pencil, ShoppingCart, Store, RotateCcw } from 'lucide-react'
import { pantryApi } from '../../api/pantry'
import { shoppingApi } from '../../api/shopping'
import { storesApi } from '../../api/stores'
import { useAuthStore } from '../../store/authStore'
import { usePantryWS } from '../../ws/usePantryWS'
import Modal from '../../components/shared/Modal'
import ProductSearch from '../../components/shared/ProductSearch'
import BarcodeScanner from '../../components/shared/BarcodeScanner'
import { productsApi } from '../../api/products'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import toast from 'react-hot-toast'
import { format, parseISO } from 'date-fns'
import { it } from 'date-fns/locale'

function PantryItemCard({ item, onFinish, onRestore, onDelete, onEdit, onAddToShopping }) {
  const isExpiringSoon = item.expiry_date && new Date(item.expiry_date) <= new Date(Date.now() + 3 * 86400000)
  const isExpired = item.expiry_date && new Date(item.expiry_date) < new Date()

  return (
    <div className={`card p-3 flex items-center gap-3 ${item.status === 'finished' ? 'opacity-60' : ''}`}>
      {item.product_image && (
        <img src={item.product_image} alt="" className="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
      )}

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{item.product_name}</p>
        {item.product_brand && <p className="text-xs text-gray-400">{item.product_brand}</p>}
        {item.note && <p className="text-xs text-gray-400 truncate">📝 {item.note}</p>}
        {item.expiry_date && (
          <p className={`text-xs flex items-center gap-1 mt-0.5 ${isExpired ? 'text-red-500' : isExpiringSoon ? 'text-orange-500' : 'text-gray-400'}`}>
            <Calendar size={11} />
            {isExpired ? 'Scaduto il ' : 'Scade il '}
            {format(parseISO(item.expiry_date), 'd MMM', { locale: it })}
          </p>
        )}
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => onEdit(item)}
          className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg"
          title="Modifica"
        >
          <Pencil size={15} />
        </button>
        {item.status === 'present' && (
          <button
            onClick={() => onFinish(item)}
            className="p-2 text-orange-500 hover:bg-orange-50 rounded-lg"
            title="Segna come terminato"
          >
            <CheckCircle size={18} />
          </button>
        )}
        {item.status === 'finished' && (
          <>
            <button
              onClick={() => onRestore(item)}
              className="p-2 text-green-500 hover:bg-green-50 rounded-lg"
              title="Ripristina in dispensa"
            >
              <RotateCcw size={16} />
            </button>
            <button
              onClick={() => onAddToShopping(item)}
              className="p-2 text-primary-500 hover:bg-primary-50 rounded-lg"
              title="Aggiungi alla lista della spesa"
            >
              <ShoppingCart size={16} />
            </button>
          </>
        )}
        <button
          onClick={() => onDelete(item)}
          className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg"
        >
          <Trash2 size={16} />
        </button>
      </div>
    </div>
  )
}

/**
 * Raggruppa items per categoria prodotto.
 * Se allCategories è fornito, include anche le categorie senza prodotti (in fondo).
 */
function groupByCategory(items, allCategories = []) {
  const groups = {}

  // Inizializza tutte le categorie note (anche vuote)
  allCategories.forEach((cat) => {
    groups[cat.name] = { name: cat.name, icon: cat.icon || '📦', categoryId: cat.id, items: [] }
  })

  items.forEach((item) => {
    const key = item.product_category_name || 'Altro'
    const icon = item.product_category_icon || '📦'
    if (!groups[key]) groups[key] = { name: key, icon, categoryId: item.product_category || null, items: [] }
    groups[key].items.push(item)
  })

  return Object.values(groups).sort((a, b) => {
    const aHas = a.items.length > 0
    const bHas = b.items.length > 0
    // Categorie con prodotti prima, vuote in fondo
    if (aHas && !bHas) return -1
    if (!aHas && bHas) return 1
    // "Altro" sempre last nel suo gruppo
    if (a.name === 'Altro') return 1
    if (b.name === 'Altro') return -1
    return a.name.localeCompare(b.name, 'it')
  })
}

export default function PantryPage() {
  const { family } = useAuthStore()
  const [tab, setTab] = useState('present')
  const [items, setItems] = useState([])
  const [categories, setCategories] = useState([])
  const [stores, setStores] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [showScanner, setShowScanner] = useState(false)
  const [addProduct, setAddProduct] = useState(null)
  const [addCategory, setAddCategory] = useState('')
  const [expiryDate, setExpiryDate] = useState('')
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [editProductName, setEditProductName] = useState('')
  const [editProductBrand, setEditProductBrand] = useState('')
  const [editExpiry, setEditExpiry] = useState('')
  const [editNote, setEditNote] = useState('')
  const [editCategory, setEditCategory] = useState('')
  const [editDefaultStore, setEditDefaultStore] = useState('')
  const [editSaving, setEditSaving] = useState(false)
  const [quickAddCategoryName, setQuickAddCategoryName] = useState(null)
  const [quickAddCategorySaving, setQuickAddCategorySaving] = useState(false)

  const load = useCallback(async () => {
    if (!family) return
    try {
      const { data } = await pantryApi.list(family.id)
      setItems(data.results || data)
    } catch {
      toast.error('Errore nel caricamento dispensa')
    } finally {
      setLoading(false)
    }
  }, [family])

  useEffect(() => { load() }, [load])

  // Carica le categorie una sola volta
  useEffect(() => {
    productsApi.categories()
      .then(({ data }) => setCategories(data))
      .catch(() => {})
  }, [])

  // Carica i negozi della famiglia
  useEffect(() => {
    if (!family) return
    storesApi.list(family.id)
      .then(({ data }) => setStores(data))
      .catch(() => {})
  }, [family])

  usePantryWS(family?.id, { onUpdate: load })

  async function handleAddToShopping(item) {
    try {
      await shoppingApi.quickAdd(family.id, { name: item.product_name })
      toast.success(`${item.product_name} aggiunto alla lista della spesa`)
    } catch (err) {
      const msg = err.response?.data?.detail || 'Già presente nella lista'
      toast.error(msg)
    }
  }

  async function handleFinish(item) {
    try {
      const { data } = await pantryApi.finish(family.id, item.id)
      toast.success(`${item.product_name} segnato come terminato`)
      if (data.auto_added_store) {
        toast.success(`Aggiunto automaticamente alla lista di ${data.auto_added_store}`, { icon: '🛒' })
      } else if (data.suggest_shopping) {
        toast(
          (t) => (
            <div className="flex items-center gap-3">
              <span className="text-sm">Vuoi aggiungerlo alla lista?</span>
              <button
                className="text-sm font-semibold text-primary-600 hover:text-primary-800 whitespace-nowrap"
                onClick={() => { handleAddToShopping(item); toast.dismiss(t.id) }}
              >
                + Aggiungi
              </button>
              <button
                className="text-sm text-gray-400 hover:text-gray-600"
                onClick={() => toast.dismiss(t.id)}
              >
                No
              </button>
            </div>
          ),
          { icon: '🛒', duration: 8000 }
        )
      }
      load()
    } catch {
      toast.error('Errore')
    }
  }

  async function handleRestore(item) {
    try {
      await pantryApi.restore(family.id, item.id)
      toast.success(`${item.product_name} ripristinato in dispensa`)
      load()
    } catch {
      toast.error('Errore nel ripristino')
    }
  }

  async function handleDelete(item) {
    try {
      await pantryApi.delete(family.id, item.id)
      toast.success('Rimosso dalla dispensa')
      load()
    } catch {
      toast.error('Errore')
    }
  }

  async function handleQuickAddToCategory(product, categoryId) {
    setQuickAddCategorySaving(true)
    try {
      let productId = product.id
      if (!productId) {
        const { data: newProduct } = await productsApi.create({
          name: product.name,
          ...(categoryId ? { category: categoryId } : {}),
        })
        productId = newProduct.id
      }
      await pantryApi.create(family.id, { product: productId })
      toast.success(`${product.name} aggiunto in dispensa`)
      setQuickAddCategoryName(null)
      load()
    } catch (err) {
      const msg = err.response?.data
      toast.error(typeof msg === 'object' ? Object.values(msg).flat().join(', ') : 'Errore nell\'aggiunta')
    } finally {
      setQuickAddCategorySaving(false)
    }
  }

  function openEdit(item) {
    setEditItem(item)
    setEditProductName(item.product_name || '')
    setEditProductBrand(item.product_brand || '')
    setEditExpiry(item.expiry_date || '')
    setEditNote(item.note || '')
    setEditCategory(item.product_category ? String(item.product_category) : '')
    setEditDefaultStore(item.product_default_store ? String(item.product_default_store) : '')
  }

  function closeEdit() {
    setEditItem(null)
    setEditProductName('')
    setEditProductBrand('')
    setEditExpiry('')
    setEditNote('')
    setEditCategory('')
    setEditDefaultStore('')
  }

  async function handleEditSave() {
    if (!editItem) return
    if (!editProductName.trim()) return toast.error('Il nome prodotto non può essere vuoto')
    setEditSaving(true)
    try {
      const saves = [
        pantryApi.update(family.id, editItem.id, {
          expiry_date: editExpiry || null,
          note: editNote || '',
        }),
      ]
      const origCat = editItem.product_category ? String(editItem.product_category) : ''
      const origStore = editItem.product_default_store ? String(editItem.product_default_store) : ''
      const productPatch = {}
      if (editProductName.trim() !== editItem.product_name)
        productPatch.name = editProductName.trim()
      if (editProductBrand !== (editItem.product_brand || ''))
        productPatch.brand = editProductBrand
      if (editCategory !== origCat)
        productPatch.category = editCategory || null
      if (editDefaultStore !== origStore)
        productPatch.default_store = editDefaultStore || null
      if (Object.keys(productPatch).length > 0)
        saves.push(productsApi.update(editItem.product, productPatch))
      await Promise.all(saves)
      toast.success('Modifiche salvate')
      closeEdit()
      load()
    } catch { toast.error('Errore nel salvataggio') } finally { setEditSaving(false) }
  }

  async function handleAddProduct() {
    if (!addProduct) return
    // Per i nuovi prodotti la categoria è obbligatoria
    if (!addProduct.id && !addCategory) {
      return toast.error('Seleziona una categoria per il prodotto')
    }
    setSaving(true)
    try {
      let productId = addProduct.id
      if (!productId) {
        const { data: newProduct } = await productsApi.create({
          name: addProduct.name,
          category: addCategory,
        })
        productId = newProduct.id
      }
      await pantryApi.create(family.id, {
        product: productId,
        expiry_date: expiryDate || null,
        note: note || '',
      })
      toast.success(`${addProduct.name} aggiunto in dispensa`)
      setShowAdd(false)
      setAddProduct(null)
      setAddCategory('')
      setExpiryDate('')
      setNote('')
      load()
    } catch (err) {
      const msg = err.response?.data
      toast.error(
        typeof msg === 'object'
          ? Object.values(msg).flat().join(', ')
          : 'Errore nell\'aggiunta'
      )
    } finally {
      setSaving(false)
    }
  }

  async function handleBarcodeScan(barcode) {
    setShowScanner(false)
    try {
      const { data } = await productsApi.scan(barcode)
      if (data.found === false) {
        toast.error('Prodotto non trovato. Aggiungilo manualmente.')
      } else {
        setAddProduct(data)
        setShowAdd(true)
      }
    } catch {
      toast.error('Errore nella scansione')
    }
  }

  const present = items.filter((i) => i.status === 'present')
  const finished = items.filter((i) => i.status === 'finished')
  const displayed = tab === 'present' ? present : finished
  // Nel tab "presenti" mostra anche le categorie vuote (per permettere l'aggiunta rapida)
  const sections = tab === 'present'
    ? groupByCategory(displayed, categories)
    : groupByCategory(displayed)

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Package size={22} className="text-primary-600" /> Dispensa
        </h1>
        <div className="flex gap-1">
          <button onClick={() => setShowScanner(true)} className="btn-secondary text-xs px-3 py-1.5">
            📷 Scansiona
          </button>
          <button onClick={() => setShowAdd(true)} className="btn-primary text-xs px-3 py-1.5">
            <Plus size={14} /> Aggiungi
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex bg-gray-100 rounded-xl p-1 gap-1">
        <button
          className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${tab === 'present' ? 'bg-white text-primary-700 shadow-sm' : 'text-gray-500'}`}
          onClick={() => setTab('present')}
        >
          Presenti ({present.length})
        </button>
        <button
          className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${tab === 'finished' ? 'bg-white text-orange-600 shadow-sm' : 'text-gray-500'}`}
          onClick={() => setTab('finished')}
        >
          Terminati ({finished.length})
        </button>
      </div>

      {/* Items divisi per sezione */}
      {loading ? (
        <div className="flex justify-center py-12"><LoadingSpinner /></div>
      ) : tab === 'finished' && finished.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-gray-400">
          <Package size={48} className="mb-3 opacity-30" />
          <p className="text-sm">Nessun prodotto terminato.</p>
        </div>
      ) : (
        <div className="space-y-5">
          {sections.map((section) => {
            const isQuickAddOpen = quickAddCategoryName === section.name
            return (
              <div key={section.name}>
                {/* Header categoria */}
                <div className="flex items-center gap-2 mb-2 px-1">
                  <span className="text-base leading-none">{section.icon}</span>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex-1">
                    {section.name} ({section.items.length})
                  </p>
                  {tab === 'present' && (
                    <button
                      onClick={() => setQuickAddCategoryName(isQuickAddOpen ? null : section.name)}
                      disabled={quickAddCategorySaving}
                      className={`p-1 rounded-lg transition-colors disabled:opacity-40 ${
                        isQuickAddOpen
                          ? 'text-primary-600 bg-primary-100'
                          : 'text-gray-300 hover:text-primary-600 hover:bg-primary-50'
                      }`}
                      title="Aggiungi prodotto in questa categoria"
                    >
                      <Plus size={13} />
                    </button>
                  )}
                </div>

                {/* Pannello aggiunta rapida inline */}
                {isQuickAddOpen && (
                  <div className="mb-2 p-3 bg-primary-50 rounded-xl space-y-1.5">
                    <ProductSearch
                      onSelect={(p) => handleQuickAddToCategory(p, section.categoryId)}
                      onCreateNew={(name) => handleQuickAddToCategory({ name }, section.categoryId)}
                      placeholder="Cerca o crea prodotto..."
                      autoFocus
                      showScanButton
                    />
                    <button
                      onClick={() => setQuickAddCategoryName(null)}
                      className="text-xs text-gray-400 hover:text-gray-600"
                    >
                      Annulla
                    </button>
                  </div>
                )}

                {/* Items o placeholder vuoto */}
                {section.items.length > 0 ? (
                  <div className="space-y-2">
                    {section.items.map((item) => (
                      <PantryItemCard
                        key={item.id}
                        item={item}
                        onFinish={handleFinish}
                        onRestore={handleRestore}
                        onDelete={handleDelete}
                        onEdit={openEdit}
                        onAddToShopping={handleAddToShopping}
                      />
                    ))}
                  </div>
                ) : !isQuickAddOpen && (
                  <p className="text-xs text-gray-300 text-center py-2 px-1">
                    Nessun prodotto — usa + per aggiungere
                  </p>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Add Modal */}
      <Modal
        open={showAdd}
        onClose={() => { setShowAdd(false); setAddProduct(null); setAddCategory('') }}
        title="Aggiungi in dispensa"
      >
        <div className="space-y-4">
          {!addProduct ? (
            <ProductSearch
              onSelect={setAddProduct}
              onCreateNew={(name) => setAddProduct({ id: null, name })}
              autoFocus
            />
          ) : (
            <>
              <div className="flex items-center gap-3 p-3 bg-primary-50 rounded-xl">
                {addProduct.image_url && (
                  <img src={addProduct.image_url} alt="" className="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
                )}
                <div>
                  <p className="font-medium text-gray-900">{addProduct.name}</p>
                  {addProduct.brand && <p className="text-xs text-gray-500">{addProduct.brand}</p>}
                </div>
                <button onClick={() => setAddProduct(null)} className="ml-auto text-xs text-gray-400 underline">
                  Cambia
                </button>
              </div>

              {/* Categoria — obbligatoria solo per nuovi prodotti */}
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
                <label className="label">Data scadenza (opzionale)</label>
                <input
                  className="input"
                  type="date"
                  value={expiryDate}
                  onChange={(e) => setExpiryDate(e.target.value)}
                />
              </div>

              <div>
                <label className="label">Note (opzionale)</label>
                <input
                  className="input"
                  placeholder="Es. frigo ripiano 2"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                />
              </div>

              <button
                className="btn-primary w-full"
                onClick={handleAddProduct}
                disabled={saving}
              >
                {saving ? 'Aggiunta...' : 'Aggiungi in dispensa'}
              </button>
            </>
          )}
        </div>
      </Modal>

      {/* Barcode Scanner */}
      {showScanner && (
        <BarcodeScanner
          onResult={handleBarcodeScan}
          onClose={() => setShowScanner(false)}
        />
      )}

      {/* Edit modal */}
      <Modal open={!!editItem} onClose={closeEdit} title="Modifica prodotto">
        <div className="space-y-4">
          <div>
            <label className="label">Nome prodotto</label>
            <input
              className="input"
              placeholder="Nome prodotto"
              value={editProductName}
              onChange={(e) => setEditProductName(e.target.value)}
            />
          </div>

          <div>
            <label className="label">Brand (opzionale)</label>
            <input
              className="input"
              placeholder="Es. Barilla"
              value={editProductBrand}
              onChange={(e) => setEditProductBrand(e.target.value)}
            />
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

          {stores.length > 0 && (
            <div>
              <label className="label flex items-center gap-1">
                <Store size={13} className="text-gray-400" /> Negozio preferito (opzionale)
              </label>
              <select
                className="input"
                value={editDefaultStore}
                onChange={(e) => setEditDefaultStore(e.target.value)}
              >
                <option value="">Nessun negozio preferito</option>
                {stores.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="label flex items-center gap-1">
              <Calendar size={13} className="text-gray-400" /> Data scadenza (opzionale)
            </label>
            <input
              className="input"
              type="date"
              value={editExpiry}
              onChange={(e) => setEditExpiry(e.target.value)}
            />
          </div>
          <div>
            <label className="label">Note (opzionale)</label>
            <input
              className="input"
              placeholder="Es. frigo ripiano 2"
              value={editNote}
              onChange={(e) => setEditNote(e.target.value)}
            />
          </div>
          <button className="btn-primary w-full" onClick={handleEditSave} disabled={editSaving}>
            {editSaving ? 'Salvataggio...' : 'Salva modifiche'}
          </button>
        </div>
      </Modal>
    </div>
  )
}
