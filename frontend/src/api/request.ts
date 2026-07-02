import axios from 'axios'
import { useUserStore } from '@/stores/user'
import router from '@/router'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 150000,
})

request.interceptors.request.use((config) => {
  const userStore = useUserStore()
  if (userStore.token) {
    config.headers.Authorization = `Bearer ${userStore.token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    const data = response.data
    const newToken = response.headers['x-new-token']
    if (newToken) {
      useUserStore().updateToken(newToken)
    }
    if (data.code && data.code !== 200 && data.code !== 201) {
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  (error) => {
    if (error.response?.status === 401) {
      useUserStore().clearAuth()
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else if (error.response?.status === 403) {
      router.push('/403')
    } else if (error.response?.status === 429) {
      ElMessage.error('请求过于频繁，请稍后再试')
    }
    return Promise.reject(error)
  },
)

export default request
