const { get, post, del, uploadShot, downloadShot } = require('../../utils/request')

Page({
  data: {
    editing: false,
    hazardTypes: [], hazardTypeLabels: [], hazardTypeIndex: -1,
    risks: [], riskLabels: [], riskIndex: -1,
    description: '', rectifyOwner: '', rectifyRequirement: '',
    shots: [],   // [{ shot_id 或 null, path, existing }]
    submitting: false
  },
  onLoad(options) {
    this.taskId = options.taskId
    this.recordId = options.recordId || ''
    this.hazardId = options.hazardId || ''
    this.loadDicts().then(() => { if (this.hazardId) this.loadHazard() })
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
  async loadHazard() {
    try {
      const task = await get('/rail/patrol/tasks/' + this.taskId)
      const h = (task.hazards || []).find(x => x.hazard_id === this.hazardId)
      if (!h) return
      const shots = []
      for (const s of (h.shots || [])) {
        try { shots.push({ shot_id: s.shot_id, path: await downloadShot(s.shot_id), existing: true }) }
        catch (e) { shots.push({ shot_id: s.shot_id, path: '', existing: true }) }
      }
      this.setData({
        editing: true,
        description: h.description,
        rectifyOwner: h.rectify_owner || '',
        rectifyRequirement: h.rectify_requirement || '',
        hazardTypeIndex: Math.max(-1, this.data.hazardTypes.findIndex(t => t.value === h.hazard_type)),
        riskIndex: Math.max(-1, this.data.risks.findIndex(r => r.value === h.risk_level)),
        shots
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
        const shots = this.data.shots.concat(res.tempFiles.map(f => ({ shot_id: null, path: f.tempFilePath, existing: false })))
        this.setData({ shots })
      }
    })
  },
  async removeShot(e) {
    const i = e.currentTarget.dataset.index
    const item = this.data.shots[i]
    if (item.existing && item.shot_id) {
      try { await del('/rail/patrol/shots/' + item.shot_id) } catch (err) { wx.showToast({ title: err.message, icon: 'none' }); return }
    }
    const shots = this.data.shots.slice(); shots.splice(i, 1); this.setData({ shots })
  },
  async submit() {
    const { description, hazardTypeIndex, hazardTypes, riskIndex, risks, rectifyOwner, rectifyRequirement, shots, submitting } = this.data
    if (submitting) return
    if (!description.trim()) { wx.showToast({ title: '请填写隐患描述', icon: 'none' }); return }
    this.setData({ submitting: true })
    try {
      const payload = {
        description: description.trim(),
        hazard_type: hazardTypeIndex >= 0 ? hazardTypes[hazardTypeIndex].value : '',
        risk_level: riskIndex >= 0 ? risks[riskIndex].value : '',
        rectify_owner: rectifyOwner,
        rectify_requirement: rectifyRequirement
      }
      let hazard
      if (this.hazardId) {
        hazard = await post('/rail/patrol/hazards/' + this.hazardId, payload)
      } else {
        payload.record_id = this.recordId
        hazard = await post('/rail/patrol/tasks/' + this.taskId + '/hazards', payload)
      }
      for (const s of shots) {
        if (!s.existing) await uploadShot(hazard.hazard_id, s.path)
      }
      wx.showToast({ title: this.hazardId ? '隐患已修改' : '隐患已记录', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) {
      wx.showModal({ title: '保存失败', content: e.message, showCancel: false })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
