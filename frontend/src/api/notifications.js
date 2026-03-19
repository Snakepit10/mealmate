import client from './client'

export const notificationsApi = {
  list: (params) => client.get('/notifications/', { params }),

  markRead: (id) => client.patch(`/notifications/${id}/read/`),

  markAllRead: () => client.post('/notifications/read-all/'),

  delete: (id) => client.delete(`/notifications/${id}/`),

  getSettings: () => client.get('/notifications/settings/'),

  updateSettings: (data) => client.patch('/notifications/settings/', data),

  registerPush: (subscription) =>
    client.post('/notifications/push/register/', subscription),

  unregisterPush: (endpoint) =>
    client.delete('/notifications/push/unregister/', { data: { endpoint } }),
}
