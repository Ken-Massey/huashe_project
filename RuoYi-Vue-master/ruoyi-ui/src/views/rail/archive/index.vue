<template>
  <div class="app-container archive-page">
    <section class="archive-workspace">
      <header class="page-head">
        <h2>项目档案</h2>
        <el-button type="primary" icon="el-icon-plus" v-hasPermi="['rail:archive:add']" @click="openProjectDialog()">新建项目</el-button>
      </header>
      <aside class="project-pane panel">
        <div class="pane-head">
          <div><strong>项目</strong><span>{{ filteredProjects.length }}</span></div>
          <el-tooltip content="刷新项目" placement="top"><el-button type="text" icon="el-icon-refresh" @click="loadProjects" /></el-tooltip>
        </div>
        <div class="project-filter">
          <el-input v-model.trim="keyword" clearable prefix-icon="el-icon-search" placeholder="搜索项目名称" />
        </div>
        <div v-loading="projectsLoading" class="project-list">
          <button
            v-for="item in filteredProjects"
            :key="item.project_id"
            type="button"
            class="project-card"
            :class="{ active: item.project_id === selectedProjectId, archived: item.status === 'archived' }"
            @click="selectProject(item.project_id)"
          >
            <span class="project-mark"><i class="el-icon-office-building" /></span>
            <span class="project-copy">
              <strong>{{ item.name }}</strong>
              <span class="project-stats">{{ item.stage_count || 0 }} 个阶段 · {{ item.completed_stage_count || 0 }} 个已审核</span>
            </span>
            <el-tag v-if="item.status === 'archived'" size="mini" type="info">已归档</el-tag>
          </button>
          <div v-if="!projectsLoading && !filteredProjects.length" class="compact-empty">
            <i class="el-icon-folder-opened" />
            <p>暂无项目档案</p>
            <span>新建项目后可继续添加任意阶段</span>
          </div>
        </div>
      </aside>

      <section class="stage-pane panel">
        <template v-if="projectDetail">
          <div class="project-title">
            <div>
              <el-tag v-if="projectDetail.status === 'archived'" size="mini" type="info">已归档</el-tag>
              <h3>{{ projectDetail.name }}</h3>
              <p>{{ projectDetail.description || '尚未填写项目说明' }}</p>
            </div>
            <el-dropdown trigger="click" @command="projectCommand">
              <el-button type="text" icon="el-icon-more" class="more-button" />
              <el-dropdown-menu slot="dropdown">
                <el-dropdown-item command="edit" icon="el-icon-edit" v-hasPermi="['rail:archive:edit']">重命名/编辑项目</el-dropdown-item>
                <el-dropdown-item v-if="projectDetail.status === 'active'" command="archive" icon="el-icon-folder-delete" divided v-hasPermi="['rail:archive:remove']">归档项目</el-dropdown-item>
                <el-dropdown-item v-else command="restore" icon="el-icon-refresh-left" divided v-hasPermi="['rail:archive:edit']">恢复项目</el-dropdown-item>
                <el-dropdown-item command="delete" icon="el-icon-delete" divided v-hasPermi="['rail:archive:remove']">永久删除项目</el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
          </div>
          <div class="stage-heading">
            <div><strong>项目阶段</strong><span>阶段名称和顺序均可人工设置</span></div>
            <el-button v-if="projectDetail.status === 'active'" size="mini" type="primary" plain icon="el-icon-plus" v-hasPermi="['rail:archive:add']" @click="openStageDialog()">新增阶段</el-button>
          </div>
          <div v-loading="detailLoading" class="stage-list">
            <article
              v-for="stage in projectDetail.stages"
              :key="stage.stage_id"
              class="stage-card"
              :class="{ active: stage.stage_id === selectedStageId, archived: stage.status === 'archived' }"
              @click="openStageInAudit(stage)"
            >
              <div class="stage-axis"><span>{{ stage.stage_order }}</span><i /></div>
              <div class="stage-main">
                <div class="stage-name">
                  <strong>{{ displayStageName(stage.name) }}</strong>
                  <el-tag size="mini" :type="auditStatusType(stage.audit_status)">{{ auditStatusLabel(stage.audit_status) }}</el-tag>
                </div>
                <p>{{ stage.description || '暂无阶段说明' }}</p>
                <small v-if="stage.audit_status === 'success'">{{ formatBeijingTime(stage.audit_date) || '审核已完成' }} · {{ stage.risk_level || '待判断' }}</small>
                <small v-else-if="stage.audit_status === 'failed'" class="danger-text">上次审核失败，可重新提交</small>
                <small v-else>等待发起审核</small>
              </div>
              <el-dropdown trigger="click" @click.native.stop @command="command => stageCommand(command, stage)">
                <el-button type="text" icon="el-icon-more" class="more-button" />
                <el-dropdown-menu slot="dropdown">
                  <el-dropdown-item command="edit" icon="el-icon-edit" v-hasPermi="['rail:archive:edit']">编辑阶段</el-dropdown-item>
                  <el-dropdown-item v-if="stage.status === 'active'" command="archive" icon="el-icon-folder-delete" divided v-hasPermi="['rail:archive:remove']">归档阶段</el-dropdown-item>
                  <el-dropdown-item v-else command="restore" icon="el-icon-refresh-left" divided v-hasPermi="['rail:archive:edit']">恢复阶段</el-dropdown-item>
                </el-dropdown-menu>
              </el-dropdown>
            </article>
            <div v-if="!detailLoading && !projectDetail.stages.length" class="compact-empty stage-empty">
              <i class="el-icon-guide" />
              <p>该项目还没有阶段</p>
              <span>阶段不受固定名称限制，可按实际流程新增</span>
            </div>
          </div>
        </template>
        <div v-else class="full-empty"><i class="el-icon-office-building" /><p>选择项目查看阶段</p></div>
      </section>

      <section class="audit-pane panel">
        <template v-if="selectedStage">
          <div class="audit-head">
            <div>
              <span>阶段 {{ selectedStage.stage_order }}</span>
              <h3>{{ displayStageName(selectedStage.name) }}</h3>
            </div>
            <el-tag :type="auditStatusType(selectedStage.audit_status)">{{ auditStatusLabel(selectedStage.audit_status) }}</el-tag>
          </div>
          <div v-loading="auditLoading" class="audit-content">
            <template v-if="auditRecord && auditRecord.status === 'success'">
              <div class="archive-review-body">
                <section class="overall-review-card">
                  <div class="overall-review-head">
                    <h4>综合意见</h4>
                    <el-tag size="mini" :type="riskTagType(auditRecord.risk_level)">{{ auditRecord.risk_level || '待判断' }}</el-tag>
                  </div>
                  <p>{{ archiveOverallOpinionText || '暂无综合意见。' }}</p>
                </section>
                <section class="review-items-section">
                  <h4>具体意见 <span>{{ archiveReviewItems.length }}</span></h4>
                  <article v-for="item in archiveReviewItems" :key="item.order_no" class="review-item-card">
                    <div class="review-item-head">
                      <span class="review-order">{{ item.order_no }}</span>
                      <div>
                        <h4>{{ displayReviewTitle(item) }}</h4>
                        <el-tag v-if="item.risk_level" size="mini" :type="riskTagType(item.risk_level)">{{ item.risk_level }}</el-tag>
                      </div>
                    </div>
                    <div v-if="item.conclusion || item.analysis || item.result" class="review-conclusion">
                      <span>审核意见</span>{{ item.conclusion || item.analysis || item.result }}
                    </div>
                    <div v-if="item.recommendation" class="review-recommendation"><span>建议</span>{{ item.recommendation }}</div>
                    <div v-if="formatBasis(item.basis)" class="review-basis">依据：{{ formatBasis(item.basis) }}</div>
                  </article>
                  <el-empty v-if="!archiveReviewItems.length" description="暂无具体审核意见" />
                </section>
              </div>
            </template>
            <div v-else-if="auditRecord && auditRecord.status === 'failed'" class="audit-state failed-state">
              <i class="el-icon-warning-outline" />
              <h4>本阶段审核未完成</h4>
              <p>{{ auditRecord.error_message || '审核任务执行失败，可返回案例审核页面重新提交。' }}</p>
              <small>已尝试 {{ auditRecord.attempt_count || 1 }} 次</small>
              <el-button type="primary" plain @click="goAudit()">重新审核</el-button>
            </div>
            <div v-else-if="auditRecord && ['pending','running'].includes(auditRecord.status)" class="audit-state running-state">
              <i class="el-icon-loading" />
              <h4>审核任务正在处理</h4>
              <p>任务完成后审核结果会自动写入本阶段档案。</p>
            </div>
            <div v-else class="audit-state">
              <i class="el-icon-document-add" />
              <h4>该阶段尚未审核</h4>
              <p>前往案例审核并绑定当前项目与阶段，完成后结果将自动归档。</p>
              <el-button v-if="selectedStage.status === 'active' && projectDetail.status === 'active'" type="primary" @click="goAudit()">前往审核</el-button>
            </div>
          </div>
        </template>
        <div v-else class="full-empty"><i class="el-icon-document-checked" /><p>选择阶段查看审核记录</p></div>
      </section>
    </section>

    <el-dialog :title="projectDialogMode === 'edit' ? '编辑项目' : '新建项目'" :visible.sync="projectDialogOpen" width="520px" append-to-body @closed="resetProjectForm">
      <el-form ref="projectForm" :model="projectForm" :rules="projectRules" label-width="86px">
        <el-form-item label="项目名称" prop="name"><el-input v-model.trim="projectForm.name" maxlength="120" show-word-limit /></el-form-item>
        <el-form-item label="项目说明" prop="description"><el-input v-model.trim="projectForm.description" type="textarea" :rows="4" maxlength="2000" show-word-limit /></el-form-item>
      </el-form>
      <div slot="footer"><el-button @click="projectDialogOpen=false">取消</el-button><el-button type="primary" :loading="savingProject" @click="saveProject">保存</el-button></div>
    </el-dialog>

    <el-dialog :title="stageDialogMode === 'edit' ? '编辑阶段' : '新增阶段'" :visible.sync="stageDialogOpen" width="500px" append-to-body @closed="resetStageForm">
      <el-form ref="stageForm" :model="stageForm" :rules="stageRules" label-width="86px">
        <el-form-item label="阶段名称" prop="name">
          <el-input v-model.trim="stageForm.name" maxlength="120" show-word-limit placeholder="可输入任意实际阶段名称" />
          <div class="stage-suggestions"><span>快捷填写</span><el-button v-for="name in commonStageNames" :key="name" size="mini" plain @click="stageForm.name=name">{{ name }}</el-button></div>
        </el-form-item>
        <el-form-item label="阶段顺序" prop="stage_order"><el-input-number v-model="stageForm.stage_order" :min="1" :max="999" controls-position="right" /></el-form-item>
        <el-form-item label="阶段说明" prop="description"><el-input v-model.trim="stageForm.description" type="textarea" :rows="4" maxlength="2000" show-word-limit /></el-form-item>
      </el-form>
      <div slot="footer"><el-button @click="stageDialogOpen=false">取消</el-button><el-button type="primary" :loading="savingStage" @click="saveStage">保存</el-button></div>
    </el-dialog>
  </div>
