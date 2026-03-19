import { useState, useEffect, useCallback } from 'react'
import { Plus, UtensilsCrossed, Search, Star, Clock, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { recipesApi } from '../../api/recipes'
import { useAuthStore } from '../../store/authStore'
import LoadingSpinner from '../../components/shared/LoadingSpinner'

const DIFFICULTY = { easy: 'Facile', medium: 'Media', hard: 'Difficile' }
const DIFFICULTY_COLOR = { easy: 'text-green-600', medium: 'text-amber-600', hard: 'text-red-600' }

function RecipeCard({ recipe }) {
  return (
    <Link to={`/recipes/${recipe.id}`} className="card overflow-hidden hover:shadow-md transition-shadow">
      {recipe.cover_image
        ? <img src={recipe.cover_image} alt={recipe.title} className="w-full h-36 object-cover" />
        : <div className="w-full h-36 bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
            <UtensilsCrossed size={36} className="text-primary-400" />
          </div>
      }
      <div className="p-3">
        <p className="font-semibold text-gray-900 text-sm truncate">{recipe.title}</p>
        <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
          {recipe.average_rating > 0 && (
            <span className="flex items-center gap-0.5 text-amber-500">
              <Star size={11} fill="currentColor" /> {recipe.average_rating.toFixed(1)}
            </span>
          )}
          {(recipe.prep_time || recipe.cook_time) && (
            <span className="flex items-center gap-0.5">
              <Clock size={11} /> {(recipe.prep_time || 0) + (recipe.cook_time || 0)} min
            </span>
          )}
          {recipe.servings && (
            <span className="flex items-center gap-0.5">
              <Users size={11} /> {recipe.servings}
            </span>
          )}
          <span className={`ml-auto ${DIFFICULTY_COLOR[recipe.difficulty] || ''}`}>
            {DIFFICULTY[recipe.difficulty] || recipe.difficulty}
          </span>
        </div>
      </div>
    </Link>
  )
}

export default function RecipesPage() {
  const { family } = useAuthStore()
  const [recipes, setRecipes] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all') // all | family | public

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (search) params.search = search
      if (filter === 'family' && family) params.family_id = family.id
      if (filter === 'public') params.is_public = true
      const { data } = await recipesApi.list(params)
      setRecipes(data.results || data)
    } catch {
      setRecipes([])
    } finally {
      setLoading(false)
    }
  }, [search, filter, family])

  useEffect(() => {
    const t = setTimeout(load, 300)
    return () => clearTimeout(t)
  }, [load])

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <UtensilsCrossed size={22} className="text-primary-600" /> Ricette
        </h1>
        <Link to="/recipes/new" className="btn-primary text-xs px-3 py-1.5">
          <Plus size={14} /> Nuova
        </Link>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          className="input pl-9"
          placeholder="Cerca ricette..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Filter tabs */}
      <div className="flex bg-gray-100 rounded-xl p-1 gap-1">
        {[['all', 'Tutte'], ['family', 'Mie'], ['public', 'Pubbliche']].map(([val, label]) => (
          <button
            key={val}
            className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-colors ${filter === val ? 'bg-white text-primary-700 shadow-sm' : 'text-gray-500'}`}
            onClick={() => setFilter(val)}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><LoadingSpinner /></div>
      ) : recipes.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-gray-400">
          <UtensilsCrossed size={48} className="mb-3 opacity-30" />
          <p className="text-sm">Nessuna ricetta trovata.</p>
          <Link to="/recipes/new" className="mt-3 text-primary-600 text-sm font-medium underline">
            Crea la prima ricetta
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {recipes.map((r) => <RecipeCard key={r.id} recipe={r} />)}
        </div>
      )}
    </div>
  )
}
