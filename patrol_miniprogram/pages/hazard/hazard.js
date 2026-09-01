const { get, post, uploadShot } = require('../../utils/request')

Page({
  data: {
    hazardTypes: [], hazardTypeLabels: [], hazardTypeIndex: -1,
    risks: [], riskLabels: [], riskIndex: -1,
    description: '', rectifyOwner: '',
    shots: [],   // [{ shot_id 或 null, path }]
    submitting: false
  },
  onLoad(options) {
    this.taskId = options.taskId
    this.recordId = options.recordId || ''
    this.loadDicts()
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
  onTypeChange(e) { this.setData({ hazardTypeIndex: Number(e.detail.value) }) },
  onRiskChange(e) { this.setData({ riskIndex: Number(e.detail.value) }) },
  onInput(e) { this.setData({ [e.currentTarget.dataset.field]: e.detail.value }) },
  chooseShots() {
    const remain = 9 - this.data.shots.length
    if (remain <= 0) return
    wx.chooseMedia({
      count: remain, mediaType: ['image'], sourceType: ['camera', 'album'], sizeType: ['compressed'],
      success: res => {
        const shots = this.data.shots.concat(res.tempFiles.map(f => ({ shot_id: null, path: f.tempFilePath })))
        this.setData({ shots })
      }
    })
  },
  removeShot(e) {
    const i = e.currentTarget.dataset.index
    const shots = this.data.shots.slice(); shots.splice(i, 1); this.setData({ shots })
  },
  async submit() {
    const { description, hazardTypeIndex, hazardTypes, riskIndex, risks, rectifyOwner, shots, submitting } = this.data
    if (submitting) return
    if (!description.trim()) { wx.showToast({ title: '请填写隐患描述', icon: 'none' }); return }
    this.setData({ submitting: true })
    try {
      const hazard = await post('/rail/patrol/tasks/' + this.taskId + '/hazards', {
        record_id: this.recordId,
        description: description.trim(),
        hazard_type: hazardTypeIndex >= 0 ? hazardTypes[hazardTypeIndex].value : '',
        risk_level: riskIndex >= 0 ? risks[riskIndex].value : '',
        rectify_owner: rectifyOwner
      })
      for (const s of shots) {
        await uploadShot(hazard.hazard_id, s.path)
      }
      wx.showToast({ title: '隐患已记录', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) {
      wx.showModal({ title: '保存失败', content: e.message, showCancel: false })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
