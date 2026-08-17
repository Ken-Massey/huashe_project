import request from '@/utils/request'

export function listArchiveProjects(params) {
  return request({ url: '/rail/archives/projects', method: 'get', params })
}

export function createArchiveProject(data) {
  return request({ url: '/rail/archives/projects', method: 'post', data })
}

export function resolveArchiveProjectStage(data) {
  return request({ url: '/rail/archives/resolve', method: 'post', data })
}

export function getArchiveProject(id, includeArchivedStages = false) {
  return request({
    url: `/rail/archives/projects/${id}`,
    method: 'get',
    params: { includeArchivedStages }
  })
}

export function updateArchiveProject(id, data) {
  return request({ url: `/rail/archives/projects/${id}`, method: 'post', data })
}

export function deleteArchiveProject(id) {
  return request({ url: `/rail/archives/projects/${id}`, method: 'delete' })
}

export function archiveProject(id) {
  return request({ url: `/rail/archives/projects/${id}/archive`, method: 'post' })
}

export function restoreProject(id) {
  return request({ url: `/rail/archives/projects/${id}/restore`, method: 'post' })
}

export function createArchiveStage(projectId, data) {
  return request({ url: `/rail/archives/projects/${projectId}/stages`, method: 'post', data })
}

export function getArchiveStage(id) {
  return request({ url: `/rail/archives/stages/${id}`, method: 'get' })
}

export function updateArchiveStage(id, data) {
  return request({ url: `/rail/archives/stages/${id}`, method: 'post', data })
}

export function archiveStage(id) {
  return request({ url: `/rail/archives/stages/${id}/archive`, method: 'post' })
}

export function restoreStage(id) {
  return request({ url: `/rail/archives/stages/${id}/restore`, method: 'post' })
}

export function getStageAudit(id) {
  return request({ url: `/rail/archives/stages/${id}/audit`, method: 'get' })
}

export function getPreviousStageAudits(id) {
  return request({ url: `/rail/archives/stages/${id}/previous-audits`, method: 'get' })
}

export function getLatestProjectAuditForm(id) {
  return request({ url: `/rail/archives/projects/${id}/latest-audit-form`, method: 'get' })
}
