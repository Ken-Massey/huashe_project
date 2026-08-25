const config = require('./utils/config')

App({
  globalData: {
    baseURL: config.baseURL,
    token: '',
    userName: ''
  },
  onLaunch() {
    this.globalData.token = wx.getStorageSync('patrol_token') || ''
    this.globalData.userName = wx.getStorageSync('patrol_username') || ''
  }
})
