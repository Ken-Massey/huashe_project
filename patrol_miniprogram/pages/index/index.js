const { get } = require('../../utils/request')

const STATUS = { pending: '待执行', executing: '执行中', completed: '已完成', closed: '已关闭' }

Page({
  data: { tasks: [], loading: false },
  onShow() { this.load() },
  onPullDownRefresh() { this.load().finally(() => wx.stopPullDownRefresh()) },
  async load() {
    this.setData({ loading: true })
    try {
      const res = await get('/rail/patrol/tasks', { page: 1, size: 50 })
      const tasks = (res.items || []).map(t => Object.assign({}, t, { statusLabel: STATUS[t.status] || t.status }))
      this.setData({ tasks })
    } catch (e) {
      wx.showToast({ title: e.message, icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },
  openTask(e) {
    wx.navigateTo({ url: '/pages/task/task?id=' + e.currentTarget.dataset.id })
  },
  logout() {
    wx.removeStorageSync('patrol_token')
    wx.removeStorageSync('patrol_username')
    getApp().globalData.token = ''
    wx.reLaunch({ url: '/pages/login/login' })
  },
  formatTime(v) { return v ? String(v).replace('T', ' ').slice(0, 16) : '-' }
})
