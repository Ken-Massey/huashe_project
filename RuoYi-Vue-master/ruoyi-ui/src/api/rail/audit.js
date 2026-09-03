import request from '@/utils/request'

const uploadConfig = { timeout: 120000, headers: { 'Content-Type': 'multipart/form-data', repeatSubmit: false } }

function upload(url, form) {
  return request({ url, method: 'post', data: form, ...uploadConfig })
}

export function createReplyTask(form) { return upload('/rail/reply/tasks', form) }
export function recognizeReplyLetter(form) { return upload('/rail/reply/recognize', form) }
export function createAuditTask(form) { return upload('/rail/audit/tasks', form) }
export function createAdviceTask(form) { return upload('/rail/advice/tasks', form) }
export function createFullTask(form) { return upload('/rail/full/tasks', form) }
export function getTask(id) { return request({ url: `/rail/tasks/${id}`, method: 'get' }) }
export function listTasks(limit = 20) { return request({ url: '/rail/tasks', method: 'get', params: { limit } }) }
export function getTaskResult(id) { return request({ url: `/rail/tasks/${id}/result`, method: 'get' }) }
export function getTaskFiles(id) { return request({ url: `/rail/tasks/${id}/files`, method: 'get' }) }
export function downloadTaskFile(taskId, fileId) {
  return request({ url: `/rail/tasks/${taskId}/files/${fileId}`, method: 'get', responseType: 'blob', timeout: 120000 })
}

