const { get, downloadPhoto } = require('../../utils/request')

Page({
  data: {
    event: null,
    photoPaths: {},
    loading: false
  },
  onLoad(options) {
    this.eventId = options.id
    this.load()
  },
  async load() {
    this.setData({ loading: true })
    try {
      const event = await get('/api/v1/patrol/events/' + this.eventId)
      this.setData({ event })
      const paths = {}
      for (const p of (event.photos || [])) {
        try {
          paths[p.photo_id] = await downloadPhoto(p.photo_id)
        } catch (e) { /* 单张失败不阻断整体 */ }
      }
      this.setData({ photoPaths: paths })
    } catch (e) {
      wx.showToast({ title: e.message, icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },
  previewPhoto(e) {
    const id = e.currentTarget.dataset.id
    wx.previewImage({ current: this.data.photoPaths[id], urls: Object.values(this.data.photoPaths) })
  },
  formatTime(value) {
    if (!value) return '-'
    return String(value).replace('T', ' ').slice(0, 19)
  }
})
