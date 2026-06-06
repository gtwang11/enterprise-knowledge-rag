import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const role = ref(localStorage.getItem('role') || '')
  const displayName = ref(localStorage.getItem('displayName') || '')
  const isFirstLogin = ref(localStorage.getItem('isFirstLogin') === 'true')

  function setAuth(t: string, r: string, name: string, first: boolean) {
    token.value = t
    role.value = r
    displayName.value = name
    isFirstLogin.value = first
    localStorage.setItem('token', t)
    localStorage.setItem('role', r)
    localStorage.setItem('displayName', name)
    localStorage.setItem('isFirstLogin', String(first))
  }

  function clearAuth() {
    token.value = ''
    role.value = ''
    displayName.value = ''
    isFirstLogin.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('displayName')
    localStorage.removeItem('isFirstLogin')
  }

  function updateToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function setFirstLoginDone() {
    isFirstLogin.value = false
    localStorage.setItem('isFirstLogin', 'false')
  }

  return { token, role, displayName, isFirstLogin, setAuth, clearAuth, updateToken, setFirstLoginDone }
})
