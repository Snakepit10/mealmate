import client from './client'

export const familiesApi = {
  list: () => client.get('/families/'),

  create: (name) => client.post('/families/', { name }),

  get: (id) => client.get(`/families/${id}/`),

  update: (id, data) => client.patch(`/families/${id}/`, data),

  delete: (id) => client.delete(`/families/${id}/`),

  join: (invite_code) => client.post('/families/join/', { invite_code }),

  leave: (id) => client.post(`/families/${id}/leave/`),

  transferAdmin: (id, memberId) =>
    client.post(`/families/${id}/transfer-admin/`, { member_id: memberId }),

  regenerateInvite: (id) => client.post(`/families/${id}/invite/`),

  // Members
  listMembers: (id) => client.get(`/families/${id}/members/`),

  addMember: (id, data) => client.post(`/families/${id}/members/`, data),

  updateMember: (id, mid, data) => client.patch(`/families/${id}/members/${mid}/`, data),

  removeMember: (id, mid) => client.delete(`/families/${id}/members/${mid}/`),
}
