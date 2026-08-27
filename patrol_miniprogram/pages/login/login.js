const { login } = require('../../utils/request')

Page({
  data: {
    username: '',
    password: '',
    loading: false,
    focusField: '',
    showPassword: false,
    loginError: ''
  },
  onLoad() {
    const app = getApp()
    // 已登录直接进入
    if (app.globalData.token) {
      wx.reLaunch({ url: '/pages/index/index' })
    }
  },
  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [field]: e.detail.value, loginError: '' })
  },
  onFocus(e) {
    this.setData({ focusField: e.currentTarget.dataset.field, loginError: '' })
  },
  onBlur() {
    this.setData({ focusField: '' })
  },
  togglePassword() {
    this.setData({ showPassword: !this.data.showPassword })
  },
  async submit() {
    const { username, password, loading } = this.data
    if (loading) return
    if (!username.trim()) {
      this.setData({ loginError: '请输入账号' })
      return
    }
    if (!password) {
      this.setData({ loginError: '请输入密码' })
      return
    }
    this.setData({ loading: true, loginError: '' })
    try {
      const token = await login(username.trim(), password)
      wx.setStorageSync('patrol_token', token)
      wx.setStorageSync('patrol_username', username.trim())
      getApp().globalData.token = token
      getApp().globalData.userName = username.trim()
      wx.reLaunch({ url: '/pages/index/index' })
    } catch (e) {
      this.setData({ loginError: e.message || '登录失败，请检查账号密码' })
    } finally {
      this.setData({ loading: false })
    }
  }
})