</template>

<script>
import {
  listArchiveProjects, createArchiveProject, getArchiveProject, updateArchiveProject,
  deleteArchiveProject, archiveProject, restoreProject, createArchiveStage, updateArchiveStage,
  archiveStage, restoreStage, getStageAudit
} from '@/api/rail/archive'

const emptyProject = () => ({ name: '', description: '' })
const emptyStage = () => ({ name: '', stage_order: 1, description: '' })

export default {
  name: 'RailProjectArchive',
  data() {
    return {
      keyword: '', projects: [], projectsLoading: false,
      selectedProjectId: '', projectDetail: null, detailLoading: false,
      selectedStageId: '', auditRecord: null, auditLoading: false,
      projectDialogOpen: false, projectDialogMode: 'create', projectForm: emptyProject(), savingProject: false,
      stageDialogOpen: false, stageDialogMode: 'create', stageForm: emptyStage(), editingStageId: '', savingStage: false,
      commonStageNames: ['出让', '规划', '方案设计', '施工图设计', '施工准备', '施工实施', '竣工复核'],
      projectRules: { name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }] },
      stageRules: {
        name: [{ required: true, message: '请输入阶段名称', trigger: 'blur' }],
        stage_order: [{ required: true, message: '请输入阶段顺序', trigger: 'change' }]
      }
    }
  },
  computed: {
    filteredProjects() {
      const keyword = String(this.keyword || '').trim().toLocaleLowerCase()
      if (!keyword) return this.projects
      return this.projects.filter(item => String(item.name || '').toLocaleLowerCase().includes(keyword))
    },
    selectedStage() {
      return this.projectDetail && this.projectDetail.stages.find(item => item.stage_id === this.selectedStageId)
    },
    riskReport() {
      return this.auditRecord && this.auditRecord.result_data && this.auditRecord.result_data.dynamic_regulation_audit && this.auditRecord.result_data.dynamic_regulation_audit.risk_report
    },
    findings() { return (this.riskReport && this.riskReport.findings) || [] },
    requiredSupplements() { return (this.riskReport && this.riskReport.required_supplements) || [] },
    archiveResultData() {
      return (this.auditRecord && this.auditRecord.result_data) || {}
    },
    archiveReviewItems() {
      const data = this.archiveResultData
      const latest = data.latest_result || {}
      const candidates = [
        data.review_items,
        latest.items,
        latest.review_items,
        data.items
      ].find(value => Array.isArray(value) && value.length)
      if (candidates) {
        return candidates
          .filter(item => !this.isOverallReviewItem(item))
          .map((item, index) => ({ ...item, order_no: index + 1 }))
      }
      return (this.findings || []).map((item, index) => ({
        order_no: index + 1,
        title: item.title || item.name || `审核事项 ${index + 1}`,
        conclusion: item.conclusion || item.analysis || item.result || '',
        recommendation: item.recommendation || '',
        risk_level: item.risk_level || item.severity || '提示',
        basis: item.basis || []
      }))
    },
    archiveOverallOpinionText() {
      const data = this.archiveResultData
      const latest = data.latest_result || {}
      const overall = data.overall_opinion || latest.overall_opinion || {}
      if (overall && (overall.conclusion || overall.recommendation)) {
        return overall.conclusion || overall.recommendation
      }
      const report = this.riskReport || {}
      return report.overall_conclusion || (this.auditRecord && this.auditRecord.summary) || ''
    }
  },
  watch: {
    keyword() {
      this.syncFilteredSelection()
    }
  },
  created() { this.loadProjects() },
  methods: {
    async loadProjects() {
      this.projectsLoading = true
      try {
        this.projects = await listArchiveProjects({ keyword: '', includeArchived: false }) || []
        if (!this.projects.some(item => item.project_id === this.selectedProjectId)) this.selectedProjectId = ''
        if (!this.selectedProjectId && this.filteredProjects.length) this.selectedProjectId = this.filteredProjects[0].project_id
        if (this.selectedProjectId) await this.loadProjectDetail()
        else { this.projectDetail = null; this.selectedStageId = ''; this.auditRecord = null }
      } finally { this.projectsLoading = false }
    },
    syncFilteredSelection() {
      const visibleProjects = this.filteredProjects
      if (visibleProjects.some(item => item.project_id === this.selectedProjectId)) return
      this.selectedProjectId = visibleProjects.length ? visibleProjects[0].project_id : ''
      this.selectedStageId = ''
      this.auditRecord = null
      if (this.selectedProjectId) this.loadProjectDetail()
      else this.projectDetail = null
    },
    async selectProject(id) {
      if (id === this.selectedProjectId && this.projectDetail) return
      this.selectedProjectId = id
      this.selectedStageId = ''
      this.auditRecord = null
      await this.loadProjectDetail()
    },
    async loadProjectDetail(preferredStageId) {
      if (!this.selectedProjectId) return
      this.detailLoading = true
      try {
        this.projectDetail = await getArchiveProject(this.selectedProjectId, false)
        const stages = this.projectDetail.stages || []
        const target = preferredStageId || this.selectedStageId
        this.selectedStageId = stages.some(item => item.stage_id === target) ? target : (stages[0] && stages[0].stage_id) || ''
        if (this.selectedStageId) await this.loadAudit()
      } finally { this.detailLoading = false }
    },
    async selectStage(id) {
      if (id === this.selectedStageId && this.auditRecord) return
      this.selectedStageId = id
      await this.loadAudit()
    },
    async loadAudit() {
      if (!this.selectedStageId) { this.auditRecord = null; return }
      this.auditLoading = true
      try { this.auditRecord = await getStageAudit(this.selectedStageId) }
      finally { this.auditLoading = false }
    },
    openProjectDialog(item) {
      this.projectDialogMode = item ? 'edit' : 'create'
      this.projectForm = item ? { name: item.name, description: item.description || '' } : emptyProject()
      this.projectDialogOpen = true
    },
    resetProjectForm() { this.projectForm = emptyProject(); if (this.$refs.projectForm) this.$refs.projectForm.clearValidate() },
    saveProject() {
      this.$refs.projectForm.validate(async valid => {
        if (!valid) return
        this.savingProject = true
        try {
          const value = this.projectDialogMode === 'edit'
            ? await updateArchiveProject(this.selectedProjectId, this.projectForm)
            : await createArchiveProject(this.projectForm)
          this.projectDialogOpen = false
          this.selectedProjectId = value.project_id
          await this.loadProjects()
          this.$message.success(this.projectDialogMode === 'edit' ? '项目已更新' : '项目已创建')
        } finally { this.savingProject = false }
      })
    },
    async projectCommand(command) {
      if (command === 'edit') return this.openProjectDialog(this.projectDetail)
      if (command === 'delete') {
        await this.$confirm(
          `将永久删除“${this.projectDetail.name}”及其全部阶段和审核记录，删除后不可恢复。`,
          '永久删除项目',
          { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
        )
        await deleteArchiveProject(this.selectedProjectId)
        this.selectedProjectId = ''
        this.selectedStageId = ''
        this.projectDetail = null
        this.auditRecord = null
        await this.loadProjects()
        this.$message.success('项目及其审核档案已删除')
        return
      }
      if (command === 'archive') {
        await this.$confirm('归档后不能新增阶段或发起审核，历史记录仍会保留。', '归档项目', { type: 'warning' })
        await archiveProject(this.selectedProjectId)
        this.$message.success('项目已归档')
      } else if (command === 'restore') {
        await restoreProject(this.selectedProjectId)
        this.$message.success('项目已恢复')
      }
      await this.loadProjects()
    },
    openStageDialog(stage) {
      this.stageDialogMode = stage ? 'edit' : 'create'
      this.editingStageId = stage ? stage.stage_id : ''
      this.stageForm = stage
        ? { name: stage.name, stage_order: stage.stage_order, description: stage.description || '' }
        : { ...emptyStage(), stage_order: ((this.projectDetail && this.projectDetail.stages.length) || 0) + 1 }
      this.stageDialogOpen = true
    },
    resetStageForm() { this.stageForm = emptyStage(); this.editingStageId = ''; if (this.$refs.stageForm) this.$refs.stageForm.clearValidate() },
    saveStage() {
      this.$refs.stageForm.validate(async valid => {
        if (!valid) return
        this.savingStage = true
        try {
          const value = this.stageDialogMode === 'edit'
            ? await updateArchiveStage(this.editingStageId, this.stageForm)
            : await createArchiveStage(this.selectedProjectId, this.stageForm)
          this.stageDialogOpen = false
          await this.loadProjectDetail(value.stage_id)
          await this.loadProjects()
          this.$message.success(this.stageDialogMode === 'edit' ? '阶段已更新' : '阶段已创建')
        } finally { this.savingStage = false }
      })
    },
    async stageCommand(command, stage) {
      if (command === 'edit') return this.openStageDialog(stage)
      if (command === 'archive') {
        await this.$confirm('归档阶段不会删除已有审核记录。', '归档阶段', { type: 'warning' })
        await archiveStage(stage.stage_id)
        this.$message.success('阶段已归档')
      } else if (command === 'restore') {
        await restoreStage(stage.stage_id)
        this.$message.success('阶段已恢复')
      }
      await this.loadProjectDetail(stage.stage_id)
      await this.loadProjects()
    },
    async openStageInAudit(stage) {
      if (!stage || !stage.stage_id) return
      this.selectedStageId = stage.stage_id
      this.auditLoading = true
      try {
        const record = await getStageAudit(stage.stage_id)
        this.auditRecord = record
        this.goAudit(stage, record)
      } catch (error) {
        this.goAudit(stage)
      } finally {
        this.auditLoading = false
      }
    },
    goAudit(stage = null, record = null) {
      const targetStage = stage || this.selectedStage
      const audit = record || this.auditRecord || {}
      const resultData = audit.result_data || {}
      const sessionId = audit.audit_session_id || resultData.audit_session_id || ''
      const query = {
        projectId: this.selectedProjectId,
        stageId: targetStage && targetStage.stage_id ? targetStage.stage_id : this.selectedStageId
      }
      if (sessionId) query.sessionId = sessionId
      this.$router.push({ path: '/rail/audit', query })
    },
    auditStatusLabel(value) { return ({ pending: '排队中', running: '审核中', success: '已审核', failed: '审核失败' })[value] || '未审核' },
    auditStatusType(value) { return ({ pending: 'info', running: 'warning', success: 'success', failed: 'danger' })[value] || 'info' },
    displayStageName(value) {
      const name = String(value || '').trim()
      return ['出让', '规划', '设计', '施工'].includes(name) ? `${name}阶段` : name
    },
    formatBeijingTime(value) {
      if (!value) return ''
      const date = new Date(value)
      if (Number.isNaN(date.getTime())) return String(value).replace('T', ' ').replace(/\+08:00$/, '').slice(0, 16)
      return new Intl.DateTimeFormat('zh-CN', {
        timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit', hour12: false
      }).format(date).replace(/\//g, '-')
    },
    riskTagType(value) { return ['重大', '高'].includes(value) ? 'danger' : (value === '中' ? 'warning' : (value === '低' ? 'success' : 'info')) },
    riskClass(value) { return ['重大', '高'].includes(value) ? 'risk-high' : (value === '中' ? 'risk-medium' : 'risk-low') },
    isOverallReviewItem(item) {
      const sourceKind = String(item && item.source && item.source.kind || '')
      const title = String(item && item.title || '').trim()
      return sourceKind === 'overall_summary' || title === '综合意见' || title === '综合审核结论'
    },
    displayReviewTitle(item) {
      const title = String(item && item.title || '').trim()
      if (!title || /^自动审核意见\d*$/.test(title)) return `审核事项 ${item && item.order_no || ''}`.trim()
      return title
    },
    formatBasis(value) {
      if (!value) return ''
      const list = Array.isArray(value) ? value : [value]
      return list.map(item => {
        if (!item) return ''
        if (typeof item === 'string') return item
        return [item.source || item.file || item.document, item.clause || item.article, item.quote || item.text]
          .filter(Boolean)
          .join(' ')
      }).filter(Boolean).join('；')
    }
  }
}
</script>

<style scoped>
.archive-page { height: 100vh; min-height: 650px; margin: -20px; overflow: hidden; background: #fff; color: #26312e; }
.page-head { display: flex; height: 76px; grid-column: 1 / -1; align-items: center; justify-content: space-between; border-bottom: 1px solid #e2e8e5; padding: 0 24px; background: #f4f7f6; }
.page-head h2 { margin: 0; font-size: 23px; font-weight: 600; line-height: 1; }
.archive-workspace { display: grid; height: 100%; grid-template-rows: 76px minmax(0,1fr); grid-template-columns: clamp(270px, 20%, 320px) clamp(330px, 25%, 400px) minmax(420px,1fr); overflow: hidden; border: 0; background: #fff; }
.panel { min-width: 0; min-height: 0; height: 100%; overflow: hidden; }.project-pane,.stage-pane { display: flex; flex-direction: column; border-right: 1px solid #e2e8e5; }.project-pane { background: #f0f4f8; }.audit-pane { display: flex; flex-direction: column; }
.pane-head { display: flex; height: 58px; align-items: center; justify-content: space-between; border-bottom: 1px solid #e7ece9; padding: 0 18px; }
.pane-head>div { display: flex; align-items: center; gap: 9px; }.pane-head strong { font-size: 16px; }.pane-head span { display: inline-flex; min-width: 24px; height: 20px; align-items: center; justify-content: center; border-radius: 10px; background: #e5f1ed; color: #327a68; font-size: 12px; }
.project-filter { padding: 14px 14px 10px; }
.project-list { min-height: 0; flex: 1; overflow: auto; padding: 0 10px 14px; }
.project-card { display: flex; width: 100%; min-height: 86px; align-items: flex-start; gap: 11px; margin: 5px 0; border: 1px solid transparent; border-radius: 5px; padding: 15px 12px; background: transparent; color: inherit; font: inherit; text-align: left; cursor: pointer; }
.project-card:hover { background: #f3f8f6; }.project-card.active { border-color: #c8dfd7; background: #e9f4f0; }.project-card.archived { opacity: .65; }
.project-mark { display: flex; width: 34px; height: 38px; flex: none; align-items: center; justify-content: center; border-radius: 3px; background: #d9ece5; color: #347f6c; font-size: 18px; }
.project-copy { display: flex; min-width: 0; flex: 1; flex-direction: column; }.project-copy strong { overflow: hidden; font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }.project-stats { margin-top: 9px; color: #4b776b; font-size: 12px; }
.project-title { display: flex; flex: none; align-items: flex-start; justify-content: space-between; border-bottom: 1px solid #e7ece9; padding: 20px; }.project-title h3 { margin: 5px 0; font-size: 19px; }.project-title p { margin: 0; color: #7a8581; font-size: 13px; line-height: 1.5; }
.more-button { padding: 4px 7px; color: #66736f; font-size: 18px; }
.stage-heading { display: flex; height: 66px; align-items: center; justify-content: space-between; padding: 0 20px; }.stage-heading>div { display: flex; flex-direction: column; gap: 4px; }.stage-heading strong { font-size: 15px; }.stage-heading span { color: #8b9591; font-size: 12px; }
.stage-list { min-height: 0; flex: 1; overflow: auto; padding: 0 12px 20px; }.stage-card { position: relative; display: grid; grid-template-columns: 42px minmax(0,1fr) 26px; min-height: 112px; border: 1px solid transparent; border-radius: 5px; padding: 13px 9px 13px 4px; cursor: pointer; }.stage-card:hover { background: #f5f8f7; }.stage-card.active { border-color: #cbded8; background: #edf5f2; }.stage-card.archived { opacity: .6; }
.stage-axis { display: flex; flex-direction: column; align-items: center; }.stage-axis span { z-index: 1; display: flex; width: 28px; height: 28px; align-items: center; justify-content: center; border: 2px solid #69a393; border-radius: 50%; background: #fff; color: #337b69; font-size: 12px; font-weight: 600; }.stage-axis i { position: absolute; top: 40px; bottom: -18px; width: 1px; background: #d5e1dd; }.stage-card:last-child .stage-axis i { display: none; }
.stage-main { min-width: 0; }.stage-name { display: flex; align-items: center; justify-content: space-between; gap: 8px; }.stage-name strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.stage-main p { display: -webkit-box; overflow: hidden; margin: 8px 0; color: #737e7a; font-size: 13px; line-height: 1.5; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }.stage-main small { color: #89938f; }.danger-text { color: #c45656 !important; }
.audit-pane { background: #fbfcfc; }.audit-head { display: flex; min-height: 82px; flex: none; align-items: center; justify-content: space-between; border-bottom: 1px solid #e2e8e5; padding: 14px 24px; background: #fff; }.audit-head span { color: #6f897f; font-size: 12px; }.audit-head h3 { margin: 6px 0 0; font-size: 19px; }.audit-content { min-height: 0; flex: 1; overflow: auto; padding: 20px 24px; }
.archive-review-body { display: flex; flex-direction: column; gap: 18px; }
.overall-review-card { border: 1px solid #d9e9e3; border-left: 4px solid #2f7d69; border-radius: 8px; padding: 14px 16px; background: #f6fbf9; }
.overall-review-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.overall-review-head h4 { margin: 0; color: #1f4f43; font-size: 15px; }
.overall-review-card p { margin: 0; color: #263833; font-weight: 600; line-height: 1.8; white-space: pre-wrap; }
.review-items-section>h4 { display: flex; align-items: center; gap: 7px; margin: 0 0 12px; color: #35413d; font-size: 14px; }.review-items-section>h4 span { color: #7b8883; font-size: 12px; font-weight: 400; }
.review-item-card { margin-bottom: 12px; border: 1px solid #e2e9e6; border-radius: 8px; padding: 15px 16px; background: #fff; }
.review-item-card:hover { border-color: #c7ddd5; box-shadow: 0 6px 18px rgba(39, 71, 61, .06); }
.review-item-head { display: grid; grid-template-columns: 34px minmax(0,1fr); gap: 10px; align-items: start; }
.review-order { display: inline-flex; width: 28px; height: 28px; align-items: center; justify-content: center; border: 2px solid #67a897; border-radius: 50%; color: #2f7d69; font-weight: 700; }
.review-item-head h4 { display: inline; margin: 0 8px 0 0; color: #1f2f2b; font-size: 16px; }
.review-conclusion { margin: 12px 0 0 44px; color: #263833; font-weight: 600; line-height: 1.8; white-space: pre-wrap; }
.review-conclusion span { margin-right: 8px; color: #2f7d69; font-weight: 700; }
.review-recommendation { margin: 10px 0 0 44px; padding: 9px 11px; border-left: 3px solid #67a897; background: #f4f9f7; color: #34413d; line-height: 1.7; }
.review-recommendation span { margin-right: 8px; color: #2f7d69; font-weight: 600; }
.review-basis { margin: 9px 0 0 44px; color: #76827d; font-size: 12px; line-height: 1.6; }
.detail-body { margin-top: 20px; }.detail-section { margin-bottom: 22px; }.detail-section h4 { display: flex; align-items: center; gap: 7px; margin: 0 0 11px; color: #35413d; font-size: 14px; }.detail-section h4 span { color: #7b8883; font-size: 12px; font-weight: 400; }.summary-text { margin: 0; border-left: 3px solid #77aa9b; padding: 11px 14px; background: #f0f6f4; color: #4b5753; line-height: 1.75; white-space: pre-wrap; }
.finding-card { margin-bottom: 10px; border: 1px solid #e1e7e4; border-radius: 4px; padding: 13px 15px; background: #fff; }.finding-card>div { display: flex; align-items: center; justify-content: space-between; gap: 12px; }.finding-card p { margin: 9px 0 5px; color: #505c58; line-height: 1.65; }.finding-card small { color: #397865; line-height: 1.5; }
.supplement-row { display: grid; grid-template-columns: 25px 1fr; gap: 8px; border-bottom: 1px solid #e7ece9; padding: 10px 0; }.supplement-row>span { display: flex; width: 22px; height: 22px; align-items: center; justify-content: center; border-radius: 50%; background: #f1e6ce; color: #9b722c; font-size: 12px; }.supplement-row p { display: flex; flex-direction: column; gap: 4px; margin: 0; color: #69746f; }.supplement-row strong { color: #35413d; }
.audit-state,.full-empty,.compact-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; color: #8b9692; text-align: center; }.audit-state { min-height: 390px; }.audit-state i,.full-empty i { margin-bottom: 13px; color: #9ba9a4; font-size: 44px; }.audit-state h4 { margin: 0 0 8px; color: #4f5b57; font-size: 16px; }.audit-state p { max-width: 440px; margin: 0 0 18px; line-height: 1.6; }.audit-state small { margin: -8px 0 18px; }.failed-state i { color: #cf7777; }.running-state i { color: #b69251; }.full-empty { height: 100%; }.full-empty p { margin: 0; }.compact-empty { min-height: 240px; }.compact-empty i { margin-bottom: 9px; font-size: 32px; }.compact-empty p { margin: 0 0 5px; color: #66726e; }.compact-empty span { font-size: 12px; }.stage-empty { min-height: 260px; }.stage-suggestions { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 8px; }.stage-suggestions span { margin-right: 3px; color: #8a9490; font-size: 12px; }
@media (max-width: 1250px) { .archive-workspace { grid-template-columns: 250px 310px minmax(360px,1fr); } }
@media (max-width: 900px) { .archive-page { height: auto; min-height: calc(100vh - 84px); overflow: visible; }.archive-workspace { height: auto; grid-template-rows: 76px auto auto auto; grid-template-columns: 1fr; overflow: visible; }.project-pane,.stage-pane { min-height: 480px; border-right: 0; border-bottom: 1px solid #e2e8e5; }.project-list,.stage-list,.audit-content { height: auto; max-height: 620px; }.audit-pane { min-height: 560px; } }
</style>
