import { useState, useEffect, useCallback } from 'react'
import { ChevronLeft, ChevronRight, Plus, Trash2, CalendarDays } from 'lucide-react'
import { calendarApi } from '../../api/calendar'
import { useAuthStore } from '../../store/authStore'
import { useCalendarWS } from '../../ws/useCalendarWS'
import { getWeekDays, nextWeek, prevWeek, formatDay, formatDate, isToday } from '../../utils/dates'
import Modal from '../../components/shared/Modal'
import LoadingSpinner from '../../components/shared/LoadingSpinner'
import { recipesApi } from '../../api/recipes'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { it } from 'date-fns/locale'

const MEAL_TYPES = [
  { value: 'breakfast', label: 'Colazione', emoji: '☕' },
  { value: 'lunch', label: 'Pranzo', emoji: '🍽️' },
  { value: 'dinner', label: 'Cena', emoji: '🌙' },
  { value: 'snack', label: 'Spuntino', emoji: '🍎' },
]

export default function CalendarPage() {
  const { family } = useAuthStore()
  const [weekRef, setWeekRef] = useState(new Date())
  const [calendars, setCalendars] = useState([])
  const [activeCalendar, setActiveCalendar] = useState(null)
  const [slots, setSlots] = useState([])
  const [entriesBySlot, setEntriesBySlot] = useState({})
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [addTarget, setAddTarget] = useState(null) // { date, meal_type }
  const [addMode, setAddMode] = useState('recipe') // 'recipe' | 'note'
  const [recipeQuery, setRecipeQuery] = useState('')
  const [recipeResults, setRecipeResults] = useState([])
  const [selectedRecipe, setSelectedRecipe] = useState(null)
  const [noteText, setNoteText] = useState('')
  const [saving, setSaving] = useState(false)

  const days = getWeekDays(weekRef)

  const loadCalendars = useCallback(async () => {
    if (!family) return
    try {
      const { data } = await calendarApi.listCalendars(family.id)
      const cals = data.results || data
      setCalendars(cals)
      if (cals.length > 0 && !activeCalendar) {
        setActiveCalendar(cals[0])
      }
    } catch {}
  }, [family])

  const loadWeek = useCallback(async () => {
    if (!family || !activeCalendar) return
    setLoading(true)
    try {
      const from = formatDate(days[0])
      const to = formatDate(days[6])
      const { data } = await calendarApi.listSlots(family.id, activeCalendar.id, { date_from: from, date_to: to })
      const slotList = data.results || data
      setSlots(slotList)
      // Load entries for each slot
      const entriesMap = {}
      await Promise.all(
        slotList.map(async (slot) => {
          try {
            const res = await calendarApi.listEntries(family.id, activeCalendar.id, slot.id)
            entriesMap[slot.id] = res.data.results || res.data
          } catch {
            entriesMap[slot.id] = []
          }
        })
      )
      setEntriesBySlot(entriesMap)
    } catch {
      toast.error('Errore nel caricamento calendario')
    } finally {
      setLoading(false)
    }
  }, [family, activeCalendar, weekRef])

  useEffect(() => { loadCalendars() }, [loadCalendars])
  useEffect(() => { if (activeCalendar) loadWeek() }, [loadWeek])
  useCalendarWS(family?.id, { onUpdate: loadWeek })

  useEffect(() => {
    if (!recipeQuery.trim() || recipeQuery.length < 2) { setRecipeResults([]); return }
    const t = setTimeout(async () => {
      try {
        const { data } = await recipesApi.list({ search: recipeQuery, page_size: 8 })
        setRecipeResults(data.results || data)
      } catch {}
    }, 300)
    return () => clearTimeout(t)
  }, [recipeQuery])

  async function createCalendar() {
    try {
      const { data } = await calendarApi.createCalendar(family.id, {
        name: 'Calendario famiglia',
        color: '#059669',
      })
      setCalendars([data])
      setActiveCalendar(data)
      toast.success('Calendario creato!')
    } catch { toast.error('Errore nella creazione') }
  }

  function openAdd(date, meal_type) {
    setAddTarget({ date: formatDate(date), meal_type })
    setSelectedRecipe(null)
    setNoteText('')
    setRecipeQuery('')
    setRecipeResults([])
    setShowAdd(true)
  }

  async function handleAddEntry() {
    if (!addTarget) return
    setSaving(true)
    try {
      // Create/get slot
      const slotRes = await calendarApi.createSlot(family.id, activeCalendar.id, {
        date: addTarget.date,
        meal_type: addTarget.meal_type,
      })
      const slot = slotRes.data

      // Create entry
      const entryPayload = {}
      if (selectedRecipe) entryPayload.recipe_id = selectedRecipe.id
      else entryPayload.note = noteText

      const entryRes = await calendarApi.createEntry(family.id, activeCalendar.id, slot.id, entryPayload)
      const entry = entryRes.data

      if (entry.missing_ingredients?.length > 0) {
        toast(`Ingredienti mancanti aggiunti alla spesa: ${entry.missing_ingredients.join(', ')}`, {
          icon: '🛒',
          duration: 5000,
        })
      } else {
        toast.success('Pasto aggiunto!')
      }

      setShowAdd(false)
      loadWeek()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Errore nell\'aggiunta')
    } finally {
      setSaving(false)
    }
  }

  async function handleDeleteEntry(slotId, entryId) {
    try {
      await calendarApi.deleteEntry(family.id, activeCalendar.id, slotId, entryId)
      toast.success('Pasto rimosso')
      loadWeek()
    } catch { toast.error('Errore') }
  }

  function getSlot(date, meal_type) {
    const dateStr = formatDate(date)
    return slots.find((s) => s.date === dateStr && s.meal_type === meal_type)
  }

  function getEntries(slotId) {
    return entriesBySlot[slotId] || []
  }

  if (!activeCalendar) {
    return (
      <div className="p-4 flex flex-col items-center py-16">
        <CalendarDays size={48} className="text-gray-300 mb-4" />
        <p className="text-gray-500 text-sm mb-4">Nessun calendario creato</p>
        <button className="btn-primary" onClick={createCalendar}>
          <Plus size={16} /> Crea calendario
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {/* Week navigation */}
      <div className="sticky top-14 bg-white z-10 border-b border-gray-200 px-4 py-2">
        <div className="flex items-center justify-between mb-2">
          <button onClick={() => setWeekRef(prevWeek(weekRef))} className="p-1.5 rounded-lg hover:bg-gray-100">
            <ChevronLeft size={18} />
          </button>
          <span className="text-sm font-semibold text-gray-700">
            {format(days[0], 'MMM d', { locale: it })} – {format(days[6], 'MMM d yyyy', { locale: it })}
          </span>
          <button onClick={() => setWeekRef(nextWeek(weekRef))} className="p-1.5 rounded-lg hover:bg-gray-100">
            <ChevronRight size={18} />
          </button>
        </div>

        {/* Day headers */}
        <div className="grid grid-cols-7 gap-1">
          {days.map((day) => (
            <div key={day.toISOString()} className="text-center">
              <div className={`inline-flex flex-col items-center w-8 h-8 rounded-full justify-center mx-auto ${
                isToday(day) ? 'bg-primary-600 text-white' : 'text-gray-500'
              }`}>
                <span className="text-xs font-medium leading-none">
                  {format(day, 'EEE', { locale: it }).slice(0, 1).toUpperCase()}
                </span>
                <span className="text-xs leading-none">{format(day, 'd')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Meal rows */}
      {loading ? (
        <div className="flex justify-center py-12"><LoadingSpinner /></div>
      ) : (
        <div className="px-3 space-y-3 pb-4">
          {MEAL_TYPES.map(({ value, label, emoji }) => (
            <div key={value}>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1 flex items-center gap-1">
                {emoji} {label}
              </p>
              <div className="grid grid-cols-7 gap-1">
                {days.map((day) => {
                  const slot = getSlot(day, value)
                  const entries = slot ? getEntries(slot.id) : []
                  return (
                    <div
                      key={day.toISOString()}
                      className={`min-h-[52px] rounded-lg border-2 flex flex-col overflow-hidden cursor-pointer transition-colors ${
                        isToday(day) ? 'border-primary-200 bg-primary-50' : 'border-gray-100 bg-white hover:border-primary-200'
                      }`}
                      onClick={() => openAdd(day, value)}
                    >
                      {entries.map((entry) => (
                        <div key={entry.id} className="group relative px-1 py-0.5">
                          <p className="text-xs text-gray-700 leading-tight truncate">
                            {entry.recipe?.title || entry.note || '—'}
                          </p>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDeleteEntry(slot.id, entry.id) }}
                            className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 p-0.5 text-red-400 bg-white rounded"
                          >
                            <Trash2 size={10} />
                          </button>
                        </div>
                      ))}
                      {entries.length === 0 && (
                        <div className="flex-1 flex items-center justify-center text-gray-200">
                          <Plus size={14} />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add entry modal */}
      <Modal
        open={showAdd}
        onClose={() => setShowAdd(false)}
        title={addTarget ? `${MEAL_TYPES.find((m) => m.value === addTarget.meal_type)?.emoji} ${MEAL_TYPES.find((m) => m.value === addTarget.meal_type)?.label}` : 'Aggiungi pasto'}
      >
        <div className="space-y-4">
          {/* Mode toggle */}
          <div className="flex bg-gray-100 rounded-xl p-1 gap-1">
            <button
              className={`flex-1 py-1.5 text-xs font-medium rounded-lg ${addMode === 'recipe' ? 'bg-white text-primary-700 shadow-sm' : 'text-gray-500'}`}
              onClick={() => setAddMode('recipe')}
            >
              🍽️ Ricetta
            </button>
            <button
              className={`flex-1 py-1.5 text-xs font-medium rounded-lg ${addMode === 'note' ? 'bg-white text-primary-700 shadow-sm' : 'text-gray-500'}`}
              onClick={() => setAddMode('note')}
            >
              ✏️ Nota libera
            </button>
          </div>

          {addMode === 'recipe' && !selectedRecipe && (
            <div>
              <input
                className="input"
                placeholder="Cerca ricetta..."
                value={recipeQuery}
                onChange={(e) => setRecipeQuery(e.target.value)}
                autoFocus
              />
              {recipeResults.length > 0 && (
                <div className="mt-1 border border-gray-100 rounded-xl overflow-hidden">
                  {recipeResults.map((r) => (
                    <button
                      key={r.id}
                      className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 text-left"
                      onClick={() => { setSelectedRecipe(r); setRecipeQuery(r.title) }}
                    >
                      <span className="text-sm font-medium">{r.title}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {addMode === 'recipe' && selectedRecipe && (
            <div className="flex items-center gap-3 p-3 bg-primary-50 rounded-xl">
              <span className="flex-1 text-sm font-medium">{selectedRecipe.title}</span>
              <button className="text-xs text-gray-400 underline" onClick={() => setSelectedRecipe(null)}>
                Cambia
              </button>
            </div>
          )}

          {addMode === 'note' && (
            <div>
              <label className="label">Descrizione</label>
              <input
                className="input"
                placeholder="Es. Pizza da Gigi, Resto al lavoro..."
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                autoFocus
              />
            </div>
          )}

          <button
            className="btn-primary w-full"
            onClick={handleAddEntry}
            disabled={saving || (addMode === 'recipe' && !selectedRecipe) || (addMode === 'note' && !noteText.trim())}
          >
            {saving ? 'Aggiunta...' : 'Aggiungi pasto'}
          </button>
        </div>
      </Modal>
    </div>
  )
}
