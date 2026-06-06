import request from './request'

export const authApi = {
  login(username: string, password: string) {
    return request.post('/auth/login', { username, password })
  },
  logout() {
    return request.post('/auth/logout')
  },
  changePassword(oldPassword: string, newPassword: string, confirmPassword: string) {
    return request.put('/auth/change-password', { old_password: oldPassword, new_password: newPassword, confirm_password: confirmPassword })
  },
  refreshToken() {
    return request.post('/auth/refresh')
  },
}
