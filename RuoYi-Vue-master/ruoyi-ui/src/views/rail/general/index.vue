<template>
  <div class="app-container general-page">
    <header class="page-head">
      <div>
        <h2>通用管理</h2>
        <p>覆盖临时事项、安全隐患、工作总结、统计分析、态势研判和数据上报等常态化工作</p>
      </div>
      <div class="head-actions">
        <el-button type="primary" icon="el-icon-plus" v-hasPermi="['rail:general:add']" @click="openItemDialog()">登记事项</el-button>
        <el-button type="success" icon="el-icon-document-add" v-hasPermi="['rail:general:report']" @click="openReportDialog()">新增报表</el-button>
      </div>
    </header>

    <section class="stat-cards">
      <button type="button" class="stat-card" @click="filterItemStatus('')">
        <span class="stat-num">{{ itemTotal }}</span><span class="stat-label">事项总数</span>
      </button>
      <button type="button" class="stat-card" @click="filterItemType('hazard')">
        <span class="stat-num">{{ countByType('hazard') }}</span><span class="stat-label">安全隐患</span>
      </button>
      <button type="button" class="stat-card" @click="filterItemStatus('submitted')">
        <span class="stat-num">{{ countByStatus('submitted') }}</span><span class="stat-label">待审核</span>
      </button>
      <button type="button" class="stat-card" @click="filterItemStatus('closed')">
        <span class="stat-num">{{ countByStatus('closed') }}</span><span class="stat-label">已闭环</span>
      </button>
      <button type="button" class="stat-card" @click="activeTab = 'reports'">
        <span class="stat-num">{{ reportTotal }}</span><span class="stat-label">总结报表</span>
      </button>
    </section>

    <el-tabs v-model="activeTab" class="general-tabs">
      <el-tab-pane label="事项台账" name="items">
        <section class="panel filter-panel">
          <el-form :model="itemQuery" inline size="small" @submit.native.prevent>
            <el-form-item label="事项类型">
              <el-select v-model="itemQuery.itemType" clearable placeholder="全部类型" style="width: 160px">
                <el-option v-for="item in itemTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="itemQuery.status" clearable placeholder="全部状态" style="width: 140px">
                <el-option v-for="item in itemStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="关键字">
              <el-input v-model.trim="itemQuery.keyword" clearable placeholder="标题/内容/位置" @keyup.enter.native="handleItemQuery" />
            </el-form-item>
            <el-form-item label="项目">
              <el-input v-model.trim="itemQuery.projectName" clearable placeholder="关联项目" @keyup.enter.native="handleItemQuery" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="el-icon-search" @click="handleItemQuery">查询</el-button>
              <el-button icon="el-icon-refresh-left" @click="resetItemQuery">重置</el-button>
            </el-form-item>
          </el-form>
        </section>

        <section class="panel table-panel">
          <el-table v-loading="itemLoading" :data="itemList" border stripe>
            <el-table-column prop="itemCode" label="事项编号" width="170" show-overflow-tooltip />
            <el-table-column prop="itemTitle" label="事项标题" min-width="220" show-overflow-tooltip />
            <el-table-column label="类型" width="120">
              <template slot-scope="scope">{{ itemTypeText(scope.row.itemType) }}</template>
            </el-table-column>
            <el-table-column prop="projectName" label="关联项目" min-width="170" show-overflow-tooltip />
            <el-table-column prop="responsibleUser" label="责任人" width="100" />
            <el-table-column label="等级" width="90" align="center">
              <template slot-scope="scope">
                <el-tag v-if="scope.row.severityLevel" size="mini" :type="severityTag(scope.row.severityLevel)">{{ severityText(scope.row.severityLevel) }}</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="105" align="center">
              <template slot-scope="scope">
                <el-tag size="mini" :type="statusTag(scope.row.status)">{{ itemStatusText(scope.row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="dueTime" label="截止时间" width="160" />
            <el-table-column label="操作" width="335" fixed="right" align="center">
              <template slot-scope="scope">
                <el-button size="mini" type="text" icon="el-icon-view" @click="openItemDetail(scope.row)">详情</el-button>
                <el-button size="mini" type="text" icon="el-icon-edit" v-hasPermi="['rail:general:edit']" @click="openItemDialog(scope.row)">编辑</el-button>
                <el-button size="mini" type="text" icon="el-icon-top" v-hasPermi="['rail:general:submit']" @click="submitItem(scope.row)">提交</el-button>
                <el-button size="mini" type="text" icon="el-icon-check" v-hasPermi="['rail:general:review']" @click="reviewItem(scope.row)">审核</el-button>
                <el-button size="mini" type="text" icon="el-icon-circle-check" v-hasPermi="['rail:general:close']" @click="closeItem(scope.row)">闭环</el-button>
                <el-button size="mini" type="text" class="danger-link" v-hasPermi="['rail:general:remove']" @click="removeItem(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <pagination v-show="itemTotal > 0" :total="itemTotal" :page.sync="itemQuery.pageNum" :limit.sync="itemQuery.pageSize" @pagination="loadItems" />
        </section>
      </el-tab-pane>

      <el-tab-pane label="总结报表" name="reports">
        <section class="panel filter-panel">
          <el-form :model="reportQuery" inline size="small" @submit.native.prevent>
            <el-form-item label="报表类型">
              <el-select v-model="reportQuery.reportType" clearable placeholder="全部类型" style="width: 170px">
                <el-option v-for="item in reportTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="reportQuery.status" clearable placeholder="全部状态" style="width: 140px">
                <el-option v-for="item in reportStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="周期">
              <el-input v-model.trim="reportQuery.reportPeriod" clearable placeholder="如 2026-08" @keyup.enter.native="handleReportQuery" />
            </el-form-item>
            <el-form-item label="关键字">
              <el-input v-model.trim="reportQuery.keyword" clearable placeholder="标题/正文" @keyup.enter.native="handleReportQuery" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="el-icon-search" @click="handleReportQuery">查询</el-button>
              <el-button icon="el-icon-refresh-left" @click="resetReportQuery">重置</el-button>
            </el-form-item>
          </el-form>
        </section>

        <section class="panel table-panel">
          <el-table v-loading="reportLoading" :data="reportList" border stripe>
            <el-table-column prop="reportCode" label="记录编号" width="170" show-overflow-tooltip />
            <el-table-column prop="reportTitle" label="标题" min-width="230" show-overflow-tooltip />
            <el-table-column label="类型" width="130">
              <template slot-scope="scope">{{ reportTypeText(scope.row.reportType) }}</template>
            </el-table-column>
            <el-table-column prop="reportPeriod" label="周期" width="110" />
            <el-table-column prop="submitUnit" label="上报单位" min-width="150" show-overflow-tooltip />
            <el-table-column label="状态" width="105" align="center">
              <template slot-scope="scope">
                <el-tag size="mini" :type="statusTag(scope.row.status)">{{ reportStatusText(scope.row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="updateTime" label="更新时间" width="160" />
            <el-table-column label="操作" width="350" fixed="right" align="center">
              <template slot-scope="scope">
                <el-button size="mini" type="text" icon="el-icon-view" @click="openReportDetail(scope.row)">详情</el-button>
                <el-button size="mini" type="text" icon="el-icon-edit" v-hasPermi="['rail:general:edit']" @click="openReportDialog(scope.row)">编辑</el-button>
                <el-button size="mini" type="text" icon="el-icon-top" v-hasPermi="['rail:general:submit']" @click="submitReport(scope.row)">提交</el-button>
                <el-button size="mini" type="text" icon="el-icon-check" v-hasPermi="['rail:general:review']" @click="reviewReport(scope.row)">审核</el-button>
                <el-button size="mini" type="text" icon="el-icon-upload2" v-hasPermi="['rail:general:report']" @click="publishReport(scope.row)">上报</el-button>
                <el-button size="mini" type="text" class="danger-link" v-hasPermi="['rail:general:remove']" @click="removeReport(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <pagination v-show="reportTotal > 0" :total="reportTotal" :page.sync="reportQuery.pageNum" :limit.sync="reportQuery.pageSize" @pagination="loadReports" />
        </section>
      </el-tab-pane>
    </el-tabs>

    <el-drawer :visible.sync="detailVisible" size="58%" custom-class="general-drawer" :with-header="false">
      <div v-if="detailTitle" class="drawer-body">
        <div class="drawer-head">
          <div>
            <h3>{{ detailTitle }}</h3>
            <p>{{ detailSubtitle }}</p>
          </div>
          <el-tag :type="statusTag(detail.status)">{{ activeDetailType === 'item' ? itemStatusText(detail.status) : reportStatusText(detail.status) }}</el-tag>
        </div>
        <el-descriptions :column="2" border size="small">
          <template v-if="activeDetailType === 'item'">
            <el-descriptions-item label="事项编号">{{ detail.itemCode || '-' }}</el-descriptions-item>
            <el-descriptions-item label="事项类型">{{ itemTypeText(detail.itemType) }}</el-descriptions-item>
            <el-descriptions-item label="关联项目">{{ detail.projectName || '-' }}</el-descriptions-item>
            <el-descriptions-item label="线路">{{ detail.lineName || '-' }}</el-descriptions-item>
            <el-descriptions-item label="位置" :span="2">{{ detail.locationDesc || '-' }}</el-descriptions-item>
            <el-descriptions-item label="事项内容" :span="2">{{ detail.itemContent || '-' }}</el-descriptions-item>
            <el-descriptions-item label="责任单位">{{ detail.responsibleUnit || '-' }}</el-descriptions-item>
            <el-descriptions-item label="责任人">{{ detail.responsibleUser || '-' }}</el-descriptions-item>
            <el-descriptions-item label="审核意见" :span="2">{{ detail.reviewOpinion || '-' }}</el-descriptions-item>
            <el-descriptions-item label="闭环说明" :span="2">{{ detail.closeRemark || '-' }}</el-descriptions-item>
          </template>
          <template v-else>
            <el-descriptions-item label="记录编号">{{ detail.reportCode || '-' }}</el-descriptions-item>
            <el-descriptions-item label="报表类型">{{ reportTypeText(detail.reportType) }}</el-descriptions-item>
            <el-descriptions-item label="周期">{{ detail.reportPeriod || '-' }}</el-descriptions-item>
            <el-descriptions-item label="上报单位">{{ detail.submitUnit || '-' }}</el-descriptions-item>
            <el-descriptions-item label="接收单位">{{ detail.receiveUnit || '-' }}</el-descriptions-item>
            <el-descriptions-item label="审核意见">{{ detail.reviewOpinion || '-' }}</el-descriptions-item>
            <el-descriptions-item label="正文" :span="2">{{ detail.summaryContent || '-' }}</el-descriptions-item>
          </template>
        </el-descriptions>

        <section class="detail-section">
          <div class="section-head">
            <h4>附件材料</h4>
            <el-upload
              v-hasPermi="['rail:general:upload']"
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="uploadAttachment"
            >
              <el-button size="mini" icon="el-icon-paperclip">上传附件</el-button>
            </el-upload>
          </div>
          <el-table :data="detail.attachments || []" size="small" border>
            <el-table-column prop="fileName" label="文件名称" min-width="220" show-overflow-tooltip />
            <el-table-column label="大小" width="100">
              <template slot-scope="scope">{{ formatSize(scope.row.fileSize) }}</template>
            </el-table-column>
            <el-table-column prop="createTime" label="上传时间" width="160" />
            <el-table-column label="操作" width="120">
              <template slot-scope="scope">
                <el-button type="text" size="mini" @click="downloadAttachment(scope.row)">下载</el-button>
                <el-button type="text" size="mini" class="danger-link" v-hasPermi="['rail:general:upload']" @click="removeAttachment(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="detail-section">
          <h4>操作留痕</h4>
          <el-timeline v-if="detail.logs && detail.logs.length">
            <el-timeline-item v-for="log in detail.logs" :key="log.logId" :timestamp="log.createTime">
              <div class="log-title">{{ log.actionName }}</div>
              <div class="muted">{{ log.operatorName || '系统' }} {{ log.opinion || '' }}</div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无操作记录" />
        </section>
      </div>
    </el-drawer>

    <el-dialog :title="itemForm.itemId ? '编辑事项' : '登记事项'" :visible.sync="itemDialogVisible" width="760px" append-to-body>
      <el-form ref="itemFormRef" :model="itemForm" :rules="itemRules" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="事项类型" prop="itemType">
              <el-select v-model="itemForm.itemType" style="width: 100%">
                <el-option v-for="item in itemTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="严重程度">
              <el-select v-model="itemForm.severityLevel" clearable style="width: 100%">
                <el-option label="高" value="high" />
                <el-option label="中" value="medium" />
                <el-option label="低" value="low" />
                <el-option label="提示" value="tip" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="事项标题" prop="itemTitle">
              <el-input v-model="itemForm.itemTitle" maxlength="200" />
            </el-form-item>
          </el-col>
          <el-col :span="12"><el-form-item label="关联项目"><el-input v-model="itemForm.projectName" maxlength="200" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="线路"><el-input v-model="itemForm.lineName" maxlength="100" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="位置描述"><el-input v-model="itemForm.locationDesc" maxlength="500" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="责任单位"><el-input v-model="itemForm.responsibleUnit" maxlength="200" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="责任人"><el-input v-model="itemForm.responsibleUser" maxlength="80" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="发生时间"><el-date-picker v-model="itemForm.occurTime" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="完成期限"><el-date-picker v-model="itemForm.dueTime" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" style="width: 100%" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="事项内容"><el-input v-model="itemForm.itemContent" type="textarea" :rows="5" maxlength="8000" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注"><el-input v-model="itemForm.remark" type="textarea" :rows="2" maxlength="500" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <span slot="footer">
        <el-button @click="itemDialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="saving" @click="saveItem">保 存</el-button>
      </span>
    </el-dialog>

    <el-dialog :title="reportForm.reportId ? '编辑报表' : '新增报表'" :visible.sync="reportDialogVisible" width="760px" append-to-body>
      <el-form ref="reportFormRef" :model="reportForm" :rules="reportRules" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="报表类型" prop="reportType">
              <el-select v-model="reportForm.reportType" style="width: 100%">
                <el-option v-for="item in reportTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12"><el-form-item label="周期"><el-input v-model="reportForm.reportPeriod" placeholder="如 2026-08 / 2026" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="标题" prop="reportTitle"><el-input v-model="reportForm.reportTitle" maxlength="200" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="上报单位"><el-input v-model="reportForm.submitUnit" maxlength="200" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="接收单位"><el-input v-model="reportForm.receiveUnit" maxlength="200" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="正文"><el-input v-model="reportForm.summaryContent" type="textarea" :rows="8" maxlength="20000" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注"><el-input v-model="reportForm.remark" type="textarea" :rows="2" maxlength="500" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <span slot="footer">
        <el-button @click="reportDialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="saving" @click="saveReport">保 存</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import {
  archiveGeneralItem,
  createGeneralItem,
  createGeneralReport,
  deleteGeneralAttachment,
  deleteGeneralItem,
  deleteGeneralReport,
  getGeneralItem,
  getGeneralReport,
  getGeneralStatistics,
  listGeneralItems,
  listGeneralReports,
  publishGeneralReport,
  reviewGeneralItem,
  reviewGeneralReport,
  closeGeneralItem,
  submitGeneralItem,
  submitGeneralReport,
  updateGeneralItem,
  updateGeneralReport,
  uploadItemAttachment,
  uploadReportAttachment
} from '@/api/rail/general'

export default {
  name: 'RailGeneral',
  data() {
    return {
      activeTab: 'items',
      itemLoading: false,
      reportLoading: false,
      saving: false,
      itemList: [],
      reportList: [],
      itemTotal: 0,
      reportTotal: 0,
      statistics: { items: [], reports: [] },
      itemQuery: { pageNum: 1, pageSize: 10, itemType: '', status: '', keyword: '', projectName: '' },
      reportQuery: { pageNum: 1, pageSize: 10, reportType: '', status: '', reportPeriod: '', keyword: '' },
      itemDialogVisible: false,
      reportDialogVisible: false,
      detailVisible: false,
      activeDetailType: 'item',
      detail: {},
      itemForm: {},
      reportForm: {},
      itemTypeOptions: [
        { label: '临时事项', value: 'temporary' },
        { label: '安全隐患', value: 'hazard' },
        { label: '月度总结', value: 'monthly_summary' },
        { label: '年度总结', value: 'annual_summary' },
        { label: '数据上报', value: 'data_report' },
        { label: '其他', value: 'other' }
      ],
      reportTypeOptions: [
        { label: '月度总结', value: 'monthly_summary' },
        { label: '年度总结', value: 'annual_summary' },
        { label: '统计报表', value: 'statistics' },
        { label: '态势分析', value: 'situation' },
        { label: '数据上报', value: 'data_report' },
        { label: '其他', value: 'other' }
      ],
      itemStatusOptions: [
        { label: '草稿', value: 'draft' },
        { label: '已提交', value: 'submitted' },
        { label: '处理中', value: 'processing' },
        { label: '待复核', value: 'pending_review' },
        { label: '已完成', value: 'completed' },
        { label: '已闭环', value: 'closed' },
        { label: '已归档', value: 'archived' },
        { label: '已退回', value: 'returned' }
      ],
      reportStatusOptions: [
        { label: '草稿', value: 'draft' },
        { label: '已提交', value: 'submitted' },
        { label: '已审核', value: 'reviewed' },
        { label: '已发布', value: 'published' },
        { label: '已上报', value: 'reported' },
        { label: '已归档', value: 'archived' },
        { label: '已退回', value: 'returned' }
      ],
      itemRules: {
        itemType: [{ required: true, message: '请选择事项类型', trigger: 'change' }],
        itemTitle: [{ required: true, message: '请输入事项标题', trigger: 'blur' }]
      },
      reportRules: {
        reportType: [{ required: true, message: '请选择报表类型', trigger: 'change' }],
        reportTitle: [{ required: true, message: '请输入标题', trigger: 'blur' }]
      }
    }
  },
  computed: {
    detailTitle() {
      return this.activeDetailType === 'item' ? this.detail.itemTitle : this.detail.reportTitle
    },
    detailSubtitle() {
      if (this.activeDetailType === 'item') {
        return `${this.itemTypeText(this.detail.itemType)} · ${this.detail.projectName || '未关联项目'} · ${this.detail.createTime || ''}`
      }
      return `${this.reportTypeText(this.detail.reportType)} · ${this.detail.reportPeriod || '未填写周期'} · ${this.detail.createTime || ''}`
    }
  },
  created() {
    this.loadItems()
    this.loadReports()
    this.loadStatistics()
  },
  methods: {
    loadItems() {
      this.itemLoading = true
      return listGeneralItems(this.itemQuery).then(res => {
        this.itemList = res.rows || []
        this.itemTotal = res.total || 0
      }).finally(() => {
        this.itemLoading = false
      })
    },
    loadReports() {
      this.reportLoading = true
      return listGeneralReports(this.reportQuery).then(res => {
        this.reportList = res.rows || []
        this.reportTotal = res.total || 0
      }).finally(() => {
        this.reportLoading = false
      })
    },
    loadStatistics() {
      getGeneralStatistics({}).then(res => {
        this.statistics = res.data || { items: [], reports: [] }
      })
    },
    handleItemQuery() {
      this.itemQuery.pageNum = 1
      this.loadItems()
    },
    resetItemQuery() {
      this.itemQuery = { pageNum: 1, pageSize: 10, itemType: '', status: '', keyword: '', projectName: '' }
      this.loadItems()
    },
    handleReportQuery() {
      this.reportQuery.pageNum = 1
      this.loadReports()
    },
    resetReportQuery() {
      this.reportQuery = { pageNum: 1, pageSize: 10, reportType: '', status: '', reportPeriod: '', keyword: '' }
      this.loadReports()
    },
    filterItemType(type) {
      this.activeTab = 'items'
      this.itemQuery.itemType = type
      this.handleItemQuery()
    },
    filterItemStatus(status) {
      this.activeTab = 'items'
      this.itemQuery.status = status
      this.handleItemQuery()
    },
    openItemDialog(row) {
      this.itemForm = row ? { ...row } : { itemType: 'temporary', priority: 'normal', sourceChannel: 'manual', status: 'draft' }
      this.itemDialogVisible = true
      this.$nextTick(() => this.$refs.itemFormRef && this.$refs.itemFormRef.clearValidate())
    },
    saveItem() {
      this.$refs.itemFormRef.validate(valid => {
        if (!valid) return
        this.saving = true
        const request = this.itemForm.itemId ? updateGeneralItem(this.itemForm) : createGeneralItem(this.itemForm)
        request.then(() => {
          this.$modal.msgSuccess('保存成功')
          this.itemDialogVisible = false
          this.loadItems()
          this.loadStatistics()
        }).finally(() => {
          this.saving = false
        })
      })
    },
    removeItem(row) {
      this.$modal.confirm(`确认删除事项“${row.itemTitle}”？`).then(() => deleteGeneralItem(row.itemId)).then(() => {
        this.$modal.msgSuccess('删除成功')
        this.loadItems()
        this.loadStatistics()
      })
    },
    submitItem(row) {
      this.$prompt('可填写提交说明', '提交事项', { inputType: 'textarea', inputPlaceholder: '非必填', confirmButtonText: '提交', cancelButtonText: '取消' }).then(({ value }) => {
        return submitGeneralItem(row.itemId, { opinion: value || '' })
      }).then(() => {
        this.$modal.msgSuccess('提交成功')
        this.loadItems()
      })
    },
    reviewItem(row) {
      this.$prompt('填写审核意见；留空表示通过', '审核事项', { inputType: 'textarea', confirmButtonText: '通过', cancelButtonText: '退回', distinguishCancelAndClose: true }).then(({ value }) => {
        return reviewGeneralItem(row.itemId, { status: 'processing', reviewOpinion: value || '审核通过' })
      }).catch(action => {
        if (action === 'cancel') {
          return reviewGeneralItem(row.itemId, { status: 'returned', reviewOpinion: '退回修改' }).then(() => this.$modal.msgSuccess('已退回'))
        }
      }).then(() => {
        this.loadItems()
      })
    },
    closeItem(row) {
      this.$prompt('填写闭环说明', '事项闭环', { inputType: 'textarea', inputPlaceholder: '已完成并闭环', confirmButtonText: '闭环', cancelButtonText: '取消' }).then(({ value }) => {
        return closeGeneralItem(row.itemId, { closeRemark: value || '已完成并闭环' })
      }).then(() => {
        this.$modal.msgSuccess('已闭环')
        this.loadItems()
        this.loadStatistics()
      })
    },
    openItemDetail(row) {
      this.activeDetailType = 'item'
      this.detailVisible = true
      getGeneralItem(row.itemId).then(res => {
        this.detail = res.data || {}
      })
    },
    openReportDialog(row) {
      this.reportForm = row ? { ...row } : { reportType: 'monthly_summary', status: 'draft' }
      this.reportDialogVisible = true
      this.$nextTick(() => this.$refs.reportFormRef && this.$refs.reportFormRef.clearValidate())
    },
    saveReport() {
      this.$refs.reportFormRef.validate(valid => {
        if (!valid) return
        this.saving = true
        const request = this.reportForm.reportId ? updateGeneralReport(this.reportForm) : createGeneralReport(this.reportForm)
        request.then(() => {
          this.$modal.msgSuccess('保存成功')
          this.reportDialogVisible = false
          this.loadReports()
          this.loadStatistics()
        }).finally(() => {
          this.saving = false
        })
      })
    },
    removeReport(row) {
      this.$modal.confirm(`确认删除报表“${row.reportTitle}”？`).then(() => deleteGeneralReport(row.reportId)).then(() => {
        this.$modal.msgSuccess('删除成功')
        this.loadReports()
        this.loadStatistics()
      })
    },
    submitReport(row) {
      submitGeneralReport(row.reportId, {}).then(() => {
        this.$modal.msgSuccess('提交成功')
        this.loadReports()
      })
    },
    reviewReport(row) {
      this.$prompt('填写审核意见；留空表示通过', '审核报表', { inputType: 'textarea', confirmButtonText: '通过', cancelButtonText: '退回', distinguishCancelAndClose: true }).then(({ value }) => {
        return reviewGeneralReport(row.reportId, { status: 'reviewed', reviewOpinion: value || '审核通过' })
      }).catch(action => {
        if (action === 'cancel') {
          return reviewGeneralReport(row.reportId, { status: 'returned', reviewOpinion: '退回修改' }).then(() => this.$modal.msgSuccess('已退回'))
        }
      }).then(() => {
        this.loadReports()
      })
    },
    publishReport(row) {
      publishGeneralReport(row.reportId, { status: 'reported', opinion: '数据已上报' }).then(() => {
        this.$modal.msgSuccess('已上报')
        this.loadReports()
      })
    },
    openReportDetail(row) {
      this.activeDetailType = 'report'
      this.detailVisible = true
      getGeneralReport(row.reportId).then(res => {
        this.detail = res.data || {}
      })
    },
    uploadAttachment(file) {
      const form = new FormData()
      form.append('file', file.raw)
      form.append('fileType', 'attachment')
      const request = this.activeDetailType === 'item'
        ? uploadItemAttachment(this.detail.itemId, form)
        : uploadReportAttachment(this.detail.reportId, form)
      request.then(() => {
        this.$modal.msgSuccess('上传成功')
        if (this.activeDetailType === 'item') this.openItemDetail(this.detail)
        else this.openReportDetail(this.detail)
      })
    },
    downloadAttachment(row) {
      this.download(`/rail/general/attachments/${row.attachmentId}/download`, {}, row.fileName)
    },
    removeAttachment(row) {
      this.$modal.confirm(`确认删除附件“${row.fileName}”？`).then(() => deleteGeneralAttachment(row.attachmentId)).then(() => {
        this.$modal.msgSuccess('删除成功')
        if (this.activeDetailType === 'item') this.openItemDetail(this.detail)
        else this.openReportDetail(this.detail)
      })
    },
    countByType(type) {
      return (this.statistics.items || []).filter(item => item.itemType === type).reduce((sum, item) => sum + Number(item.total || 0), 0)
    },
    countByStatus(status) {
      return (this.statistics.items || []).filter(item => item.status === status).reduce((sum, item) => sum + Number(item.total || 0), 0)
    },
    itemTypeText(value) {
      const item = this.itemTypeOptions.find(i => i.value === value)
      return item ? item.label : value || '-'
    },
    reportTypeText(value) {
      const item = this.reportTypeOptions.find(i => i.value === value)
      return item ? item.label : value || '-'
    },
    itemStatusText(value) {
      const item = this.itemStatusOptions.find(i => i.value === value)
      return item ? item.label : value || '-'
    },
    reportStatusText(value) {
      const item = this.reportStatusOptions.find(i => i.value === value)
      return item ? item.label : value || '-'
    },
    severityText(value) {
      const map = { high: '高', medium: '中', low: '低', tip: '提示' }
      return map[value] || value
    },
    severityTag(value) {
      const map = { high: 'danger', medium: 'warning', low: 'success', tip: 'info' }
      return map[value] || 'info'
    },
    statusTag(status) {
      if (['archived', 'closed', 'published', 'reported', 'reviewed', 'completed'].includes(status)) return 'success'
      if (['submitted', 'processing', 'pending_review'].includes(status)) return 'warning'
      if (status === 'returned') return 'danger'
      return 'info'
    },
    formatSize(size) {
      const value = Number(size || 0)
      if (!value) return '-'
      if (value < 1024) return `${value}B`
      if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)}KB`
      return `${(value / 1024 / 1024).toFixed(1)}MB`
    }
  }
}
</script>

<style lang="scss" scoped>
.general-page {
  background: #f5f7f9;
  min-height: calc(100vh - 84px);
}
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  h2 { margin: 0 0 6px; font-size: 24px; color: #1f2d3d; }
  p { margin: 0; color: #7a8793; }
}
.head-actions {
  display: flex;
  gap: 10px;
}
.stat-cards {
  display: grid;
  grid-template-columns: repeat(5, minmax(120px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.stat-card {
  border: 1px solid #e4e7ed;
  background: #fff;
  border-radius: 6px;
  padding: 16px 18px;
  text-align: left;
  cursor: pointer;
  .stat-num { display: block; font-size: 26px; font-weight: 700; color: #1f2d3d; }
  .stat-label { display: block; margin-top: 6px; color: #7a8793; }
}
.general-tabs {
  ::v-deep .el-tabs__header { margin-bottom: 12px; }
}
.panel {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
}
.filter-panel { padding-bottom: 0; }
.danger-link { color: #f56c6c; }
.drawer-body { padding: 22px 28px 32px; }
.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  h3 { margin: 0 0 8px; font-size: 22px; color: #1f2d3d; }
  p { margin: 0; color: #7a8793; }
}
.detail-section {
  margin-top: 18px;
  h4 { margin: 0 0 10px; font-size: 16px; color: #1f2d3d; }
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  h4 { margin: 0; }
}
.log-title { font-weight: 600; color: #1f2d3d; }
.muted { color: #7a8793; font-size: 13px; }
@media (max-width: 960px) {
  .page-head { align-items: flex-start; flex-direction: column; }
  .stat-cards { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
}
</style>
