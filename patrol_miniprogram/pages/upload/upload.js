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
    note: '',
    submitReview: true,
    // 日常巡查的隐患声明
    hasHazard: false,
    hazardTypes: [], hazardTypeLabels: [], hazardTypeIndex: -1,
    risks: [], riskLabels: [], riskIndex: -1,
    hazardDesc: '', shots: [],
    submitting: false
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
    wx.getLocation({
      type: 'gcj02',
      success: res => { this.setData({ location: { longitude: res.longitude, latitude: res.latitude, accuracy: res.accuracy } }); wx.showToast({ title: '定位成功', icon: 'success' }) },
      fail: () => wx.showModal({ title: '定位失败', content: '请开启定位权限后重试', confirmText: '重试', success: r => { if (r.confirm) this.getLocation() } })
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
        const media = this.data.media.concat(res.tempFiles.map(f => ({ path: f.tempFilePath, kind: f.fileType === 'video' ? 'video' : 'photo' })))
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

    this.setData({ submitting: true })
    try {
      const record = await post('/rail/patrol/tasks/' + this.taskId + '/records', {
        type, hazard_id: hazardId, longitude: location.longitude, latitude: location.latitude, accuracy: location.accuracy, note
      })
      wx.showLoading({ title: '上传中…', mask: true })
      const takenAt = formatNow()
      for (let i = 0; i < media.length; i++) {
        await uploadMedia(record.record_id, media[i].path, media[i].kind, takenAt)
      }
      // 日常巡查且声明有隐患 → 创建隐患（挂在本次巡查记录下）
      if (type === 'patrol' && hasHazard) {
        const hazard = await post('/rail/patrol/tasks/' + this.taskId + '/hazards', {
          description: hazardDesc.trim(),
          hazard_type: this.data.hazardTypeIndex >= 0 ? this.data.hazardTypes[this.data.hazardTypeIndex].value : '',
          risk_level: this.data.riskIndex >= 0 ? this.data.risks[this.data.riskIndex].value : '',
          record_id: record.record_id
        })
        for (const s of shots) { await uploadShot(hazard.hazard_id, s) }
      }
      if (type === 'rectify' && submitReview) {
        await post('/rail/patrol/hazards/' + hazardId + '/submit')
      }
      wx.hideLoading()
      wx.showToast({ title: '上报成功', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) {
      wx.hideLoading()
      wx.showModal({ title: '上报失败', content: e.message, showCancel: false })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
