import client from './client'

export const shoppingApi = {
  list: (familyId, params) =>
    client.get(`/families/${familyId}/shopping/`, { params }),

  create: (familyId, data) =>
    client.post(`/families/${familyId}/shopping/`, data),

  update: (familyId, iid, data) =>
    client.patch(`/families/${familyId}/shopping/${iid}/`, data),

  delete: (familyId, iid) =>
    client.delete(`/families/${familyId}/shopping/${iid}/`),

  check: (familyId, iid) =>
    client.post(`/families/${familyId}/shopping/${iid}/check/`),

  uncheck: (familyId, iid) =>
    client.post(`/families/${familyId}/shopping/${iid}/uncheck/`),

  unavailable: (familyId, iid) =>
    client.post(`/families/${familyId}/shopping/${iid}/unavailable/`),

  quickAdd: (familyId, data) =>
    client.post(`/families/${familyId}/shopping/quick-add/`, data),

  complete: (familyId) =>
    client.post(`/families/${familyId}/shopping/complete/`),

  listHistory: (familyId) =>
    client.get(`/families/${familyId}/shopping/history/`),

  getHistory: (familyId, hid) =>
    client.get(`/families/${familyId}/shopping/history/${hid}/`),

  reuseHistory: (familyId, hid) =>
    client.post(`/families/${familyId}/shopping/history/${hid}/reuse/`),
}
