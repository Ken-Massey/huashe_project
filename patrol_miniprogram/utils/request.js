// 网络请求封装：携带若依 JWT（Authorization: Bearer）
const { baseURL } = require('./config')

function getToken() {
  return wx.getStorageSync('patrol_token') || ''
}

function request(path, options = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: baseURL + path,
      method: options.method || 'GET',
      data: options.data || {},
      timeout: options.timeout || 15000,
      header: Object.assign(
        { 'Content-Type': 'application/json', Authorization: 'Bearer ' + getToken() },
        options.header || {}
      ),
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          wx.removeStorageSync('patrol_token')
          wx.reLaunch({ url: '/pages/login/login' })
          reject(new Error('登录已过期'))
        } else {
          const detail = (res.data && (res.data.msg || res.data.detail)) || '请求失败'
          reject(new Error(detail + '（' + res.statusCode + '）'))
        }
      },
      fail(err) {
        reject(new Error((err && err.errMsg) || '网络连接失败'))
      }
    })
  })
}

function get(path, data) { return request(path, { method: 'GET', data }) }
function post(path, data) { return request(path, { method: 'POST', data }) }

// 账号密码登录小程序（独立接口，免验证码，仅允许小程序登录权限账号）
function login(username, password) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: baseURL + '/miniapp/login',
      method: 'POST',
      data: { username, password, code: '', uuid: '' },
      header: { 'Content-Type': 'application/json' },
      success(res) {
        if (res.statusCode === 200 && res.data && res.data.token) {
          resolve(res.data.token)
        } else {
          reject(new Error((res.data && (res.data.msg || res.data.detail)) || '登录失败'))
        }
      },
      fail(err) { reject(new Error((err && err.errMsg) || '登录失败')) }
    })
  })
}

// 上传媒体文件到指定记录
function uploadMedia(recordId, filePath, kind, takenAt, onProgress) {
  return new Promise((resolve, reject) => {
    const task = wx.uploadFile({
      url: baseURL + '/rail/patrol/records/' + recordId + '/media',
      filePath,
      name: 'file',
      header: { Authorization: 'Bearer ' + getToken() },
      formData: { kind, taken_at: takenAt || '' },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try { resolve(JSON.parse(res.data)) } catch (e) { resolve(res.data) }
        } else {
          reject(new Error('上传失败（' + res.statusCode + '）'))
        }
      },
      fail(err) { reject(new Error((err && err.errMsg) || '上传失败')) }
    })
    if (onProgress && task && task.onProgressUpdate) {
      task.onProgressUpdate(onProgress)
    }
  })
}

// 下载媒体到临时路径（图片/视频预览）
function downloadMedia(mediaId) {
  return new Promise((resolve, reject) => {
    wx.downloadFile({
      url: baseURL + '/rail/patrol/media/' + mediaId + '/file',
      header: { Authorization: 'Bearer ' + getToken() },
      success(res) {
        if (res.statusCode === 200) resolve(res.tempFilePath)
        else reject(new Error('加载失败（' + res.statusCode + '）'))
      },
      fail(err) { reject(new Error((err && err.errMsg) || '加载失败')) }
    })
  })
}

// 下载隐患圈注截图
function downloadShot(shotId) {
  return new Promise((resolve, reject) => {
    wx.downloadFile({
      url: baseURL + '/rail/patrol/shots/' + shotId + '/file',
      header: { Authorization: 'Bearer ' + getToken() },
      success(res) {
        if (res.statusCode === 200) resolve(res.tempFilePath)
        else reject(new Error('加载失败（' + res.statusCode + '）'))
      },
      fail(err) { reject(new Error((err && err.errMsg) || '加载失败')) }
    })
  })
}

// 下载监测方案文档到临时路径
function downloadDoc(docId) {
  return new Promise((resolve, reject) => {
    wx.downloadFile({
      url: baseURL + '/rail/patrol/docs/' + docId + '/file',
      header: { Authorization: 'Bearer ' + getToken() },
      success(res) {
        if (res.statusCode === 200) resolve(res.tempFilePath)
        else reject(new Error('加载失败（' + res.statusCode + '）'))
      },
      fail(err) { reject(new Error((err && err.errMsg) || '下载失败')) }
    })
  })
}

// 上传隐患圈注截图
function uploadShot(hazardId, filePath, onProgress) {
  return new Promise((resolve, reject) => {
    const task = wx.uploadFile({
      url: baseURL + '/rail/patrol/hazards/' + hazardId + '/shots',
      filePath,
      name: 'file',
      header: { Authorization: 'Bearer ' + getToken() },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try { resolve(JSON.parse(res.data)) } catch (e) { resolve(res.data) }
        } else {
          reject(new Error('截图上传失败（' + res.statusCode + '）'))
        }
      },
      fail(err) { reject(new Error((err && err.errMsg) || '截图上传失败')) }
    })
    if (onProgress && task && task.onProgressUpdate) {
      task.onProgressUpdate(onProgress)
    }
  })
}

module.exports = { request, get, post, login, uploadMedia, downloadMedia, downloadShot, downloadDoc, uploadShot, baseURL, getToken }

