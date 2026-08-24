const { get, post, del, downloadMedia, downloadShot } = require('../../utils/request')

const TASK_STATUS = { pending: '待执行', executing: '执行中', completed: '已完成', closed: '已关闭' }
const HAZARD_STATUS = { pending_confirm: '待确认', pending_rectify: '待整改', rectifying: '整改中', pending_review: '待复核', closed: '已闭环' }

Page({
  data: { task: null, timeline: [], photoPaths: {}, shotPaths: {}, loading: false },
  onLoad(options) { this.taskId = options.id },
  onShow() { this.load() },
  async load() {
    this.setData({ loading: true })
    try {
      const task = await get('/rail/patrol/tasks/' + this.taskId)
      task.statusLabel = TASK_STATUS[task.status] || task.status
      ;(task.hazards || []).forEach(h => { h.statusLabel = HAZARD_STATUS[h.status] || h.status })

      // 记录下挂隐患 + 独立隐患，最新在上
      const timeline = []
      const attached = {}
      ;(task.hazards || []).forEach(h => { attached[h.hazard_id] = false })
      ;(task.records || []).forEach(r => {
        const hazards = (task.hazards || []).filter(h => h.record_id === r.record_id)
        hazards.forEach(h => { attached[h.hazard_id] = true })
        timeline.push({ kind: 'record', time: r.created_at || '', data: Object.assign({}, r, { hazards }) })
      })
      ;(task.hazards || []).forEach(h => {
        if (!attached[h.hazard_id]) timeline.push({ kind: 'hazard', time: h.created_at || '', data: Object.assign({}, h, { hazards: [] }) })
      })
      timeline.sort((a, b) => (b.time || '').localeCompare(a.time || ''))

      this.setData({ task, timeline })

      const photoPaths = {}, shotPaths = {}
      for (const r of (task.records || [])) {
        for (const m of (r.media || [])) {
          if (m.kind === 'photo') { try { photoPaths[m.media_id] = await downloadMedia(m.media_id) } catch (e) {} }
        }
      }
      for (const h of (task.hazards || [])) {
        for (const s of (h.shots || [])) { try { shotPaths[s.shot_id] = await downloadShot(s.shot_id) } catch (e) {} }
      }
      this.setData({ photoPaths, shotPaths })
    } catch (e) {
      wx.showToast({ title: e.message, icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },
  goUpload() { wx.navigateTo({ url: '/pages/upload/upload?taskId=' + this.taskId }) },
  goAddHazard(e) {
    const recordId = e.currentTarget.dataset.record
    wx.navigateTo({ url: '/pages/hazard/hazard?taskId=' + this.taskId + '&recordId=' + recordId })
  },
  editHazard(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/hazard/hazard?taskId=' + this.taskId + '&hazardId=' + id })
  },
  deleteHazard(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '删除隐患',
      content: '确认删除该隐患？',
      success: async r => {
        if (!r.confirm) return
        try { await del('/rail/patrol/hazards/' + id); wx.showToast({ title: '已删除', icon: 'success' }); this.load() }
        catch (err) { wx.showModal({ title: '删除失败', content: err.message, showCancel: false }) }
      }
    })
  },
  submitReview(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '提交复核',
      content: '确认整改已完成，提交平台复核？',
      success: async r => {
        if (!r.confirm) return
        try { await post('/rail/patrol/hazards/' + id + '/submit'); wx.showToast({ title: '已提交复核', icon: 'success' }); this.load() }
        catch (err) { wx.showModal({ title: '提交失败', content: err.message, showCancel: false }) }
      }
    })
  },
  preview(e) {
    const id = e.currentTarget.dataset.id
    wx.previewImage({ current: this.data.photoPaths[id], urls: Object.values(this.data.photoPaths) })
  },
  previewShot(e) {
    const id = e.currentTarget.dataset.id
    wx.previewImage({ current: this.data.shotPaths[id], urls: Object.values(this.data.shotPaths) })
  },
  async playVideo(e) {
    const id = e.currentTarget.dataset.id
    try {
      const path = await downloadMedia(id)
      wx.previewMedia({ sources: [{ url: path, type: 'video' }] })
    } catch (err) { wx.showToast({ title: err.message, icon: 'none' }) }
  },
  formatTime(v) { return v ? String(v).replace('T', ' ').slice(0, 16) : '-' }
})
