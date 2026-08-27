const { get } = require('../../utils/request')

const STATUS = { pending: '待执行', executing: '执行中', completed: '已完成', closed: '已关闭' }

function formatDispatchTime(iso) {
  if (!iso) return ''
  const d = new Date(String(iso).replace(' ', 'T'))
  if (isNaN(d.getTime())) return String(iso).replace('T', ' ').slice(0, 16)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const thatDay = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const diffDays = Math.round((today - thatDay) / 86400000)
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  if (diffDays === 0) return `今天 ${hh}:${mm}`
  if (diffDays === 1) return `昨天 ${hh}:${mm}`
  if (diffDays > 1 && d.getFullYear() === now.getFullYear()) return `${d.getMonth() + 1}月${d.getDate()}日 ${hh}:${mm}`
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

Page({
  data: { tasks: [], loading: false, firstLoad: true, username: '', stats: { total: 0, pending: 0, done: 0, hazard: 0 } },
  onShow() { this.load() },
  onPullDownRefresh() { this.load().finally(() => wx.stopPullDownRefresh()) },
  async load() {
    this.setData({ loading: true })
    try {
      const res = await get('/rail/patrol/tasks', { page: 1, size: 50 })
      const now = Date.now()
      const tasks = (res.items || []).map(t => {
        const created = t.created_at ? new Date(String(t.created_at).replace(' ', 'T')) : null
        const overdue = (t.status === 'pending' || t.status === 'executing') && created && !isNaN(created.getTime()) && (now - created.getTime() > 86400000)
        return Object.assign({}, t, {
          statusLabel: STATUS[t.status] || t.status,
          statusType: t.status === 'pending' ? 'pending' : (t.status === 'completed' || t.status === 'closed' ? 'done' : 'doing'),
          dispatchTime: formatDispatchTime(t.created_at || t.dispatch_time),
          overdue: !!overdue
        })
      })
      const stats = {
        total: tasks.length,
        pending: tasks.filter(t => t.status === 'pending' || t.status === 'executing').length,
        done: tasks.filter(t => t.status === 'completed' || t.status === 'closed').length,
        hazard: tasks.reduce((s, t) => s + (t.open_hazard_count || 0), 0)
      }
      this.setData({ tasks, stats, username: wx.getStorageSync('patrol_username') || '' })
    } catch (e) {
      wx.showToast({ title: e.message, icon: 'none' })
    } finally {
      this.setData({ loading: false, firstLoad: false })
    }
  },
  openTask(e) {
    wx.navigateTo({ url: '/pages/task/task?id=' + e.currentTarget.dataset.id })
  },
  logout() {
    wx.showModal({
      title: '提示',
      content: '确定退出登录吗？',
      success: (res) => {
        if (!res.confirm) return
        wx.removeStorageSync('patrol_token')
        wx.removeStorageSync('patrol_username')
        getApp().globalData.token = ''
        wx.reLaunch({ url: '/pages/login/login' })
      }
    })
  }
})
