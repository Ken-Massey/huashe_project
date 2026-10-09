/* Run with: node scripts/check-patrol-mobile.cjs
 * Uses installed Vue/Axios and mocked APIs; never writes business data.
 */
const assert = require('assert')
const fs = require('fs')
const path = require('path')
const compiler = require('vue-template-compiler/browser')
const Vue = require('vue/dist/vue.runtime.common.dev')
const axios = require('axios')
const read = relative => fs.readFileSync(path.join(__dirname, '..', relative), 'utf8')
let checks = 0
function check(condition, message) { assert.ok(condition, message); checks++ }
const flow = new Function(read('src/views/rail/patrol-mobile/flow.js').replace(/\bexport /g, '') +
  '; return { buildPatrolTimeline, dispatchTime, groupTimeline, isOverdue, summarizeOpinions, dateLabel }')()
const mobile = compiler.parseComponent(read('src/views/rail/patrol-mobile/index.vue'))
const compiled = compiler.compile(mobile.template.content)
check(compiled.errors.length === 0, '巡查页面模板可编译')
check(compiler.compile(compiler.parseComponent(read('src/views/login.vue')).template.content).errors.length === 0, '平台登录模板可编译')
const warnings = []
Vue.config.warnHandler = message => warnings.push(message)
Vue.config.errorHandler = error => { throw error }
const calls = [], routes = []
let token = '', loginFailure = false, failUpload = false, serial = 0
const api = {
  clearMobileSession: () => { token = '' },
  getMobileToken: () => token,
  getMobileUser: () => token ? '巡查人员' : '',
  mobileBlob: async () => ({}),
  mobileDelete: async endpoint => calls.push({ method: 'delete', endpoint }),
  mobileGet: async (endpoint, params) => {
    calls.push({ method: 'get', endpoint, params })
    if (endpoint.includes('dicts')) return []
    return endpoint.endsWith('tasks') ? { items: [], total: 0 } : { task_id: 't1', status: 'executing', records: [], hazards: [], opinions: [] }
  },
  mobileLogin: async (username, password) => {
    calls.push({ method: 'login', username, password })
    if (loginFailure) throw new Error('账号或密码错误')
    return { token: 'patrol-token' }
  },
  mobilePost: async (endpoint, data) => { calls.push({ method: 'post', endpoint, data }); return { record_id: 'new-r', hazard_id: 'new-h' } },
  mobileUpload: async (endpoint, file, fields) => {
    if (failUpload) { failUpload = false; throw new Error('模拟传输中断') }
    calls.push({ method: 'upload', endpoint, file, fields })
  },
  saveMobileSession: (value, username) => { token = value; calls.push({ method: 'saveSession', value, username }) },
  locate: async () => { throw new Error('模拟定位不可用') }
}
const url = { createObjectURL: () => 'blob:test-' + (++serial), revokeObjectURL: () => {} }
const browser = { isSecureContext: true, confirm: () => true, addEventListener: () => {}, removeEventListener: () => {} }
const component = new Function(...Object.keys(api), ...Object.keys(flow), 'window', 'URL', 'setTimeout', 'clearTimeout',
  mobile.script.content.replace(/^import .*$/gm, '').replace('export default', 'return'))(
  ...Object.values(api), ...Object.values(flow), browser, url, () => 0, () => {})
