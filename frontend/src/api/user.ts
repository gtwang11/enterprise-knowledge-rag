import request from './request'

export const userApi = {
  list(params: Record<string, any> = {}) {
    return request.get('/users', { params })
  },
  get(id: number) {
    return request.get(`/users/${id}`)
  },
  create(data: Record<string, any>) {
    return request.post('/users', data)
  },
  update(id: number, data: Record<string, any>) {
    return request.put(`/users/${id}`, data)
  },
  toggleStatus(id: number) {
    return request.patch(`/users/${id}/status`)
  },
  resetPassword(id: number) {
    return request.post(`/users/${id}/reset-password`)
  },
  delete(id: number) {
    return request.delete(`/users/${id}`)
  },
}
