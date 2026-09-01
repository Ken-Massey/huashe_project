import request from '@/utils/request'

// 字典
export function listPatrolDicts(dictType = 'line') {
  return request({ url: '/rail/patrol/dicts', method: 'get', params: { dictType } })
}
export function createPatrolDict(data) {
  return request({ url: '/rail/patrol/dicts', method: 'post', data })
}
export function updatePatrolDict(id, data) {
  return request({ url: `/rail/patrol/dicts/${id}`, method: 'post', data })
}
export function deletePatrolDict(id) {
  return request({ url: `/rail/patrol/dicts/${id}`, method: 'delete' })
}

// 任务
export function listPatrolTasks(params) {
  return request({ url: '/rail/patrol/tasks', method: 'get', params })
}
export function getPatrolTask(id) {
  return request({ url: `/rail/patrol/tasks/${id}`, method: 'get' })
}
export function createPatrolTask(data) {
  return request({ url: '/rail/patrol/tasks', method: 'post', data })
}
export function updatePatrolTask(id, data) {
  return request({ url: `/rail/patrol/tasks/${id}`, method: 'post', data })
}
export function setPatrolTaskStatus(id, status) {
  return request({ url: `/rail/patrol/tasks/${id}/status`, method: 'post', data: { status } })
}
export function reopenPatrolTask(id) {
  return request({ url: `/rail/patrol/tasks/${id}/reopen`, method: 'post' })
}
export function deletePatrolTask(id) {
  return request({ url: `/rail/patrol/tasks/${id}`, method: 'delete' })
}
export function getPatrolStatistics(params) {
  return request({ url: '/rail/patrol/statistics', method: 'get', params })
}

// 巡查记录与媒体
export function getPatrolMediaFile(id) {
  return request({ url: `/rail/patrol/media/${id}/file`, method: 'get', responseType: 'blob' })
}

// 隐患
export function createPatrolHazard(taskId, data) {
  return request({ url: `/rail/patrol/tasks/${taskId}/hazards`, method: 'post', data })
}
export function confirmPatrolHazard(hazardId, data) {
  return request({ url: `/rail/patrol/hazards/${hazardId}/confirm`, method: 'post', data })
}
export function reviewPatrolHazard(hazardId, data) {
  return request({ url: `/rail/patrol/hazards/${hazardId}/review`, method: 'post', data })
}
export function updatePatrolHazard(hazardId, data) {
  return request({ url: `/rail/patrol/hazards/${hazardId}`, method: 'post', data })
}
export function deletePatrolHazard(hazardId) {
  return request({ url: `/rail/patrol/hazards/${hazardId}`, method: 'delete' })
}
export function uploadPatrolShot(hazardId, form) {
  return request({
    url: `/rail/patrol/hazards/${hazardId}/shots`,
    method: 'post',
    data: form,
    timeout: 120000,
    headers: { 'Content-Type': 'multipart/form-data', repeatSubmit: false }
  })
}
export function getPatrolShotFile(id) {
  return request({ url: `/rail/patrol/shots/${id}/file`, method: 'get', responseType: 'blob' })
}

// 监测方案文档
export function uploadPatrolDoc(taskId, form) {
  return request({
    url: `/rail/patrol/tasks/${taskId}/docs`,
    method: 'post',
    data: form,
    timeout: 120000,
    headers: { 'Content-Type': 'multipart/form-data', repeatSubmit: false }
  })
}
export function getPatrolDocFile(id) {
  return request({ url: `/rail/patrol/docs/${id}/file`, method: 'get', responseType: 'blob' })
}
export function deletePatrolDoc(id) {
  return request({ url: `/rail/patrol/docs/${id}`, method: 'delete' })
}