// Only isolate lifecycle networking; real computed values, methods and render functions stay intact.
delete component.created
delete component.beforeDestroy
delete component.watch
component.render = new Function(compiled.render)
component.staticRenderFns = compiled.staticRenderFns.map(code => new Function(code))
function page(query = {}) {
  return new Vue({ ...component, beforeCreate() {
    this.$route = { query }
    this.$router = {
      push: async route => routes.push(route),
      replace: async route => { routes.push(route); this.$route.query = route.query || {} }
    }
  } })
}
const text = node => node ? (node.text || '') + (node.children || []).map(text).join('') : ''
const file = name => ({ name, size: 100, type: 'image/jpeg' })
const task = {
  task_id: 't1', name: '桥梁巡查', status: 'executing',
  records: [
    { record_id: 'r2', type: 'patrol', created_at: '2026-10-09 08:00:00', media: [] },
    { record_id: 'r1', type: 'patrol', created_at: '2026-10-08 08:00:00', media: [] },
    { record_id: 'rf', type: 'rectify', hazard_id: 'h1', created_at: '2026-10-09 09:00:00', note: '继承整改备注', media: [] }
  ],
  hazards: [
    { hazard_id: 'h1', record_id: 'r1', status: 'rectifying', description: '安全围挡未封闭', shots: [] },
    { hazard_id: 'h2', record_id: 'missing', status: 'pending_confirm', description: '独立隐患', created_at: '2026-10-09 10:00:00', shots: [] }
  ],
  opinions: [{ opinion_id: 'o1', status: 'pending_photo', title: '现场核查', photos: [], created_at: '2026-10-08 08:00:00' }]
}
async function run() {
  let instance = page({ view: 'login' })
  check(instance.showLogin && text(instance._render()).includes('登录巡查端'), '未登录展示独立巡查登录')
  instance.credentials = { username: ' 巡查员 ', password: 'test-password' }
  loginFailure = true
  await instance.login()
  check(instance.loginError === '账号或密码错误' && !instance.loggedIn, '登录失败可见，不进入任务列表')
  loginFailure = false
  await instance.login()
  check(instance.loggedIn && !instance.showLogin, '登录成功进入列表')
  check(calls.some(c => c.method === 'login' && c.username === '巡查员'), '账号去除首尾空格')
  check(calls.filter(c => c.endpoint === '/rail/patrol/tasks').length === 1, '登录只加载一次任务列表')
  check(routes[routes.length - 1].path === '/rail/patrol-mobile' && !routes[routes.length - 1].query, '登录返回独立巡查列表')
  instance = page({ view: 'login' })
  check(instance.showLogin, '显式登录入口不会被已有令牌绕过')
  instance = page()
  instance.tasks = [{ task_id: 't1', name: '施工安全巡查', status: 'pending', open_hazard_count: 3 }, { task_id: 't2', status: 'completed' }]
  instance.total = 2
  check(instance.activeCount === 1 && instance.doneCount === 1 && instance.openHazards === 3, '待办、完成、未闭环统计')
  check(text(instance._render()).includes('施工安全巡查'), '任务列表渲染')
  const original = JSON.stringify(task)
  const timeline = flow.buildPatrolTimeline(task)
  check(JSON.stringify(task) === original, '时间线不修改接口数据')
  check(timeline.length === 3, '独立隐患、巡查记录不丢失')
  check(timeline.find(e => e.data.record_id === 'r1').data.batchNo === 1, '批次按巡查时间排序')
  check(timeline.find(e => e.data.record_id === 'r1').hazards[0].rectifyRecords.length === 1, '整改归属于隐患')
  check(flow.groupTimeline(timeline).length === 2, '时间线按日分组')
  check(flow.dateLabel('2026-10-09 08:00:00', new Date(2026, 9, 9)) === '今天', '当天日期标签')
  check(flow.dateLabel('2026-10-08 08:00:00', new Date(2026, 9, 9)) === '昨天', '昨天日期标签')
  check(!flow.isOverdue({ status: 'closed', created_at: '2020-01-01' }), '已结束任务不标记超时')
  check(flow.buildPatrolTimeline({ ...task, hazards: task.hazards.concat({ hazard_id: 'h3', record_id: 'rf', description: '孤立关联隐患' }) }).some(e => e.key === 'hazard:h3'), '关联折叠整改记录的隐患仍展示')
  instance = page({ view: 'detail', task: 't1' })
  instance.task = task
  instance.buildTimeline(task)
  let content = text(instance._render())
  check(content.includes('整改图片上传') && content.includes('整改完成') && !content.includes('整改记录 ·'), '隐患折叠时关键整改操作可见')
  instance.expandedHazards = { h1: true }; instance.opinionsOpen = true
  content = text(instance._render())
  check(content.includes('继承整改备注') && content.includes('提交核查'), '展开整改历史和审核意见')
  instance.task = { ...task, status: 'closed' }
  content = text(instance._render())
  check(!content.includes('整改图片上传') && !content.includes('上传照片/视频'), '已结束任务只读')
  instance = page({ view: 'upload', task: 't1' }); instance.task = task; instance.upload.hasHazard = true
  content = text(instance._render())
  const order = ['上报类型', '现场定位', '照片/视频', '本次巡查是否有隐患', '本次上传名称', '备注']
  check(order.every((label, i) => i === 0 || content.indexOf(label) > content.indexOf(order[i - 1])), '恢复小程序上报字段顺序')
  instance.openPicker('media')
  check(text(instance._render()).includes('录视频'), '支持拍照、相册、录视频、选择视频')
  let clicked = false; instance.$refs.cameraInput = { click: () => { clicked = true } }
  instance.selectSource('camera')
  check(clicked && instance.picker.scope === 'media' && !instance.sourcePicker, '原生相机文件选择')
  instance = page({ view: 'detail', task: 't1' }); instance.task = task
  instance.startQuickRectify(task.hazards[0])
  check(!instance.quick.visible && instance.sourcePicker.scope === 'quick', '整改先选照片再确认')
  check(instance.quick.recordId === 'rf' && instance.quick.note === '继承整改备注', '复用本轮整改及备注')
  instance.picker = { scope: 'quick' }
  await instance.onFiles({ target: { files: [file('a.jpg')], value: '' } }, 'photo')
  check(instance.quick.visible && instance.quick.files.length === 1, '选照后显示确认弹窗')
  await instance.submitQuick()
  check(calls.some(c => c.method === 'upload' && c.endpoint === '/rail/patrol/records/rf/media'), '向现有整改记录补传')
  check(!instance.quick.visible && !instance.quick.files.length && !instance.progressLabel, '上传成功释放文件、关闭弹窗和进度')
  instance = page({ view: 'detail', task: 't1' }); instance.task = { ...task, records: [] }
  instance.quick = { visible: true, hazardId: 'h1', recordId: '', existingPhotos: 0, note: '整改', files: [{ file: file('retry.jpg'), url: 'blob:retry', kind: 'photo' }] }
  failUpload = true
  await instance.submitQuick()
  check(instance.quick.recordId === 'new-r' && instance.quick.files.length === 1, '失败保留记录ID与未上传照片')
  const beforeRetry = calls.filter(c => c.method === 'post' && c.endpoint === '/rail/patrol/tasks/t1/records').length
  await instance.submitQuick()
  check(calls.filter(c => c.method === 'post' && c.endpoint === '/rail/patrol/tasks/t1/records').length === beforeRetry, '重试不重复创建整改记录')
  check(calls.some(c => c.data && c.data.type === 'rectify' && c.data.longitude === null), '快速整改允许定位失败，保持原规则')
  instance = page({ view: 'hazard', task: 't1' }); instance.task = task; instance.hazardForm.id = 'h1'
  check(text(instance._render()).includes('原有截图保留'), '隐患修改保留原截图')
  check(warnings.length === 0, '所有页面无Vue渲染警告')
  // Verify actual Axios transformation and isolated token storage without networking.
  const values = { 'Admin-Token': 'platform-token', patrol_mobile_token: 'patrol-token' }
  const storage = { getItem: key => values[key], setItem: (key, value) => { values[key] = value }, removeItem: key => { delete values[key] } }
  class Form {
    constructor() { this.rows = [] }
    append(key, value) { this.rows.push([key, value]) }
    entries() { return this.rows[Symbol.iterator]() }
    get [Symbol.toStringTag]() { return 'FormData' }
  }
  const moduleSource = read('src/views/rail/patrol-mobile/api.js').replace(/^import .*$/gm, '').replace(/\bexport /g, '')
  const client = new Function('axios', 'localStorage', 'window', 'FormData', 'process', moduleSource +
    '; return { api, mobileUpload, mobileLogin, clearMobileSession }')(axios, storage, browser, Form, { env: { VUE_APP_BASE_API: '/dev-api' } })
  const originalHeader = axios.defaults.headers['Content-Type']
  axios.defaults.headers['Content-Type'] = 'application/json;charset=utf-8'
  client.api.defaults.headers['Content-Type'] = 'application/json;charset=utf-8'
  const requests = []
  client.api.defaults.adapter = async config => { requests.push(config); return { data: { code: 200, token: 'test' }, config, status: 200 } }
  try {
    for (const endpoint of ['/rail/patrol/records/r/media', '/rail/patrol/hazards/h/shots', '/rail/patrol/opinions/o/photos']) await client.mobileUpload(endpoint, file('upload.jpg'), { kind: 'photo' })
    check(requests.every(r => r.data instanceof Form), 'JSON全局头不再把图片FormData变成JSON')
    check(requests.every(r => r.timeout === 120000 && r.headers.Authorization === 'Bearer patrol-token'), '上传超时和巡查鉴权保留')
    await client.mobileLogin('巡查员', 'test')
    check(!requests[requests.length - 1].headers.Authorization, '巡查登录不带旧令牌')
    client.clearMobileSession()
    check(values['Admin-Token'] === 'platform-token' && !values.patrol_mobile_token, '退出巡查不影响平台令牌')
  } finally { if (originalHeader === undefined) delete axios.defaults.headers['Content-Type']; else axios.defaults.headers['Content-Type'] = originalHeader }
  console.log('PASS: ' + checks + ' checks; no business API calls or writes.')
}
module.exports = run
if (require.main === module) run().catch(error => { console.error(error); process.exitCode = 1 })
