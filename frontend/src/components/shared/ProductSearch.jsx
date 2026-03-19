import { useState, useCallback, useEffect } from 'react'
import { Search, X, Plus, Camera } from 'lucide-react'
import { productsApi } from '../../api/products'
import LoadingSpinner from './LoadingSpinner'
import BarcodeScanner from './BarcodeScanner'
import toast from 'react-hot-toast'

let debounceTimer = null

export default function ProductSearch({
  onSelect,
  onCreateNew,
  placeholder = 'Cerca prodotto...',
  autoFocus = false,
  showScanButton = false,
}) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [showScanner, setShowScanner] = useState(false)
  const [scanLoading, setScanLoading] = useState(false)

  const search = useCallback(async (q) => {
    if (!q.trim() || q.length < 2) {
      setResults([])
      return
    }
    setLoading(true)
    try {
      const { data } = await productsApi.list({ search: q, page_size: 10 })
      setResults(data.results || data)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => search(query), 350)
    return () => clearTimeout(debounceTimer)
  }, [query, search])

  const trimmed = query.trim()
  const showResults = trimmed.length >= 2 && (loading || results.length > 0)
  const showCreate = !!onCreateNew && trimmed.length >= 1

  function handleClear() {
    setQuery('')
    setResults([])
  }

  function handleCreate() {
    onCreateNew(trimmed)
    handleClear()
  }

  async function handleBarcodeScan(barcode) {
    setShowScanner(false)
    setScanLoading(true)
    try {
      const { data } = await productsApi.scan(barcode)
      if (data.found === false) {
        toast.error('Prodotto non trovato. Cercalo per nome.')
      } else {
        onSelect(data)
        handleClear()
      }
    } catch (err) {
      if (err.response?.status === 404) {
        toast.error('Prodotto non trovato. Cercalo per nome.')
      } else {
        toast.error('Errore nella scansione')
      }
    } finally {
      setScanLoading(false)
    }
  }

  // Padding destro input: spazio per camera + clear se entrambi visibili
  const prClass = showScanButton
    ? query ? 'pr-16' : 'pr-9'
    : 'pr-8'

  return (
    <>
      <div className="space-y-1">
        {/* Search input */}
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            autoFocus={autoFocus}
            className={`input pl-9 ${prClass}`}
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />

          {/* Bottone clear (spostato a destra se c'è anche la camera) */}
          {query && (
            <button
              className={`absolute ${showScanButton ? 'right-9' : 'right-2'} top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600`}
              onClick={handleClear}
              type="button"
            >
              <X size={16} />
            </button>
          )}

          {/* Bottone scansione barcode */}
          {showScanButton && (
            <button
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary-600 disabled:opacity-40 transition-colors"
              onClick={() => setShowScanner(true)}
              disabled={scanLoading}
              type="button"
              title="Scansiona codice a barre"
            >
              {scanLoading
                ? <LoadingSpinner size="sm" />
                : <Camera size={16} />
              }
            </button>
          )}
        </div>

        {/* Search results */}
        {showResults && (
          <div className="w-full bg-white rounded-xl shadow border border-gray-100 overflow-hidden">
            {loading && (
              <div className="flex justify-center py-3">
                <LoadingSpinner size="sm" />
              </div>
            )}
            {results.map((p) => (
              <button
                key={p.id}
                type="button"
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 text-left"
                onClick={() => { onSelect(p); handleClear() }}
              >
                {p.image_url && (
                  <img src={p.image_url} alt="" className="w-8 h-8 rounded object-cover flex-shrink-0" />
                )}
                <div>
                  <p className="text-sm font-medium text-gray-900">{p.name}</p>
                  {p.brand && <p className="text-xs text-gray-500">{p.brand}</p>}
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Create new — always visible while typing */}
        {showCreate && (
          <button
            type="button"
            disabled={trimmed.length < 2}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border border-dashed text-left transition-colors
              ${trimmed.length >= 2
                ? 'border-primary-300 hover:bg-primary-50 cursor-pointer'
                : 'border-gray-200 opacity-50 cursor-default'
              }`}
            onClick={trimmed.length >= 2 ? handleCreate : undefined}
          >
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
              <Plus size={16} className="text-primary-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-primary-700">
                {trimmed.length >= 2 ? `Crea "${trimmed}"` : 'Crea nuovo prodotto'}
              </p>
              <p className="text-xs text-gray-400">
                {trimmed.length >= 2 ? 'Aggiungi come nuovo prodotto' : 'Digita il nome sopra per aggiungere'}
              </p>
            </div>
          </button>
        )}
      </div>

      {/* Scanner full-screen overlay */}
      {showScanner && (
        <BarcodeScanner
          onResult={handleBarcodeScan}
          onClose={() => setShowScanner(false)}
        />
      )}
    </>
  )
}
