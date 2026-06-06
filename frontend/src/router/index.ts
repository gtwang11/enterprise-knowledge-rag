import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    redirect: '/qa',
    meta: { requiresAuth: true },
  },
  {
    path: '/qa',
    name: 'Qa',
    component: () => import('@/views/qa/QaView.vue'),
    meta: { requiresAuth: true, roles: ['operator', 'admin', 'expert'] },
  },
  {
    path: '/tickets/my',
    name: 'MyTickets',
    component: () => import('@/views/tickets/MyTicketsView.vue'),
    meta: { requiresAuth: true, roles: ['operator'] },
  },
  {
    path: '/tickets/pending',
    name: 'PendingTickets',
    component: () => import('@/views/tickets/PendingTicketsView.vue'),
    meta: { requiresAuth: true, roles: ['expert'] },
  },
  {
    path: '/tickets/all',
    name: 'AllTickets',
    component: () => import('@/views/tickets/AdminTicketsView.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/tickets/:id',
    name: 'TicketDetail',
    component: () => import('@/views/tickets/TicketDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/faq',
    name: 'FaqList',
    component: () => import('@/views/faq/FaqListView.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'expert'] },
  },
  {
    path: '/faq/create',
    name: 'FaqCreate',
    component: () => import('@/views/faq/FaqFormView.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/faq/:id/edit',
    name: 'FaqEdit',
    component: () => import('@/views/faq/FaqFormView.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/faq/import',
    name: 'FaqImport',
    component: () => import('@/views/faq/FaqImportView.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/users',
    name: 'UserList',
    component: () => import('@/views/users/UserListView.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/users/create',
    name: 'UserCreate',
    component: () => import('@/views/users/UserFormView.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/users/:id/edit',
    name: 'UserEdit',
    component: () => import('@/views/users/UserFormView.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/dashboard/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/qa/history',
    name: 'QaHistory',
    component: () => import('@/views/qa/QaHistoryView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/profile/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/views/error/ForbiddenView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFoundView.vue'),
    meta: { requiresAuth: false },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
