import request from '@/utils/request'

export function listMeetings(params) {
  return request({ url: '/rail/meeting/list', method: 'get', params })
}

export function getMeeting(meetingId) {
  return request({ url: `/rail/meeting/${meetingId}`, method: 'get' })
}

export function createMeeting(data) {
  return request({ url: '/rail/meeting', method: 'post', data })
}

export function updateMeeting(data) {
  return request({ url: '/rail/meeting', method: 'put', data })
}

export function deleteMeeting(meetingId) {
  return request({ url: `/rail/meeting/${meetingId}`, method: 'delete' })
}

export function notifyMeeting(meetingId, data) {
  return request({ url: `/rail/meeting/${meetingId}/notify`, method: 'post', data })
}

export function markMeetingHeld(meetingId) {
  return request({ url: `/rail/meeting/${meetingId}/held`, method: 'post' })
}

export function archiveMeeting(meetingId) {
  return request({ url: `/rail/meeting/${meetingId}/archive`, method: 'post' })
}

export function addParticipant(meetingId, data) {
  return request({ url: `/rail/meeting/${meetingId}/participants`, method: 'post', data })
}

export function updateParticipant(data) {
  return request({ url: '/rail/meeting/participants', method: 'put', data })
}

export function deleteParticipant(participantId) {
  return request({ url: `/rail/meeting/participants/${participantId}`, method: 'delete' })
}

export function uploadMeetingFile(meetingId, form) {
  return request({
    url: `/rail/meeting/${meetingId}/files`,
    method: 'post',
    data: form,
    timeout: 120000,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function deleteMeetingFile(fileId) {
  return request({ url: `/rail/meeting/files/${fileId}`, method: 'delete' })
}

export function saveMinutes(meetingId, data) {
  return request({ url: `/rail/meeting/${meetingId}/minutes`, method: 'post', data })
}

export function confirmMinutes(meetingId, data) {
  return request({ url: `/rail/meeting/${meetingId}/minutes/confirm`, method: 'post', data })
}

export function addIssue(meetingId, data) {
  return request({ url: `/rail/meeting/${meetingId}/issues`, method: 'post', data })
}

export function updateIssue(data) {
  return request({ url: '/rail/meeting/issues', method: 'put', data })
}

export function deleteIssue(issueId) {
  return request({ url: `/rail/meeting/issues/${issueId}`, method: 'delete' })
}

export function addDecision(meetingId, data) {
  return request({ url: `/rail/meeting/${meetingId}/decisions`, method: 'post', data })
}

export function updateDecision(data) {
  return request({ url: '/rail/meeting/decisions', method: 'put', data })
}

export function deleteDecision(decisionId) {
  return request({ url: `/rail/meeting/decisions/${decisionId}`, method: 'delete' })
}

export function listTodos(params) {
  return request({ url: '/rail/meeting/todos', method: 'get', params })
}

export function addTodo(meetingId, data) {
  return request({ url: `/rail/meeting/${meetingId}/todos`, method: 'post', data })
}

export function updateTodo(data) {
  return request({ url: '/rail/meeting/todos', method: 'put', data })
}

export function deleteTodo(todoId) {
  return request({ url: `/rail/meeting/todos/${todoId}`, method: 'delete' })
}
