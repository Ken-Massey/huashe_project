const { get, post, del, downloadMedia, downloadShot } = require('../../utils/request')

const TASK_STATUS = { pending: '待执行', executing: '执行中', completed: '已完成', closed: '已关闭' }
const HAZARD_STATUS = { pending_confirm: '待确认', pending_rectify: '待整改', rectifying: '整改中', pending_review: '待复核', closed: '已闭环' }
const HAZARD_STEPS = ['pending_confirm', 'pending_rectify', 'rectifying', 'pending_review', 'closed']
const HAZARD_STEP_LABELS = ['待确认', '待整改', '整改中', '待复核', '已闭环']

function formatDateKey(iso) {
  if (!iso) return ''
  const d = new Date(String(iso).replace(' ', 'T'))
  if (isNaN(d.getTime())) return ''
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
}

function formatDateLabel(iso) {
  if (!iso) return ''
  const d = new Date(String(iso).replace(' ', 'T'))
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const thatDay = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const diffDays = Math.round((today - thatDay) / 86400000)
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (d.getFullYear() === now.getFullYear()) return `${d.getMonth() + 1}月${d.getDate()}日`
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`
}

function buildHazardSteps(status) {
  const idx = HAZARD_STEPS.indexOf(status)
  return HAZARD_STEPS.map((key, i) => ({
    key,
    label: HAZARD_STEP_LABELS[i],
    done: i < idx || status === 'closed',
    current: i === idx && status !== 'closed'
  }))
}

Page({
  data: { task: null, groups: [], photoPaths: {}, shotPaths: {}, loading: false },
  onLoad(options) { this.taskId = options.id },
  onShow() { this.load() },
  async load() {
    this.setData({ loading: true })
    try {
      const task = await get('/rail/patrol/tasks/' + this.taskId)
      task.statusLabel = TASK_STATUS[task.status] || task.status

      // 隐患映射：挂整改记录 + 状态步骤
      const hazardMap = {}
      ;(task.hazards || []).forEach(h => {
        h.statusLabel = HAZARD_STATUS[h.status] || h.status
        h.steps = buildHazardSteps(h.status)
        h.rectifyRecords = []
        hazardMap[h.hazard_id] = h
      })

      // 分离日常巡查记录和整改反馈：整改反馈挂到对应隐患下
      const timeline = []
      ;(task.records || []).forEach(r => {
        if (r.type === 'rectify' && r.hazard_id && hazardMap[r.hazard_id]) {
          hazardMap[r.hazard_id].rectifyRecords.push(r)
        } else {
          const hazards = (task.hazards || []).filter(h => h.record_id === r.record_id)
          timeline.push({ kind: 'record', time: r.created_at || '', data: Object.assign({}, r, { hazards }) })
        }
      })
      // 独立隐患（未关联巡查记录）
      ;(task.hazards || []).forEach(h => {
        if (!h.record_id) {
          timeline.push({ kind: 'hazard', time: h.created_at || '', data: Object.assign({}, h, { hazards: [] }) })
        }
      })
      timeline.sort((a, b) => (b.time || '').localeCompare(a.time || ''))

      // 整改记录按时间正序（早→晚），方便查看整改进展
      Object.values(hazardMap).forEach(h => {
        h.rectifyRecords.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))
      })

      // 按日期分组
      const groups = []
      timeline.forEach(item => {
        const dateKey = formatDateKey(item.time)
        let group = groups.find(g => g.dateKey === dateKey)
        if (!group) {
          group = { dateKey, dateLabel: formatDateLabel(item.time), isToday: formatDateLabel(item.time) === '今天', items: [] }
          groups.push(group)
        }
        group.items.push(item)
      })

      this.setData({ task, groups })

      // 并行下载照片和截图
      const photoIds = [], shotIds = []
      ;(task.records || []).forEach(r => {
        (r.media || []).forEach(m => { if (m.kind === 'photo') photoIds.push(m.media_id) })
      })
      ;(task.hazards || []).forEach(h => {
        (h.shots || []).forEach(s => shotIds.push(s.shot_id))
      })
      const [photoEntries, shotEntries] = await Promise.all([
        Promise.all(photoIds.map(id => downloadMedia(id).then(p => [id, p]).catch(() => [id, '']))),
        Promise.all(shotIds.map(id => downloadShot(id).then(p => [id, p]).catch(() => [id, ''])))
      ])
      const photoPaths = {}, shotPaths = {}
      photoEntries.forEach(([id, p]) => { if (p) photoPaths[id] = p })
      shotEntries.forEach(([id, p]) => { if (p) shotPaths[id] = p })
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
    wx.showLoading({ title: '加载中…' })
    try {
      const path = await downloadMedia(id)
      wx.hideLoading()
      wx.previewMedia({ sources: [{ url: path, type: 'video' }] })
    } catch (err) {
      wx.hideLoading()
      wx.showToast({ title: err.message, icon: 'none' })
    }
  }
})
