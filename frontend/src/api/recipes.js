import client from './client'

export const recipesApi = {
  list: (params) => client.get('/recipes/', { params }),

  get: (id) => client.get(`/recipes/${id}/`),

  create: (data) => client.post('/recipes/', data),

  update: (id, data) => client.patch(`/recipes/${id}/`, data),

  delete: (id) => client.delete(`/recipes/${id}/`),

  publish: (id) => client.post(`/recipes/${id}/publish/`),

  unpublish: (id) => client.post(`/recipes/${id}/unpublish/`),

  fork: (id) => client.post(`/recipes/${id}/fork/`),

  report: (id, reason) => client.post(`/recipes/${id}/report/`, { reason }),

  importUrl: (url) => client.post('/recipes/import/', { url }),

  categories: () => client.get('/recipes/categories/'),

  suggestions: (familyId) =>
    client.get('/recipes/suggestions/', { params: { family_id: familyId } }),

  // Ingredients
  listIngredients: (id) => client.get(`/recipes/${id}/ingredients/`),

  addIngredient: (id, data) => client.post(`/recipes/${id}/ingredients/`, data),

  updateIngredient: (id, iid, data) =>
    client.patch(`/recipes/${id}/ingredients/${iid}/`, data),

  deleteIngredient: (id, iid) =>
    client.delete(`/recipes/${id}/ingredients/${iid}/`),

  // Instructions
  listInstructions: (id) => client.get(`/recipes/${id}/instructions/`),

  addInstruction: (id, data) => client.post(`/recipes/${id}/instructions/`, data),

  updateInstruction: (id, sid, data) =>
    client.patch(`/recipes/${id}/instructions/${sid}/`, data),

  deleteInstruction: (id, sid) =>
    client.delete(`/recipes/${id}/instructions/${sid}/`),

  // Ratings
  listRatings: (id) => client.get(`/recipes/${id}/ratings/`),

  addRating: (id, data) => client.post(`/recipes/${id}/ratings/`, data),

  updateRating: (id, rid, data) =>
    client.patch(`/recipes/${id}/ratings/${rid}/`, data),

  deleteRating: (id, rid) =>
    client.delete(`/recipes/${id}/ratings/${rid}/`),
}
