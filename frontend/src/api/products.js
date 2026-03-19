import client from './client'

export const productsApi = {
  list: (params) => client.get('/products/', { params }),

  get: (id) => client.get(`/products/${id}/`),

  create: (data) => client.post('/products/', data),

  update: (id, data) => client.patch(`/products/${id}/`, data),

  byBarcode: (code) => client.get(`/products/barcode/${code}/`),

  scan: (barcode) => client.post('/products/scan/', { barcode }),

  categories: () => client.get('/products/categories/'),

  units: () => client.get('/products/units/'),
}
