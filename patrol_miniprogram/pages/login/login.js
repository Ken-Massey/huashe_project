const { login } = require('../../utils/request')

Page({
  data: { username: '', password: '', loading: false },
  onLoad() {
    const app = getApp()
    // 已登录直接进入
    if (app.globalData.token) {
      wx.reLaunch({ url: '/pages/index/index' })
    }
  },
  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [field]: e.detail.value })
  },
  async submit() {
    const { username, password, loading } = this.data
    if (loading) return
    if (!username.trim()) { wx.showToast({ title: '请输入账号', icon: 'none' }); return }
    if (!password) { wx.showToast({ title: '请输入密码', icon: 'none' }); return }
    this.setData({ loading: true })
    try {
      const token = await login(username.trim(), password)
      wx.setStorageSync('patrol_token', token)
      wx.setStorageSync('patrol_username', username.trim())
      getApp().globalData.token = token
      getApp().globalData.userName = username.trim()
      wx.reLaunch({ url: '/pages/index/index' })
    } catch (e) {
      wx.showModal({ title: '登录失败', content: e.message, showCancel: false })
    } finally {
      this.setData({ loading: false })
    }
  }
})