export function listKnowledge(params) { return request({ url: '/rail/knowledge/cases', method: 'get', params }) }
export function getKnowledge(id) { return request({ url: `/rail/knowledge/cases/${id}`, method: 'get' }) }
export function getKnowledgeContent(id, limit = 50000) {
  return request({ url: `/rail/knowledge/cases/${id}/content`, method: 'get', params: { limit } })
}
export function getKnowledgeStats() { return request({ url: '/rail/knowledge/stats', method: 'get' }) }
export function importKnowledge(form) { return upload('/rail/knowledge/cases', form) }
export function listCaseFolders() { return request({ url: '/rail/knowledge/case-folders', method: 'get' }) }
export function createCaseFolder(name, parentId = null) { return request({ url: '/rail/knowledge/case-folders', method: 'post', data: { name, parent_id: parentId } }) }
export function renameCaseFolder(id, name) { return request({ url: `/rail/knowledge/case-folders/${id}/rename`, method: 'post', data: { name } }) }
export function deleteCaseFolder(id) { return request({ url: `/rail/knowledge/case-folders/${id}`, method: 'delete' }) }
export function moveCaseToFolder(id, folderId) { return request({ url: `/rail/knowledge/cases/${id}/folder`, method: 'post', data: { folder_id: folderId || null } }) }
export function renameKnowledgeCase(id, name) { return request({ url: `/rail/knowledge/cases/${id}/rename`, method: 'post', data: { name } }) }
export function disableKnowledge(id) { return request({ url: `/rail/knowledge/cases/${id}`, method: 'delete' }) }
export function restoreKnowledge(id) { return request({ url: `/rail/knowledge/cases/${id}/restore`, method: 'post' }) }
export function deleteKnowledge(id) { return request({ url: `/rail/knowledge/cases/${id}/permanent`, method: 'delete' }) }
export function downloadKnowledgeFile(id) {
  return request({ url: `/rail/knowledge/cases/${id}/file`, method: 'get', responseType: 'blob', timeout: 120000 })
}
export function listRegulations(params) { return request({ url: '/rail/knowledge/regulations', method: 'get', params }) }
export function getRegulation(id) { return request({ url: `/rail/knowledge/regulations/${id}`, method: 'get' }) }
export function getRegulationContent(id, limit = 100000) { return request({ url: `/rail/knowledge/regulations/${id}/content`, method: 'get', params: { limit } }) }
export function getRegulationStats() { return request({ url: '/rail/knowledge/regulations/stats', method: 'get' }) }
export function importRegulation(form) { return upload('/rail/knowledge/regulations', form) }
export function listRegulationFolders() { return request({ url: '/rail/knowledge/regulation-folders', method: 'get' }) }
export function createRegulationFolder(name, parentId = null) { return request({ url: '/rail/knowledge/regulation-folders', method: 'post', data: { name, parent_id: parentId } }) }
export function renameRegulationFolder(id, name) { return request({ url: `/rail/knowledge/regulation-folders/${id}/rename`, method: 'post', data: { name } }) }
export function deleteRegulationFolder(id) { return request({ url: `/rail/knowledge/regulation-folders/${id}`, method: 'delete' }) }
export function moveRegulationToFolder(id, folderId) { return request({ url: `/rail/knowledge/regulations/${id}/folder`, method: 'post', data: { folder_id: folderId || null } }) }
export function renameRegulation(id, name) { return request({ url: `/rail/knowledge/regulations/${id}/rename`, method: 'post', data: { name } }) }
export function generateRegulationRules(id) { return request({ url: `/rail/knowledge/regulations/${id}/generate-rules`, method: 'post' }) }
export function disableRegulation(id) { return request({ url: `/rail/knowledge/regulations/${id}`, method: 'delete' }) }
export function restoreRegulation(id) { return request({ url: `/rail/knowledge/regulations/${id}/restore`, method: 'post' }) }
export function deleteRegulation(id) { return request({ url: `/rail/knowledge/regulations/${id}/permanent`, method: 'delete' }) }
export function downloadRegulationFile(id) { return request({ url: `/rail/knowledge/regulations/${id}/file`, method: 'get', responseType: 'blob', timeout: 120000 }) }
export function listLibraryAssets(params) { return request({ url: '/rail/knowledge/assets', method: 'get', params }) }
export function uploadLibraryAsset(form) { return upload('/rail/knowledge/assets', form) }
export function renameLibraryAsset(id, name) { return request({ url: `/rail/knowledge/assets/${id}/rename`, method: 'post', data: { name } }) }
export function moveLibraryAsset(id, folderId) { return request({ url: `/rail/knowledge/assets/${id}/folder`, method: 'post', data: { folder_id: folderId || null } }) }
export function deleteLibraryAsset(id) { return request({ url: `/rail/knowledge/assets/${id}`, method: 'delete' }) }
export function downloadLibraryAsset(id) { return request({ url: `/rail/knowledge/assets/${id}/file`, method: 'get', responseType: 'blob', timeout: 120000 }) }
export function listRegulationRules(params) { return request({ url: '/rail/knowledge/rules', method: 'get', params }) }
export function updateRegulationRule(id, rule) { return request({ url: `/rail/knowledge/rules/${id}`, method: 'post', data: { rule } }) }
export function testRegulationRule(id, data) { return request({ url: `/rail/knowledge/rules/${id}/test`, method: 'post', data: { data } }) }
export function publishRegulationRule(id) { return request({ url: `/rail/knowledge/rules/${id}/publish`, method: 'post' }) }
export function askAgent(data) { return request({ url: '/rail/agent/ask', method: 'post', data, timeout: 180000 }) }
export function getAgentConfig() { return request({ url: '/rail/agent/config', method: 'get' }) }
export function saveAgentConfig(data) { return request({ url: '/rail/agent/config', method: 'post', data }) }
export function listAgentSessions(limit = 50) { return request({ url: '/rail/agent/sessions', method: 'get', params: { limit } }) }
export function createAgentSession(data = {}) { return request({ url: '/rail/agent/sessions', method: 'post', data }) }
export function getAgentSession(id) { return request({ url: `/rail/agent/sessions/${id}`, method: 'get' }) }
export function renameAgentSession(id, title) { return request({ url: `/rail/agent/sessions/${id}/rename`, method: 'post', data: { title } }) }
export function deleteAgentSession(id) { return request({ url: `/rail/agent/sessions/${id}`, method: 'delete' }) }

export function createAuditSession(data) { return request({ url: '/rail/audit-sessions', method: 'post', data }) }
export function getAuditSession(id) { return request({ url: `/rail/audit-sessions/${id}`, method: 'get' }) }
export function createAuditSessionItem(sessionId, data) { return request({ url: `/rail/audit-sessions/${sessionId}/items`, method: 'post', data }) }
export function updateAuditSessionItem(sessionId, itemId, data) { return request({ url: `/rail/audit-sessions/${sessionId}/items/${itemId}`, method: 'post', data }) }
export function deleteAuditSessionItem(sessionId, itemId) { return request({ url: `/rail/audit-sessions/${sessionId}/items/${itemId}`, method: 'delete' }) }
export function reviseAuditSession(sessionId, instruction) {
  return request({ url: `/rail/audit-sessions/${sessionId}/chat`, method: 'post', data: { instruction }, timeout: 180000 })
}
export function writeAuditSessionToArchive(sessionId, data) {
  return request({ url: `/rail/audit-sessions/${sessionId}/archive`, method: 'post', data, timeout: 120000 })
}
export function generateAuditSessionReply(sessionId, data) {
  return request({
    url: `/rail/audit-sessions/${sessionId}/reply`,
    method: 'post',
    data,
    responseType: 'blob',
    timeout: 180000
  })
}
