import request from '@/utils/request'

export function listAuditWorkflow(query) {
  return request({
    url: '/rail/audit/workflow/list',
    method: 'get',
    params: query
  })
}

export function listAuditTodo(query) {
  return request({
    url: '/rail/audit/workflow/todo',
    method: 'get',
    params: query
  })
}

export function getAuditWorkflow(workflowId) {
  return request({
    url: '/rail/audit/workflow/' + workflowId,
    method: 'get'
  })
}

export function getAuditTasks(workflowId) {
  return request({
    url: '/rail/audit/workflow/' + workflowId + '/tasks',
    method: 'get'
  })
}

export function getAuditLogs(workflowId) {
  return request({
    url: '/rail/audit/workflow/' + workflowId + '/logs',
    method: 'get'
  })
}

export function getAuditSnapshots(workflowId) {
  return request({
    url: '/rail/audit/workflow/' + workflowId + '/snapshots',
    method: 'get'
  })
}

export function listAuditFlowNodes(query) {
  return request({
    url: '/rail/audit/workflow/nodes',
    method: 'get',
    params: query
  })
}

export function submitAuditWorkflow(data) {
  return request({
    url: '/rail/audit/workflow/submit',
    method: 'post',
    data
  })
}

export function approveAuditWorkflow(data) {
  return request({
    url: '/rail/audit/workflow/approve',
    method: 'post',
    data
  })
}

export function returnAuditWorkflow(data) {
  return request({
    url: '/rail/audit/workflow/return',
    method: 'post',
    data
  })
}

export function archiveAuditWorkflow(data) {
  return request({
    url: '/rail/audit/workflow/archive',
    method: 'post',
    data
  })
}
