import request from './request'

export const qaApi = {
  ask(question: string) {
    return request.post('/qa/ask', { question })
  },
  history(params: Record<string, any> = {}) {
    return request.get('/qa/history', { params })
  },
}
