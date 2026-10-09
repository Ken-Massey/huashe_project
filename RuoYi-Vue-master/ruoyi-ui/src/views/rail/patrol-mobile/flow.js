const timestamp = value => new Date(String(value || '').replace(' ', 'T')).getTime() || 0

export function dateLabel(value, now = new Date()) {
  const time = timestamp(value)
  if (!time) return '日期未记录'
  const date = new Date(time)
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const day = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const days = Math.round((today - day) / 86400000)
  if (days === 0) return '今天'
  if (days === 1) return '昨天'
  return date.getFullYear() === now.getFullYear()
    ? `${date.getMonth() + 1}月${date.getDate()}日`
    : `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
}

export function dispatchTime(value) {
  const time = timestamp(value)
  if (!time) return ''
  const date = new Date(time)
  return `${dateLabel(value)} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

export function isOverdue(task, now = Date.now()) {
  const time = timestamp(task.created_at || task.dispatch_time)
  return ['pending', 'executing'].includes(task.status) && time > 0 && now - time > 86400000
}

export function buildPatrolTimeline(task) {
  const records = task.records || []
  const hazards = (task.hazards || []).map(h => {
    const description = String(h.description || '').replace(/\s+/g, ' ').trim()
    return { ...h, descShort: description.length > 42 ? description.slice(0, 42) + '…' : description, rectifyRecords: [] }
  })
  const byId = Object.fromEntries(hazards.map(h => [h.hazard_id, h]))
  const batches = {}
  records.filter(r => r.type === 'patrol').slice()
    .sort((a, b) => timestamp(a.created_at) - timestamp(b.created_at))
    .forEach((r, i) => { batches[r.record_id] = i + 1 })
  // 整改记录折叠进隐患，不单独占时间线；孤立关联也要保留展示。
  const visibleRecordIds = new Set(records.filter(r => !(r.type === 'rectify' && byId[r.hazard_id])).map(r => r.record_id))
  const timeline = []
  records.forEach(record => {
    if (record.type === 'rectify' && byId[record.hazard_id]) {
      byId[record.hazard_id].rectifyRecords.push(record)
    } else {
      timeline.push({
        key: 'record:' + record.record_id,
        kind: 'record', time: record.created_at,
        data: { ...record, batchNo: batches[record.record_id] || 0 },
        hazards: hazards.filter(h => h.record_id === record.record_id)
      })
    }
  })
  hazards.filter(h => !h.record_id || !visibleRecordIds.has(h.record_id)).forEach(h => {
    timeline.push({ key: 'hazard:' + h.hazard_id, kind: 'hazard', time: h.created_at, data: h, hazards: [h] })
  })
  hazards.forEach(h => h.rectifyRecords.sort((a, b) => timestamp(a.created_at) - timestamp(b.created_at)))
  return timeline.sort((a, b) => timestamp(b.time) - timestamp(a.time))
}

export function groupTimeline(timeline) {
  const groups = []
  timeline.forEach(entry => {
    const time = timestamp(entry.time)
    const date = new Date(time)
    const key = time ? `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}` : 'unknown'
    let group = groups.find(item => item.key === key)
    if (!group) {
      group = { key, label: dateLabel(entry.time), entries: [] }
      groups.push(group)
    }
    group.entries.push(entry)
  })
  return groups
}

export function summarizeOpinions(opinions) {
  const summary = { done: 0, pending_photo: 0, photo_taken: 0, returned: 0, lastTime: '' }
  let latest = 0
  ;(opinions || []).forEach(opinion => {
    if (Object.prototype.hasOwnProperty.call(summary, opinion.status) && opinion.status !== 'lastTime') summary[opinion.status]++
    const value = opinion.check_time || opinion.updated_at || opinion.created_at
    if (timestamp(value) > latest) { latest = timestamp(value); summary.lastTime = value }
  })
  return summary
}
