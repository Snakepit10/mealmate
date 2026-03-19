import client from './client'

export const pantryApi = {
  list: (familyId, params) =>
    client.get(`/families/${familyId}/pantry/`, { params }),

  get: (familyId, pid) =>
    client.get(`/families/${familyId}/pantry/${pid}/`),

  create: (familyId, data) =>
    client.post(`/families/${familyId}/pantry/`, data),

  update: (familyId, pid, data) =>
    client.patch(`/families/${familyId}/pantry/${pid}/`, data),

  delete: (familyId, pid) =>
    client.delete(`/families/${familyId}/pantry/${pid}/`),

  finish: (familyId, pid) =>
    client.post(`/families/${familyId}/pantry/${pid}/finish/`),

  restore: (familyId, pid) =>
    client.post(`/families/${familyId}/pantry/${pid}/restore/`),

  expiring: (familyId, days) =>
    client.get(`/families/${familyId}/pantry/expiring/`, { params: { days } }),

  history: (familyId, params) =>
    client.get(`/families/${familyId}/pantry/history/`, { params }),
}
