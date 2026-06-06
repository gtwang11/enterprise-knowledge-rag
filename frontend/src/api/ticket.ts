import request from './request'

export const ticketApi = {
  list(params: Record<string, any> = {}) {
    return request.get('/tickets', { params })
  },
  create(data: Record<string, any>) {
    return request.post('/tickets', data)
  },
  get(id: number) {
    return request.get(`/tickets/${id}`)
  },
  claim(id: number) {
    return request.post(`/tickets/${id}/claim`)
  },
  submitSolution(id: number, solution: string) {
    return request.put(`/tickets/${id}/solution`, { solution })
  },
  reject(id: number, reason: string) {
    return request.post(`/tickets/${id}/reject`, { reason })
  },
  confirm(id: number) {
    return request.post(`/tickets/${id}/confirm`)
  },
  unconfirm(id: number) {
    return request.post(`/tickets/${id}/unconfirm`)
  },
  publishToFaq(id: number, data: Record<string, any>) {
    return request.post(`/tickets/${id}/publish-faq`, data)
  },
  delete(id: number) {
    return request.delete(`/tickets/${id}`)
  },
}
