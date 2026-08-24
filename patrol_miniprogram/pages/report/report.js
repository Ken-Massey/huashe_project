const { get, post, uploadPhoto } = require('../../utils/request')

function formatNow() {
  const d = new Date()
  const pad = n => (n < 10 ? '0' + n : '' + n)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

Page({
  data: {
    lineOptions: [],
    lineLabels: [],
    lineIndex: -1,
    typeOptions: [],
    typeLabels: [],
    typeIndex: -1,
    photos: [],
    location: null,
    locationDesc: '',
    constructor: '',
    reporterName: '',
    reporterUnit: '',
    remark: '',
    submitting: false
  },
  onLoad() {
    this.loadDicts()
    const app = getApp()
    this.setData({
      reporterName: app.globalData.reporterName || '',
      reporterUnit: app.globalData.reporterUnit || ''
    })
  },
  async loadDicts() {
    try {
      const lines = await get('/api/v1/patrol/dicts', { dict_type: 'line' })
      const types = await get('/api/v1/patrol/dicts', { dict_type: 'construction_type' })
      this.setData({
        lineOptions: lines || [],
        lineLabels: (lines || []).map(i => i.label),
        typeOptions: types || [],
        typeLabels: (types || []).map(i => i.label)
      })
    } catch (e) {
      wx.showToast({ title: e.message, icon: 'none' })
    }
  },
  onLineChange(e) {
    this.setData({ lineIndex: Number(e.detail.value) })
  },
  onTypeChange(e) {
    this.setData({ typeIndex: Number(e.detail.value) })
  },
  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [field]: e.detail.value })
  },
  choosePhotos() {
    const remain = 9 - this.data.photos.length
    if (remain <= 0) {
      wx.showToast({ title: '最多上传9张照片', icon: 'none' })
      return
    }
    wx.chooseMedia({
      count: remain,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      sizeType: ['compressed'],
      success: res => {
        const photos = this.data.photos.concat(res.tempFiles.map(f => ({ path: f.tempFilePath, size: f.size })))
        this.setData({ photos })
      }
    })
  },
  previewPhoto(e) {
    const index = e.currentTarget.dataset.index
    wx.previewImage({ current: this.data.photos[index].path, urls: this.data.photos.map(p => p.path) })
  },
  removePhoto(e) {
    const index = e.currentTarget.dataset.index
    const photos = this.data.photos.slice()
    photos.splice(index, 1)
    this.setData({ photos })
  },
  getLocation() {
    wx.getLocation({
      type: 'gcj02',
      success: res => {
        this.setData({ location: { longitude: res.longitude, latitude: res.latitude, accuracy: res.accuracy } })
        wx.showToast({ title: '定位成功', icon: 'success' })
      },
      fail: () => {
        wx.showModal({
          title: '定位失败',
          content: '请开启定位权限后重试，现场巡查需要记录位置。',
          confirmText: '重试',
          success: r => { if (r.confirm) this.getLocation() }
        })
      }
    })
  },
  async submit() {
    if (this.data.submitting) return
    const { photos, location, reporterName, lineIndex } = this.data
    if (!photos.length) { wx.showToast({ title: '请先拍摄或选择现场照片', icon: 'none' }); return }
    if (!location) { wx.showToast({ title: '请先获取现场定位', icon: 'none' }); return }
    if (!reporterName.trim()) { wx.showToast({ title: '请填写上报人姓名', icon: 'none' }); return }
    if (lineIndex < 0) { wx.showToast({ title: '请选择线路', icon: 'none' }); return }

    this.setData({ submitting: true })
    try {
      const line = this.data.lineOptions[lineIndex]
      const type = this.data.typeIndex >= 0 ? this.data.typeOptions[this.data.typeIndex] : null
      const event = await post('/api/v1/patrol/events', {
        line: line ? line.value : '',
        location_desc: this.data.locationDesc,
        longitude: location.longitude,
        latitude: location.latitude,
        accuracy: location.accuracy,
        constructor: this.data.constructor,
        construction_type: type ? type.value : '',
        reporter_name: reporterName.trim(),
        reporter_unit: this.data.reporterUnit,
        remark: this.data.remark
      })

      wx.showLoading({ title: '上传照片中…', mask: true })
      const takenAt = formatNow()
      for (let i = 0; i < photos.length; i++) {
        await uploadPhoto(event.event_id, photos[i].path, takenAt)
      }
      wx.hideLoading()

      try {
        wx.setStorageSync('patrol_reporter_name', reporterName.trim())
        wx.setStorageSync('patrol_reporter_unit', this.data.reporterUnit)
      } catch (e) { /* ignore */ }

      wx.showToast({ title: '上报成功', icon: 'success' })
      setTimeout(() => {
        wx.redirectTo({ url: '/pages/detail/detail?id=' + event.event_id })
      }, 800)
    } catch (e) {
      wx.hideLoading()
      wx.showModal({ title: '上报失败', content: e.message, showCancel: false })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
