import axios from 'axios'

const TOKEN_KEY = 'patrol_mobile_token'
const USER_KEY = 'patrol_mobile_username'

export const getMobileToken = () => localStorage.getItem(TOKEN_KEY) || ''
export const getMobileUser = () => localStorage.getItem(USER_KEY) || ''

export function clearMobileSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function saveMobileSession(token, username) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, username)
}

const api = axios.create({
  baseURL: process.env.VUE_APP_BASE_API,
  timeout: 30000
})

api.interceptors.request.use(config => {
  const token = getMobileToken()
  if (token && !config.skipMobileToken) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(response => {
  if (response.config.responseType === 'blob') return response.data
  const body = response.data
  if (body && body.code && body.code !== 200) {
    if (body.code === 401) {
      clearMobileSession()
      window.dispatchEvent(new Event('patrol-mobile-unauthorized'))
    }
    throw new Error(body.msg || '请求失败')
  }
  return body
}, error => {
  const status = error.response && error.response.status
  if (status === 401) {
    clearMobileSession()
    window.dispatchEvent(new Event('patrol-mobile-unauthorized'))
  }
  const body = error.response && error.response.data
  const message = (body && (body.msg || body.detail)) || error.message || '网络连接失败'
  return Promise.reject(new Error(typeof message === 'string' ? message : '请求失败'))
})

export const mobileLogin = (username, password) => api.post('/miniapp/login', {
  username, password, code: '', uuid: ''
}, { skipMobileToken: true })

export const mobileGet = (path, params) => api.get(path, { params })
export const mobilePost = (path, data) => api.post(path, data || {})
export const mobileDelete = path => api.delete(path)
export const mobileBlob = path => api.get(path, { responseType: 'blob', timeout: 120000 })

export function mobileUpload(path, file, fields = {}, onProgress) {
  const form = new FormData()
  form.append('file', file, file.name || 'capture.jpg')
  Object.keys(fields).forEach(key => {
    if (fields[key] !== null && fields[key] !== undefined) form.append(key, fields[key])
  })
  return api.post(path, form, {
    timeout: 120000,
    onUploadProgress: event => {
      if (onProgress && event.total) onProgress(Math.round(event.loaded / event.total * 100))
    }
  })
}
