import request from '@/utils/request'

export function listGeneralItems(params) {
  return request({ url: '/rail/general/items/list', method: 'get', params })
}

export function getGeneralItem(itemId) {
  return request({ url: `/rail/general/items/${itemId}`, method: 'get' })
}

export function createGeneralItem(data) {
  return request({ url: '/rail/general/items', method: 'post', data })
}

export function updateGeneralItem(data) {
  return request({ url: '/rail/general/items', method: 'put', data })
}

export function deleteGeneralItem(itemId) {
  return request({ url: `/rail/general/items/${itemId}`, method: 'delete' })
}

export function submitGeneralItem(itemId, data) {
  return request({ url: `/rail/general/items/${itemId}/submit`, method: 'post', data })
}

export function reviewGeneralItem(itemId, data) {
  return request({ url: `/rail/general/items/${itemId}/review`, method: 'post', data })
}

export function closeGeneralItem(itemId, data) {
  return request({ url: `/rail/general/items/${itemId}/close`, method: 'post', data })
}

export function archiveGeneralItem(itemId) {
  return request({ url: `/rail/general/items/${itemId}/archive`, method: 'post' })
}

export function listGeneralReports(params) {
  return request({ url: '/rail/general/reports/list', method: 'get', params })
}

export function getGeneralReport(reportId) {
  return request({ url: `/rail/general/reports/${reportId}`, method: 'get' })
}

export function createGeneralReport(data) {
  return request({ url: '/rail/general/reports', method: 'post', data })
}

export function updateGeneralReport(data) {
  return request({ url: '/rail/general/reports', method: 'put', data })
}

export function deleteGeneralReport(reportId) {
  return request({ url: `/rail/general/reports/${reportId}`, method: 'delete' })
}

export function submitGeneralReport(reportId, data) {
  return request({ url: `/rail/general/reports/${reportId}/submit`, method: 'post', data })
}

export function reviewGeneralReport(reportId, data) {
  return request({ url: `/rail/general/reports/${reportId}/review`, method: 'post', data })
}

export function publishGeneralReport(reportId, data) {
  return request({ url: `/rail/general/reports/${reportId}/publish`, method: 'post', data })
}

export function archiveGeneralReport(reportId) {
  return request({ url: `/rail/general/reports/${reportId}/archive`, method: 'post' })
}

export function uploadItemAttachment(itemId, form) {
  return request({
    url: `/rail/general/items/${itemId}/attachments`,
    method: 'post',
    data: form,
    timeout: 120000,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function uploadReportAttachment(reportId, form) {
  return request({
    url: `/rail/general/reports/${reportId}/attachments`,
    method: 'post',
    data: form,
    timeout: 120000,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function deleteGeneralAttachment(attachmentId) {
  return request({ url: `/rail/general/attachments/${attachmentId}`, method: 'delete' })
}

export function getGeneralStatistics(params) {
  return request({ url: '/rail/general/statistics', method: 'get', params })
}
