<template>
  <div class="app-container patrol-page">
    <header class="page-head">
      <div class="head-left">
        <h2>现场符合性巡查</h2>
        <p>平台派发巡查任务，巡查员小程序上报媒体，平台记录隐患并整改闭环</p>
      </div>
      <el-button type="primary" plain icon="el-icon-collection-tag" v-hasPermi="['rail:patrol:dict']" @click="openDictDialog">字典管理</el-button>
    </header>

    <el-tabs v-model="activeTab" @tab-click="onTabClick">
      <el-tab-pane label="巡查任务" name="tasks">
        <section class="stat-cards">
          <button type="button" class="stat-card" @click="filterStatus('')"><span class="stat-num">{{ statistics.total || 0 }}</span><span class="stat-label">全部任务</span></button>
          <button type="button" class="stat-card" @click="filterStatus('pending')"><span class="stat-num">{{ statistics.pending || 0 }}</span><span class="stat-label">待执行</span></button>
          <button type="button" class="stat-card" @click="filterStatus('executing')"><span class="stat-num">{{ statistics.executing || 0 }}</span><span class="stat-label">执行中</span></button>
          <button type="button" class="stat-card" @click="filterStatus('completed')"><span class="stat-num">{{ statistics.completed || 0 }}</span><span class="stat-label">已完成</span></button>
          <button type="button" class="stat-card" @click="filterStatus('closed')"><span class="stat-num">{{ statistics.closed || 0 }}</span><span class="stat-label">已关闭</span></button>
        </section>

        <section class="panel filter-panel">
          <el-form :inline="true" @submit.native.prevent>
            <el-form-item label="线路">
              <el-select v-model="query.line" clearable filterable placeholder="全部线路" style="width: 130px">
                <el-option v-for="item in lineDict" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="query.status" clearable placeholder="全部状态" style="width: 120px">
                <el-option label="待执行" value="pending" /><el-option label="执行中" value="executing" />
                <el-option label="已完成" value="completed" /><el-option label="已关闭" value="closed" />
              </el-select>
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model.trim="query.keyword" clearable placeholder="任务名/编号" style="width: 150px" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="el-icon-search" @click="search">查询</el-button>
              <el-button icon="el-icon-refresh" @click="resetQuery">重置</el-button>
              <el-button type="success" icon="el-icon-plus" v-hasPermi="['rail:patrol:manage']" @click="openNewTask">新建任务</el-button>
            </el-form-item>
          </el-form>
        </section>

        <section class="panel table-panel">
          <el-table v-loading="loading" :data="tasks" border stripe>
            <el-table-column prop="task_no" label="任务编号" min-width="140" fixed>
              <template slot-scope="scope"><span class="mono">{{ scope.row.task_no }}</span></template>
            </el-table-column>
            <el-table-column prop="name" label="任务名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="line" label="线路" width="90" />
            <el-table-column prop="assigned_user_name" label="指派巡查员" width="110">
              <template slot-scope="scope">{{ scope.row.assigned_user_name || '-' }}</template>
            </el-table-column>
            <el-table-column label="隐患" width="70" align="center">
              <template slot-scope="scope"><span :class="{ 'danger-text': scope.row.hazard_count }">{{ scope.row.hazard_count || 0 }}</span></template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template slot-scope="scope"><el-tag size="small" :type="taskTagType(scope.row)">{{ taskStatusLabel(scope.row) }}</el-tag></template>
            </el-table-column>
            <el-table-column label="派发时间" width="160">
              <template slot-scope="scope">{{ formatTime(scope.row.dispatch_time || scope.row.created_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right" align="center">
              <template slot-scope="scope">
                <el-button size="mini" type="text" icon="el-icon-view" @click="openDetail(scope.row)">详情</el-button>
                <el-button v-if="scope.row.status === 'pending'" size="mini" type="text" icon="el-icon-delete" class="danger-link" v-hasPermi="['rail:patrol:manage']" @click="doDeleteTask(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination class="pagination" background layout="total, sizes, prev, pager, next" :total="total" :page-size="query.size" :current-page="query.page" :page-sizes="[10, 20, 50, 100]" @size-change="onSizeChange" @current-change="onPageChange" />
        </section>
      </el-tab-pane>

      <el-tab-pane label="历史事件" name="legacy">
        <section class="panel table-panel">
          <el-table v-loading="legacyLoading" :data="legacyTasks" border stripe>
            <el-table-column prop="task_no" label="事件编号" min-width="140"><template slot-scope="scope"><span class="mono">{{ scope.row.task_no }}</span></template></el-table-column>
            <el-table-column prop="line" label="线路" width="100" />
            <el-table-column prop="location_desc" label="位置" min-width="180" show-overflow-tooltip />
            <el-table-column prop="dispatcher" label="历史上报人" width="120" />
            <el-table-column label="标记" width="90" align="center"><template><el-tag size="mini" type="info">历史</el-tag></template></el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template slot-scope="scope"><el-button size="mini" type="text" icon="el-icon-view" @click="openDetail(scope.row)">查看</el-button><el-button size="mini" type="text" icon="el-icon-refresh-left" v-hasPermi="['rail:patrol:manage']" @click="doReopen(scope.row)">重启</el-button></template>
            </el-table-column>
          </el-table>
        </section>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建任务 -->
    <el-dialog title="新建巡查任务" :visible.sync="taskDialogVisible" width="560px">
      <el-form ref="taskFormRef" :model="taskForm" :rules="taskRules" label-width="90px">
        <el-form-item label="任务名称" prop="name"><el-input v-model="taskForm.name" maxlength="120" placeholder="如：新街口站东侧基坑巡查" /></el-form-item>
        <el-form-item label="线路"><el-select v-model="taskForm.line" clearable filterable style="width: 100%"><el-option v-for="item in lineDict" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
        <el-form-item label="位置描述"><el-input v-model="taskForm.location_desc" maxlength="200" placeholder="站点/区间/里程" /></el-form-item>
        <el-form-item label="巡查内容"><el-input v-model="taskForm.requirement" type="textarea" :rows="3" maxlength="2000" placeholder="巡查要求、符合性核查要点" /></el-form-item>
        <el-form-item label="指派巡查员"><el-select v-model="taskForm.assigned_user_id" filterable style="width: 100%" @change="onAccountChange"><el-option v-for="u in patrolAccounts" :key="u.userId" :label="u.nickName || u.userName" :value="String(u.userId)" /></el-select></el-form-item>
        <el-form-item label="备注"><el-input v-model="taskForm.remark" maxlength="1000" /></el-form-item>
        <el-divider content-position="left">监测方案（选填）</el-divider>
        <el-form-item label="监测频率"><el-input v-model="taskForm.monitor_frequency" type="textarea" :rows="2" maxlength="2000" placeholder="如：每天 2 次 / 每周 1 次" /></el-form-item>
        <el-form-item label="监测点位"><el-input v-model="taskForm.monitor_points" type="textarea" :rows="2" maxlength="2000" placeholder="点位布设与编号" /></el-form-item>
        <el-form-item label="预警阈值"><el-input v-model="taskForm.warning_threshold" type="textarea" :rows="2" maxlength="2000" placeholder="累计值/速率报警阈值" /></el-form-item>
        <el-form-item label="应急预案"><el-input v-model="taskForm.emergency_plan" type="textarea" :rows="2" maxlength="2000" /></el-form-item>
        <el-form-item label="数据报送要求"><el-input v-model="taskForm.report_requirement" type="textarea" :rows="2" maxlength="2000" /></el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="taskDialogVisible = false">取 消</el-button><el-button type="primary" :loading="taskSaving" @click="submitTask">提 交</el-button></span>
    </el-dialog>

    <!-- 任务详情 -->
    <el-dialog title="巡查任务详情" :visible.sync="detailVisible" width="920px" top="4vh">
      <div v-if="detail" v-loading="detailLoading" class="detail-body">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="任务编号"><span class="mono">{{ detail.task_no }}</span></el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag size="small" :type="taskTagType(detail)">{{ taskStatusLabel(detail) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="任务名称" :span="2">{{ detail.name }}</el-descriptions-item>
          <el-descriptions-item label="线路">{{ detail.line || '-' }}</el-descriptions-item>
          <el-descriptions-item label="指派巡查员">{{ detail.assigned_user_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="位置" :span="2">{{ detail.location_desc || '-' }}</el-descriptions-item>
          <el-descriptions-item label="巡查内容" :span="2">{{ detail.requirement || '-' }}</el-descriptions-item>
          <el-descriptions-item label="派发人">{{ detail.dispatcher || '-' }}</el-descriptions-item>
          <el-descriptions-item label="派发时间">{{ formatTime(detail.dispatch_time || detail.created_at) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 监测方案 -->
        <div class="monitor-card">
          <div class="monitor-head">
            <span class="monitor-title">📋 监测方案</span>
            <el-button v-hasPermi="['rail:patrol:manage','rail:patrol:review']" size="mini" type="primary" plain icon="el-icon-edit" @click="openMonitorEdit">编辑监测方案</el-button>
          </div>
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="监测频率" :span="2">{{ detail.monitor_frequency || '—' }}</el-descriptions-item>
            <el-descriptions-item label="监测点位" :span="2">{{ detail.monitor_points || '—' }}</el-descriptions-item>
            <el-descriptions-item label="预警阈值" :span="2">{{ detail.warning_threshold || '—' }}</el-descriptions-item>
            <el-descriptions-item label="应急预案" :span="2">{{ detail.emergency_plan || '—' }}</el-descriptions-item>
            <el-descriptions-item label="数据报送要求" :span="2">{{ detail.report_requirement || '—' }}</el-descriptions-item>
          </el-descriptions>
          <div class="monitor-opinion">
            <div class="monitor-opinion-label">监测审查意见</div>
            <div class="monitor-opinion-text">{{ detail.review_opinion || '暂无审查意见' }}</div>
          </div>
          <div class="monitor-docs">
            <div class="monitor-docs-label">监测方案文档（{{ detail.docs ? detail.docs.length : 0 }}）</div>
            <div v-if="detail.docs && detail.docs.length" class="doc-list">
              <div v-for="d in detail.docs" :key="d.doc_id" class="doc-item">
                <span class="doc-icon">{{ docIcon(d) }}</span>
                <span class="doc-name" :title="d.file_name">{{ d.file_name }}</span>
                <span class="doc-size">{{ formatSize(d.size) }}</span>
                <el-button size="mini" type="text" @click="viewDoc(d)">查看</el-button>
                <el-button size="mini" type="text" @click="downloadDoc(d)">下载</el-button>
                <el-button v-hasPermi="['rail:patrol:manage','rail:patrol:review']" size="mini" type="text" class="danger-link" @click="deleteDoc(d)">删除</el-button>
              </div>
            </div>
            <div v-else class="muted">暂无文档</div>
          </div>
        </div>

        <div class="detail-actions">
          <el-button v-if="detail.status === 'pending'" size="small" type="primary" plain v-hasPermi="['rail:patrol:manage']" @click="setStatus(detail, 'executing')">开始执行</el-button>
          <el-button v-if="['pending','executing'].includes(detail.status)" size="small" type="success" plain v-hasPermi="['rail:patrol:manage']" @click="setStatus(detail, 'completed')">标记完成</el-button>
          <el-button v-if="['pending','executing'].includes(detail.status)" size="small" type="warning" plain v-hasPermi="['rail:patrol:manage']" @click="setStatus(detail, 'closed')">关闭任务</el-button>
          <el-button v-if="['completed','closed'].includes(detail.status)" size="small" type="primary" plain icon="el-icon-refresh-left" v-hasPermi="['rail:patrol:manage']" @click="doReopen(detail)">重启任务</el-button>
          <el-button size="small" type="primary" plain icon="el-icon-edit" v-hasPermi="['rail:patrol:manage']" @click="openEditTask(detail)">编辑/改派</el-button>
          <el-button size="small" type="danger" plain icon="el-icon-warning-outline" v-hasPermi="['rail:patrol:review']" @click="openHazardDialog(detail)">记录隐患</el-button>
        </div>

        <div class="section">
          <h4>巡查时间线
            <el-tag v-if="remainingHazards > 0" size="mini" type="danger">剩余 {{ remainingHazards }} 个隐患未闭环</el-tag>
          </h4>
          <div v-if="timeline.length" class="record-timeline">
            <article v-for="item in timeline" :key="item.kind + '_' + item.data.id" class="timeline-item">
              <!-- 巡查记录：时间/巡查员 → 照片 → 隐患 -->
              <div class="tl-head">
                <el-tag v-if="item.kind === 'record'" size="mini" :type="item.data.type === 'rectify' ? 'warning' : 'success'">{{ item.data.type === 'rectify' ? '整改反馈' : '日常巡查' }}</el-tag>
                <el-tag v-else size="mini" type="danger">风险隐患</el-tag>
                <span class="muted">{{ item.data.created_by_name || '-' }} · {{ formatTime(item.data.created_at) }}</span>
                <el-button v-if="item.kind === 'record' && item.data.type === 'patrol'" size="mini" type="text" icon="el-icon-warning-outline" @click="openHazardDialog(item.data)">添加隐患</el-button>
              </div>
              <div v-if="item.kind === 'record' && item.data.note" class="record-note">{{ item.data.note }}</div>
              <div v-if="item.kind === 'record' && item.data.media && item.data.media.length" class="media-grid">
                <template v-for="m in item.data.media">
                  <div v-if="m.kind === 'photo'" :key="m.media_id" class="media-thumb-wrap">
                    <el-image :src="mediaUrl(m)" fit="cover" :preview-src-list="photoPreviewList" class="media-thumb" />
                  </div>
                  <button v-else :key="m.media_id" type="button" class="media-video" @click="playVideo(m)"><i class="el-icon-video-play" />视频</button>
                </template>
              </div>
              <!-- 该条目关联的隐患（记录下挂隐患 / 独立隐患） -->
              <div v-for="h in (item.kind === 'record' ? item.data.hazards : [item.data])" :key="h.hazard_id" class="hazard-block" :class="{ 'hazard-closed': h.status === 'closed' }">
                <!-- 隐患进展栏 -->
                <div class="hazard-steps">
                  <div v-for="s in hazardSteps(h)" :key="s.key" class="hazard-step" :class="{ done: s.done, current: s.current }">
                    <div class="hazard-step-line"></div>
                    <div class="hazard-step-dot"></div>
                    <div class="hazard-step-label">{{ s.label }}</div>
                  </div>
                </div>
                <div class="hazard-meta">
                  <el-tag size="mini" type="info" v-if="h.hazard_type">{{ h.hazard_type }}</el-tag>
                  <el-tag size="mini" :type="h.risk_level === '高' ? 'danger' : (h.risk_level === '中' ? 'warning' : 'info')" v-if="h.risk_level">{{ h.risk_level }}</el-tag>
                  <el-tag size="mini" :type="hazardTagType(h)">{{ hazardStatusLabel(h) }}</el-tag>
                  <span v-if="h.rectify_owner" class="muted">整改责任人：{{ h.rectify_owner }}</span>
                </div>
                <div v-if="h.shots && h.shots.length" class="media-grid">
                  <div v-for="s in h.shots" :key="s.shot_id" class="media-thumb-wrap">
                    <el-image :src="shotUrl(s)" fit="cover" :preview-src-list="shotPreviewList" class="media-thumb" />
                    <span class="hazard-badge">截图</span>
                  </div>
                </div>
                <div class="hazard-desc">{{ h.description }}</div>
                <div v-if="h.rectify_requirement" class="hazard-req">整改要求：{{ h.rectify_requirement }}</div>
                <!-- 嵌套整改记录 -->
                <div v-if="h.rectifyRecords && h.rectifyRecords.length" class="rectify-list">
                  <div class="rectify-title">整改记录（{{ h.rectifyRecords.length }}）</div>
                  <div v-for="rr in h.rectifyRecords" :key="rr.record_id" class="rectify-item">
                    <div class="rectify-head"><span class="muted">{{ rr.created_by_name || '-' }} · {{ formatTime(rr.created_at) }}</span></div>
                    <div v-if="rr.note" class="rectify-note">{{ rr.note }}</div>
                    <div v-if="rr.media && rr.media.length" class="media-grid">
                      <template v-for="rm in rr.media">
                        <div v-if="rm.kind === 'photo'" :key="rm.media_id" class="media-thumb-wrap">
                          <el-image :src="mediaUrl(rm)" fit="cover" :preview-src-list="photoPreviewList" class="media-thumb" />
                        </div>
                        <button v-else :key="rm.media_id" type="button" class="media-video" @click="playVideo(rm)"><i class="el-icon-video-play" />视频</button>
                      </template>
                    </div>
                  </div>
                </div>
                <div v-if="h.review_comment" class="hazard-req">复核意见：{{ h.review_comment }}</div>
                <div class="hazard-ops">
                  <el-button v-if="h.status === 'pending_confirm'" size="mini" type="primary" plain v-hasPermi="['rail:patrol:review']" @click="openConfirm(h)">确认并下发整改要求</el-button>
                  <el-button v-if="h.status === 'pending_review'" size="mini" type="success" plain v-hasPermi="['rail:patrol:review']" @click="openReview(h)">复核意见</el-button>
                </div>
              </div>
            </article>
          </div>
          <div v-else class="compact-empty"><i class="el-icon-time" /><p>暂无巡查记录</p></div>
        </div>
      </div>
      <span slot="footer"><el-button @click="detailVisible = false">关 闭</el-button></span>
    </el-dialog>

    <!-- 记录隐患 -->
    <el-dialog title="记录问题隐患" :visible.sync="hazardDialogVisible" width="560px" append-to-body>
      <el-form ref="hazardFormRef" :model="hazardForm" :rules="hazardRules" label-width="90px">
        <el-form-item label="隐患描述" prop="description"><el-input v-model="hazardForm.description" type="textarea" :rows="3" maxlength="2000" placeholder="违规施工、超范围施工等具体情况" /></el-form-item>
        <el-form-item label="隐患类型"><el-select v-model="hazardForm.hazard_type" clearable style="width: 100%"><el-option v-for="i in hazardTypeDict" :key="i.value" :label="i.label" :value="i.value" /></el-select></el-form-item>
        <el-form-item label="风险等级"><el-select v-model="hazardForm.risk_level" clearable style="width: 100%"><el-option v-for="i in riskDict" :key="i.value" :label="i.label" :value="i.value" /></el-select></el-form-item>
        <el-form-item label="关联巡查记录"><el-select v-model="hazardForm.record_id" clearable filterable style="width: 100%" placeholder="可选，挂到某条巡查记录下"><el-option v-for="r in detailRecords" :key="r.record_id" :label="'[巡查] ' + formatTime(r.created_at)" :value="r.record_id" /></el-select></el-form-item>
        <el-form-item label="圈注截图">
          <el-upload action="#" :auto-upload="false" list-type="picture-card" :limit="9" multiple accept="image/*" :on-change="onShotChange" :on-remove="onShotChange" :file-list="shotFileList">
            <i class="el-icon-plus" />
          </el-upload>
        </el-form-item>
        <el-form-item label="整改责任人"><el-input v-model="hazardForm.rectify_owner" maxlength="120" placeholder="施工方名称" /></el-form-item>
        <el-form-item label="整改要求" prop="rectify_requirement"><el-input v-model="hazardForm.rectify_requirement" type="textarea" :rows="3" maxlength="2000" placeholder="平台记录隐患时填写整改要求" /></el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="hazardDialogVisible = false">取 消</el-button><el-button type="primary" :loading="hazardSaving" @click="submitHazard">提 交</el-button></span>
    </el-dialog>

    <!-- 确认隐患 -->
    <el-dialog title="确认隐患并下发整改要求" :visible.sync="confirmVisible" width="500px" append-to-body>
      <el-form label-width="90px">
        <el-form-item label="整改要求"><el-input v-model="confirmForm.rectify_requirement" type="textarea" :rows="4" maxlength="2000" placeholder="明确整改要求与限期" /></el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="confirmVisible = false">取 消</el-button><el-button type="primary" @click="submitConfirm">确 认</el-button></span>
    </el-dialog>

    <!-- 复核隐患 -->
    <el-dialog title="复核整改情况" :visible.sync="reviewVisible" width="500px" append-to-body>
      <el-form label-width="90px">
        <el-form-item label="复核结论"><el-radio-group v-model="reviewForm.result"><el-radio label="closed">通过（闭环）</el-radio><el-radio label="reject">不通过（退回整改）</el-radio></el-radio-group></el-form-item>
        <el-form-item label="复核意见"><el-input v-model="reviewForm.comment" type="textarea" :rows="3" maxlength="2000" /></el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="reviewVisible = false">取 消</el-button><el-button type="primary" @click="submitReview">提 交</el-button></span>
    </el-dialog>

    <!-- 编辑监测方案 -->
    <el-dialog title="编辑监测方案" :visible.sync="monitorVisible" width="560px" append-to-body>
      <el-form label-width="100px">
        <el-form-item label="监测审查意见"><el-input v-model="monitorForm.review_opinion" type="textarea" :rows="4" maxlength="2000" placeholder="技术审核 / 参数复核 / 点位核验 / 监测要求判定的审查意见" /></el-form-item>
        <el-form-item label="方案文档">
          <el-upload action="#" :auto-upload="false" :limit="9" multiple accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.webp,.bmp" :on-change="onDocChange">
            <el-button size="small" icon="el-icon-upload2">选择文件</el-button>
            <div slot="tip" class="el-upload__tip">支持 PDF / Word / 图片，单个 ≤50MB，最多 9 个；保存后生效</div>
          </el-upload>
        </el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="monitorVisible = false">取 消</el-button><el-button type="primary" :loading="monitorSaving" @click="submitMonitor">保 存</el-button></span>
    </el-dialog>

    <!-- 视频预览 -->
    <el-dialog title="视频预览" :visible.sync="videoVisible" width="640px" append-to-body>
      <video v-if="videoUrl" :src="videoUrl" controls style="width: 100%; max-height: 60vh;" />
      <span slot="footer"><el-button @click="videoVisible = false">关 闭</el-button></span>
    </el-dialog>

    <!-- 字典管理 -->
    <el-dialog title="巡查字典管理" :visible.sync="dictVisible" width="680px" append-to-body>
      <el-tabs v-model="dictType">
        <el-tab-pane label="线路" name="line" /><el-tab-pane label="施工类型" name="construction_type" />
        <el-tab-pane label="隐患类型" name="hazard_type" /><el-tab-pane label="风险等级" name="hazard_risk" />
      </el-tabs>
      <div class="dict-toolbar"><span class="muted">共 {{ dictItems.length }} 项</span><el-button size="mini" type="primary" icon="el-icon-plus" @click="openDictEdit()">新增</el-button></div>
      <el-table v-loading="dictLoading" :data="dictItems" size="small" border>
        <el-table-column prop="label" label="名称" min-width="140" />
        <el-table-column prop="sort" label="排序" width="70" align="center" />
        <el-table-column label="启用" width="80" align="center"><template slot-scope="scope"><el-tag size="mini" :type="scope.row.enabled ? 'success' : 'info'">{{ scope.row.enabled ? '启用' : '停用' }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="130" align="center">
          <template slot-scope="scope">
            <el-button size="mini" type="text" icon="el-icon-edit" @click="openDictEdit(scope.row)">编辑</el-button>
            <el-button size="mini" type="text" icon="el-icon-delete" class="danger-link" @click="doDeleteDict(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <span slot="footer"><el-button @click="dictVisible = false">关 闭</el-button></span>
    </el-dialog>

    <!-- 字典编辑 -->
    <el-dialog :title="dictEditingId ? '编辑字典项' : '新增字典项'" :visible.sync="dictEditVisible" width="420px" append-to-body>
      <el-form ref="dictFormRef" :model="dictForm" :rules="dictRules" label-width="80px">
        <el-form-item label="名称" prop="label"><el-input v-model="dictForm.label" maxlength="60" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="dictForm.sort" :min="0" :max="10000" /></el-form-item>
        <el-form-item label="启用"><el-switch v-model="dictForm.enabled" :active-value="1" :inactive-value="0" /></el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="dictEditVisible = false">取 消</el-button><el-button type="primary" :loading="dictSaving" @click="submitDict">保 存</el-button></span>
    </el-dialog>
  </div>
</template>

<script>
import {
  listPatrolTasks, getPatrolTask, createPatrolTask, updatePatrolTask, setPatrolTaskStatus, deletePatrolTask, reopenPatrolTask,
  getPatrolStatistics, createPatrolHazard, confirmPatrolHazard, reviewPatrolHazard, updatePatrolHazard, deletePatrolHazard, getPatrolMediaFile, getPatrolShotFile, uploadPatrolShot,
  listPatrolDicts, createPatrolDict, updatePatrolDict, deletePatrolDict,
  uploadPatrolDoc, getPatrolDocFile, deletePatrolDoc
} from '@/api/rail/patrol'
import { listUser } from '@/api/system/user'
import { checkPermi } from '@/utils/permission'

export default {
  name: 'RailPatrol',
  data() {
    return {
      activeTab: 'tasks',
      loading: false, detailLoading: false, legacyLoading: false,
      taskSaving: false, hazardSaving: false, dictSaving: false, shotFiles: [], editingHazardId: null,
      tasks: [], legacyTasks: [], total: 0, statistics: {},
      lineDict: [], hazardTypeDict: [], riskDict: [], patrolAccounts: [],
      query: { page: 1, size: 20, line: '', status: '', keyword: '' },
      detailVisible: false, detail: null, photoUrls: {}, videoUrls: {}, shotUrls: {}, videoVisible: false, videoUrl: '',
      taskDialogVisible: false, taskForm: {}, taskRules: { name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }] },
      hazardDialogVisible: false, hazardForm: {}, hazardRules: { description: [{ required: true, message: '请输入隐患描述', trigger: 'blur' }] },
      confirmVisible: false, confirmForm: { rectify_requirement: '' }, confirmTarget: null,
      reviewVisible: false, reviewForm: { result: 'closed', comment: '' }, reviewTarget: null,
      monitorVisible: false, monitorForm: { review_opinion: '' }, monitorSaving: false, docFiles: [],
      dictVisible: false, dictType: 'line', dictItems: [], dictLoading: false,
      dictEditingId: null, dictEditVisible: false, dictForm: { label: '', sort: 0, enabled: 1 },
      dictRules: { label: [{ required: true, message: '请输入名称', trigger: 'blur' }] }
    }
  },
  computed: {
    canManagePatrol() {
      return checkPermi(['rail:patrol:manage']) || checkPermi(['system:user:list'])
    },
    detailRecords() { return this.detail ? (this.detail.records || []).filter(r => r.type === 'patrol') : [] },
    photoPreviewList() { return Object.values(this.photoUrls) },
    remainingHazards() {
      return this.detail ? (this.detail.hazards || []).filter(h => h.status !== 'closed').length : 0
    },
    taskPhotoOptions() {
      const opts = []
      if (!this.detail) return opts
      this.detail.records.forEach(r => {
        ;(r.media || []).forEach((m, i) => {
          if (m.kind === 'photo') {
            opts.push({
              media_id: m.media_id,
              label: `${r.type === 'rectify' ? '[整改]' : '[巡查]'} ${this.formatTime(r.created_at)} · 第${i + 1}张`
            })
          }
        })
      })
      return opts
    },
    timeline() {
      if (!this.detail) return []
      const items = []
      const attached = new Set()
      // 隐患映射：挂整改记录
      const hazardMap = {}
      ;(this.detail.hazards || []).forEach(h => {
        h.rectifyRecords = []
        hazardMap[h.hazard_id] = h
      })
      // 分离日常巡查和整改反馈：整改反馈挂到对应隐患下
      ;(this.detail.records || []).forEach(r => {
        if (r.type === 'rectify' && r.hazard_id && hazardMap[r.hazard_id]) {
          hazardMap[r.hazard_id].rectifyRecords.push(r)
        } else {
          const hazards = (this.detail.hazards || []).filter(h => h.record_id === r.record_id)
          hazards.forEach(h => attached.add(h.hazard_id))
          items.push({ kind: 'record', time: r.created_at || '', data: { id: r.record_id, ...r, hazards } })
        }
      })
      // 独立隐患（未关联巡查记录）
      ;(this.detail.hazards || []).forEach(h => {
        if (!attached.has(h.hazard_id)) {
          items.push({ kind: 'hazard', time: h.created_at || '', data: { id: h.hazard_id, ...h, hazards: [] } })
        }
      })
      // 整改记录按时间正序（早→晚）
      Object.values(hazardMap).forEach(h => {
        h.rectifyRecords.sort((a, b) => (a.created_at || '').localeCompare(b.created_at || ''))
      })
      return items.sort((a, b) => (b.time || '').localeCompare(a.time || ''))
    },
    shotPreviewList() { return Object.values(this.shotUrls) }
  },
  watch: {
    dictType() { if (this.dictVisible) this.loadDictItems() }
  },
  created() {
    this.loadLineDict()
    this.loadHazardDicts()
    if (this.canManagePatrol) {
      this.loadAccounts()
    }
    this.refresh()
  },
  methods: {
    async refresh() { await Promise.all([this.loadStatistics(), this.loadTasks()]) },
    async loadStatistics() { this.statistics = await getPatrolStatistics({}) || {} },
    async loadTasks() {
      this.loading = true
      try { const r = await listPatrolTasks(this.query) || {}; this.tasks = r.items || []; this.total = r.total || 0 }
      finally { this.loading = false }
    },
    async loadLegacy() {
      this.legacyLoading = true
      try { const r = await listPatrolTasks({ page: 1, size: 200 }) || {}; this.legacyTasks = (r.items || []).filter(t => t.legacy) }
      finally { this.legacyLoading = false }
    },
    onTabClick(tab) { if (tab.name === 'legacy') this.loadLegacy() },
    async loadLineDict() { this.lineDict = await listPatrolDicts('line') || [] },
    async loadHazardDicts() {
      this.hazardTypeDict = await listPatrolDicts('hazard_type') || []
      this.riskDict = await listPatrolDicts('hazard_risk') || []
    },
    async loadAccounts() {
      if (!this.canManagePatrol) {
        this.patrolAccounts = []
        return
      }
      try {
        const res = await listUser({ pageNum: 1, pageSize: 200, status: '0' })
        const rows = res.rows || []
        // 只有勾选「小程序」登录权限（can_mini=1）的账号可作为巡查员
        this.patrolAccounts = rows.filter(u => u.canMini === '1' || u.canMini === 1)
      } catch (e) { this.patrolAccounts = [] }
    },
    onAccountChange(uid) {
      const u = this.patrolAccounts.find(x => String(x.userId) === uid)
      this.taskForm.assigned_user_name = u ? (u.nickName || u.userName) : ''
    },
    search() { this.query.page = 1; this.loadTasks(); this.loadStatistics() },
    resetQuery() { this.query = { page: 1, size: 20, line: '', status: '', keyword: '' }; this.refresh() },
    filterStatus(s) { this.query.status = s; this.query.page = 1; this.loadTasks() },
    onPageChange(p) { this.query.page = p; this.loadTasks() },
    onSizeChange(s) { this.query.size = s; this.query.page = 1; this.loadTasks() },
    taskStatusLabel(row) { return { pending: '待执行', executing: '执行中', completed: '已完成', closed: '已关闭' }[row.status] || row.status },
    taskTagType(row) { return { pending: 'info', executing: 'primary', completed: 'success', closed: 'info' }[row.status] || 'info' },
    hazardStatusLabel(h) { return { pending_confirm: '待确认', pending_rectify: '待整改', rectifying: '整改中', pending_review: '待复核', closed: '已闭环' }[h.status] || h.status },
    hazardTagType(h) { return { pending_confirm: 'warning', pending_rectify: 'warning', rectifying: 'primary', pending_review: 'warning', closed: 'success' }[h.status] || 'info' },
    hazardSteps(h) {
      const steps = [
        { key: 'pending_confirm', label: '待确认' },
        { key: 'pending_rectify', label: '待整改' },
        { key: 'rectifying', label: '整改中' },
        { key: 'pending_review', label: '待复核' },
        { key: 'closed', label: '已闭环' }
      ]
      const idx = steps.findIndex(s => s.key === h.status)
      return steps.map((s, i) => ({
        ...s,
        done: i < idx || h.status === 'closed',
        current: i === idx && h.status !== 'closed'
      }))
    },
    formatTime(v) { if (!v) return '-'; return String(v).replace('T', ' ').slice(0, 19) },

    async openNewTask() {
      this.taskForm = { name: '', line: '', location_desc: '', requirement: '', assigned_user_id: '', assigned_user_name: '', remark: '', monitor_frequency: '', monitor_points: '', warning_threshold: '', emergency_plan: '', report_requirement: '' }
      await this.loadAccounts()
      this.taskDialogVisible = true
    },
    submitTask() {
      this.$refs.taskFormRef.validate(async valid => {
        if (!valid) return
        this.taskSaving = true
        try { await createPatrolTask(this.taskForm); this.$message.success('任务已创建'); this.taskDialogVisible = false; this.refresh() }
        finally { this.taskSaving = false }
      })
    },
    openEditTask(task) {
      this.taskForm = { name: task.name, line: task.line, location_desc: task.location_desc, requirement: task.requirement, assigned_user_id: task.assigned_user_id, assigned_user_name: task.assigned_user_name, remark: task.remark, monitor_frequency: task.monitor_frequency || '', monitor_points: task.monitor_points || '', warning_threshold: task.warning_threshold || '', emergency_plan: task.emergency_plan || '', report_requirement: task.report_requirement || '' }
      this.editingTaskId = task.task_id
      this.taskDialogVisible = true
    },
    async setStatus(task, status) {
      if (status === 'completed') {
        const openHazards = (task.hazards || []).filter(h => h.status !== 'closed').length
        if (openHazards) { this.$message.warning('存在未闭环隐患，不能标记完成'); return }
      }
      await setPatrolTaskStatus(task.task_id, status)
      this.$message.success('状态已更新')
      this.refresh(); if (this.detailVisible) this.openDetail({ task_id: task.task_id })
    },
    doDeleteTask(task) {
      this.$confirm(`确认删除待执行任务 ${task.task_no}？`, '删除确认', { type: 'warning' }).then(async () => {
        await deletePatrolTask(task.task_id); this.$message.success('已删除'); this.refresh()
      }).catch(() => {})
    },
    doReopen(task) {
      this.$confirm(`确认重启任务 ${task.task_no}？重启后状态变为「执行中」。`, '重启确认', { type: 'warning' }).then(async () => {
        await reopenPatrolTask(task.task_id); this.$message.success('已重启'); this.refresh(); this.loadLegacy()
        if (this.detailVisible) this.openDetail({ task_id: task.task_id })
      }).catch(() => {})
    },
    async openDetail(task) {
      this.detailVisible = true; this.detailLoading = true; this.detail = null; this.photoUrls = {}; this.videoUrls = {}; this.shotUrls = {}
      try {
        const detail = await getPatrolTask(task.task_id)
        // 预加载全部照片与截图 URL，再挂载 detail，避免图片 src 从空到 blob 造成首屏闪烁
        const photoIds = []
        ;(detail.records || []).forEach(r => (r.media || []).forEach(m => { if (m.kind === 'photo') photoIds.push(m.media_id) }))
        const shotIds = []
        ;(detail.hazards || []).forEach(h => (h.shots || []).forEach(s => shotIds.push(s.shot_id)))
        await Promise.all(photoIds.map(id => this.loadMediaUrl(id)))
        await Promise.all(shotIds.map(id => this.loadShotUrl(id)))
        this.detail = detail
      } finally { this.detailLoading = false }
    },
    async loadMediaUrl(mediaId) {
      if (this.photoUrls[mediaId] !== undefined) return
      try { const blob = await getPatrolMediaFile(mediaId); this.$set(this.photoUrls, mediaId, URL.createObjectURL(blob)) }
      catch (e) { this.$set(this.photoUrls, mediaId, '') }
    },
    mediaUrl(m) { return this.photoUrls[m.media_id] || '' },
    hazardOnMedia(mediaId) {
      return (this.detail && this.detail.hazards) ? this.detail.hazards.find(h => h.media_id === mediaId) : null
    },
    mediaRefLabel(h) {
      if (!h) return ''
      if (h.video_time) return '视频 ' + h.video_time + ' 秒'
      if (!h.media_id) return ''
      for (const r of (this.detail ? this.detail.records : [])) {
        const i = (r.media || []).findIndex(m => m.media_id === h.media_id)
        if (i >= 0) return `${r.type === 'rectify' ? '[整改]' : '[巡查]'} 第 ${i + 1} 张照片`
      }
      return '关联照片'
    },
    mediaUrlById(mediaId) {
      if (!mediaId || !this.detail) return ''
      for (const r of this.detail.records) {
        const m = (r.media || []).find(x => x.media_id === mediaId)
        if (m) return this.mediaUrl(m)
      }
      return ''
    },
    async loadShotUrl(shotId) {
      if (this.shotUrls[shotId] !== undefined) return
      try { const blob = await getPatrolShotFile(shotId); this.$set(this.shotUrls, shotId, URL.createObjectURL(blob)) }
      catch (e) { this.$set(this.shotUrls, shotId, '') }
    },
    shotUrl(s) { return this.shotUrls[s.shot_id] || '' },
    async playVideo(m) {
      try { const blob = await getPatrolMediaFile(m.media_id); this.videoUrl = URL.createObjectURL(blob); this.videoVisible = true }
      catch (e) { this.$message.error('视频加载失败') }
    },

    openHazardDialog(obj) {
      this.hazardTaskId = this.detail.task_id
      this.editingHazardId = null
      this.hazardForm = { description: '', hazard_type: '', risk_level: '', record_id: (obj && obj.record_id) || '', rectify_owner: '', rectify_requirement: '' }
      this.shotFiles = []
      this.hazardDialogVisible = true
    },
    openHazardEdit(h) {
      this.hazardTaskId = this.detail.task_id
      this.editingHazardId = h.hazard_id
      this.hazardForm = { description: h.description, hazard_type: h.hazard_type, risk_level: h.risk_level, record_id: h.record_id, rectify_owner: h.rectify_owner, rectify_requirement: h.rectify_requirement }
      this.shotFiles = []
      this.hazardDialogVisible = true
    },
    doDeleteHazard(h) {
      this.$confirm(`确认删除隐患「${(h.description || '').slice(0, 20)}」？`, '删除确认', { type: 'warning' }).then(async () => {
        await deletePatrolHazard(h.hazard_id); this.$message.success('已删除'); this.reloadDetail(); this.refresh()
      }).catch(() => {})
    },
    onShotChange(file, fileList) {
      this.shotFiles = fileList.map(f => f.raw).filter(Boolean)
    },
    submitHazard() {
      this.$refs.hazardFormRef.validate(async valid => {
        if (!valid) return
        this.hazardSaving = true
        try {
          const hazard = this.editingHazardId
            ? await updatePatrolHazard(this.editingHazardId, this.hazardForm)
            : await createPatrolHazard(this.hazardTaskId, this.hazardForm)
          for (const f of this.shotFiles) {
            const fd = new FormData()
            fd.append('file', f)
            await uploadPatrolShot(hazard.hazard_id, fd)
          }
          this.$message.success(this.editingHazardId ? '隐患已修改' : '隐患已记录')
          this.hazardDialogVisible = false
          this.reloadDetail()
        } finally { this.hazardSaving = false }
      })
    },
    openConfirm(h) { this.confirmTarget = h; this.confirmForm = { rectify_requirement: h.rectify_requirement || '' }; this.confirmVisible = true },
    async submitConfirm() {
      if (!this.confirmForm.rectify_requirement) { this.$message.warning('请填写整改要求'); return }
      await confirmPatrolHazard(this.confirmTarget.hazard_id, this.confirmForm)
      this.$message.success('已确认并下发整改要求'); this.confirmVisible = false; this.reloadDetail()
    },
    openReview(h) { this.reviewTarget = h; this.reviewForm = { result: 'closed', comment: '' }; this.reviewVisible = true },
    async submitReview() {
      await reviewPatrolHazard(this.reviewTarget.hazard_id, this.reviewForm)
      this.$message.success('复核完成'); this.reviewVisible = false; this.reloadDetail(); this.refresh()
    },
    reloadDetail() { if (this.detail) this.openDetail({ task_id: this.detail.task_id }) },

    // ---- 监测方案文档 ----
    openMonitorEdit() {
      this.monitorForm = { review_opinion: this.detail.review_opinion || '' }
      this.docFiles = []
      this.monitorVisible = true
    },
    onDocChange(file, fileList) {
      this.docFiles = fileList.map(f => f.raw).filter(Boolean)
    },
    async submitMonitor() {
      this.monitorSaving = true
      try {
        const tid = this.detail.task_id
        for (const f of this.docFiles) {
          const fd = new FormData()
          fd.append('file', f)
          await uploadPatrolDoc(tid, fd)
        }
        await updatePatrolTask(tid, { review_opinion: this.monitorForm.review_opinion })
        this.$message.success('已保存')
        this.monitorVisible = false
        this.docFiles = []
        this.reloadDetail()
      } finally {
        this.monitorSaving = false
      }
    },
    async viewDoc(d) {
      try {
        const blob = await getPatrolDocFile(d.doc_id)
        const url = URL.createObjectURL(blob)
        if (d.kind === 'image' || d.kind === 'pdf') window.open(url, '_blank')
        else this.triggerDownload(d.file_name, url)
      } catch (e) { this.$message.error('打开失败') }
    },
    async downloadDoc(d) {
      try {
        const blob = await getPatrolDocFile(d.doc_id)
        this.triggerDownload(d.file_name, URL.createObjectURL(blob))
      } catch (e) { this.$message.error('下载失败') }
    },
    triggerDownload(name, url) {
      const a = document.createElement('a')
      a.href = url
      a.download = name
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    },
    deleteDoc(d) {
      this.$confirm(`确认删除文档「${d.file_name}」？`, '删除确认', { type: 'warning' }).then(async () => {
        await deletePatrolDoc(d.doc_id); this.$message.success('已删除'); this.reloadDetail()
      }).catch(() => {})
    },
    docIcon(d) {
      if (d.kind === 'image') return '🖼'
      if (d.kind === 'word') return '📄'
      return '📕'
    },
    formatSize(n) {
      if (n === null || n === undefined) return ''
      if (n < 1024) return n + ' B'
      if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB'
      return (n / 1024 / 1024).toFixed(1) + ' MB'
    },

    async openDictDialog() { this.dictVisible = true; await this.loadDictItems() },
    async loadDictItems() {
      this.dictLoading = true
      try { this.dictItems = await listPatrolDicts(this.dictType) || [] } finally { this.dictLoading = false }
    },
    openDictEdit(row) {
      this.dictEditingId = row ? row.dict_id : null
      this.dictForm = row ? { label: row.label, sort: row.sort, enabled: row.enabled } : { label: '', sort: 0, enabled: 1 }
      this.dictEditVisible = true
    },
    submitDict() {
      this.$refs.dictFormRef.validate(async valid => {
        if (!valid) return
        this.dictSaving = true
        try {
          const payload = { label: this.dictForm.label, sort: this.dictForm.sort, enabled: this.dictForm.enabled }
          if (this.dictEditingId) await updatePatrolDict(this.dictEditingId, payload)
          else await createPatrolDict({ type: this.dictType, ...payload })
          this.$message.success('保存成功'); this.dictEditVisible = false; await this.loadDictItems()
          this.loadLineDict(); this.loadHazardDicts()
        } finally { this.dictSaving = false }
      })
    },
    doDeleteDict(row) {
      this.$confirm(`确认删除字典项「${row.label}」？`, '删除确认', { type: 'warning' }).then(async () => {
        await deletePatrolDict(row.dict_id); this.$message.success('已删除'); this.loadDictItems(); this.loadLineDict(); this.loadHazardDicts()
      }).catch(() => {})
    }
  }
}
</script>

<style scoped>
.patrol-page { min-height: 100vh; padding: 22px 24px; }
.page-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; }
.page-head h2 { margin: 0; color: #202725; font-size: 22px; font-weight: 600; }
.page-head p { margin: 6px 0 0; color: #7c8783; font-size: 13px; }
.head-left { min-width: 0; }
.mono { font-family: 'SFMono-Regular', Consolas, monospace; color: #246f5d; font-weight: 600; }
.danger-text { color: #f56c6c; }
.muted { color: #9aa5a1; font-size: 12px; }

.stat-cards { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 14px; }
.stat-card { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; padding: 16px 18px; border: 1px solid #e3e7e6; border-radius: 8px; background: #fff; cursor: pointer; text-align: left; }
.stat-card:hover { box-shadow: 0 4px 14px rgba(38, 118, 99, .08); }
.stat-num { color: #202725; font-size: 26px; font-weight: 600; line-height: 1; }
.stat-label { color: #7c8783; font-size: 13px; }

.panel { background: #fff; border: 1px solid #e3e7e6; border-radius: 8px; }
.filter-panel { padding: 16px 18px 0; margin-bottom: 14px; }
.table-panel { padding: 14px 18px; }
.pagination { margin-top: 14px; text-align: right; }

.detail-body { max-height: 68vh; overflow-y: auto; padding-right: 6px; }
.detail-actions { margin: 14px 0; }
.section { margin-top: 20px; }
.section h4 { margin: 0 0 10px; color: #202725; font-size: 15px; }
.section h4 span { color: #7c8783; font-weight: 400; }

.hazard-list { display: flex; flex-direction: column; gap: 10px; }
.hazard-card { border: 1px solid #e3e7e6; border-radius: 6px; padding: 12px 14px; }
.hazard-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.hazard-desc { font-weight: 600; color: #202725; }
.hazard-meta { display: flex; align-items: center; gap: 8px; margin: 8px 0; flex-wrap: wrap; }
.hazard-req { color: #4a5450; font-size: 13px; margin-top: 6px; }
.hazard-ops { margin-top: 8px; }

.record-timeline { display: flex; flex-direction: column; gap: 10px; }
.record-item { border-left: 3px solid #cfe3db; padding-left: 14px; }
.timeline-item { border-left: 3px solid #cfe3db; padding-left: 14px; }
.tl-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.record-head { display: flex; align-items: center; gap: 10px; }
.record-note { color: #4a5450; margin: 6px 0; }
.media-grid { display: flex; gap: 10px; flex-wrap: wrap; }
.media-thumb { width: 120px; height: 90px; border-radius: 4px; }
.media-thumb-wrap { position: relative; width: 120px; height: 90px; }
.media-thumb-wrap .media-thumb { width: 100%; height: 100%; }
.hazard-badge { position: absolute; top: 4px; right: 4px; padding: 0 6px; border-radius: 10px; background: #f56c6c; color: #fff; font-size: 11px; line-height: 18px; cursor: help; }
.media-video { width: 120px; height: 90px; border: 1px solid #e3e7e6; border-radius: 4px; background: #f0f4f2; color: #246f5d; cursor: pointer; }

.dict-toolbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.compact-empty { padding: 26px 0; text-align: center; color: #9aa5a1; }
.compact-empty i { font-size: 30px; }
.compact-empty p { margin: 8px 0 2px; color: #6b7571; }

/* 隐患块 */
.hazard-block { border: 1px solid #fbe3e3; border-radius: 8px; padding: 14px 16px; margin-top: 10px; background: #fefafa; }
.hazard-block.hazard-closed { border-color: #d9edc8; background: #f5fbf3; }

/* 隐患进展栏 */
.hazard-steps { display: flex; align-items: flex-start; margin-bottom: 12px; }
.hazard-step { display: flex; flex-direction: column; align-items: center; flex: 1; position: relative; }
.hazard-step-dot { width: 14px; height: 14px; border-radius: 50%; background: #dcdfe6; border: 3px solid #fff; box-shadow: 0 0 0 2px #dcdfe6; z-index: 1; }
.hazard-step.done .hazard-step-dot { background: #67c23a; box-shadow: 0 0 0 2px #67c23a; }
.hazard-step.current .hazard-step-dot { background: #409eff; box-shadow: 0 0 0 2px #409eff, 0 0 0 6px rgba(64,158,255,0.18); }
.hazard-step-label { margin-top: 6px; font-size: 11px; color: #c0c4cc; white-space: nowrap; }
.hazard-step.done .hazard-step-label { color: #67c23a; }
.hazard-step.current .hazard-step-label { color: #409eff; font-weight: 600; }
.hazard-step-line { position: absolute; top: 7px; left: 50%; width: 100%; height: 2px; background: #dcdfe6; z-index: 0; }
.hazard-step.done .hazard-step-line { background: #67c23a; }
.hazard-step:last-child .hazard-step-line { display: none; }

/* 嵌套整改记录 */
.rectify-list { margin-top: 12px; padding: 12px; background: rgba(255,255,255,0.7); border-radius: 6px; border: 1px dashed #f0d0a0; }
.rectify-title { font-size: 13px; font-weight: 600; color: #e6a23c; margin-bottom: 8px; }
.rectify-item { padding: 8px 0; border-top: 1px solid #f5e6d0; }
.rectify-item:first-child { border-top: none; padding-top: 0; }
.rectify-head { margin-bottom: 4px; }
.rectify-note { color: #4a5450; font-size: 13px; margin-bottom: 6px; }

/* 监测方案 */
.monitor-card { margin: 16px 0; padding: 16px; background: #f8fbfe; border: 1px solid #e3edf7; border-radius: 8px; }
.monitor-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.monitor-title { font-size: 15px; font-weight: 700; color: #2d5d95; }
.monitor-opinion { margin-top: 12px; padding: 12px; background: #fefaf0; border: 1px dashed #f0d0a0; border-radius: 6px; }
.monitor-opinion-label { font-size: 13px; font-weight: 600; color: #e6a23c; margin-bottom: 6px; }
.monitor-opinion-text { font-size: 13px; color: #303133; white-space: pre-wrap; word-break: break-all; }
.monitor-docs { margin-top: 12px; }
.monitor-docs-label { font-size: 13px; font-weight: 600; color: #606266; margin-bottom: 8px; }
.doc-list { display: flex; flex-direction: column; gap: 6px; }
.doc-item { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: #fff; border: 1px solid #ebeef5; border-radius: 6px; }
.doc-icon { font-size: 18px; }
.doc-name { flex: 1; min-width: 0; font-size: 13px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-size { font-size: 12px; color: #a8abb2; white-space: nowrap; }
</style>
