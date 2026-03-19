import client from './client'

export const sharingApi = {
  list: (params) => client.get('/shares/', { params }),

  create: (data) => client.post('/shares/', data),

  get: (id) => client.get(`/shares/${id}/`),

  update: (id, data) => client.patch(`/shares/${id}/`, data),

  delete: (id) => client.delete(`/shares/${id}/`),

  accept: (id) => client.post(`/shares/${id}/accept/`),

  reject: (id) => client.post(`/shares/${id}/reject/`),
}
