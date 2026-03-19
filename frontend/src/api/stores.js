import client from './client'

export const storesApi = {
  categories: () =>
    client.get('/store-categories/'),

  list: (familyId) =>
    client.get(`/families/${familyId}/stores/`),

  create: (familyId, data) =>
    client.post(`/families/${familyId}/stores/`, data),

  get: (familyId, sid) =>
    client.get(`/families/${familyId}/stores/${sid}/`),

  update: (familyId, sid, data) =>
    client.patch(`/families/${familyId}/stores/${sid}/`, data),

  delete: (familyId, sid) =>
    client.delete(`/families/${familyId}/stores/${sid}/`),

  listAisles: (familyId, sid) =>
    client.get(`/families/${familyId}/stores/${sid}/aisles/`),

  createAisle: (familyId, sid, data) =>
    client.post(`/families/${familyId}/stores/${sid}/aisles/`, data),

  updateAisle: (familyId, sid, aid, data) =>
    client.patch(`/families/${familyId}/stores/${sid}/aisles/${aid}/`, data),

  deleteAisle: (familyId, sid, aid) =>
    client.delete(`/families/${familyId}/stores/${sid}/aisles/${aid}/`),

  duplicate: (familyId, sid) =>
    client.post(`/families/${familyId}/stores/${sid}/duplicate/`),

  reorderAisles: (familyId, sid, order) =>
    client.post(`/families/${familyId}/stores/${sid}/aisles/reorder/`, { order }),
}
