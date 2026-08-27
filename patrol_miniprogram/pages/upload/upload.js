const { get, post, uploadMedia, uploadShot } = require('../../utils/request')

function formatNow() {
  const d = new Date()
  const pad = n => (n < 10 ? '0' + n : '' + n)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

Page({
  data: {
    typeIndex: 0,
    types: ['日常巡查', '整改反馈'],
    hazards: [], hazardLabels: [], hazardIndex: -1,
    media: [],
    location: null,
    locStatus: '',      // 定位状态文字
    locAccuracy: 0,     // 定位精度（米）
    note: '',
    submitReview: true,
    // 日常巡查的隐患声明
    hasHazard: false,
    hazardTypes: [], hazardTypeLabels: [], hazardTypeIndex: -1,
    risks: [], riskLabels: [], riskIndex: -1,
    hazardDesc: '', shots: [],
    submitting: false,
    // 上传进度
    uploadProgress: 0,
    uploadLabel: ''
  },
  onLoad(options) {
    this.taskId = options.taskId
    this.loadHazards()
    this.loadDicts()
  },
  async loadHazards() {
    try {
      const task = await get('/rail/patrol/tasks/' + this.taskId)
      const hazards = (task.hazards || []).filter(h => h.status === 'pending_rectify' || h.status === 'rectifying')
      this.setData({ hazards, hazardLabels: hazards.map(h => h.description.slice(0, 20)) })
    } catch (e) { /* 忽略 */ }
  },
  async loadDicts() {
    try {
      const types = await get('/rail/patrol/dicts', { dictType: 'hazard_type' })
      const risks = await get('/rail/patrol/dicts', { dictType: 'hazard_risk' })
      this.setData({
        hazardTypes: types || [], hazardTypeLabels: (types || []).map(i => i.label),
        risks: risks || [], riskLabels: (risks || []).map(i => i.label)
      })
    } catch (e) { /* 忽略 */ }
  },
  onTypeChange(e) { this.setData({ typeIndex: Number(e.detail.value) }) },
  onHazardChange(e) { this.setData({ hazardIndex: Number(e.detail.value) }) },
  onHazardTypeChange(e) { this.setData({ hazardTypeIndex: Number(e.detail.value) }) },
  onRiskChange(e) { this.setData({ riskIndex: Number(e.detail.value) }) },
  onHasHazard(e) { this.setData({ hasHazard: e.detail.value }) },
  onNote(e) { this.setData({ note: e.detail.value }) },
  onInput(e) { this.setData({ [e.currentTarget.dataset.field]: e.detail.value }) },
  onSubmitReview(e) { this.setData({ submitReview: e.detail.value }) },
  getLocation() {
    this.setData({ locStatus: 'locating' })
    wx.getLocation({
      type: 'gcj02',
      success: res => {
        this.setData({
          location: { longitude: res.longitude, latitude: res.latitude, accuracy: res.accuracy },
          locStatus: 'success',
          locAccuracy: Math.round(res.accuracy)
        })
        wx.showToast({ title: '定位成功', icon: 'success' })
      },
      fail: () => {
        this.setData({ locStatus: 'fail' })
        wx.showModal({
          title: '定位失败',
          content: '请检查定位权限是否开启，或在备注中填写位置描述',
          confirmText: '重试',
          success: r => { if (r.confirm) this.getLocation() }
        })
      }
    })
  },
  chooseMedia() {
    wx.chooseMedia({
      count: 9 - this.data.media.length,
      mediaType: ['image', 'video'],
      sourceType: ['camera', 'album'],
      sizeType: ['compressed'],
      maxDuration: 60,
      success: res => {
        const media = this.data.media.concat(res.tempFiles.map(f => ({
          path: f.tempFilePath,
          kind: f.fileType === 'video' ? 'video' : 'photo',
          size: f.size || 0,
          duration: f.duration || 0
        })))
        this.setData({ media })
      }
    })
  },
  removeMedia(e) {
    const i = e.currentTarget.dataset.index
    const media = this.data.media.slice(); media.splice(i, 1); this.setData({ media })
  },
  chooseShots() {
    const remain = 9 - this.data.shots.length
    if (remain <= 0) return
    wx.chooseMedia({
      count: remain, mediaType: ['image'], sourceType: ['camera', 'album'], sizeType: ['compressed'],
      success: res => { this.setData({ shots: this.data.shots.concat(res.tempFiles.map(f => f.tempFilePath)) }) }
    })
  },
  removeShot(e) {
    const i = e.currentTarget.dataset.index
    const shots = this.data.shots.slice(); shots.splice(i, 1); this.setData({ shots })
  },
  async submit() {
    const { typeIndex, hazardIndex, hazards, media, location, note, submitReview, hasHazard, hazardDesc, shots, submitting } = this.data
    if (submitting) return
    const type = typeIndex === 0 ? 'patrol' : 'rectify'
    if (!media.length) { wx.showToast({ title: '请先选择照片/视频', icon: 'none' }); return }
    if (!location) { wx.showToast({ title: '请先获取定位', icon: 'none' }); return }
    let hazardId = ''
    if (type === 'rectify') {
      if (hazardIndex < 0) { wx.showToast({ title: '请选择关联隐患', icon: 'none' }); return }
      hazardId = hazards[hazardIndex].hazard_id
    }
    if (type === 'patrol' && hasHazard && !hazardDesc.trim()) { wx.showToast({ title: '请填写隐患描述', icon: 'none' }); return }

    this.setData({ submitting: true, uploadProgress: 0, uploadLabel: '正在提交…' })
    try {
      const record = await post('/rail/patrol/tasks/' + this.taskId + '/records', {
        type, hazard_id: hazardId, longitude: location.longitude, latitude: location.latitude, accuracy: location.accuracy, note
      })

      // 串行上传媒体，带进度
      const totalFiles = media.length + (type === 'patrol' && hasHazard ? shots.length : 0)
      let doneFiles = 0
      const takenAt = formatNow()

      for (let i = 0; i < media.length; i++) {
        const m = media[i]
        this.setData({ uploadLabel: `正在上传 ${i + 1}/${media.length}` })
        await uploadMedia(record.record_id, m.path, m.kind, takenAt, (p) => {
          // 单个文件内的进度，折算到总进度
          const fileBase = doneFiles / totalFiles * 100
          const fileSpan = 1 / totalFiles * 100
          this.setData({ uploadProgress: Math.round(fileBase + p.progress / 100 * fileSpan) })
        })
        doneFiles++
        this.setData({ uploadProgress: Math.round(doneFiles / totalFiles * 100) })
      }

      // 日常巡查且声明有隐患 → 创建隐患（挂在本次巡查记录下）
      if (type === 'patrol' && hasHazard) {
        this.setData({ uploadLabel: '正在保存隐患…' })
        const hazard = await post('/rail/patrol/tasks/' + this.taskId + '/hazards', {
          description: hazardDesc.trim(),
          hazard_type: this.data.hazardTypeIndex >= 0 ? this.data.hazardTypes[this.data.hazardTypeIndex].value : '',
          risk_level: this.data.riskIndex >= 0 ? this.data.risks[this.data.riskIndex].value : '',
          record_id: record.record_id
        })
        for (let i = 0; i < shots.length; i++) {
          this.setData({ uploadLabel: `正在上传截图 ${i + 1}/${shots.length}` })
          await uploadShot(hazard.hazard_id, shots[i], (p) => {
            const fileBase = doneFiles / totalFiles * 100
            const fileSpan = 1 / totalFiles * 100
            this.setData({ uploadProgress: Math.round(fileBase + p.progress / 100 * fileSpan) })
          })
          doneFiles++
          this.setData({ uploadProgress: Math.round(doneFiles / totalFiles * 100) })
        }
      }
      if (type === 'rectify' && submitReview) {
        this.setData({ uploadLabel: '正在提交复核…' })
        await post('/rail/patrol/hazards/' + hazardId + '/submit')
      }
      this.setData({ uploadProgress: 100, uploadLabel: '上报成功' })
      wx.showToast({ title: '上报成功', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) {
      wx.showModal({ title: '上报失败', content: e.message, showCancel: false })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
