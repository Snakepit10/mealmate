import { create } from 'zustand'
import { authApi } from '../api/auth'
import { familiesApi } from '../api/families'

export const useAuthStore = create((set, get) => ({
  user: null,
  family: null,
  isAuthenticated: false,
  loading: true,

  init: async () => {
    const access = localStorage.getItem('access')
    if (!access) {
      set({ loading: false })
      return
    }
    try {
      const { data: user } = await authApi.me()
      set({ user, isAuthenticated: true })
      // Try to load family memberships
      await get().loadFamily()
    } catch {
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      set({ user: null, isAuthenticated: false })
    } finally {
      set({ loading: false })
    }
  },

  login: async (email, password) => {
    const { data } = await authApi.login(email, password)
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)
    set({ user: data.user, isAuthenticated: true })
    await get().loadFamily()
  },

  register: async (name, email, password, password2) => {
    const { data } = await authApi.register(name, email, password, password2)
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)
    set({ user: data.user, isAuthenticated: true, family: null })
  },

  logout: async () => {
    const refresh = localStorage.getItem('refresh')
    try { if (refresh) await authApi.logout(refresh) } catch {}
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    set({ user: null, family: null, isAuthenticated: false })
  },

  loadFamily: async () => {
    // 1. Prova con il family_id salvato nel localStorage (accesso diretto, più veloce)
    const savedFamilyId = localStorage.getItem('family_id')
    if (savedFamilyId) {
      try {
        const { data } = await familiesApi.get(savedFamilyId)
        set({ family: data })
        return
      } catch {
        localStorage.removeItem('family_id')
      }
    }
    // 2. Fallback API: lista tutte le famiglie dell'utente
    //    Utile al primo accesso da un nuovo dispositivo (localStorage vuoto)
    try {
      const { data } = await familiesApi.list()
      const first = Array.isArray(data) ? data[0] : null
      if (first) {
        localStorage.setItem('family_id', first.id)
        set({ family: first })
        return
      }
    } catch {}
    set({ family: null })
  },

  setFamily: (family) => {
    if (family) {
      localStorage.setItem('family_id', family.id)
    } else {
      localStorage.removeItem('family_id')
    }
    set({ family })
  },

  updateUser: (user) => set({ user }),
}))
