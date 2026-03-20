import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Plus, Trash2, GripVertical, Link } from 'lucide-react'
import { useForm, useFieldArray } from 'react-hook-form'
import { recipesApi } from '../../api/recipes'
import { useAuthStore } from '../../store/authStore'
import ProductSearch from '../../components/shared/ProductSearch'
import ImageUpload from '../../components/shared/ImageUpload'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import toast from 'react-hot-toast'

export default function RecipeCreatePage() {
  const { id } = useParams()
  const isEdit = !!id
  const navigate = useNavigate()
  const { family } = useAuthStore()
  const [loading, setLoading] = useState(isEdit)
  const [ingredients, setIngredients] = useState([])
  const [steps, setSteps] = useState([{ text: '' }])
  const [saving, setSaving] = useState(false)
  const [coverImageFile, setCoverImageFile] = useState(null)
  const [coverImagePreview, setCoverImagePreview] = useState(null)
  const [importedImageUrl, setImportedImageUrl] = useState(null)
  const [importUrl, setImportUrl] = useState('')
  const [importOpen, setImportOpen] = useState(false)
  const [importing, setImporting] = useState(false)

  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    defaultValues: {
      title: '', description: '', servings: '', prep_time: '', cook_time: '',
      difficulty: 'easy', is_public: false, is_draft: false,
    }
  })

  useEffect(() => {
    if (!isEdit) return
    async function load() {
      try {
        const [rRes, iRes, instrRes] = await Promise.all([
          recipesApi.get(id),
          recipesApi.listIngredients(id),
          recipesApi.listInstructions(id),
        ])
        const r = rRes.data
        reset({
          title: r.title || '',
          description: r.description || '',
          servings: r.servings || '',
          prep_time: r.prep_time || '',
          cook_time: r.cook_time || '',
          difficulty: r.difficulty || 'easy',
          is_public: r.is_public || false,
          is_draft: r.is_draft || false,
        })
        if (r.cover_image) setCoverImagePreview(r.cover_image)
        else if (r.cover_image_url) {
          setCoverImagePreview(r.cover_image_url)
          setImportedImageUrl(r.cover_image_url)
        }
        setIngredients((iRes.data.results || iRes.data).map((i) => ({
          id: i.id,
          product: i.product,
          product_id: i.product?.id,
          quantity: i.quantity || '',
          is_optional: i.is_optional || false,
          note: i.note || '',
        })))
        setSteps((instrRes.data.results || instrRes.data).map((s) => ({ id: s.id, text: s.text })))
      } catch { toast.error('Errore nel caricamento') }
      finally { setLoading(false) }
    }
    load()
  }, [id, isEdit, reset])

  async function handleImport() {
    if (!importUrl.trim()) return
    setImporting(true)
    try {
      const { data } = await recipesApi.importUrl(importUrl.trim())
      reset({
        title: data.title || '',
        description: data.description || '',
        servings: data.servings ?? '',
        prep_time: data.prep_time ?? '',
        cook_time: data.cook_time ?? '',
        difficulty: 'easy',
        is_public: false,
        is_draft: false,
      })
      if (data.steps?.length) {
        setSteps(data.steps.map((text) => ({ text })))
      }
      if (data.ingredients?.length) {
        setIngredients(data.ingredients.map((ing) => ({
          product: { id: ing.product_id, name: ing.product_name },
          product_id: ing.product_id,
          quantity: ing.quantity || '',
          is_optional: false,
          note: '',
        })))
      }
      if (data.image_url) {
        setCoverImagePreview(data.image_url)
        setImportedImageUrl(data.image_url)
      }
      setImportOpen(false)
      setImportUrl('')
      toast.success('Ricetta importata! Controlla ingredienti e dati.')
    } catch (err) {
      const status = err.response?.status
      if (status === 422) {
        toast.error('Impossibile estrarre la ricetta da questo sito.')
      } else if (status === 503) {
        toast.error('Servizio di importazione non disponibile.')
      } else {
        toast.error("Errore durante l'importazione.")
      }
    } finally {
      setImporting(false)
    }
  }

  function addIngredient(product) {
    setIngredients((prev) => [...prev, { product, product_id: product.id, quantity: '', is_optional: false, note: '' }])
  }

  function removeIngredient(idx) {
    setIngredients((prev) => prev.filter((_, i) => i !== idx))
  }

  function updateIngredient(idx, field, value) {
    setIngredients((prev) => prev.map((ing, i) => i === idx ? { ...ing, [field]: value } : ing))
  }

  function addStep() {
    setSteps((prev) => [...prev, { text: '' }])
  }

  function removeStep(idx) {
    setSteps((prev) => prev.filter((_, i) => i !== idx))
  }

  function updateStep(idx, value) {
    setSteps((prev) => prev.map((s, i) => i === idx ? { ...s, text: value } : s))
  }

  async function onSubmit(formData) {
    setSaving(true)
    try {
      const payload = {
        ...formData,
        family_id: family?.id || null,
        servings: formData.servings ? parseInt(formData.servings) : null,
        prep_time: formData.prep_time ? parseInt(formData.prep_time) : null,
        cook_time: formData.cook_time ? parseInt(formData.cook_time) : null,
        // Se abbiamo un URL immagine da importazione (non un file caricato), salvalo nel campo URL
        cover_image_url: (!coverImageFile && importedImageUrl) ? importedImageUrl : undefined,
      }

      let recipeId = id
      if (isEdit) {
        await recipesApi.update(id, payload)
      } else {
        const { data } = await recipesApi.create(payload)
        recipeId = data.id
      }

      // Upload cover image if selected (file locale ha precedenza sull'URL importato)
      if (coverImageFile) {
        const fd = new FormData()
        fd.append('cover_image', coverImageFile)
        await recipesApi.update(recipeId, fd)
      } else if (isEdit && coverImagePreview === null) {
        // User removed the image
        await recipesApi.update(recipeId, { cover_image: null, cover_image_url: '' })
      }

      // Save ingredients (delete all and recreate for simplicity)
      if (!isEdit) {
        for (const ing of ingredients) {
          if (ing.product_id) {
            await recipesApi.addIngredient(recipeId, {
              product: ing.product_id,   // serializer si aspetta "product", non "product_id"
              quantity: ing.quantity || '',  // CharField: testo libero "350 g", "q.b.", ecc.
              is_optional: ing.is_optional,
              note: ing.note || '',
              order: ingredients.indexOf(ing),
            })
          }
        }
        for (let i = 0; i < steps.length; i++) {
          if (steps[i].text.trim()) {
            await recipesApi.addInstruction(recipeId, {
              step_number: i + 1,
              text: steps[i].text,
            })
          }
        }
      }

      toast.success(isEdit ? 'Ricetta aggiornata!' : 'Ricetta creata!')
      navigate(`/recipes/${recipeId}`)
    } catch (err) {
      const data = err.response?.data
      const msg = data ? Object.values(data).flat().join(', ') : 'Errore nel salvataggio'
      toast.error(msg)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="flex justify-center py-16"><LoadingSpinner /></div>

  return (
    <div className="pb-8">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 z-10 px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="p-1.5 rounded-lg hover:bg-gray-100">
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-lg font-semibold flex-1">{isEdit ? 'Modifica ricetta' : 'Nuova ricetta'}</h1>
        <button
          onClick={handleSubmit(onSubmit)}
          className="btn-primary text-sm px-4 py-1.5"
          disabled={saving}
        >
          {saving ? 'Salvataggio...' : 'Salva'}
        </button>
      </div>

      {/* Import da URL — solo in creazione */}
      {!isEdit && (
        <div className="px-4 pt-3">
          {!importOpen ? (
            <button
              type="button"
              onClick={() => setImportOpen(true)}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 border border-dashed border-primary-400 rounded-xl text-primary-600 text-sm font-medium hover:bg-primary-50 transition-colors"
            >
              <Link size={15} />
              Importa da link
            </button>
          ) : (
            <div className="card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-gray-800 flex items-center gap-1.5">
                  <Link size={14} /> Importa ricetta da URL
                </p>
                <button
                  type="button"
                  onClick={() => { setImportOpen(false); setImportUrl('') }}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  Annulla
                </button>
              </div>
              <input
                className="input text-sm"
                type="url"
                placeholder="https://ricette.giallozafferano.it/..."
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleImport()}
                autoFocus
              />
              <p className="text-xs text-gray-400">
                Funziona con GialloZafferano, BBC Good Food e altri siti che usano lo standard schema.org/Recipe.
              </p>
              <button
                type="button"
                onClick={handleImport}
                disabled={importing || !importUrl.trim()}
                className="btn-primary text-sm w-full"
              >
                {importing ? 'Importazione in corso...' : 'Importa'}
              </button>
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="px-4 pt-4 space-y-5">
        {/* Basic info */}
        <div className="card p-4 space-y-3">
          <h2 className="font-semibold text-gray-800">Informazioni base</h2>

          <ImageUpload
            preview={coverImageFile ? URL.createObjectURL(coverImageFile) : coverImagePreview}
            onChange={(file) => {
              setCoverImageFile(file)
              if (!file) {
                setCoverImagePreview(null)
                setImportedImageUrl(null)
              }
            }}
            aspectRatio="wide"
          />

          <div>
            <label className="label">Titolo *</label>
            <input className="input" placeholder="Es. Pasta al pomodoro" {...register('title', { required: 'Titolo obbligatorio' })} />
            {errors.title && <p className="text-xs text-red-500 mt-1">{errors.title.message}</p>}
          </div>
          <div>
            <label className="label">Descrizione</label>
            <textarea className="input resize-none" rows={3} placeholder="Descrizione breve..." {...register('description')} />
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="label">Porzioni</label>
              <input className="input" type="number" min="1" placeholder="4" {...register('servings')} />
            </div>
            <div>
              <label className="label">Prep (min)</label>
              <input className="input" type="number" min="0" placeholder="15" {...register('prep_time')} />
            </div>
            <div>
              <label className="label">Cottura (min)</label>
              <input className="input" type="number" min="0" placeholder="30" {...register('cook_time')} />
            </div>
          </div>
          <div>
            <label className="label">Difficoltà</label>
            <select className="input" {...register('difficulty')}>
              <option value="easy">Facile</option>
              <option value="medium">Media</option>
              <option value="hard">Difficile</option>
            </select>
          </div>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" className="rounded text-primary-600" {...register('is_public')} />
              Pubblica
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" className="rounded text-primary-600" {...register('is_draft')} />
              Bozza
            </label>
          </div>
        </div>

        {/* Ingredients */}
        <div className="card p-4 space-y-3">
          <h2 className="font-semibold text-gray-800">Ingredienti</h2>
          {ingredients.map((ing, idx) => (
            <div key={idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {ing.product?.name ?? (
                    <span className="text-amber-600 italic text-xs">{ing.note || 'Da collegare'}</span>
                  )}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <input
                    className="input text-xs py-1 w-20"
                    placeholder="Quantità"
                    value={ing.quantity}
                    onChange={(e) => updateIngredient(idx, 'quantity', e.target.value)}
                  />
                  <label className="flex items-center gap-1 text-xs cursor-pointer whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={ing.is_optional}
                      onChange={(e) => updateIngredient(idx, 'is_optional', e.target.checked)}
                    />
                    Opzionale
                  </label>
                </div>
              </div>
              <button type="button" onClick={() => removeIngredient(idx)} className="p-1.5 text-gray-400 hover:text-red-500">
                <Trash2 size={15} />
              </button>
            </div>
          ))}
          <ProductSearch onSelect={addIngredient} placeholder="Aggiungi ingrediente..." />
        </div>

        {/* Steps */}
        <div className="card p-4 space-y-3">
          <h2 className="font-semibold text-gray-800">Procedimento</h2>
          {steps.map((step, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <div className="w-6 h-6 rounded-full bg-primary-600 text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-2">
                {idx + 1}
              </div>
              <textarea
                className="input resize-none flex-1 text-sm"
                rows={2}
                placeholder={`Passo ${idx + 1}...`}
                value={step.text}
                onChange={(e) => updateStep(idx, e.target.value)}
              />
              {steps.length > 1 && (
                <button type="button" onClick={() => removeStep(idx)} className="p-1.5 text-gray-400 hover:text-red-500 mt-1">
                  <Trash2 size={15} />
                </button>
              )}
            </div>
          ))}
          <button type="button" onClick={addStep} className="btn-secondary text-sm w-full">
            <Plus size={14} /> Aggiungi passo
          </button>
        </div>
      </form>
    </div>
  )
}
