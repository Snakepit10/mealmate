import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuthStore } from '../../store/authStore'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register: registerUser } = useAuthStore()
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm()
  const password = watch('password', '')

  async function onSubmit({ name, email, password, password2 }) {
    try {
      await registerUser(name, email, password, password2)
      navigate('/family/setup', { replace: true })
    } catch (err) {
      const data = err.response?.data
      if (data) {
        const msg = Object.values(data).flat().join(', ')
        toast.error(msg)
      } else {
        toast.error('Registrazione fallita')
      }
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
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
              placeholder="Almeno 8 caratteri"
              {...register('password', { required: 'Password obbligatoria', minLength: { value: 8, message: 'Almeno 8 caratteri' } })}
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
