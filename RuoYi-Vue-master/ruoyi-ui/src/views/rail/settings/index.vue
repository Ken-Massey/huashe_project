<template>
  <div class="settings-page">
    <header><h2>设置</h2><p>管理当前账号、界面显示、任务消息和大模型服务。</p></header>
    <el-tabs v-model="activeTab" tab-position="left" class="settings-tabs" @tab-click="tabChanged">
      <el-tab-pane label="账号" name="account">
        <section class="setting-section">
          <h3>账号信息</h3>
          <dl><dt>登录账号</dt><dd>{{ user.name || '-' }}</dd><dt>用户名称</dt><dd>{{ user.nickName || '-' }}</dd><dt>角色</dt><dd>{{ roleText }}</dd></dl>
          <div class="commands"><el-button icon="el-icon-user" @click="$router.push('/user/profile')">个人资料与密码</el-button><el-button type="danger" plain icon="el-icon-switch-button" @click="logout">退出登录</el-button></div>
        </section>
      </el-tab-pane>
      <el-tab-pane label="字体大小" name="font">
        <section class="setting-section">
          <h3>界面字体</h3><p class="hint">调整表单、表格和正文的显示字号，仅保存在当前浏览器。</p>
          <el-radio-group v-model="fontSize" @change="applyFontSize"><el-radio-button label="small">小</el-radio-button><el-radio-button label="standard">标准</el-radio-button><el-radio-button label="large">大</el-radio-button></el-radio-group>
          <div class="font-preview">轨道交通保护区智能审核文字预览</div>
        </section>
      </el-tab-pane>
      <el-tab-pane label="消息中心" name="messages">
        <section class="setting-section">
          <div class="section-head"><h3>最近任务</h3><el-button icon="el-icon-refresh" circle title="刷新" :loading="loading" @click="loadMessages" /></div>
          <el-empty v-if="!loading && tasks.length === 0" description="暂无任务消息" />
          <div v-for="task in tasks" :key="task.task_id" class="task-message">
            <i :class="statusIcon(task.status)" /><div><strong>{{ taskLabel(task.task_type) }}</strong><span>{{ task.message || task.status }}</span></div><time>{{ task.updated_at || task.created_at || '' }}</time>
          </div>
        </section>
      </el-tab-pane>
      <el-tab-pane label="已归档项目" name="archives">
        <section class="setting-section archive-section">
          <div class="section-head">
            <div><h3>已归档项目</h3><p class="hint">归档项目不会出现在项目档案列表中，恢复后可继续新增阶段和发起审核。</p></div>
            <el-button icon="el-icon-refresh" circle title="刷新" :loading="archivedLoading" @click="loadArchivedProjects" />
          </div>
          <el-empty v-if="!archivedLoading && archivedProjects.length === 0" description="暂无已归档项目" />
          <div v-loading="archivedLoading" class="archived-projects">
            <article v-for="item in archivedProjects" :key="item.project_id" class="archived-project">
              <span class="archive-icon"><i class="el-icon-folder" /></span>
              <div class="archive-copy">
                <strong>{{ item.name }}</strong>
                <span>{{ item.stage_count || 0 }} 个阶段 · {{ item.completed_stage_count || 0 }} 个已审核</span>
              </div>
              <div class="archive-actions">
                <el-button size="mini" type="primary" plain icon="el-icon-refresh-left" v-hasPermi="['rail:archive:edit']" @click="restoreArchivedProject(item)">恢复</el-button>
                <el-button size="mini" type="danger" plain icon="el-icon-delete" v-hasPermi="['rail:archive:remove']" @click="removeArchivedProject(item)">永久删除</el-button>
              </div>
            </article>
          </div>
        </section>
      </el-tab-pane>
      <el-tab-pane label="大模型" name="model">
        <section class="setting-section">
          <h3>大模型服务</h3>
          <p class="hint">使用硅基流动 Qwen3.5 快速模型，不占用本机显卡和内存，按实际输入和输出 Token 计费。API Key 仅保存在本机 Python 服务中。</p>
          <el-alert v-if="modelStatus.configured" :title="`已就绪：${modelStatus.provider_label} · ${modelStatus.model}`" type="success" :closable="false" show-icon />
          <el-alert v-else title="尚未配置硅基流动 API Key，智能体暂不可用。" type="warning" :closable="false" show-icon />
          <el-form label-position="top" class="model-form">
            <el-form-item label="服务商"><el-input value="硅基流动 SiliconFlow" disabled /></el-form-item>
            <el-form-item label="快速模型"><el-input value="Qwen/Qwen3.5-35B-A3B" disabled /></el-form-item>
            <el-form-item label="API Key">
              <el-input v-model="modelForm.api_key" type="password" show-password autocomplete="new-password" :placeholder="modelStatus.configured ? '留空表示继续使用当前密钥' : '请输入硅基流动 API Key'" />
            </el-form-item>
            <el-button type="primary" icon="el-icon-check" :loading="savingModel" @click="saveModel">保存配置</el-button>
          </el-form>
        </section>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import { getAgentConfig, listTasks, saveAgentConfig } from '@/api/rail/audit'
