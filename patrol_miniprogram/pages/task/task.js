const { get, post, downloadMedia, downloadShot, downloadDoc, uploadMedia } = require('../../utils/request')

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

function formatNow() {
  const d = new Date()
  const pad = n => (n < 10 ? '0' + n : '' + n)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function parseTs(s) {
  const d = new Date(String(s || '').replace(' ', 'T'))
  return isNaN(d.getTime()) ? 0 : d.getTime()
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
  data: {
    task: null, groups: [], photoPaths: {}, shotPaths: {}, loading: false,
    rectifyUpload: { visible: false, hazardId: '', recordId: '', files: [], note: '' }
  },
  onLoad(options) { this.taskId = options.id },
  onShow() { this.load() },
  async load() {
    this.setData({ loading: true })
    try {
      const task = await get('/rail/patrol/tasks/' + this.taskId)
      task.statusLabel = TASK_STATUS[task.status] || task.status
      this.hazards = task.hazards || []
      this.records = task.records || []

      // 隐患映射：挂整改记录 + 状态步骤
      const hazardMap = {}
        ; (task.hazards || []).forEach(h => {
          h.statusLabel = HAZARD_STATUS[h.status] || h.status
          h.steps = buildHazardSteps(h.status)
          h.rectifyRecords = []
          hazardMap[h.hazard_id] = h
        })

      // 分离日常巡查记录和整改反馈：整改反馈挂到对应隐患下
      const timeline = []
        ; (task.records || []).forEach(r => {
          if (r.type === 'rectify' && r.hazard_id && hazardMap[r.hazard_id]) {
            hazardMap[r.hazard_id].rectifyRecords.push(r)
          } else {
            const hazards = (task.hazards || []).filter(h => h.record_id === r.record_id)
            timeline.push({ kind: 'record', time: r.created_at || '', data: Object.assign({}, r, { hazards }) })
          }
        })
        // 独立隐患（未关联巡查记录）
        ; (task.hazards || []).forEach(h => {
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
        ; (task.records || []).forEach(r => {
          (r.media || []).forEach(m => { if (m.kind === 'photo') photoIds.push(m.media_id) })
        })
        ; (task.hazards || []).forEach(h => {
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
  uploadRectifyPhotos(e) {
    const id = e.currentTarget.dataset.id
    wx.chooseMedia({
      count: 9,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      sizeType: ['compressed'],
      success: res => {
        const files = (res.tempFiles || []).map(f => f.tempFilePath)
        if (!files.length) return
        const cur = this.currentRectifyRecord(id)
        this.setData({
          rectifyUpload: {
            visible: true,
            hazardId: id,
            recordId: cur ? cur.record_id : '',
            files,
            note: cur ? (cur.note || '') : ''
          }
        })
      }
    })
  },
  // 当前轮整改反馈记录：review_time 之后创建的整改记录（被驳回后新一轮则无 → 新建）
  currentRectifyRecord(hazardId) {
    const hazard = (this.hazards || []).find(h => h.hazard_id === hazardId)
    const reviewTime = hazard ? (hazard.review_time || '') : ''
    const list = (this.records || [])
      .filter(r => r.type === 'rectify' && r.hazard_id === hazardId)
      .filter(r => !reviewTime || parseTs(r.created_at) > parseTs(reviewTime))
      .sort((a, b) => parseTs(b.created_at) - parseTs(a.created_at))
    return list[0] || null
  },
  onRectifyNote(e) { this.setData({ 'rectifyUpload.note': e.detail.value }) },
  cancelRectifyUpload() { this.setData({ 'rectifyUpload.visible': false }) },
  noop() { },
  confirmRectifyUpload() {
    const up = this.data.rectifyUpload
    if (!up.files.length) return
    this.setData({ 'rectifyUpload.visible': false })
    wx.showLoading({ title: '上传中…' })
    this.doRectifyUpload(up)
  },
  async doRectifyUpload(up) {
    try {
      const takenAt = formatNow()
      let recordId = up.recordId
      if (recordId) {
        // 追加到同一条整改反馈记录：先继承并更新备注，新图片追加其后
        await post('/rail/patrol/records/' + recordId, { note: (up.note || '').trim() })
      } else {
        // 新建一条整改反馈记录（自动带定位；定位失败仍可上传，坐标留空）
        let longitude = '', latitude = '', accuracy = ''
        try {
          const loc = await this.getLocationOnce()
          longitude = loc.longitude
          latitude = loc.latitude
          accuracy = loc.accuracy
        } catch (err) { /* 忽略定位失败 */ }
        const record = await post('/rail/patrol/tasks/' + this.taskId + '/records', {
          type: 'rectify', hazard_id: up.hazardId,
          longitude, latitude, accuracy,
          note: (up.note || '').trim()
        })
        recordId = record.record_id
      }
      for (let i = 0; i < up.files.length; i++) {
        await uploadMedia(recordId, up.files[i], 'photo', takenAt)
      }
      wx.hideLoading()
      wx.showToast({ title: '上传成功', icon: 'success' })
      this.load()
    } catch (err) {
      wx.hideLoading()
      wx.showModal({ title: '上传失败', content: err.message, showCancel: false })
    }
  },
  getLocationOnce() {
    return new Promise((resolve, reject) => {
      wx.getLocation({ type: 'gcj02', success: resolve, fail: reject })
    })
  },
  submitReview(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '整改完成',
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
  },
  openDoc(e) {
    const id = e.currentTarget.dataset.id
    const kind = e.currentTarget.dataset.kind
    wx.showLoading({ title: '打开中…' })
    downloadDoc(id).then(path => {
      wx.hideLoading()
      if (kind === 'image') {
        wx.previewImage({ current: path, urls: [path] })
      } else {
        wx.openDocument({
          filePath: path, showMenu: true,
          fail: () => wx.showToast({ title: '无法预览该文件', icon: 'none' })
        })
      }
    }).catch(err => { wx.hideLoading(); wx.showToast({ title: err.message, icon: 'none' }) })
  },
  saveDoc(e) {
    const id = e.currentTarget.dataset.id
    const kind = e.currentTarget.dataset.kind
    wx.showLoading({ title: '下载中…' })
    downloadDoc(id).then(path => {
      wx.hideLoading()
      if (kind === 'image') {
        wx.saveImageToPhotosAlbum({
          filePath: path,
          success: () => wx.showToast({ title: '已保存到相册', icon: 'success' }),
          fail: () => wx.showToast({ title: '保存失败，请授权相册', icon: 'none' })
        })
      } else {
        wx.openDocument({
          filePath: path, showMenu: true,
          success: () => wx.showToast({ title: '已打开，可转发/保存', icon: 'none' }),
          fail: () => wx.showToast({ title: '无法打开该文件', icon: 'none' })
        })
      }
    }).catch(err => { wx.hideLoading(); wx.showToast({ title: err.message, icon: 'none' }) })
  }
})
