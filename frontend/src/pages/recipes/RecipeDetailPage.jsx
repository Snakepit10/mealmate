import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Clock, Users, Star, Edit, Trash2, GitBranch, Globe, Lock, Share2 } from 'lucide-react'
import { recipesApi } from '../../api/recipes'
import { sharingApi } from '../../api/sharing'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../store/authStore'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import ConfirmDialog from '../../components/shared/ConfirmDialog'
import Modal from '../../components/shared/Modal'
import toast from 'react-hot-toast'

const DIFFICULTY = { easy: 'Facile', medium: 'Media', hard: 'Difficile' }

export default function RecipeDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [recipe, setRecipe] = useState(null)
  const [ingredients, setIngredients] = useState([])
  const [instructions, setInstructions] = useState([])
  const [ratings, setRatings] = useState([])
  const [loading, setLoading] = useState(true)
  const [showDelete, setShowDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [showShare, setShowShare] = useState(false)
  const [shareEmail, setShareEmail] = useState('')
  const [sharePermission, setSharePermission] = useState('read')
  const [shareTarget, setShareTarget] = useState(null) // { id, name }
  const [shareLooking, setShareLooking] = useState(false)
  const [sharing, setSharing] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const [rRes, iRes, instrRes, ratingRes] = await Promise.all([
          recipesApi.get(id),
          recipesApi.listIngredients(id),
          recipesApi.listInstructions(id),
          recipesApi.listRatings(id),
        ])
        setRecipe(rRes.data)
        setIngredients(iRes.data.results || iRes.data)
        setInstructions(instrRes.data.results || instrRes.data)
        setRatings(ratingRes.data.results || ratingRes.data)
      } catch {
        toast.error('Ricetta non trovata')
        navigate('/recipes')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id, navigate])

  async function handleDelete() {
    setDeleting(true)
    try {
      await recipesApi.delete(id)
      toast.success('Ricetta eliminata')
      navigate('/recipes')
    } catch { toast.error('Errore') } finally { setDeleting(false) }
  }

  async function handlePublish() {
    try {
      if (recipe.is_public) {
        await recipesApi.unpublish(id)
        setRecipe({ ...recipe, is_public: false })
        toast.success('Ricetta resa privata')
      } else {
        await recipesApi.publish(id)
        setRecipe({ ...recipe, is_public: true })
        toast.success('Ricetta pubblicata!')
      }
    } catch { toast.error('Errore') }
  }

  async function handleLookupUser() {
    if (!shareEmail.trim()) return
    setShareLooking(true)
    setShareTarget(null)
    try {
      const { data } = await authApi.lookupUser(shareEmail.trim())
      setShareTarget(data)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Utente non trovato')
    } finally {
      setShareLooking(false)
    }
  }

  async function handleShare() {
    if (!shareTarget) return
    setSharing(true)
    try {
      await sharingApi.create({
        resource_type: 'recipe',
        resource_id: id,
        shared_with_user: shareTarget.id,
        permission: sharePermission,
      })
      toast.success(`Ricetta condivisa con ${shareTarget.name}`)
      setShowShare(false)
      setShareEmail('')
      setShareTarget(null)
      setSharePermission('read')
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || err.response?.data?.detail || 'Errore nella condivisione')
    } finally {
      setSharing(false)
    }
  }

  async function handleFork() {
    try {
      const { data } = await recipesApi.fork(id)
      toast.success('Ricetta copiata nella tua raccolta!')
      navigate(`/recipes/${data.id}`)
    } catch { toast.error('Errore nella copia') }
  }

  if (loading) return <div className="flex justify-center py-16"><LoadingSpinner /></div>
  if (!recipe) return null

  const isOwner = recipe.created_by === user?.id
  const totalTime = (recipe.prep_time || 0) + (recipe.cook_time || 0)

  return (
    <div className="pb-6">
      {/* Cover */}
      <div className="relative">
        {(recipe.cover_image || recipe.cover_image_url)
          ? <img src={recipe.cover_image || recipe.cover_image_url} alt={recipe.title} className="w-full h-56 object-cover" />
          : <div className="w-full h-56 bg-gradient-to-br from-primary-100 to-primary-300 flex items-center justify-center">
              <span className="text-6xl">🍽️</span>
            </div>
        }
        <button onClick={() => navigate(-1)} className="absolute top-4 left-4 bg-white/90 backdrop-blur p-2 rounded-full shadow">
          <ArrowLeft size={18} />
        </button>
        {isOwner && (
          <div className="absolute top-4 right-4 flex gap-2">
            <button onClick={() => setShowShare(true)} className="bg-white/90 backdrop-blur p-2 rounded-full shadow">
              <Share2 size={18} className="text-primary-600" />
            </button>
            <Link to={`/recipes/${id}/edit`} className="bg-white/90 backdrop-blur p-2 rounded-full shadow">
              <Edit size={18} className="text-gray-700" />
            </Link>
            <button onClick={() => setShowDelete(true)} className="bg-white/90 backdrop-blur p-2 rounded-full shadow">
              <Trash2 size={18} className="text-red-500" />
            </button>
          </div>
        )}
      </div>

      <div className="px-4 pt-4 space-y-5">
        {/* Title & meta */}
        <div>
          <div className="flex items-start justify-between gap-2">
            <h1 className="text-xl font-bold text-gray-900">{recipe.title}</h1>
            <span className={`flex-shrink-0 badge ${recipe.is_public ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
              {recipe.is_public ? <Globe size={12} /> : <Lock size={12} />}
              <span className="ml-1">{recipe.is_public ? 'Pubblica' : 'Privata'}</span>
            </span>
          </div>

          <div className="flex flex-wrap gap-4 mt-2 text-sm text-gray-500">
            {totalTime > 0 && (
              <span className="flex items-center gap-1"><Clock size={14} /> {totalTime} min</span>
            )}
            {recipe.servings && (
              <span className="flex items-center gap-1"><Users size={14} /> {recipe.servings} persone</span>
            )}
            {recipe.average_rating > 0 && (
              <span className="flex items-center gap-1 text-amber-500">
                <Star size={14} fill="currentColor" /> {recipe.average_rating.toFixed(1)} ({recipe.ratings_count})
              </span>
            )}
            <span className="text-primary-600 font-medium">{DIFFICULTY[recipe.difficulty] || recipe.difficulty}</span>
          </div>

          {recipe.description && (
            <p className="mt-3 text-sm text-gray-600 leading-relaxed">{recipe.description}</p>
          )}
        </div>

        {/* Ingredients */}
        {ingredients.length > 0 && (
          <div>
            <h2 className="font-semibold text-gray-900 mb-3">Ingredienti</h2>
            <div className="card divide-y divide-gray-100">
              {ingredients.map((ing) => (
                <div key={ing.id} className="flex items-center justify-between px-4 py-2.5">
                  <span className={`text-sm ${ing.is_optional ? 'text-gray-400 italic' : 'text-gray-900'}`}>
                    {ing.product?.name}
                    {ing.is_optional && ' (opzionale)'}
                    {ing.note && <span className="text-gray-400"> — {ing.note}</span>}
                  </span>
                  {ing.quantity && (
                    <span className="text-sm text-gray-500 ml-2">
                      {ing.quantity} {ing.unit?.abbreviation || ''}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Instructions */}
        {instructions.length > 0 && (
          <div>
            <h2 className="font-semibold text-gray-900 mb-3">Procedimento</h2>
            <div className="space-y-3">
              {instructions.map((step) => (
                <div key={step.id} className="flex gap-3">
                  <div className="w-7 h-7 rounded-full bg-primary-600 text-white text-sm font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                    {step.step_number}
                  </div>
                  <p className="text-sm text-gray-700 leading-relaxed pt-0.5">{step.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 flex-wrap">
          {isOwner && (
            <button onClick={handlePublish} className="btn-secondary flex-1">
              {recipe.is_public ? <Lock size={14} /> : <Globe size={14} />}
              {recipe.is_public ? 'Rendi privata' : 'Pubblica'}
            </button>
          )}
          {!isOwner && (
            <button onClick={handleFork} className="btn-secondary flex-1">
              <GitBranch size={14} /> Copia ricetta
            </button>
          )}
        </div>

        {/* Ratings */}
        {ratings.length > 0 && (
          <div>
            <h2 className="font-semibold text-gray-900 mb-3">Valutazioni</h2>
            <div className="space-y-2">
              {ratings.map((r) => (
                <div key={r.id} className="card p-3">
                  <div className="flex items-center gap-2">
                    <div className="flex">
                      {[1,2,3,4,5].map((s) => (
                        <Star key={s} size={12} className={s <= r.score ? 'text-amber-400 fill-amber-400' : 'text-gray-200 fill-gray-200'} />
                      ))}
                    </div>
                    <span className="text-xs text-gray-400">{r.user_name || 'Utente'}</span>
                  </div>
                  {r.comment && <p className="text-sm text-gray-600 mt-1">{r.comment}</p>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <ConfirmDialog
        open={showDelete}
        onClose={() => setShowDelete(false)}
        onConfirm={handleDelete}
        title="Elimina ricetta"
        message={`Sei sicuro di voler eliminare "${recipe.title}"? Questa azione non può essere annullata.`}
        loading={deleting}
      />

      {/* Share Modal */}
      <Modal
        open={showShare}
        onClose={() => { setShowShare(false); setShareEmail(''); setShareTarget(null); setSharePermission('read') }}
        title="Condividi ricetta"
      >
        <div className="space-y-4">
          {!shareTarget ? (
            <>
              <p className="text-sm text-gray-500">Inserisci l'email dell'utente con cui vuoi condividere questa ricetta.</p>
              <div className="flex gap-2">
                <input
                  className="input flex-1"
                  type="email"
                  placeholder="email@esempio.com"
                  value={shareEmail}
                  onChange={(e) => setShareEmail(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleLookupUser()}
                />
                <button
                  className="btn-secondary px-4"
                  onClick={handleLookupUser}
                  disabled={shareLooking || !shareEmail.trim()}
                >
                  {shareLooking ? '...' : 'Cerca'}
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3 p-3 bg-primary-50 rounded-xl">
                <div className="w-9 h-9 rounded-full bg-primary-200 flex items-center justify-center font-bold text-primary-700">
                  {shareTarget.name[0]}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{shareTarget.name}</p>
                </div>
                <button onClick={() => setShareTarget(null)} className="text-xs text-gray-400 underline">
                  Cambia
                </button>
              </div>

              <div>
                <label className="label">Permessi</label>
                <select
                  className="input"
                  value={sharePermission}
                  onChange={(e) => setSharePermission(e.target.value)}
                >
                  <option value="read">Lettura (può solo vedere)</option>
                  <option value="write">Scrittura (può modificare)</option>
                </select>
              </div>

              <button
                className="btn-primary w-full"
                onClick={handleShare}
                disabled={sharing}
              >
                {sharing ? 'Condivisione...' : 'Condividi ricetta'}
              </button>
            </>
          )}
        </div>
      </Modal>
    </div>
  )
}
