import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register: registerUser } = useAuthStore()
  const { register, handleSubmit, watch, setError, formState: { errors, isSubmitting } } = useForm()
  const password = watch('password', '')
  const [serverErrors, setServerErrors] = useState({})

  async function onSubmit({ name, email, password, password2 }) {
    setServerErrors({})
    try {
      await registerUser(name, email, password, password2)
      navigate('/family/setup', { replace: true })
    } catch (err) {
      const data = err.response?.data
      if (data) {
        // Map server field errors back to form fields
        const fieldMap = { password_confirm: 'password2' }
        let hasFieldError = false
        const newServerErrors = {}

        Object.entries(data).forEach(([field, msgs]) => {
          const formField = fieldMap[field] || field
          const msgStr = Array.isArray(msgs) ? msgs.join(', ') : String(msgs)
          if (['name', 'email', 'password', 'password2'].includes(formField)) {
            setError(formField, { type: 'server', message: msgStr })
            hasFieldError = true
          } else if (field !== 'non_field_errors') {
            newServerErrors[field] = msgStr
          }
        })

        // non_field_errors or unmapped errors → toast
        const nonField = data.non_field_errors || data.detail
        const extra = Object.values(newServerErrors).join(', ')
        const toastMsg = [
          ...(nonField ? (Array.isArray(nonField) ? nonField : [String(nonField)]) : []),
          ...(extra ? [extra] : []),
        ].join(', ')

        if (toastMsg) toast.error(toastMsg)
        else if (!hasFieldError) toast.error('Registrazione fallita')
      } else {
        toast.error('Errore di rete. Riprova.')
      }
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-primary-600 flex items-center justify-center mb-3">
            <span className="text-white font-bold text-3xl">M</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Crea account</h1>
          <p className="text-sm text-gray-500 mt-1">Inizia a usare MealMate</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="card p-6 space-y-4">
          <div>
            <label className="label">Nome</label>
            <input
              className="input"
              placeholder="Mario Rossi"
              {...register('name', { required: 'Nome obbligatorio' })}
            />
            {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name.message}</p>}
          </div>

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
              placeholder="Almeno 8 caratteri, non comune"
              {...register('password', {
                required: 'Password obbligatoria',
                minLength: { value: 8, message: 'Almeno 8 caratteri' },
              })}
            />
            {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
          </div>

          <div>
            <label className="label">Conferma password</label>
            <input
              className="input"
              type="password"
              placeholder="Ripeti la password"
              {...register('password2', {
                required: 'Conferma la password',
                validate: (v) => v === password || 'Le password non corrispondono',
              })}
            />
            {errors.password2 && <p className="text-xs text-red-500 mt-1">{errors.password2.message}</p>}
          </div>

          <p className="text-xs text-gray-400">
            La password deve avere almeno 8 caratteri e non essere troppo semplice (es. evita "password123").
          </p>

          <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Registrazione...' : 'Crea account'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-600 mt-4">
          Hai già un account?{' '}
          <Link to="/login" className="text-primary-600 font-medium hover:underline">
            Accedi
          </Link>
        </p>
      </div>
    </div>
  )
}
