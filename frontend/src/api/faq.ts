import request from './request'

export const faqApi = {
  list(params: Record<string, any> = {}) {
    return request.get('/faq', { params })
  },
  get(id: number) {
    return request.get(`/faq/${id}`)
  },
  create(data: Record<string, any>) {
    return request.post('/faq', data)
  },
  update(id: number, data: Record<string, any>) {
    return request.put(`/faq/${id}`, data)
  },
  delete(id: number) {
    return request.delete(`/faq/${id}`)
  },
  batchDelete(ids: number[]) {
    return request.post('/faq/batch-delete', { ids })
  },
  importFile(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/faq/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}
