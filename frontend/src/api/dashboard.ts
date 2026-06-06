import request from './request'
import { useUserStore } from '@/stores/user'

export const dashboardApi = {
  get() {
    const role = useUserStore().role
    return request.get(`/dashboard/${role}`)
  },
}
