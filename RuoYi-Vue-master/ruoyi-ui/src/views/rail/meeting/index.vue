<template>
  <div class="app-container meeting-page">
    <header class="page-head">
      <div>
        <h2>会议协调管理</h2>
        <p>保护区方案评审会、协调会、专题会全过程线上留痕，问题和待办可跟踪闭环</p>
      </div>
      <el-button type="primary" icon="el-icon-plus" v-hasPermi="['rail:meeting:add']" @click="openMeetingDialog()">新建会议</el-button>
    </header>

    <section class="stat-cards">
      <button type="button" class="stat-card" @click="filterStatus('')">
        <span class="stat-num">{{ statistics.total }}</span><span class="stat-label">全部会议</span>
      </button>
      <button type="button" class="stat-card" @click="filterStatus('notified')">
        <span class="stat-num">{{ statistics.notified }}</span><span class="stat-label">已通知</span>
      </button>
      <button type="button" class="stat-card" @click="filterStatus('held')">
        <span class="stat-num">{{ statistics.held }}</span><span class="stat-label">已召开</span>
      </button>
      <button type="button" class="stat-card" @click="filterStatus('tracking')">
        <span class="stat-num">{{ statistics.tracking }}</span><span class="stat-label">待闭环</span>
      </button>
      <button type="button" class="stat-card" @click="filterStatus('archived')">
        <span class="stat-num">{{ statistics.archived }}</span><span class="stat-label">已归档</span>
      </button>
    </section>

    <section class="panel filter-panel">
      <el-form :model="queryParams" inline size="small" @submit.native.prevent>
        <el-form-item label="会议名称">
          <el-input v-model.trim="queryParams.meetingName" clearable placeholder="输入会议名称" @keyup.enter.native="handleQuery" />
        </el-form-item>
        <el-form-item label="会议类型">
          <el-select v-model="queryParams.meetingType" clearable placeholder="全部类型" style="width: 150px">
            <el-option v-for="item in meetingTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryParams.status" clearable placeholder="全部状态" style="width: 140px">
            <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-input v-model.trim="queryParams.projectName" clearable placeholder="关联项目" @keyup.enter.native="handleQuery" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="handleQuery">查询</el-button>
          <el-button icon="el-icon-refresh-left" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <section class="panel table-panel">
      <el-table v-loading="loading" :data="meetingList" border stripe>
        <el-table-column prop="meetingCode" label="会议编号" width="170" show-overflow-tooltip />
        <el-table-column prop="meetingName" label="会议名称" min-width="220" show-overflow-tooltip />
        <el-table-column label="会议类型" width="130">
          <template slot-scope="scope">{{ meetingTypeText(scope.row.meetingType) }}</template>
        </el-table-column>
        <el-table-column prop="projectName" label="关联项目" min-width="180" show-overflow-tooltip />
        <el-table-column label="会议时间" width="165">
          <template slot-scope="scope">{{ scope.row.meetingTime || '-' }}</template>
        </el-table-column>
        <el-table-column prop="meetingPlace" label="地点/链接" min-width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="110" align="center">
          <template slot-scope="scope">
            <el-tag size="small" :type="statusTag(scope.row.status)">{{ statusText(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="340" fixed="right" align="center">
          <template slot-scope="scope">
            <el-button size="mini" type="text" icon="el-icon-view" @click="openDetail(scope.row)">详情</el-button>
            <el-button size="mini" type="text" icon="el-icon-edit" v-hasPermi="['rail:meeting:edit']" @click="openMeetingDialog(scope.row)">编辑</el-button>
            <el-button size="mini" type="text" icon="el-icon-message" v-hasPermi="['rail:meeting:notify']" @click="openNotify(scope.row)">通知</el-button>
            <el-button v-if="scope.row.status !== 'held' && scope.row.status !== 'archived'" size="mini" type="text" icon="el-icon-check" v-hasPermi="['rail:meeting:edit']" @click="doMarkHeld(scope.row)">已召开</el-button>
            <el-button size="mini" type="text" icon="el-icon-folder-checked" v-hasPermi="['rail:meeting:archive']" @click="doArchive(scope.row)">归档</el-button>
            <el-button size="mini" type="text" icon="el-icon-delete" class="danger-link" v-hasPermi="['rail:meeting:remove']" @click="doDeleteMeeting(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <pagination v-show="total > 0" :total="total" :page.sync="queryParams.pageNum" :limit.sync="queryParams.pageSize" @pagination="loadMeetings" />
    </section>

    <el-dialog :title="meetingForm.meetingId ? '编辑会议' : '新建会议'" :visible.sync="meetingDialogVisible" width="760px" append-to-body>
      <el-form ref="meetingFormRef" :model="meetingForm" :rules="meetingRules" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="会议名称" prop="meetingName">
              <el-input v-model="meetingForm.meetingName" maxlength="200" placeholder="如：涉铁保护区方案评审会" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="会议类型" prop="meetingType">
              <el-select v-model="meetingForm.meetingType" placeholder="选择类型" style="width: 100%">
                <el-option v-for="item in meetingTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联项目">
              <el-input v-model="meetingForm.projectName" maxlength="200" placeholder="项目名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="会议时间">
              <el-date-picker v-model="meetingForm.meetingTime" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" placeholder="选择时间" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="会议地点">
              <el-input v-model="meetingForm.meetingPlace" maxlength="255" placeholder="线下地点" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="线上链接">
              <el-input v-model="meetingForm.onlineUrl" maxlength="500" placeholder="腾讯会议/其他链接" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="主持单位">
              <el-input v-model="meetingForm.hostUnit" maxlength="200" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="组织单位">
              <el-input v-model="meetingForm.organizeUnit" maxlength="200" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="会议主题">
              <el-input v-model="meetingForm.meetingTopic" maxlength="500" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="会议议程">
              <el-input v-model="meetingForm.agenda" type="textarea" :rows="4" maxlength="4000" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <span slot="footer">
        <el-button @click="meetingDialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="saving" @click="submitMeeting">保 存</el-button>
      </span>
    </el-dialog>

    <el-drawer :visible.sync="detailVisible" size="72%" custom-class="meeting-drawer" :with-header="false">
      <div v-if="detail.meetingId" class="drawer-body">
        <div class="drawer-head">
          <div>
            <h3>{{ detail.meetingName }}</h3>
            <p>{{ meetingTypeText(detail.meetingType) }} · {{ detail.projectName || '未关联项目' }} · {{ detail.meetingTime || '未定时间' }}</p>
          </div>
          <div class="drawer-actions">
            <el-button v-if="detail.status !== 'held' && detail.status !== 'archived'" size="mini" type="primary" plain icon="el-icon-check" v-hasPermi="['rail:meeting:edit']" @click="doMarkHeld(detail)">标记已召开</el-button>
            <el-tag :type="statusTag(detail.status)">{{ statusText(detail.status) }}</el-tag>
          </div>
        </div>

        <el-descriptions :column="2" border size="small" class="meeting-desc">
          <el-descriptions-item label="会议编号">{{ detail.meetingCode || '-' }}</el-descriptions-item>
          <el-descriptions-item label="会议地点">{{ detail.meetingPlace || '-' }}</el-descriptions-item>
          <el-descriptions-item label="线上链接">
            <a v-if="detail.onlineUrl" :href="detail.onlineUrl" target="_blank">{{ detail.onlineUrl }}</a>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="主持单位">{{ detail.hostUnit || '-' }}</el-descriptions-item>
          <el-descriptions-item label="组织单位">{{ detail.organizeUnit || '-' }}</el-descriptions-item>
          <el-descriptions-item label="会议主题">{{ detail.meetingTopic || '-' }}</el-descriptions-item>
          <el-descriptions-item label="会议议程" :span="2">{{ detail.agenda || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="closure-summary">
          <span>问题 {{ closedCount(detail.issues) }}/{{ (detail.issues || []).length }}</span>
          <span>决议 {{ closedCount(detail.decisions) }}/{{ (detail.decisions || []).length }}</span>
          <span>待办 {{ closedCount(detail.todos) }}/{{ (detail.todos || []).length }}</span>
          <el-tag size="small" :type="canArchiveDetail ? 'success' : 'warning'">
            {{ canArchiveDetail ? '已满足归档条件' : '需完成纪要确认和事项闭环' }}
          </el-tag>
        </div>

        <el-tabs v-model="detailTab" class="detail-tabs">
          <el-tab-pane label="参会人员" name="participants">
            <div class="tab-toolbar">
              <el-button size="small" type="primary" plain icon="el-icon-plus" v-hasPermi="['rail:meeting:participant']" @click="openParticipantDialog()">新增人员</el-button>
            </div>
            <el-table :data="detail.participants || []" size="small" border>
              <el-table-column prop="participantName" label="姓名" width="120" />
              <el-table-column prop="unitName" label="单位" min-width="180" show-overflow-tooltip />
              <el-table-column prop="duty" label="职务" width="120" />
              <el-table-column prop="phone" label="电话" width="130" />
              <el-table-column label="签到" width="90">
                <template slot-scope="scope">
                  <el-tag size="mini" :type="scope.row.signStatus === '1' ? 'success' : 'info'">{{ scope.row.signStatus === '1' ? '已签到' : '未签到' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template slot-scope="scope">
                  <el-button type="text" size="mini" @click="openParticipantDialog(scope.row)">编辑</el-button>
                  <el-button type="text" size="mini" class="danger-link" @click="removeParticipant(scope.row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="会议材料" name="files">
            <div class="file-upload" v-hasPermi="['rail:meeting:file']">
              <el-select v-model="fileForm.fileType" size="small" style="width: 150px">
                <el-option label="会议材料" value="material" />
                <el-option label="会议通知" value="notice" />
                <el-option label="会议纪要" value="minutes" />
                <el-option label="签到表" value="sign" />
                <el-option label="归档附件" value="archive" />
              </el-select>
              <el-input v-model="fileForm.description" size="small" clearable placeholder="材料说明" />
              <el-upload action="#" :auto-upload="false" :file-list="fileList" :on-change="onFileChange" :on-remove="onFileChange">
                <el-button size="small" icon="el-icon-paperclip">选择文件</el-button>
              </el-upload>
              <el-button size="small" type="primary" :loading="uploading" @click="submitFile">上传材料</el-button>
            </div>
            <el-table :data="detail.files || []" size="small" border>
              <el-table-column prop="fileName" label="文件名称" min-width="240" show-overflow-tooltip />
              <el-table-column label="类型" width="110">
                <template slot-scope="scope">{{ fileTypeText(scope.row.fileType) }}</template>
              </el-table-column>
              <el-table-column label="大小" width="100">
                <template slot-scope="scope">{{ formatSize(scope.row.fileSize) }}</template>
              </el-table-column>
              <el-table-column prop="description" label="说明" min-width="180" show-overflow-tooltip />
              <el-table-column prop="createTime" label="上传时间" width="160" />
              <el-table-column label="操作" width="120">
                <template slot-scope="scope">
                  <el-button type="text" size="mini" @click="downloadFile(scope.row)">下载</el-button>
                  <el-button type="text" size="mini" class="danger-link" v-hasPermi="['rail:meeting:file']" @click="removeFile(scope.row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="会议纪要" name="minutes">
            <el-form :model="minutesForm" label-width="90px">
              <el-form-item label="纪要标题">
                <el-input v-model="minutesForm.minutesTitle" maxlength="200" />
              </el-form-item>
              <el-form-item label="纪要正文">
                <el-input v-model="minutesForm.minutesContent" type="textarea" :rows="10" maxlength="20000" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" v-hasPermi="['rail:meeting:minutes']" @click="submitMinutes">保存纪要</el-button>
                <el-button type="success" plain v-hasPermi="['rail:meeting:confirm']" @click="doConfirmMinutes">确认纪要</el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="问题清单" name="issues">
            <meeting-item-panel
              type="issue"
              :rows="detail.issues || []"
              @add="openItemDialog('issue')"
              @edit="openItemDialog('issue', $event)"
              @close="closeItem('issue', $event)"
              @remove="removeIssue"
            />
          </el-tab-pane>

          <el-tab-pane label="决议事项" name="decisions">
            <meeting-item-panel
              type="decision"
              :rows="detail.decisions || []"
              @add="openItemDialog('decision')"
              @edit="openItemDialog('decision', $event)"
              @close="closeItem('decision', $event)"
              @remove="removeDecision"
            />
          </el-tab-pane>

          <el-tab-pane label="待办闭环" name="todos">
            <meeting-item-panel
              type="todo"
              :rows="detail.todos || []"
              @add="openItemDialog('todo')"
              @edit="openItemDialog('todo', $event)"
              @close="closeItem('todo', $event)"
              @remove="removeTodo"
            />
          </el-tab-pane>

          <el-tab-pane label="操作留痕" name="logs">
            <el-timeline v-if="detail.logs && detail.logs.length">
              <el-timeline-item v-for="log in detail.logs" :key="log.logId" :timestamp="log.createTime">
                <div class="log-title">{{ log.actionName }}</div>
                <div class="muted">{{ log.operatorName || '系统' }}</div>
                <p v-if="log.opinion">{{ log.opinion }}</p>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无操作记录" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-drawer>

    <el-dialog title="会议通知" :visible.sync="notifyVisible" width="560px" append-to-body>
      <el-input v-model="notifyForm.noticeContent" type="textarea" :rows="8" maxlength="4000" placeholder="填写会议通知内容" />
      <span slot="footer">
        <el-button @click="notifyVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitNotify">发送通知</el-button>
      </span>
    </el-dialog>

    <el-dialog :title="participantForm.participantId ? '编辑参会人员' : '新增参会人员'" :visible.sync="participantVisible" width="540px" append-to-body>
      <el-form ref="participantFormRef" :model="participantForm" :rules="participantRules" label-width="90px">
        <el-form-item label="姓名" prop="participantName"><el-input v-model="participantForm.participantName" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="participantForm.unitName" /></el-form-item>
        <el-form-item label="职务"><el-input v-model="participantForm.duty" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="participantForm.phone" /></el-form-item>
        <el-form-item label="签到"><el-switch v-model="participantForm.signStatus" active-value="1" inactive-value="0" /></el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="participantVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitParticipant">保 存</el-button>
      </span>
    </el-dialog>

    <el-dialog :title="itemDialogTitle" :visible.sync="itemVisible" width="620px" append-to-body>
      <el-form :model="itemForm" label-width="100px">
        <el-form-item :label="itemTitleLabel"><el-input v-model="itemForm.title" maxlength="200" /></el-form-item>
        <el-form-item label="内容"><el-input v-model="itemForm.content" type="textarea" :rows="5" maxlength="4000" /></el-form-item>
        <el-form-item label="责任单位"><el-input v-model="itemForm.responsibleUnit" maxlength="200" /></el-form-item>
        <el-form-item label="责任人"><el-input v-model="itemForm.responsibleUser" maxlength="80" /></el-form-item>
        <el-form-item label="截止时间"><el-date-picker v-model="itemForm.dueTime" type="datetime" value-format="yyyy-MM-dd HH:mm:ss" style="width: 100%" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="itemForm.status" style="width: 100%">
            <el-option v-for="item in itemStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="闭环说明">
          <el-input v-model="itemForm.closeRemark" type="textarea" :rows="3" maxlength="1000" placeholder="完成或闭环时填写处理说明" />
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="itemVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitItem">保 存</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import {
  listMeetings, getMeeting, createMeeting, updateMeeting, deleteMeeting, notifyMeeting, markMeetingHeld, archiveMeeting,
  addParticipant, updateParticipant, deleteParticipant,
  uploadMeetingFile, deleteMeetingFile, saveMinutes, confirmMinutes,
  addIssue, updateIssue, deleteIssue, addDecision, updateDecision, deleteDecision,
  addTodo, updateTodo, deleteTodo
} from '@/api/rail/meeting'

const MeetingItemPanel = {
  props: { type: String, rows: { type: Array, default: () => [] } },
  computed: {
    titleLabel() {
      return this.type === 'issue' ? '问题标题' : this.type === 'decision' ? '决议标题' : '待办标题'
    },
    contentProp() {
      return this.type === 'issue' ? 'issueContent' : this.type === 'decision' ? 'decisionContent' : 'todoContent'
    },
    titleProp() {
      return this.type === 'issue' ? 'issueTitle' : this.type === 'decision' ? 'decisionTitle' : 'todoTitle'
    }
  },
  methods: {
    statusText(status) {
      const map = { open: '待处理', processing: '处理中', resolved: '已解决', completed: '已完成', pending: '待办', done: '已完成', closed: '已闭环', overdue: '已逾期' }
      return map[status] || status || '-'
    },
    statusTag(status) {
      if (['closed', 'done', 'completed', 'resolved'].includes(status)) return 'success'
      if (['processing'].includes(status)) return 'warning'
      if (['overdue'].includes(status)) return 'danger'
      return 'info'
    }
  },
  template: `
    <div>
      <div class="tab-toolbar">
        <el-button size="small" type="primary" plain icon="el-icon-plus" v-hasPermi="['rail:meeting:item','rail:meeting:todo']" @click="$emit('add')">新增</el-button>
      </div>
      <el-table :data="rows" size="small" border>
        <el-table-column :prop="titleProp" :label="titleLabel" min-width="180" show-overflow-tooltip />
        <el-table-column :prop="contentProp" label="内容" min-width="260" show-overflow-tooltip />
        <el-table-column prop="responsibleUnit" label="责任单位" min-width="150" show-overflow-tooltip />
        <el-table-column prop="responsibleUser" label="责任人" width="100" />
        <el-table-column prop="dueTime" label="截止时间" width="155" />
        <el-table-column label="状态" width="90">
          <template slot-scope="scope"><el-tag size="mini" :type="statusTag(scope.row.status)">{{ statusText(scope.row.status) }}</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template slot-scope="scope">
            <el-button type="text" size="mini" @click="$emit('edit', scope.row)">编辑</el-button>
            <el-button v-if="!['closed', 'done', 'completed', 'resolved'].includes(scope.row.status)" type="text" size="mini" @click="$emit('close', scope.row)">闭环</el-button>
            <el-button type="text" size="mini" class="danger-link" @click="$emit('remove', scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  `
}

export default {
  name: 'RailMeeting',
  components: { MeetingItemPanel },
  data() {
    return {
      loading: false,
      saving: false,
      uploading: false,
      total: 0,
      meetingList: [],
      queryParams: { pageNum: 1, pageSize: 10, meetingName: '', meetingType: '', status: '', projectName: '' },
      meetingTypeOptions: [
        { label: '方案评审会', value: 'review' },
        { label: '协调会', value: 'coordination' },
        { label: '专题会', value: 'special' },
        { label: '专家审查会', value: 'expert' },
        { label: '技术交底会', value: 'technical' },
        { label: '其他', value: 'other' }
      ],
      statusOptions: [
        { label: '草稿', value: 'draft' },
        { label: '已通知', value: 'notified' },
        { label: '已召开', value: 'held' },
        { label: '纪要编制中', value: 'minuting' },
        { label: '待事项闭环', value: 'tracking' },
        { label: '已归档', value: 'archived' },
        { label: '已取消', value: 'cancelled' }
      ],
      meetingDialogVisible: false,
      meetingForm: {},
      meetingRules: {
        meetingName: [{ required: true, message: '会议名称不能为空', trigger: 'blur' }],
        meetingType: [{ required: true, message: '会议类型不能为空', trigger: 'change' }]
      },
      detailVisible: false,
      detailTab: 'participants',
      detail: {},
      notifyVisible: false,
      notifyForm: {},
      participantVisible: false,
      participantForm: {},
      participantRules: {
        participantName: [{ required: true, message: '姓名不能为空', trigger: 'blur' }]
      },
      fileForm: { fileType: 'material', description: '' },
      fileList: [],
      minutesForm: {},
      itemVisible: false,
      itemType: 'issue',
      itemForm: {},
      itemStatusOptions: [
        { label: '待处理', value: 'open' },
        { label: '处理中', value: 'processing' },
        { label: '待办', value: 'pending' },
        { label: '已完成', value: 'completed' },
        { label: '已闭环', value: 'closed' }
      ]
    }
  },
  computed: {
    statistics() {
      const stats = { total: this.meetingList.length, notified: 0, held: 0, tracking: 0, archived: 0 }
      this.meetingList.forEach(item => {
        if (Object.prototype.hasOwnProperty.call(stats, item.status)) stats[item.status] += 1
      })
      return stats
    },
    itemDialogTitle() {
      const prefix = this.itemForm.id ? '编辑' : '新增'
      const map = { issue: '问题', decision: '决议', todo: '待办' }
      return prefix + map[this.itemType]
    },
    itemTitleLabel() {
      return this.itemType === 'issue' ? '问题标题' : this.itemType === 'decision' ? '决议标题' : '待办标题'
    },
    canArchiveDetail() {
      if (!this.detail.meetingId) return false
      const minutes = this.detail.minutes || {}
      return minutes.confirmStatus === '2' &&
        this.allClosed(this.detail.issues) &&
        this.allClosed(this.detail.decisions) &&
        this.allClosed(this.detail.todos)
    }
  },
  created() {
    this.applyRouteQuery()
    this.loadMeetings().then(() => {
      const meetingId = this.$route.query.meetingId
      if (meetingId) {
        const target = this.meetingList.find(item => String(item.meetingId) === String(meetingId))
        if (target) this.openDetail(target)
      }
      if (this.$route.query.createMeeting === '1') {
        this.openMeetingDialog()
      }
    })
  },
  methods: {
    applyRouteQuery() {
      const { projectId, projectName } = this.$route.query || {}
      if (projectId) this.queryParams.projectId = projectId
      if (projectName) this.queryParams.projectName = projectName
    },
    loadMeetings() {
      this.loading = true
      return listMeetings(this.queryParams).then(res => {
        this.meetingList = res.rows || []
        this.total = res.total || 0
      }).finally(() => {
        this.loading = false
      })
    },
    handleQuery() {
      this.queryParams.pageNum = 1
      this.loadMeetings()
    },
    resetQuery() {
      this.queryParams = { pageNum: 1, pageSize: 10, meetingName: '', meetingType: '', status: '', projectName: '' }
      this.loadMeetings()
    },
    filterStatus(status) {
      this.queryParams.status = status
      this.handleQuery()
    },
    openMeetingDialog(row) {
      this.meetingForm = row ? { ...row } : {
        meetingType: 'review',
        status: 'draft',
        projectId: this.queryParams.projectId || this.$route.query.projectId || '',
        projectName: this.queryParams.projectName || this.$route.query.projectName || ''
      }
      this.meetingDialogVisible = true
      this.$nextTick(() => this.$refs.meetingFormRef && this.$refs.meetingFormRef.clearValidate())
    },
    submitMeeting() {
      this.$refs.meetingFormRef.validate(valid => {
        if (!valid) return
        this.saving = true
        const request = this.meetingForm.meetingId ? updateMeeting(this.meetingForm) : createMeeting(this.meetingForm)
        request.then(() => {
          this.$modal.msgSuccess('保存成功')
          this.meetingDialogVisible = false
          this.loadMeetings()
        }).finally(() => {
          this.saving = false
        })
      })
    },
    doDeleteMeeting(row) {
      this.$modal.confirm(`确认删除会议“${row.meetingName}”？`).then(() => deleteMeeting(row.meetingId)).then(() => {
        this.$modal.msgSuccess('删除成功')
        this.loadMeetings()
      })
    },
    openDetail(row) {
      this.detailVisible = true
      this.detailTab = 'participants'
      this.refreshDetail(row.meetingId)
    },
    refreshDetail(meetingId) {
      return getMeeting(meetingId).then(res => {
        this.detail = res.data || {}
        const minutes = this.detail.minutes || {}
        this.minutesForm = {
          minutesId: minutes.minutesId,
          minutesTitle: minutes.minutesTitle || `${this.detail.meetingName || ''}会议纪要`,
          minutesContent: minutes.minutesContent || ''
        }
      })
    },
    openNotify(row) {
      this.notifyForm = { meetingId: row.meetingId, noticeContent: row.noticeContent || this.defaultNotice(row) }
      this.notifyVisible = true
    },
    submitNotify() {
      notifyMeeting(this.notifyForm.meetingId, this.notifyForm).then(() => {
        this.$modal.msgSuccess('通知已记录')
        this.notifyVisible = false
        this.loadMeetings()
      })
    },
    doMarkHeld(row) {
      this.$modal.confirm(`确认将会议“${row.meetingName}”标记为已召开？`).then(() => markMeetingHeld(row.meetingId)).then(() => {
        this.$modal.msgSuccess('已标记为已召开')
        this.loadMeetings()
        if (this.detail.meetingId === row.meetingId) this.refreshDetail(row.meetingId)
      })
    },
    doArchive(row) {
      this.$modal.confirm(`归档前需确认会议纪要已确认，问题、决议和待办均已闭环。确认归档会议“${row.meetingName}”？`).then(() => archiveMeeting(row.meetingId)).then(() => {
        this.$modal.msgSuccess('归档成功')
        this.loadMeetings()
        if (this.detail.meetingId === row.meetingId) this.refreshDetail(row.meetingId)
      })
    },
    openParticipantDialog(row) {
      this.participantForm = row ? { ...row } : { signStatus: '0' }
      this.participantVisible = true
    },
    submitParticipant() {
      this.$refs.participantFormRef.validate(valid => {
        if (!valid) return
        const request = this.participantForm.participantId
          ? updateParticipant(this.participantForm)
          : addParticipant(this.detail.meetingId, this.participantForm)
        request.then(() => {
          this.$modal.msgSuccess('保存成功')
          this.participantVisible = false
          this.refreshDetail(this.detail.meetingId)
        })
      })
    },
    removeParticipant(row) {
      this.$modal.confirm(`确认删除参会人员“${row.participantName}”？`).then(() => deleteParticipant(row.participantId)).then(() => {
        this.$modal.msgSuccess('删除成功')
        this.refreshDetail(this.detail.meetingId)
      })
    },
    onFileChange(file, fileList) {
      this.fileList = fileList.slice(-1)
    },
    submitFile() {
      if (!this.fileList.length) {
        this.$modal.msgWarning('请选择文件')
        return
      }
      const form = new FormData()
      form.append('file', this.fileList[0].raw)
      form.append('fileType', this.fileForm.fileType)
      form.append('description', this.fileForm.description || '')
      this.uploading = true
      uploadMeetingFile(this.detail.meetingId, form).then(() => {
        this.$modal.msgSuccess('上传成功')
        this.fileList = []
        this.fileForm.description = ''
        this.refreshDetail(this.detail.meetingId)
      }).finally(() => {
        this.uploading = false
      })
    },
    downloadFile(row) {
      this.download(`/rail/meeting/files/${row.fileId}/download`, {}, row.fileName)
    },
    removeFile(row) {
      this.$modal.confirm(`确认删除文件“${row.fileName}”？`).then(() => deleteMeetingFile(row.fileId)).then(() => {
        this.$modal.msgSuccess('删除成功')
        this.refreshDetail(this.detail.meetingId)
      })
    },
    submitMinutes() {
      saveMinutes(this.detail.meetingId, this.minutesForm).then(() => {
        this.$modal.msgSuccess('纪要已保存')
        this.refreshDetail(this.detail.meetingId)
      })
    },
    doConfirmMinutes() {
      confirmMinutes(this.detail.meetingId, { ...this.minutesForm, confirmStatus: '2', confirmOpinion: '确认通过' }).then(() => {
        this.$modal.msgSuccess('纪要已确认')
        this.refreshDetail(this.detail.meetingId)
      })
    },
    openItemDialog(type, row) {
      this.itemType = type
      this.itemForm = row ? this.normalizeItemForForm(type, row) : { status: type === 'todo' ? 'pending' : 'open' }
      this.itemVisible = true
    },
    submitItem() {
      const data = this.mapItemPayload()
      let request
      if (this.itemType === 'issue') request = data.issueId ? updateIssue(data) : addIssue(this.detail.meetingId, data)
      if (this.itemType === 'decision') request = data.decisionId ? updateDecision(data) : addDecision(this.detail.meetingId, data)
      if (this.itemType === 'todo') request = data.todoId ? updateTodo(data) : addTodo(this.detail.meetingId, data)
      request.then(() => {
        this.$modal.msgSuccess('保存成功')
        this.itemVisible = false
        this.refreshDetail(this.detail.meetingId)
      })
    },
    closeItem(type, row) {
      const data = this.normalizeItemForForm(type, row)
      data.status = 'closed'
      data.closeRemark = data.closeRemark || '已完成并闭环'
      let request
      if (type === 'issue') request = updateIssue(this.mapSpecificItemPayload('issue', data))
      if (type === 'decision') request = updateDecision(this.mapSpecificItemPayload('decision', data))
      if (type === 'todo') request = updateTodo(this.mapSpecificItemPayload('todo', data))
      request.then(() => {
        this.$modal.msgSuccess('已闭环')
        this.refreshDetail(this.detail.meetingId)
        this.loadMeetings()
      })
    },
    removeIssue(row) {
      this.$modal.confirm('确认删除该问题？').then(() => deleteIssue(row.issueId)).then(() => this.refreshDetail(this.detail.meetingId))
    },
    removeDecision(row) {
      this.$modal.confirm('确认删除该决议？').then(() => deleteDecision(row.decisionId)).then(() => this.refreshDetail(this.detail.meetingId))
    },
    removeTodo(row) {
      this.$modal.confirm('确认删除该待办？').then(() => deleteTodo(row.todoId)).then(() => this.refreshDetail(this.detail.meetingId))
    },
    normalizeItemForForm(type, row) {
      if (type === 'issue') return { id: row.issueId, issueId: row.issueId, meetingId: row.meetingId, title: row.issueTitle, content: row.issueContent, responsibleUnit: row.responsibleUnit, responsibleUser: row.responsibleUser, dueTime: row.dueTime, status: row.status, closeRemark: row.closeRemark }
      if (type === 'decision') return { id: row.decisionId, decisionId: row.decisionId, meetingId: row.meetingId, title: row.decisionTitle, content: row.decisionContent, responsibleUnit: row.responsibleUnit, responsibleUser: row.responsibleUser, dueTime: row.dueTime, status: row.status, closeRemark: row.closeRemark }
      return { id: row.todoId, todoId: row.todoId, meetingId: row.meetingId, title: row.todoTitle, content: row.todoContent, responsibleUnit: row.responsibleUnit, responsibleUser: row.responsibleUser, dueTime: row.dueTime, status: row.status, closeRemark: row.closeRemark }
    },
    mapItemPayload() {
      return this.mapSpecificItemPayload(this.itemType, this.itemForm)
    },
    mapSpecificItemPayload(type, source) {
      const base = {
        meetingId: source.meetingId || this.detail.meetingId,
        responsibleUnit: source.responsibleUnit,
        responsibleUser: source.responsibleUser,
        dueTime: source.dueTime,
        status: source.status,
        closeRemark: source.closeRemark
      }
      if (type === 'issue') return { ...base, issueId: source.issueId, issueTitle: source.title, issueContent: source.content }
      if (type === 'decision') return { ...base, decisionId: source.decisionId, decisionTitle: source.title, decisionContent: source.content }
      return { ...base, todoId: source.todoId, todoTitle: source.title, todoContent: source.content }
    },
    allClosed(rows) {
      return (rows || []).every(row => ['closed', 'done', 'completed', 'resolved'].includes(row.status))
    },
    closedCount(rows) {
      return (rows || []).filter(row => ['closed', 'done', 'completed', 'resolved'].includes(row.status)).length
    },
    defaultNotice(row) {
      return `请参加“${row.meetingName}”。\n会议时间：${row.meetingTime || '待定'}\n会议地点：${row.meetingPlace || row.onlineUrl || '待定'}\n会议主题：${row.meetingTopic || ''}`
    },
    meetingTypeText(value) {
      const item = this.meetingTypeOptions.find(i => i.value === value)
      return item ? item.label : value || '-'
    },
    statusText(value) {
      const item = this.statusOptions.find(i => i.value === value)
      return item ? item.label : value || '-'
    },
    statusTag(status) {
      if (status === 'archived') return 'success'
      if (status === 'tracking') return 'warning'
      if (status === 'cancelled') return 'info'
      if (status === 'draft') return ''
      return 'primary'
    },
    fileTypeText(value) {
      const map = { material: '会议材料', notice: '会议通知', minutes: '会议纪要', sign: '签到表', archive: '归档附件', other: '其他' }
      return map[value] || value || '-'
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
.meeting-page {
  background: #f5f7f9;
  min-height: calc(100vh - 84px);
}
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  h2 { margin: 0 0 6px; font-size: 24px; color: #1f2d3d; }
  p { margin: 0; color: #7a8793; }
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
.drawer-actions {
  display: flex;
  flex: none;
  align-items: center;
  gap: 10px;
}
.meeting-desc { margin-bottom: 16px; }
.closure-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  margin: 0 0 14px;
  color: #606266;
  span {
    padding: 5px 10px;
    border-radius: 4px;
    background: #f4f7f7;
    border: 1px solid #e1ece9;
  }
}
.detail-tabs { margin-top: 12px; }
.tab-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}
.file-upload {
  display: grid;
  grid-template-columns: 150px 1fr auto auto;
  gap: 10px;
  align-items: start;
  margin-bottom: 12px;
}
.log-title { font-weight: 600; color: #1f2d3d; }
.muted { color: #7a8793; font-size: 13px; }
@media (max-width: 960px) {
  .stat-cards { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
  .file-upload { grid-template-columns: 1fr; }
}
</style>
