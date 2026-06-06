import router from './index'
import { useUserStore } from '@/stores/user'

const publicRoutes = ['/login', '/403']

router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()

  // Not logged in → redirect to login
  if (!userStore.token && to.path !== '/login') {
    if (!publicRoutes.includes(to.path)) {
      next('/login')
      return
    }
  }

  // Already logged in, visiting login page → go to home
  if (userStore.token && to.path === '/login') {
    const role = userStore.role
    if (role === 'operator') next('/qa')
    else if (role === 'expert') next('/tickets/pending')
    else if (role === 'admin') next('/dashboard')
    else next('/qa')
    return
  }

  if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
    return
  }

  if (to.meta.roles) {
    const required = to.meta.roles as string[]
    if (!required.includes(userStore.role || '')) {
      next('/403')
      return
    }
  }

  next()
})
