// 浏览器定位为 WGS-84；小程序原有坐标为 GCJ-02。仅中国境内转换，保持同一任务地图坐标系一致。
const PI = Math.PI
const A = 6378245.0
const EE = 0.006693421622965943

function offsetLat(x, y) {
  let value = -100 + 2 * x + 3 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x))
  value += (20 * Math.sin(6 * x * PI) + 20 * Math.sin(2 * x * PI)) * 2 / 3
  value += (20 * Math.sin(y * PI) + 40 * Math.sin(y / 3 * PI)) * 2 / 3
  value += (160 * Math.sin(y / 12 * PI) + 320 * Math.sin(y * PI / 30)) * 2 / 3
  return value
}

function offsetLon(x, y) {
  let value = 300 + x + 2 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x))
  value += (20 * Math.sin(6 * x * PI) + 20 * Math.sin(2 * x * PI)) * 2 / 3
  value += (20 * Math.sin(x * PI) + 40 * Math.sin(x / 3 * PI)) * 2 / 3
  value += (150 * Math.sin(x / 12 * PI) + 300 * Math.sin(x / 30 * PI)) * 2 / 3
  return value
}

export function toPatrolCoordinates(position) {
  let longitude = position.coords.longitude
  let latitude = position.coords.latitude
  if (longitude >= 72.004 && longitude <= 137.8347 && latitude >= 0.8293 && latitude <= 55.8271) {
    let dLat = offsetLat(longitude - 105, latitude - 35)
    let dLon = offsetLon(longitude - 105, latitude - 35)
    const radLat = latitude / 180 * PI
    let magic = Math.sin(radLat)
    magic = 1 - EE * magic * magic
    const sqrtMagic = Math.sqrt(magic)
    dLat = dLat * 180 / ((A * (1 - EE)) / (magic * sqrtMagic) * PI)
    dLon = dLon * 180 / (A / sqrtMagic * Math.cos(radLat) * PI)
    longitude += dLon
    latitude += dLat
  }
  return { longitude, latitude, accuracy: position.coords.accuracy }
}

export function locate() {
  if (!window.isSecureContext || !navigator.geolocation) {
    return Promise.reject(new Error('手机定位需要 HTTPS 安全地址和浏览器定位权限；本机 localhost 可例外。'))
  }
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      position => resolve(toPatrolCoordinates(position)),
      error => reject(new Error(error.code === 1 ? '定位权限被拒绝，请在浏览器设置中允许定位。' : '定位失败，请到开阔处重试。')),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    )
  })
}
