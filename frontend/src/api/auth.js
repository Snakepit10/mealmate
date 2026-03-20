import client from './client'

export const authApi = {
  login: (email, password) =>
    client.post('/auth/login/', { email, password }),

  register: (name, email, password, password2) => {
    const payload = {
      name,
      email,
      password,
      password_confirm: password2,
    }
    return client.post('/auth/register/', payload)
  },

  logout: (refresh) =>
    client.post('/auth/logout/', { refresh }),

  me: () => client.get('/auth/me/'),

  updateMe: (data) => client.patch('/auth/me/', data),

  deleteMe: () => client.delete('/auth/me/'),

  passwordReset: (email) =>
    client.post('/auth/password/reset/', { email }),

  passwordConfirm: (token, uid, password, password2) =>
    client.post('/auth/password/confirm/', { token, uid, new_password: password, new_password_confirm: password2 }),

  lookupUser: (email) =>
    client.get('/auth/users/lookup/', { params: { email } }),
}
