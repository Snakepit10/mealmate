import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm()

  async function onSubmit({ email, password }) {
    try {
      await login(email, password)
      navigate('/pantry', { replace: true })
    } catch (err) {
      const d = err.response?.data
      const msg = (typeof d?.detail === 'string' ? d.detail : null) ||
                  (typeof d?.error === 'string' ? d.error : null) ||
                  'Credenziali non valide'
      toast.error(msg)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-primary-600 flex items-center justify-center mb-3">
            <span className="text-white font-bold text-3xl">M</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">MealMate</h1>
          <p className="text-sm text-gray-500 mt-1">Accedi al tuo account</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="card p-6 space-y-4">
          <div>
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              placeholder="tu@esempio.it"
              {...register('email', { required: 'Email obbligatoria' })}
            />
            {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              placeholder="••••••••"
              {...register('password', { required: 'Password obbligatoria' })}
            />
            {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
          </div>

          <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Accesso...' : 'Accedi'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-600 mt-4">
          Non hai un account?{' '}
          <Link to="/register" className="text-primary-600 font-medium hover:underline">
            Registrati
          </Link>
        </p>
      </div>
    </div>
  )
}