import { deleteArchiveProject, listArchiveProjects, restoreProject } from '@/api/rail/archive'

export default {
  name: 'RailSettings',
  data() { return { activeTab: 'account', fontSize: localStorage.getItem('rail-font-size') || 'standard', tasks: [], loading: false, archivedProjects: [], archivedLoading: false, savingModel: false, modelForm: { api_key: '' }, modelStatus: { configured: false, provider: 'siliconflow', provider_label: '硅基流动 Qwen3.5 快速模型', model: 'Qwen/Qwen3.5-35B-A3B', api_key_hint: '未配置' } } },
  computed: {
    ...mapState({ user: state => state.user }),
    roleText() { return (this.user.roles || []).join('、') || '-' }
  },
  created() {
    this.applyFontSize(this.fontSize)
    const tab = String(this.$route.query.tab || '')
    if (['account', 'font', 'messages', 'archives', 'model'].includes(tab)) this.activeTab = tab
    if (this.activeTab === 'messages') this.loadMessages()
    if (this.activeTab === 'archives') this.loadArchivedProjects()
    if (this.activeTab === 'model') this.loadModelConfig()
  },
  methods: {
    applyFontSize(value) { localStorage.setItem('rail-font-size', value); document.body.classList.remove('font-size-small', 'font-size-standard', 'font-size-large'); document.body.classList.add(`font-size-${value}`) },
    tabChanged(tab) { if (tab.name === 'messages') this.loadMessages(); if (tab.name === 'archives') this.loadArchivedProjects(); if (tab.name === 'model') this.loadModelConfig() },
    async loadModelConfig() { try { this.modelStatus = await getAgentConfig() } catch (_) { this.modelStatus.configured = false } },
    async saveModel() {
      if (!this.modelForm.api_key && !this.modelStatus.configured) { this.$message.warning('请填写硅基流动 API Key'); return }
      this.savingModel = true
      try {
        const value = await saveAgentConfig(this.modelForm)
        this.modelStatus = value; this.modelForm.api_key = ''
        this.$message.success('大模型配置已保存')
      } finally { this.savingModel = false }
    },
    async loadMessages() { this.loading = true; try { this.tasks = await listTasks(30) } finally { this.loading = false } },
    async loadArchivedProjects() {
      this.archivedLoading = true
      try {
        const projects = await listArchiveProjects({ keyword: '', includeArchived: true }) || []
        this.archivedProjects = projects.filter(item => item.status === 'archived')
      } finally { this.archivedLoading = false }
    },
    async restoreArchivedProject(item) {
      await restoreProject(item.project_id)
      this.$message.success(`“${item.name}”已恢复到项目档案`)
      await this.loadArchivedProjects()
    },
    async removeArchivedProject(item) {
      await this.$confirm(`将永久删除“${item.name}”及其全部阶段和审核记录，删除后不可恢复。`, '永久删除项目', { type: 'warning', confirmButtonText: '永久删除' })
      await deleteArchiveProject(item.project_id)
      this.$message.success('项目已永久删除')
      await this.loadArchivedProjects()
    },
    taskLabel(value) { return ({ stage1: '复函生成', stage2_audit: '案例审核', stage2_advice: '审核意见生成', knowledge_case_import: '知识库入库' })[value] || value },
    statusIcon(value) { return value === 'success' ? 'el-icon-success success' : value === 'failed' ? 'el-icon-error failed' : 'el-icon-loading running' },
    logout() { this.$confirm('确定退出当前账号吗？', '退出登录', { type: 'warning' }).then(() => this.$store.dispatch('LogOut').then(() => { location.href = '/index' })).catch(() => {}) }
  }
}
</script>

