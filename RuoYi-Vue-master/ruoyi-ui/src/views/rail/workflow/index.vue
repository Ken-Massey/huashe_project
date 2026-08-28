<template>
  <div class="workflow-page">
    <div class="workflow-header">
      <div>
        <h1>审核流转</h1>
        <p>集中查看待办流程、审核状态和流转记录，处理后可回到案例审核继续修改。</p>
      </div>
      <el-button icon="el-icon-refresh" @click="loadData">刷新</el-button>
    </div>

    <div class="workflow-panel">
      <el-tabs v-model="activeTab" @tab-click="handleTabChange">
        <el-tab-pane label="我的待办" name="todo" />
        <el-tab-pane label="全部流程" name="all" />
      </el-tabs>

      <el-form :model="queryParams" class="query-form" size="small" inline>
        <el-form-item label="项目名称">
          <el-input
            v-model="queryParams.projectName"
            clearable
            placeholder="输入项目名称"
            @keyup.enter.native="handleQuery"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.workflowStatus" clearable placeholder="全部状态">
            <el-option
              v-for="item in statusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="handleQuery">查询</el-button>
          <el-button icon="el-icon-refresh-left" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="workflowList" class="workflow-table">
        <el-table-column label="项目名称" min-width="220">
          <template slot-scope="scope">
            <div class="project-name">{{ scope.row.projectName || '未命名项目' }}</div>
            <div class="project-meta">
              {{ scope.row.stageName || '未填写阶段' }}
              <span v-if="scope.row.auditVersion">第 {{ scope.row.auditVersion }} 版</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="流程状态" width="120">
          <template slot-scope="scope">
            <el-tag :type="statusTag(scope.row.workflowStatus)" size="mini">
              {{ statusText(scope.row.workflowStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前节点" min-width="140">
          <template slot-scope="scope">
            <span>{{ scope.row.currentNodeName || '已结束' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="当前处理人" min-width="130">
          <template slot-scope="scope">
            <span>{{ scope.row.currentAssignee || '按角色分配' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100">
          <template slot-scope="scope">
            <el-tag :type="riskTag(scope.row.latestRiskLevel)" size="mini">
              {{ scope.row.latestRiskLevel || '未评估' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="摘要" min-width="260" show-overflow-tooltip>
          <template slot-scope="scope">
            {{ scope.row.latestSummary || '暂无综合评价' }}
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="160" prop="updateTime" />
        <el-table-column label="操作" width="300" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" icon="el-icon-view" @click="openDetail(scope.row)">详情</el-button>
            <el-button type="text" icon="el-icon-position" @click="openAudit(scope.row)">进入审核</el-button>
            <el-button
              v-if="canApprove(scope.row)"
              type="text"
              icon="el-icon-check"
              @click="openAction(scope.row, 'approve')"
            >{{ approveActionLabel(scope.row) }}</el-button>
            <el-button
              v-if="canReturn(scope.row)"
              type="text"
              icon="el-icon-back"
              @click="openAction(scope.row, 'return')"
            >退回</el-button>
            <el-button
              v-if="canArchive(scope.row)"
              type="text"
              icon="el-icon-folder-checked"
              @click="openAction(scope.row, 'archive')"
            >归档</el-button>
          </template>
        </el-table-column>
      </el-table>

      <pagination
        v-show="total > 0"
        :total="total"
        :page.sync="queryParams.pageNum"
        :limit.sync="queryParams.pageSize"
        @pagination="loadData"
      />
    </div>

    <el-dialog :title="detailTitle" :visible.sync="detailVisible" width="860px" append-to-body>
      <div v-loading="detailLoading" class="detail-body">
        <div v-if="detail.workflowId" class="detail-summary">
          <div>
            <strong>{{ detail.projectName || '未命名项目' }}</strong>
            <span>{{ detail.stageName || '未填写阶段' }}</span>
          </div>
          <el-tag :type="statusTag(detail.workflowStatus)" size="mini">
            {{ statusText(detail.workflowStatus) }}
          </el-tag>
        </div>

        <el-tabs v-model="detailTab">
          <el-tab-pane label="流转记录" name="logs">
            <el-timeline v-if="logs.length">
              <el-timeline-item
                v-for="log in logs"
                :key="log.logId"
                :timestamp="log.createTime"
                placement="top"
              >
                <div class="log-title">{{ log.actionName || log.actionCode }}</div>
                <div class="log-meta">
                  {{ log.operatorName || '系统' }}
                  <span v-if="log.fromNodeCode || log.toNodeCode">
                    {{ log.fromNodeCode || '开始' }} -> {{ log.toNodeCode || '结束' }}
                  </span>
                </div>
                <p v-if="log.opinion" class="log-opinion">{{ log.opinion }}</p>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无流转记录" />
          </el-tab-pane>

          <el-tab-pane label="任务记录" name="tasks">
            <el-table :data="tasks" size="small">
              <el-table-column label="节点" prop="nodeName" min-width="120" />
              <el-table-column label="处理人" prop="assigneeName" min-width="120" />
              <el-table-column label="状态" width="100">
                <template slot-scope="scope">
                  <el-tag size="mini" :type="taskTag(scope.row.taskStatus)">
                    {{ taskText(scope.row.taskStatus) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="接收时间" prop="receivedTime" width="160" />
              <el-table-column label="处理时间" prop="handledTime" width="160" />
              <el-table-column label="意见" prop="handleOpinion" min-width="180" show-overflow-tooltip />
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="版本快照" name="snapshots">
            <el-table :data="snapshots" size="small">
              <el-table-column label="版本" width="90">
                <template slot-scope="scope">第 {{ scope.row.auditVersion || 1 }} 版</template>
              </el-table-column>
              <el-table-column label="类型" width="100" prop="opinionType" />
              <el-table-column label="标题" prop="title" min-width="180" />
              <el-table-column label="内容" prop="opinionContent" min-width="260" show-overflow-tooltip />
              <el-table-column label="时间" prop="createTime" width="160" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <el-dialog :title="actionTitle" :visible.sync="actionVisible" width="520px" append-to-body>
      <el-form ref="actionForm" :model="actionForm" label-width="84px">
        <el-form-item v-if="actionType === 'approve'" label="下一处理人">
          <el-input v-model="actionForm.assigneeName" clearable placeholder="进入下一节点时可填写处理人姓名" />
        </el-form-item>
        <el-form-item label="处理意见">
          <el-input
            v-model="actionForm.opinion"
            type="textarea"
            :rows="4"
            placeholder="填写本次流转意见"
          />
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="actionVisible = false">取消</el-button>
        <el-button type="primary" :loading="actionLoading" @click="submitAction">确认</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import {
  listAuditWorkflow,
  listAuditTodo,
  getAuditWorkflow,
  approveAuditWorkflow,
  returnAuditWorkflow,
  archiveAuditWorkflow
} from '@/api/rail/workflow'
import { checkPermi } from '@/utils/permission'

export default {
  name: 'RailWorkflow',
  data() {
    return {
      activeTab: 'todo',
      loading: false,
      workflowList: [],
      total: 0,
      queryParams: {
        pageNum: 1,
        pageSize: 10,
        projectName: '',
        workflowStatus: ''
      },
      statusOptions: [
        { label: '审核中', value: 'REVIEW' },
        { label: '终审中', value: 'FINAL' },
        { label: '已退回', value: 'RETURNED' },
        { label: '已通过', value: 'APPROVED' },
        { label: '已归档', value: 'ARCHIVED' }
      ],
      detailVisible: false,
      detailLoading: false,
      detailTab: 'logs',
      detail: {},
      logs: [],
      tasks: [],
      snapshots: [],
      actionVisible: false,
      actionLoading: false,
      actionType: '',
      currentWorkflow: null,
      actionForm: {
        assigneeName: '',
        opinion: ''
      }
    }
  },
  computed: {
    detailTitle() {
      return this.detail.workflowId ? `流程详情 #${this.detail.workflowId}` : '流程详情'
    },
    actionTitle() {
      if (this.actionType === 'approve') return this.approveActionLabel(this.currentWorkflow)
      const titles = {
        return: '退回修改',
        archive: '归档流程'
      }
      return titles[this.actionType] || '流程处理'
    }
  },
  created() {
    this.loadData()
  },
  methods: {
    loadData() {
      this.loading = true
      const params = { ...this.queryParams }
      const request = this.activeTab === 'todo' ? listAuditTodo : listAuditWorkflow
      request(params).then(response => {
        this.workflowList = Array.isArray(response.rows) ? response.rows : []
        this.total = Number(response.total || this.workflowList.length || 0)
      }).finally(() => {
        this.loading = false
      })
    },
    handleTabChange() {
      this.queryParams.pageNum = 1
      this.loadData()
    },
    handleQuery() {
      this.queryParams.pageNum = 1
      this.loadData()
    },
    resetQuery() {
      this.queryParams.projectName = ''
      this.queryParams.workflowStatus = ''
      this.handleQuery()
    },
    openAudit(row) {
      const query = {}
      if (row.workflowId) query.workflowId = row.workflowId
      if (row.sessionId) query.sessionId = row.sessionId
      if (row.projectId) query.projectId = row.projectId
      if (row.stageId) query.stageId = row.stageId
      this.$router.push({ path: '/rail/audit', query })
    },
    openDetail(row) {
      this.detailVisible = true
      this.detailLoading = true
      this.detail = {}
      this.logs = []
      this.tasks = []
      this.snapshots = []
      getAuditWorkflow(row.workflowId).then(response => {
        const data = response.data || {}
        this.detail = data.workflow || data || {}
        this.logs = Array.isArray(response.logs) ? response.logs : (Array.isArray(data.logs) ? data.logs : [])
        this.tasks = Array.isArray(response.tasks) ? response.tasks : (Array.isArray(data.tasks) ? data.tasks : [])
        this.snapshots = Array.isArray(response.snapshots) ? response.snapshots : (Array.isArray(data.snapshots) ? data.snapshots : [])
      }).finally(() => {
        this.detailLoading = false
      })
    },
    openAction(row, type) {
      this.currentWorkflow = row
      this.actionType = type
      this.actionForm = {
        assigneeName: '',
        opinion: ''
      }
      this.actionVisible = true
    },
    submitAction() {
      if (!this.currentWorkflow || !this.currentWorkflow.workflowId) {
        return
      }
      const payload = {
        workflowId: this.currentWorkflow.workflowId,
        assigneeName: this.actionForm.assigneeName,
        opinion: this.actionForm.opinion
      }
      const requestMap = {
        approve: approveAuditWorkflow,
        return: returnAuditWorkflow,
        archive: archiveAuditWorkflow
      }
      const request = requestMap[this.actionType]
      if (!request) return
      const successText = this.actionTitle
      this.actionLoading = true
      request(payload).then(() => {
        this.$message.success(`${successText}成功`)
        this.actionVisible = false
        this.loadData()
      }).finally(() => {
        this.actionLoading = false
      })
    },
    workflowStatusCode(row) {
      return row && (row.workflowStatus || row.workflow_status) || ''
    },
    workflowNodeCode(row) {
      return row && (row.currentNodeCode || row.current_node_code) || this.workflowStatusCode(row)
    },
    isReviewNode(row) {
      const code = this.workflowNodeCode(row)
      const status = this.workflowStatusCode(row)
      return code === 'REVIEW' || status === 'REVIEW'
    },
    isFinalNode(row) {
      const code = this.workflowNodeCode(row)
      const status = this.workflowStatusCode(row)
      return code === 'FINAL' || status === 'FINAL'
    },
    approveActionLabel(row) {
      return this.isFinalNode(row) ? '终审通过' : '提交终审'
    },
    canApprove(row) {
      if (this.isReviewNode(row)) return checkPermi(['rail:audit:workflow:approve', 'rail:audit:workflow:submitFinal'])
      if (this.isFinalNode(row)) return checkPermi(['rail:audit:workflow:final', 'rail:audit:workflow:approve'])
      return false
    },
    canReturn(row) {
      return (this.isReviewNode(row) || this.isFinalNode(row)) && checkPermi(['rail:audit:workflow:return'])
    },
    canArchive(row) {
      return this.workflowStatusCode(row) === 'APPROVED' && checkPermi(['rail:audit:workflow:archive'])
    },
    statusText(status) {
      const map = {
        REVIEW: '审核中',
        FINAL: '终审中',
        RETURNED: '已退回',
        APPROVED: '已通过',
        ARCHIVED: '已归档'
      }
      return map[status] || '待提交'
    },
    statusTag(status) {
      const map = {
        REVIEW: 'warning',
        FINAL: 'warning',
        RETURNED: 'danger',
        APPROVED: 'success',
        ARCHIVED: 'info'
      }
      return map[status] || ''
    },
    riskTag(level) {
      if (level === '高') return 'danger'
      if (level === '中') return 'warning'
      if (level === '低') return 'success'
      return 'info'
    },
    taskText(status) {
      const map = {
        TODO: '待处理',
        PASS: '已通过',
        RETURN: '已退回',
        CANCEL: '已取消'
      }
      return map[status] || status || '未知'
    },
    taskTag(status) {
      const map = {
        TODO: 'warning',
        PASS: 'success',
        RETURN: 'danger',
        CANCEL: 'info'
      }
      return map[status] || 'info'
    }
  }
}
</script>

<style lang="scss" scoped>
.workflow-page {
  min-height: 100vh;
  padding: 28px 32px 48px;
  background: #f5f7f8;
  color: #17312d;
}

.workflow-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.workflow-header h1 {
  margin: 0 0 8px;
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0;
}

.workflow-header p {
  margin: 0;
  color: #7b8582;
  font-size: 14px;
}

.workflow-panel {
  padding: 18px 22px 22px;
  border: 1px solid #e1e8e6;
  border-radius: 8px;
  background: #fff;
}

.query-form {
  padding: 4px 0 14px;
}

.workflow-table {
  border-top: 1px solid #edf1f0;
}

.project-name {
  color: #213a36;
  font-weight: 600;
}

.project-meta {
  margin-top: 4px;
  color: #7c8985;
  font-size: 12px;
}

.project-meta span {
  margin-left: 10px;
}

.detail-body {
  min-height: 260px;
}

.detail-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  margin-bottom: 12px;
  border: 1px solid #dce8e5;
  border-radius: 8px;
  background: #f6fbf9;
}

.detail-summary strong {
  display: block;
  margin-bottom: 4px;
}

.detail-summary span {
  color: #72817d;
  font-size: 13px;
}

.log-title {
  color: #17312d;
  font-weight: 600;
}

.log-meta {
  margin-top: 4px;
  color: #78837f;
  font-size: 13px;
}

.log-meta span {
  margin-left: 12px;
}

.log-opinion {
  margin: 8px 0 0;
  color: #344541;
  line-height: 1.7;
}
</style>