<style lang="scss" scoped>
.settings-page { min-height: 100vh; padding: 30px 36px; background: #f6f8f7; }.settings-page header { margin-bottom: 22px; }.settings-page h2 { margin: 0 0 7px; font-size: 22px; letter-spacing: 0; }.settings-page header p,.hint { color: #78817e; }
.settings-tabs { min-height: 560px; padding: 20px; border: 1px solid #e0e5e3; background: #fff; }.setting-section { max-width: 820px; padding: 4px 28px 30px; }.setting-section h3 { margin: 0 0 20px; font-size: 17px; }.setting-section dl { display: grid; grid-template-columns: 120px 1fr; margin: 0 0 26px; }.setting-section dt,.setting-section dd { margin: 0; padding: 14px 0; border-bottom: 1px solid #edf0ef; }.setting-section dt { color: #78817e; }.commands { display: flex; gap: 12px; }
.font-preview { margin-top: 28px; padding: 24px; border: 1px solid #e1e7e4; background: #f7f9f8; }.section-head { display: flex; align-items: center; justify-content: space-between; }.task-message { display: grid; grid-template-columns: 28px 1fr auto; align-items: center; padding: 15px 4px; border-bottom: 1px solid #edf0ef; }.task-message i { font-size: 18px; }.task-message .success { color: #3b8b70; }.task-message .failed { color: #c45656; }.task-message .running { color: #a67c35; }.task-message div { display: grid; gap: 5px; }.task-message span,.task-message time { color: #7b8581; font-size: 12px; }
.archive-section { max-width: 920px; }.archive-section .section-head { align-items: flex-start; }.archive-section .section-head h3 { margin-bottom: 7px; }.archive-section .section-head .hint { margin: 0; }.archived-projects { min-height: 100px; margin-top: 20px; }.archived-project { display: grid; grid-template-columns: 42px minmax(0,1fr) auto; align-items: center; gap: 13px; min-height: 74px; border-bottom: 1px solid #edf0ef; padding: 12px 4px; }.archive-icon { display: flex; width: 38px; height: 38px; align-items: center; justify-content: center; border-radius: 4px; background: #eef3f1; color: #5d756d; font-size: 18px; }.archive-copy { display: flex; min-width: 0; flex-direction: column; gap: 7px; }.archive-copy strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.archive-copy span { color: #7b8581; font-size: 12px; }.archive-actions { display: flex; gap: 8px; }
.model-form { max-width: 560px; margin-top: 22px; }.model-form ::v-deep .el-form-item { margin-bottom: 20px; }
@media (max-width: 760px) { .settings-page { padding: 20px 14px; }.setting-section { padding-right: 8px; padding-left: 8px; }.settings-tabs { padding: 12px 5px; }.task-message { grid-template-columns: 25px 1fr; }.task-message time { display: none; }.archived-project { grid-template-columns: 38px minmax(0,1fr); }.archive-actions { grid-column: 1 / -1; padding-left: 51px; } }
</style>
