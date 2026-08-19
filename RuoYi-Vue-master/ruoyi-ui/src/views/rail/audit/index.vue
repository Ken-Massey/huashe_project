<template>
  <div class="app-container case-review-page">
    <header class="page-head">
      <div>
        <h2>案例审核</h2>
      </div>
      <el-button icon="el-icon-refresh" @click="reset">重新开始</el-button>
    </header>

    <el-dialog
      title="上传审核资料"
      :visible.sync="uploadDialogVisible"
      width="820px"
      append-to-body
      class="audit-upload-dialog"
    >
      <div v-loading="recognizing || libraryAdding" :element-loading-text="libraryAdding ? '正在从知识库添加文件' : '正在识别并分类项目资料'" class="unified-upload">
        <el-tabs v-model="uploadSourceTab" class="upload-source-tabs" @tab-click="handleUploadSourceTabClick">
          <el-tab-pane label="知识库文件" name="library">
            <div class="library-picker-toolbar">
              <el-input
                v-model.trim="libraryKeyword"
                clearable
                prefix-icon="el-icon-search"
                placeholder="搜索知识库文件名称"
              />
              <el-button icon="el-icon-refresh" :loading="libraryLoading" @click="loadAuditLibraryFiles">刷新</el-button>
              <el-button type="primary" :loading="libraryAdding" :disabled="!selectedLibraryRows.length" @click="addSelectedLibraryFiles">添加所选文件</el-button>
            </div>
            <el-table
              v-loading="libraryLoading"
              class="library-picker-table"
              :data="filteredAuditLibraryRows"
              height="260"
              row-key="key"
              empty-text="暂无可选知识库文件"
              @selection-change="selectedLibraryRows = $event"
            >
              <el-table-column type="selection" width="46" />
              <el-table-column label="文件名称" min-width="260">
                <template slot-scope="{ row }">
                  <div class="library-file-cell">
                    <i :class="row.icon" />
                    <span>
                      <strong :title="row.name">{{ row.name }}</strong>
                      <small>{{ row.originalName }}</small>
                    </span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="来源" prop="sourceLabel" width="110" />
              <el-table-column label="大小" width="90">
                <template slot-scope="{ row }">{{ row.size ? formatFileSize(row.size) : '-' }}</template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="本地文件" name="local">
            <file-drop-zone
              ref="documentsPicker"
              accept=".pdf,.docx,.txt"
              :multiple="true"
              :limit="12"
              hint="支持 PDF、DOCX、TXT；最多 12 个文件，系统自动区分函件、案例和补充附件"
              @input="handleDocumentFiles"
            />
          </el-tab-pane>
        </el-tabs>
        <div v-if="documents.length" class="document-list">
          <div v-for="record in documents" :key="record.id" class="document-row">
            <i :class="record.status === 'failed' ? 'el-icon-warning-outline' : (record.status === 'done' ? 'el-icon-document-checked' : 'el-icon-loading')" />
            <div class="document-name">
              <strong :title="record.file.name">{{ record.file.name }}</strong>
              <small>{{ record.message }}</small>
            </div>
            <el-tag v-if="record.file === letterFile" size="mini" type="success">主函件</el-tag>
            <el-tag v-if="record.file === caseFile" size="mini">主案例</el-tag>
            <el-select v-model="record.role" size="mini" class="role-select" @change="documentRoleChanged(record)">
              <el-option label="函件" value="letter" />
              <el-option label="案例/方案" value="case" />
              <el-option label="补充附件" value="attachment" />
            </el-select>
            <el-button
              class="document-remove"
              type="text"
              icon="el-icon-close"
              title="移除文件"
              @click="removeDocument(record)"
            />
          </div>
        </div>
        <el-alert
          v-if="documents.length && !recognizing"
          class="recognition-alert"
          :title="`已识别 ${documents.length} 个文件，自动填充 ${recognizedFieldCount} 项；请核对文件类型和空白参数。`"
          type="success"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="hasRestoredDocuments"
          class="recognition-alert"
          title="已恢复上次上传的文件记录。浏览器无法自动恢复原始文件本体；如需重新审核，请重新选择对应文件。"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>
      <span slot="footer">
        <el-button @click="uploadDialogVisible = false">关闭</el-button>
        <el-button type="primary" :disabled="!documents.length || recognizing" @click="openDataDialog">确认并核对数据</el-button>
      </span>
    </el-dialog>

    <el-dialog
      title="资料数据确认"
      :visible.sync="dataDialogVisible"
      width="980px"
      append-to-body
      class="audit-data-dialog"
    >
        <el-alert
          v-if="recognizedFieldConflicts.length"
          class="conflict-alert"
          title="检测到多个文件中同一数据的识别结果不一致，请选择本次审核采用的值。"
          type="warning"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="dataDialogMissing.length"
          class="conflict-alert"
          :title="`还有 ${dataDialogMissing.length} 项基础信息未确认：${dataDialogMissing.map(item => item.label).join('、')}`"
          type="error"
          :closable="false"
          show-icon
        />
        <div v-if="dataDialogMissing.length" class="missing-chip-list">
          <el-tag
            v-for="item in dataDialogMissing"
            :key="`${item.tab}_${item.key}`"
            size="small"
            type="danger"
            effect="plain"
            @click="activeTab = item.tab || 'project'"
          >
            {{ item.label }}
          </el-tag>
        </div>
        <div v-if="recognizedFieldConflicts.length" class="conflict-list">
          <div v-for="conflict in recognizedFieldConflicts" :key="conflict.key" class="conflict-row">
            <span class="conflict-label">{{ fieldLabel(conflict.key) }}</span>
            <div class="conflict-options">
              <el-radio-group v-model="conflictSelections[conflict.key]" size="mini" @change="value => applyConflictValue(conflict.key, value)">
                <el-radio-button v-for="option in conflict.options" :key="option.normalized" :label="option.normalized">
                  {{ option.display }}
                </el-radio-button>
              </el-radio-group>
              <div class="conflict-source-list">
                <span v-for="option in conflict.options" :key="`src_${option.normalized}`" class="conflict-source">
                  {{ option.display }}：{{ formatConflictSources(option.sources) }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div class="parameter-area">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="项目与函件" name="project">
              <el-form :model="form" label-width="104px" class="parameter-form">
                <el-row :gutter="14">
                  <el-col :xs="24" :md="12">
                    <el-form-item label="项目名称" required>
                      <el-autocomplete
                        v-model.trim="form.project_name"
                        class="project-name-input"
                        value-key="name"
                        clearable
                        :fetch-suggestions="queryArchiveProjects"
                        :debounce="0"
                        :trigger-on-focus="true"
                        :loading="archiveLoading"
                        placeholder="自动识别，也可输入或选择历史项目"
                        @input="projectNameInputChanged"
                        @select="projectSuggestionSelected"
                        @blur="projectNameInputBlur"
                      />
                      <div
                        v-if="form.project_name && form.project_stage"
                        class="archive-field-status"
                        :class="{ locked: archiveStageLocked }"
                        :title="archiveInlineMessage"
                      >
                        <i :class="archiveStageLocked ? 'el-icon-warning-outline' : 'el-icon-folder-checked'" />
                        <span>{{ archiveInlineMessage }}</span>
                      </div>
                      <div
                        v-if="inheritedFormSource"
                        class="archive-field-status inherited"
                        :title="inheritedFormMessage"
                      >
                        <i class="el-icon-refresh-left" />
                        <span>{{ inheritedFormMessage }}</span>
                      </div>
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :md="12"><el-form-item label="收函单位"><el-input v-model.trim="form.applicant" maxlength="120" /></el-form-item></el-col>
                  <el-col :xs="24" :md="8"><el-form-item label="项目类型"><el-select v-model="form.project_type" placeholder="识别不到请人工选择"><el-option label="基坑" value="基坑" /></el-select></el-form-item></el-col>
                  <el-col :xs="24" :md="8">
                    <el-form-item label="项目阶段" required>
                      <el-select v-model="stageSelection" placeholder="自动识别，也可选择阶段" @change="stageSelectionChanged">
                        <el-option v-for="item in stageChoices" :key="item.value" :label="item.label" :value="item.value" />
                      </el-select>
                      <el-input
                        v-if="stageSelection === 'custom'"
                        v-model.trim="customStageName"
                        class="custom-stage-input"
                        maxlength="120"
                        placeholder="请输入自定义阶段名称"
                        @change="customStageChanged"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :md="8"><el-form-item label="相对关系"><el-select v-model="form.relative_relationship" placeholder="识别不到请人工选择"><el-option v-for="v in relations" :key="v" :label="v" :value="v" /></el-select></el-form-item></el-col>
                </el-row>
                <el-form-item label="涉及其他"><el-checkbox-group v-model="form.other_involvements"><el-checkbox v-for="v in otherTypes" :key="v" :label="v" /></el-checkbox-group></el-form-item>
              </el-form>
            </el-tab-pane>
            <el-tab-pane label="地铁结构" name="metro">
              <el-form :model="form" label-width="138px" class="parameter-form">
                <el-row :gutter="14">
                  <el-col :xs="24" :md="12"><el-form-item label="地铁线路"><el-input v-model.trim="form.metro_line_name" placeholder="例如：1号线" /></el-form-item></el-col>
                  <el-col :xs="24" :md="12"><el-form-item label="地铁区间"><el-input v-model.trim="form.metro_section_name" /></el-form-item></el-col>
                  <el-col :xs="24" :md="8"><el-form-item label="结构形式"><el-select v-model="form.structure_method" placeholder="识别不到请人工选择"><el-option v-for="v in methods" :key="v" :label="v" :value="v" /></el-select></el-form-item></el-col>
                  <el-col :xs="24" :md="8"><el-form-item label="结构状态"><el-select v-model="form.structure_condition" placeholder="识别不到请人工选择"><el-option label="较好" value="较好" /><el-option label="较差" value="较差" /></el-select></el-form-item></el-col>
                  <el-col :xs="24" :md="8">
                    <el-form-item label="结构埋深（m）">
                      <el-input v-model.trim="form.buried_depth_m" type="number" min="0" step="0.01" placeholder="识别不到请人工填写" />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :md="8">
                    <el-form-item label="结构宽度D（m）">
                      <el-input v-model.trim="form.outer_diameter_or_width_m" type="number" min="0" step="0.01" placeholder="识别不到请人工填写" />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :md="8"><el-form-item label="特殊区段"><el-select v-model="form.is_special_section" placeholder="识别不到可留空"><el-option label="是" :value="true" /><el-option label="否" :value="false" /></el-select></el-form-item></el-col>
                  <el-col :xs="24" :md="8"><el-form-item label="结构病害"><el-select v-model="form.disease_severity" :placeholder="diseaseSeverityPlaceholder" :disabled="form.structure_condition !== '较差'"><el-option v-for="v in diseaseSeverityOptions" :key="v" :label="v" :value="v" /></el-select></el-form-item></el-col>
                </el-row>
              </el-form>
            </el-tab-pane>
            <el-tab-pane label="基坑与地质" name="pit">
              <el-form :model="form" label-width="132px" class="parameter-form">
                <el-row :gutter="14">
                  <el-col v-if="form.project_stage==='出让'" :xs="24" :md="12">
                    <el-form-item label="用地性质">
                      <el-select v-model="landUseSelection" placeholder="请选择" @change="landUseChanged"><el-option v-for="v in landUseTypes" :key="v" :label="v" :value="v" /></el-select>
                    </el-form-item>
                  </el-col>
                  <el-col v-if="form.project_stage==='出让' && landUseSelection==='其他'" :xs="24" :md="12"><el-form-item label="其他用地性质"><el-input v-model.trim="form.land_use_type" /></el-form-item></el-col>
                  <el-col v-if="form.project_stage!=='出让'" :xs="24" :md="8">
                    <el-form-item label="基坑深度（m）">
                      <el-input
                        v-model.trim="form.pit_depth_m"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="未填写则留空"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col v-if="form.project_stage==='规划'" :xs="24" :md="8">
                    <el-form-item label="基坑长度（m）">
                      <el-input
                        v-model.trim="form.pit_length_m"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="水平/竖向至少填写一项"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :md="8">
                    <el-form-item label="水平净距（m）">
                      <el-input
                        v-model.trim="form.minimum_horizontal_clearance_m"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="水平/竖向至少填写一项"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :md="8">
                    <el-form-item label="竖向净距（m）">
                      <el-input
                        v-model.trim="form.minimum_vertical_clearance_m"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="未填写则留空"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col v-if="['设计','施工'].includes(form.project_stage)" :xs="24" :md="12">
                    <el-form-item label="降水方式">
                      <el-select v-model="form.dewatering_method" clearable filterable placeholder="请选择降水方式">
                        <el-option v-for="v in dewateringMethodOptions" :key="v" :label="v" :value="v" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col v-if="['设计','施工'].includes(form.project_stage) && form.dewatering_method === '其他'" :xs="24" :md="12">
                    <el-form-item label="其他降水">
                      <el-input v-model.trim="form.dewatering_method_other" placeholder="请填写具体降水方式" />
                    </el-form-item>
                  </el-col>
                  <el-col :xs="24" :md="8"><el-form-item label="地段区域"><el-select v-model="form.terrain_zone" placeholder="识别不到请人工选择"><el-option label="漫滩" value="漫滩" /><el-option label="非漫滩" value="非漫滩" /></el-select></el-form-item></el-col>
                  <el-col :xs="24" :md="8"><el-form-item label="软弱土"><el-select v-model="form.is_soft_soil" placeholder="识别不到请人工选择"><el-option label="是" :value="true" /><el-option label="否" :value="false" /></el-select></el-form-item></el-col>
                  <el-col :xs="24" :md="8"><el-form-item label="复杂地质水文"><el-select v-model="form.is_complex_geology_or_hydrology" placeholder="识别不到请人工选择"><el-option label="是" :value="true" /><el-option label="否" :value="false" /></el-select></el-form-item></el-col>
                </el-row>
                <el-form-item label="支护构件"><el-checkbox-group v-model="form.support_components"><el-checkbox v-for="v in supports" :key="v" :label="v" /></el-checkbox-group></el-form-item>
                <el-form-item label="保护区位置"><el-select v-model="form.protection_zone_location" placeholder="识别不到请人工选择"><el-option v-for="v in protectionZoneLocations" :key="v" :label="v" :value="v" /></el-select></el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </div>
        <span slot="footer">
          <el-button @click="dataDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmDataDialog">确认数据</el-button>
        </span>
    </el-dialog>

    <section class="result-panel">
      <div class="result-head">
        <el-tag v-if="auditSession" size="small" type="success">第 {{ currentDisplayVersion }} 版</el-tag>
      </div>
      <el-alert
        v-if="auditInputChanged"
        class="reaudit-alert"
        type="warning"
        title="资料或参数已修改，当前审核结果已不是最新。点击“重新审核”即可基于当前数据重新生成，无需重新上传。"
        show-icon
        :closable="false"
      />
      <div class="audit-chat-shell">
        <div class="audit-chat-scroll">
          <div v-if="!auditSession && !auditSubmitting && !chatMessages.length" class="empty-state">
            <i class="el-icon-chat-dot-square" />
            <p>上传资料并确认数据后，将在这里生成审核结果</p>
          </div>
          <div v-for="message in visibleChatMessages" :key="message.message_id" class="chat-row" :class="message.role">
            <span class="chat-avatar">{{ message.role === 'user' ? '我' : 'AI' }}</span>
            <div class="chat-bubble" :class="{ 'snapshot-bubble': hasMessageSnapshot(message) }">
              <template v-if="!hasMessageSnapshot(message)">
                <p class="plain-ai-message">{{ formatReadableText(message.content) }}</p>
                <div v-if="message.attachments && message.attachments.length" class="chat-attachment-list">
                  <div
                    v-for="attachment in message.attachments"
                    :key="`${message.message_id}_${attachment.id || attachment.name}`"
                    class="chat-attachment-card"
                    :title="attachment.name"
                  >
                    <span class="composer-file-icon">{{ fileTypeBadge(attachment.name) }}</span>
                    <span class="composer-file-meta">
                      <strong>{{ attachment.name }}</strong>
                      <small>{{ fileKindText(attachment.name) }} · {{ formatFileSize(attachment.size) }}</small>
                    </span>
                    <el-tag
                      size="mini"
                      effect="plain"
                      :type="attachment.role === 'letter' ? 'success' : (attachment.role === 'case' ? '' : 'info')"
                    >
                      {{ roleLabel(attachment.role) }}
                    </el-tag>
                  </div>
                </div>
              </template>
              <div v-else-if="isLatestSnapshot(message)" class="message-review-list latest">
                <div class="review-bubble-head">
                  <div>
                    <strong>这是当前最新版审核结果</strong>
                    <small>可直接编辑单条结果，也可以在下方输入修改意见让我调整。</small>
                  </div>
                  <el-button size="mini" type="primary" plain icon="el-icon-plus" @click="openReviewItemDialog()">新增条目</el-button>
                </div>
                <el-empty v-if="!messageReviewItems(message).length && !messageOverallOpinion(message)" description="暂无审核条目" />
                <div v-if="messageOverallOpinion(message)" class="overall-review-card leading">
                  <h4>综合评价</h4>
                  <p>{{ displayOverallOpinion(messageOverallOpinion(message)) }}</p>
                </div>
                <article v-for="item in messageReviewItems(message)" :key="`${message.message_id}_${item.item_id || item.order_no}`" class="review-item-card">
                  <div class="review-item-head">
                    <span class="review-order">{{ item.order_no }}</span>
                    <div>
                      <h4>{{ displayReviewTitle(item) }}</h4>
                      <el-tag v-if="item.risk_level" size="mini" :type="severityType(item.risk_level)">{{ item.risk_level }}</el-tag>
                    </div>
                    <div class="review-actions">
                      <el-button size="mini" type="text" icon="el-icon-edit" @click="openReviewItemDialog(item)">编辑</el-button>
                      <el-button size="mini" type="text" class="danger-link" icon="el-icon-delete" @click="removeReviewItem(item)">删除</el-button>
                    </div>
                  </div>
                  <div v-if="displayReviewOpinion(item)" class="review-conclusion">
                    <span>意见</span>{{ displayReviewOpinion(item) }}
                  </div>
                </article>
              </div>
              <div v-else class="message-review-list collapsed">
                <div class="snapshot-summary-line">
                  <span>{{ snapshotVersionLabel(message) }}审核意见</span>
                  <el-button type="text" size="mini" @click="toggleSnapshot(message)">
                    {{ isSnapshotExpanded(message) ? '收起' : '详情' }}
                  </el-button>
                </div>
                <div v-if="isSnapshotExpanded(message)" class="snapshot-detail">
                  <div v-if="messageOverallOpinion(message)" class="overall-review-card compact leading">
                    <h4>综合评价</h4>
                    <p>{{ displayOverallOpinion(messageOverallOpinion(message)) }}</p>
                  </div>
                  <article v-for="item in messageReviewItems(message)" :key="`${message.message_id}_${item.order_no}`" class="review-item-card compact">
                    <div class="review-item-head">
                      <span class="review-order">{{ item.order_no }}</span>
                      <div>
                        <h4>{{ displayReviewTitle(item) }}</h4>
                        <el-tag v-if="item.risk_level" size="mini" :type="severityType(item.risk_level)">{{ item.risk_level }}</el-tag>
                      </div>
                    </div>
                    <div v-if="displayReviewOpinion(item)" class="review-conclusion">
                      <span>意见</span>{{ displayReviewOpinion(item) }}
                    </div>
                  </article>
                </div>
              </div>
            </div>
          </div>
          <div v-if="auditSubmitting" class="chat-row assistant">
            <span class="chat-avatar">AI</span>
            <div class="chat-bubble">
              <p class="thinking-text"><i class="el-icon-loading" /> 正在审核资料，请稍候……</p>
            </div>
          </div>
          <div v-else-if="chatSubmitting" class="chat-row assistant">
            <span class="chat-avatar">AI</span>
            <div class="chat-bubble thinking-bubble">
              <p class="thinking-text">
                <span class="thinking-dots only-dots" aria-label="正在思考"><i /> <i /> <i /></span>
              </p>
            </div>
          </div>
        </div>
        <div class="composer-sticky-zone">
          <div class="chat-input-bar chat-composer">
            <div class="composer-input-surface">
              <div v-if="documents.length" class="composer-file-cards">
                <div
                  v-for="record in documents"
                  :key="`composer_${record.id}`"
                  class="composer-file-card"
                  :title="record.file && record.file.name"
                >
                  <span class="composer-file-icon">{{ fileTypeBadge(record.file && record.file.name) }}</span>
                  <span class="composer-file-meta">
                    <strong>{{ record.file && record.file.name }}</strong>
                    <small>{{ fileKindText(record.file && record.file.name) }} · {{ formatFileSize(record.file && record.file.size) }}</small>
                  </span>
                  <el-tag
                    size="mini"
                    effect="plain"
                    :type="record.role === 'letter' ? 'success' : (record.role === 'case' ? '' : 'info')"
                  >
                    {{ record.role === 'letter' ? '函件' : (record.role === 'case' ? '案例' : '附件') }}
                  </el-tag>
                  <el-button
                    class="composer-file-remove"
                    type="text"
                    icon="el-icon-close"
                    title="移除文件"
                    :disabled="recognizing || auditSubmitting"
                    @click="removeDocument(record)"
                  />
                </div>
              </div>
              <el-input
                v-model.trim="chatInstruction"
                class="chat-composer-input"
                type="textarea"
                :rows="2"
                maxlength="1000"
                :disabled="chatSubmitting || auditSubmitting"
                placeholder="输入“开始审核”发起审核；也可以输入修改意见，或点击右侧上传资料"
                @keydown.native="handleComposerKeydown"
              />
            </div>
            <div class="chat-composer-footer">
              <div class="composer-left">
                <el-button class="composer-pill" size="mini" plain disabled>
                  <i class="el-icon-cpu" /> 智审助手
                </el-button>
              </div>
              <div class="composer-tools">
                <el-button class="composer-icon-btn" icon="el-icon-edit-outline" :disabled="recognizing || auditSubmitting" title="查看/修改数据" @click="openDataDialog" />
                <el-button class="composer-icon-btn" icon="el-icon-paperclip" :disabled="recognizing || auditSubmitting" title="上传/查看资料" @click="openUploadDialog" />
                <el-button class="composer-send-btn" circle icon="el-icon-position" :loading="chatSubmitting || auditSubmitting" :disabled="!canSendComposer || chatSubmitting || auditSubmitting" title="发送" @click="sendChatInstruction" />
              </div>
            </div>
            <div class="result-actions">
              <span>满意后可将最新版审核结果写入项目档案；不点击则不会入档。</span>
              <div>
                <el-button icon="el-icon-folder-checked" :loading="archiveWriting" :disabled="!auditSession" @click="writeArchive(false)">写入档案</el-button>
                <el-button type="primary" icon="el-icon-document" :loading="replySubmitting" :disabled="!auditSession" @click="generateLatestReply">生成复函</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <el-dialog :title="itemDialogTitle" :visible.sync="itemDialogVisible" width="680px" append-to-body>
      <el-form label-width="86px">
        <el-form-item label="审核主题" required><el-input v-model.trim="itemForm.title" /></el-form-item>
        <el-form-item label="风险等级"><el-select v-model="itemForm.risk_level" clearable placeholder="可不填写"><el-option v-for="v in ['高','中','低','提示']" :key="v" :label="v" :value="v" /></el-select></el-form-item>
        <el-form-item label="审核结论" required><el-input v-model.trim="itemForm.conclusion" type="textarea" :rows="5" /></el-form-item>
        <el-form-item label="审核建议"><el-input v-model.trim="itemForm.recommendation" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="依据"><el-input v-model.trim="itemForm.basisText" type="textarea" :rows="3" placeholder="可填写规程条款或依据，多条可换行" /></el-form-item>
      </el-form>
      <span slot="footer">
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="itemSaving" @click="saveReviewItem">保存</el-button>
      </span>
    </el-dialog>

  </div>
</template>

<script>
import { saveAs } from 'file-saver'
import FileDropZone from '../components/FileDropZone.vue'
import {
  createFullTask, createReplyTask, recognizeReplyLetter,
  getTask, getTaskResult, getAuditSession,
  createAuditSessionItem, updateAuditSessionItem, deleteAuditSessionItem,
  reviseAuditSession, writeAuditSessionToArchive, generateAuditSessionReply,
  listKnowledge, listLibraryAssets, downloadKnowledgeFile, downloadLibraryAsset
} from '@/api/rail/audit'
import {
  listArchiveProjects, getArchiveProject,
  getPreviousStageAudits
} from '@/api/rail/archive'

function defaultForm() {
  return {
    project_name: '', applicant: '', project_type: '基坑', project_stage: '', relative_relationship: '', other_involvements: [],
    metro_line_name: '', metro_section_name: '', structure_method: '', structure_condition: '', buried_depth_m: null,
    outer_diameter_or_width_m: null, is_special_section: null, disease_severity: '', land_use_type: '',
    pit_depth_m: null, pit_length_m: null, minimum_horizontal_clearance_m: null, minimum_vertical_clearance_m: null,
    dewatering_method: '', dewatering_method_other: '', terrain_zone: '', is_soft_soil: null, is_complex_geology_or_hydrology: null,
    support_components: [], protection_zone_location: '',
    incoming_letter_excerpt: ''
  }
}

const AUDIT_DRAFT_KEY = 'rail.audit.latestDraft'
const AUDIT_DRAFT_TTL = 30 * 60 * 1000

export default {
  name: 'RailAudit',
  components: { FileDropZone },
  data() {
    return {
      activeTab: 'project', documents: [], recognizing: false, documentSequence: 0,
      auditTaskId: '', auditResult: null, replyResult: null, auditSubmitting: false, replySubmitting: false,
      auditSession: null, reviewItems: [], chatMessages: [], chatInstruction: '', chatSubmitting: false,
      expandedSnapshotIds: {},
      prepPanelExpanded: false,
      uploadDialogVisible: false,
      uploadSourceTab: 'library',
      libraryLoading: false,
      libraryAdding: false,
      libraryKeyword: '',
      libraryCases: [],
      libraryAssets: [],
      selectedLibraryRows: [],
      dataDialogVisible: false,
      dataDialogMissing: [],
      conflictSelections: {},
      auditPollingTimer: null,
      baselineAuditSignature: '',
      archiveWriting: false,
      itemDialogVisible: false, itemSaving: false, editingItemId: '',
      itemForm: { title: '', risk_level: '', conclusion: '', recommendation: '', basisText: '' },
      archiveProjects: [], archiveLoading: false, selectedArchiveProjectId: '', selectedArchiveStageId: '',
      selectedArchiveProject: null, historyPreview: { record_count: 0, records: [] }, archiveLookupSequence: 0,
      inheritedFormSource: null,
      projectNameLookupTimer: null,
      form: defaultForm(), stageSelection: '', customStageName: '', landUseSelection: '',
      stageChoices: [
        { label: '出让阶段', value: '出让' },
        { label: '规划阶段', value: '规划' },
        { label: '设计阶段', value: '设计' },
        { label: '施工阶段', value: '施工' },
        { label: '自定义', value: 'custom' }
      ],
      relations: ['单侧', '双侧'], methods: ['明挖', '暗挖（矿山法）', '盾构', '高架'],
      landUseTypes: ['居住用地', '商业服务业用地', '工业用地', '公共管理与公共服务用地', '交通运输用地', '公用设施用地', '绿地与开敞空间用地', '混合用地', '其他'],
      otherTypes: ['红线', '接口', '临时结构', '协议'],
      supports: ['围护桩', '地下连续墙', '非挤土工程桩', '挤土工程桩', '锚杆', '锚索', '土钉', '其他'],
      dewateringMethods: ['无', '明沟排水', '集水明排', '轻型井点降水', '喷射井点降水', '管井降水', '深井井点降水', '截水帷幕', '止水帷幕', '其他'],
      protectionZoneLocations: ['特别保护区', '控制保护区（非特别保护区）', '保护区外'],
      decisionItems: [
        { key: 'setback_distance', label: '退让距离' }, { key: 'impact_level', label: '影响等级' },
        { key: 'safety_assessment', label: '安全评估' }, { key: 'protective_monitoring', label: '保护监测' }
      ]
    }
  },
  computed: {
    archiveStages() { return (this.selectedArchiveProject && this.selectedArchiveProject.stages || []).filter(item => item.status === 'active') },
    selectedArchiveStage() { return this.archiveStages.find(item => item.stage_id === this.selectedArchiveStageId) || null },
    archiveStageLocked() {
      return Boolean(this.selectedArchiveStage && ['pending', 'running'].includes(this.selectedArchiveStage.audit_status))
    },
    archiveBinding() {
      if (!this.selectedArchiveProjectId) return {}
      return {
        project_id: this.selectedArchiveProjectId,
        stage_id: this.selectedArchiveStageId || '',
        stage_name: this.form.project_stage || ''
      }
    },
    archiveInlineMessage() {
      if (this.archiveStageLocked) return '该项目阶段正在审核，请选择其他阶段。'
      if (!this.selectedArchiveProject) return `档案中暂无“${this.form.project_name}”；不点击“写入档案”则不会创建档案。`
      if (!this.selectedArchiveStage) return `已匹配项目“${this.selectedArchiveProject.name}”；该阶段将在点击“写入档案”时再创建。`
      if (this.selectedArchiveStage.audit_status === 'success') return '该阶段已有审核记录；写入档案时会提示确认是否覆盖。'
      const count = Number(this.historyPreview.record_count || 0)
      return `已匹配项目档案；本次审核将参考前序 ${count} 个阶段记录，完成后可手动写入“${this.selectedArchiveStage.name}”阶段。`
    },
    inheritedFormMessage() {
      if (!this.inheritedFormSource) return ''
      return `已带入上一阶段“${this.inheritedFormSource.stage_name || '已审核阶段'}”的参数，可修改后重新审核。`
    },
    letterRecord() { return this.documents.find(item => item.role === 'letter' && this.isUploadableDocument(item)) || null },
    caseRecord() { return this.documents.find(item => item.role === 'case' && this.isUploadableDocument(item)) || null },
    letterFile() { return this.letterRecord && this.letterRecord.file },
    caseFile() { return this.caseRecord && this.caseRecord.file },
    hasAnyFile() { return this.documents.some(item => this.isUploadableDocument(item)) },
    auditLibraryRows() {
      const caseRows = (this.libraryCases || []).map(item => ({
        key: `case_${item.case_id}`,
        type: 'case',
        id: item.case_id,
        name: item.case_name || item.original_file_name || '案例文件',
        originalName: item.original_file_name || item.case_name || '',
        size: item.file_size || 0,
        sourceLabel: '案例库',
        icon: 'el-icon-document-checked'
      }))
      const assetRows = (this.libraryAssets || []).map(item => ({
        key: `asset_${item.asset_id}`,
        type: 'asset',
        id: item.asset_id,
        name: item.display_name || item.original_file_name || '资料附件',
        originalName: item.original_file_name || item.display_name || '',
        size: item.file_size || 0,
        sourceLabel: '案例文件',
        icon: this.assetIconByKind(item.file_kind)
      }))
      return [...caseRows, ...assetRows].filter(item => /\.(pdf|docx|txt)$/i.test(item.originalName || item.name || ''))
    },
    filteredAuditLibraryRows() {
      const keyword = String(this.libraryKeyword || '').trim().toLowerCase()
      if (!keyword) return this.auditLibraryRows
      return this.auditLibraryRows.filter(item => [item.name, item.originalName, item.sourceLabel].some(value => String(value || '').toLowerCase().includes(keyword)))
    },
    currentDisplayVersion() {
      const count = (this.visibleChatMessages || []).filter(message => this.hasMessageSnapshot(message)).length
      return count || Number(this.auditSession && this.auditSession.current_version) || 1
    },
    canSendComposer() {
      return Boolean(String(this.chatInstruction || '').trim() || this.hasAnyFile)
    },
    uploadableDocumentCount() { return this.documents.filter(item => this.isUploadableDocument(item)).length },
    restoredDocumentCount() { return this.documents.filter(item => item && item.restored).length },
    hasRestoredDocuments() { return this.restoredDocumentCount > 0 },
    hasOnlyRestoredDocuments() { return this.documents.length > 0 && this.uploadableDocumentCount === 0 },
    currentAuditSignature() { return this.auditInputSignature() },
    auditInputChanged() {
      return Boolean((this.auditSession || this.auditResult) && this.baselineAuditSignature && this.currentAuditSignature !== this.baselineAuditSignature)
    },
    auditButtonText() {
      if (this.auditSubmitting) return this.auditInputChanged ? '重新审核中' : '审核中'
      return this.auditInputChanged ? '重新审核' : '开始审核'
    },
    reviewBriefText() {
      const fileText = this.hasOnlyRestoredDocuments
        ? `已保留上次 ${this.restoredDocumentCount} 个文件记录；如需重新审核请重新选择文件`
        : (this.documents.length ? `已上传 ${this.uploadableDocumentCount || this.documents.length} 个文件` : '尚未上传文件')
      const projectName = String(this.form.project_name || '').trim()
      const stageName = String(this.form.project_stage || '').trim()
      const relation = String(this.form.relative_relationship || '').trim()
      const dataParts = [projectName, stageName ? `${stageName}阶段` : '', relation].filter(Boolean)
      const dataText = dataParts.length ? dataParts.join('｜') : '项目数据待确认'
      if (this.recognizing) return `${fileText}，正在识别资料……`
      if (this.auditSession) return `${fileText}，${dataText}；已生成审核结果，可继续对话修改。`
      return `${fileText}，${dataText}；点击“上传/查看资料”补充资料，确认后即可开始审核。`
    },
    auditReviewItems() {
      return (this.reviewItems || []).filter(item => !this.isOverallReviewItem(item))
    },
    currentOverallOpinion() {
      const metadata = this.auditSession && this.auditSession.metadata
      const latest = this.auditSession && this.auditSession.latest_result
      const overall = this.extractOverallOpinion(metadata, this.reviewItems) || this.extractOverallOpinion(latest, this.reviewItems)
      if (!overall) return overall
      return {
        ...overall,
        conclusion: this.displayOverallOpinion(overall)
      }
    },
    recognizedFieldCount() {
      const keys = new Set()
      this.documents.forEach(item => Object.keys(item.fields || {}).forEach(key => keys.add(key)))
      return keys.size
    },
    recognizedFieldConflicts() {
      const valuesByKey = {}
      this.documents.forEach(item => {
        Object.keys(item.fields || {}).forEach(key => {
          const value = item.fields[key]
          const normalized = this.normalizeConflictValue(value)
          if (normalized === '') return
          if (!valuesByKey[key]) valuesByKey[key] = {}
          if (!valuesByKey[key][normalized]) valuesByKey[key][normalized] = { value, sources: [] }
          valuesByKey[key][normalized].sources.push(item.file && item.file.name)
        })
      })
      return Object.keys(valuesByKey)
        .map(key => ({
          key,
          options: Object.values(valuesByKey[key]).map(item => ({
            value: item.value,
            normalized: this.normalizeConflictValue(item.value),
            display: this.normalizeConflictValue(item.value),
            sources: item.sources
          }))
        }))
        .filter(item => item.options.length > 1)
    },
    decisions() {
      const result = this.auditResult || this.replyResult
      return result && result.summary && result.summary.decision_summary
    },
    riskReport() { return this.auditResult && this.auditResult.dynamic_regulation_audit && this.auditResult.dynamic_regulation_audit.risk_report },
    allRiskSections() {
      if (!this.riskReport) return []
      return [...(this.riskReport.compliance_sections || this.riskReport.risk_sections || []), ...(this.riskReport.engineering_risk_sections || [])]
    },
    generatedOpinions() {
      const details = (this.auditResult && this.auditResult.audit_details) || {}
      return details.generated_opinions || (this.auditResult && this.auditResult.dynamic_regulation_opinions) || []
    },
    visibleChatMessages() {
      return (this.chatMessages || []).filter(message => !this.isUploadOnlyChatMessage(message))
    },
    latestAssistantSnapshotMessageId() {
      const messages = this.visibleChatMessages || []
      for (let index = messages.length - 1; index >= 0; index -= 1) {
        const message = messages[index]
        if (this.hasMessageSnapshot(message)) {
          return message.message_id
        }
      }
      return ''
    },
    bestMatch() { return this.auditResult && this.auditResult.advice_result && this.auditResult.advice_result.best_match },
    matchScore() {
      const value = this.bestMatch && (this.bestMatch.score == null ? this.bestMatch.similarity : this.bestMatch.score)
      return value == null ? '-' : `${(Number(value) * 100).toFixed(1)}%`
    },
    overallRiskType() {
      const value = (this.riskReport && this.riskReport.overall_risk_level) || ''
      return value.includes('重大') || value.includes('高') ? 'danger' : (value.includes('中') ? 'warning' : (value.includes('低') ? 'success' : 'info'))
    },
    overallSummary() {
      if (!this.riskReport) return ''
      const level = this.riskReport.overall_risk_level || '待分析'
      const parts = [
        `本项目综合风险等级为${level}。`,
        this.humanizeAuditText(this.riskReport.overview),
        this.humanizeAuditText(this.riskReport.overall_conclusion)
      ].filter(Boolean)
      return [...new Set(parts)].join(' ')
    },
    itemDialogTitle() { return this.editingItemId ? '编辑审核条目' : '新增审核条目' },
    dewateringMethodOptions() {
      const options = [...this.dewateringMethods]
      const value = String(this.form.dewatering_method || '').trim()
      if (value && !options.includes(value)) options.unshift(value)
      return options
    },
    diseaseSeverityOptions() {
      if (this.form.structure_condition === '较好') return ['无明显病害']
      if (this.form.structure_condition === '较差') return ['一般', '严重']
      return ['无明显病害', '一般', '严重']
    },
    diseaseSeverityPlaceholder() {
      if (this.form.structure_condition === '较好') return '自动填充为无明显病害'
      if (this.form.structure_condition === '较差') return '请选择一般或严重'
      return '请先选择结构状态'
    }
  },
  watch: {
    form: {
      deep: true,
      handler() {
        if (this.dataDialogVisible) this.dataDialogMissing = this.collectMissingAuditFields()
        this.saveAuditDraft()
      }
    },
    stageSelection() { this.saveAuditDraft() },
    customStageName() { this.saveAuditDraft() },
    landUseSelection() { this.saveAuditDraft() },
    'form.structure_condition'(value) { this.syncDiseaseSeverity(value) },
    'form.dewatering_method'(value) {
      if (value !== '其他' && this.form.dewatering_method_other) this.form.dewatering_method_other = ''
    }
  },
  created() {
    if (this.$route.query.sessionId) {
      this.openRouteAuditSession()
    } else {
      this.restoreAuditDraft()
      this.loadArchiveSelection()
    }
  },
  beforeDestroy() {
    if (this.projectNameLookupTimer) clearTimeout(this.projectNameLookupTimer)
    this.stopAuditPolling()
    this.saveAuditDraft()
  },
  methods: {
    openUploadDialog() {
      this.uploadDialogVisible = true
      if (this.uploadSourceTab === 'library' && !this.libraryCases.length && !this.libraryAssets.length) {
        this.loadAuditLibraryFiles()
      }
    },
    handleUploadSourceTabClick(tab) {
      if (tab && tab.name === 'library' && !this.libraryCases.length && !this.libraryAssets.length) {
        this.loadAuditLibraryFiles()
      }
    },
    async loadAuditLibraryFiles() {
      this.libraryLoading = true
      try {
        const [cases, assets] = await Promise.all([
          listKnowledge({ includeInactive: false }),
          listLibraryAssets({ library_type: 'case' })
        ])
        this.libraryCases = Array.isArray(cases) ? cases : []
        this.libraryAssets = Array.isArray(assets) ? assets : []
        this.selectedLibraryRows = []
      } catch (error) {
        this.$message.error('知识库文件加载失败，请检查服务状态')
      } finally {
        this.libraryLoading = false
      }
    },
    assetIconByKind(kind) {
      if (kind === 'image') return 'el-icon-picture-outline'
      if (kind === 'cad' || kind === 'bim') return 'el-icon-copy-document'
      if (kind === 'archive') return 'el-icon-box'
      return 'el-icon-document'
    },
    mimeTypeByName(name) {
      const suffix = String(name || '').split('.').pop().toLowerCase()
      if (suffix === 'pdf') return 'application/pdf'
      if (suffix === 'docx') return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      if (suffix === 'txt') return 'text/plain'
      return 'application/octet-stream'
    },
    async addSelectedLibraryFiles() {
      const rows = Array.isArray(this.selectedLibraryRows) ? this.selectedLibraryRows : []
      if (!rows.length) return
      this.libraryAdding = true
      try {
        const files = []
        for (const row of rows) {
          const blob = row.type === 'case'
            ? await downloadKnowledgeFile(row.id)
            : await downloadLibraryAsset(row.id)
          const fileName = row.originalName || row.name || '知识库文件'
          const file = new File([blob], fileName, {
            type: blob.type || this.mimeTypeByName(fileName),
            lastModified: Date.now()
          })
          Object.defineProperty(file, '__railAuditId', {
            value: `knowledge_${row.type}_${row.id}`,
            enumerable: false
          })
          files.push(file)
        }
        await this.handleDocumentFiles(files)
        this.$message.success(`已从知识库添加 ${files.length} 个文件`)
      } catch (error) {
        this.$message.error('知识库文件添加失败，请稍后重试')
      } finally {
        this.libraryAdding = false
      }
    },
    openDataDialog() {
      this.refreshConflictSelections()
      this.dataDialogMissing = this.collectMissingAuditFields()
      this.dataDialogVisible = true
    },
    shortFileName(name) {
      const text = String(name || '未命名文件')
      return text.length > 22 ? `${text.slice(0, 10)}…${text.slice(-9)}` : text
    },
    fileTypeBadge(name) {
      const ext = String(name || '').split('.').pop().toLowerCase()
      if (ext === 'pdf') return 'PDF'
      if (ext === 'doc' || ext === 'docx') return 'W'
      if (ext === 'txt') return 'TXT'
      return '文'
    },
    fileKindText(name) {
      const ext = String(name || '').split('.').pop().toLowerCase()
      if (ext === 'pdf') return 'PDF'
      if (ext === 'doc' || ext === 'docx') return 'Word'
      if (ext === 'txt') return 'TXT'
      return '文件'
    },
    formatFileSize(size) {
      const value = Number(size || 0)
      if (!value) return '未知大小'
      if (value < 1024) return `${value}B`
      if (value < 1024 * 1024) return `${Math.max(1, Math.round(value / 1024))}KB`
      return `${(value / 1024 / 1024).toFixed(value >= 10 * 1024 * 1024 ? 0 : 1)}MB`
    },
    isStartAuditCommand(value) {
      const text = String(value || '').replace(/\s+/g, '').trim()
      if (['开始审核', '重新审核', '审核', '开始', '重新开始审核'].includes(text)) return true
      return /(综合审核|结合.*审核|合并.*审核|继续审核|重新.*审核|基于.*附件.*审核|结合.*文件.*审核)/.test(text)
    },
    confirmDataDialog() {
      if (!this.ensureConflictsResolved()) return
      const missing = this.collectMissingAuditFields()
      if (missing.length) {
        this.dataDialogMissing = missing
        this.activeTab = missing[0].tab || 'project'
        this.$message.error(`请先确认基础信息：${missing.map(item => item.label).join('、')}`)
        return
      }
      this.dataDialogMissing = []
      this.dataDialogVisible = false
      this.saveAuditDraft()
      this.$message.success('资料数据已确认，可开始审核')
      this.scrollToResultPanel()
    },
    normalizeConflictValue(value) {
      if (value === null || value === undefined) return ''
      if (Array.isArray(value)) return value.map(item => String(item).trim()).filter(Boolean).sort().join('、')
      if (typeof value === 'boolean') return value ? '是' : '否'
      return String(value).trim()
    },
    formatConflictSources(sources = []) {
      const names = Array.from(new Set((sources || []).filter(Boolean)))
      if (!names.length) return '未知文件'
      return names.map(name => {
        const text = String(name)
        return text.length > 24 ? `${text.slice(0, 24)}…` : text
      }).join('、')
    },
    refreshConflictSelections() {
      const conflictKeys = this.recognizedFieldConflicts.map(conflict => conflict.key)
      Object.keys(this.conflictSelections || {}).forEach(key => {
        if (!conflictKeys.includes(key)) this.$delete(this.conflictSelections, key)
      })
      this.recognizedFieldConflicts.forEach(conflict => {
        const selected = this.conflictSelections[conflict.key]
        if (selected && !conflict.options.some(option => option.normalized === selected)) {
          this.$delete(this.conflictSelections, conflict.key)
        }
      })
    },
    ensureConflictsResolved() {
      const unresolved = this.recognizedFieldConflicts.filter(conflict => !this.conflictSelections[conflict.key])
      if (unresolved.length) {
        this.dataDialogVisible = true
        this.$message.warning(`请先选择冲突数据采用值：${unresolved.map(item => this.fieldLabel(item.key)).join('、')}`)
        return false
      }
      this.recognizedFieldConflicts.forEach(conflict => {
        this.applyConflictValue(conflict.key, this.conflictSelections[conflict.key])
      })
      return true
    },
    applyConflictValue(key, value) {
      const conflict = this.recognizedFieldConflicts.find(item => item.key === key)
      const option = conflict && conflict.options.find(item => item.normalized === value)
      const resolvedValue = option ? option.value : value
      if (key === 'project_stage') {
        this.applyStageValue(resolvedValue, true)
      } else if (Object.prototype.hasOwnProperty.call(this.form, key)) {
        this.$set(this.form, key, Array.isArray(resolvedValue) ? [...resolvedValue] : resolvedValue)
      }
      this.saveAuditDraft()
    },
    fieldLabel(key) {
      const labels = {
        project_name: '项目名称',
        applicant: '收函单位',
        project_type: '项目类型',
        project_stage: '项目阶段',
        relative_relationship: '相对关系',
        metro_line_name: '地铁线路',
        metro_section_name: '地铁区间',
        structure_method: '结构形式',
        structure_condition: '结构状态',
        buried_depth_m: '结构埋深',
        outer_diameter_or_width_m: '结构宽度',
        pit_depth_m: '基坑深度',
        pit_length_m: '基坑长度',
        minimum_horizontal_clearance_m: '水平净距',
        minimum_vertical_clearance_m: '竖向净距',
        dewatering_method: '降水方式',
        terrain_zone: '地段区域',
        is_soft_soil: '软弱土',
        is_complex_geology_or_hydrology: '复杂地质水文',
        support_components: '支护构件',
        protection_zone_location: '保护区位置',
        land_use_type: '用地性质'
      }
      return labels[key] || key
    },
    isUploadableDocument(item) {
      return Boolean(item && item.file && !item.restored)
    },
    scrollToResultPanel() {
      this.$nextTick(() => {
        const panel = this.$el && this.$el.querySelector('.result-panel')
        if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    },
    scrollToChatBottom() {
      this.$nextTick(() => {
        const panel = this.$el && this.$el.querySelector('.audit-chat-scroll')
        if (panel) panel.scrollTop = panel.scrollHeight
      })
    },
    auditInputSignature() {
      const documents = (this.documents || []).map(item => ({
        name: item.file && item.file.name,
        size: item.file && item.file.size,
        lastModified: item.file && item.file.lastModified,
        role: item.role
      }))
      return JSON.stringify({
        form: this.normalizedFormPayload(),
        stageSelection: this.stageSelection,
        customStageName: this.customStageName,
        landUseSelection: this.landUseSelection,
        documents
      })
    },
    saveAuditDraft() {
      const hasFormValue = Object.values(this.form || {}).some(value => {
        if (Array.isArray(value)) return value.length
        return value !== null && value !== undefined && value !== ''
      })
      if (!this.auditSession && !this.auditResult && !hasFormValue && !(this.documents || []).length) return
      const documentSummaries = (this.documents || []).map(item => ({
        id: item.id,
        name: item.file && item.file.name,
        size: item.file && item.file.size,
        type: item.file && item.file.type,
        role: item.role,
        status: item.status,
        message: item.message,
        confidence: item.confidence,
        fields: item.fields || {},
        textPreview: item.textPreview || ''
      }))
      try {
        sessionStorage.setItem(AUDIT_DRAFT_KEY, JSON.stringify({
          savedAt: Date.now(),
          form: this.form,
          activeTab: this.activeTab,
          stageSelection: this.stageSelection,
          customStageName: this.customStageName,
          landUseSelection: this.landUseSelection,
          selectedArchiveProjectId: this.selectedArchiveProjectId,
          selectedArchiveStageId: this.selectedArchiveStageId,
          auditResult: this.auditResult,
          replyResult: this.replyResult,
          auditSession: this.auditSession,
          reviewItems: this.reviewItems,
          chatMessages: this.chatMessages,
          baselineAuditSignature: this.baselineAuditSignature,
          conflictSelections: this.conflictSelections,
          documentSummaries
        }))
      } catch (error) {}
    },
    restoreAuditDraft() {
      try {
        const raw = sessionStorage.getItem(AUDIT_DRAFT_KEY)
        if (!raw) return
        const draft = JSON.parse(raw)
        if (!draft || Date.now() - Number(draft.savedAt || 0) > AUDIT_DRAFT_TTL) {
          sessionStorage.removeItem(AUDIT_DRAFT_KEY)
          return
        }
        this.form = { ...defaultForm(), ...(draft.form || {}) }
        this.sanitizeAuditOptionValues()
        this.activeTab = draft.activeTab || this.activeTab
        this.stageSelection = draft.stageSelection || ''
        this.customStageName = draft.customStageName || ''
        this.landUseSelection = draft.landUseSelection || ''
        this.selectedArchiveProjectId = draft.selectedArchiveProjectId || ''
        this.selectedArchiveStageId = draft.selectedArchiveStageId || ''
        this.auditResult = draft.auditResult || null
        this.replyResult = draft.replyResult || null
        this.auditSession = draft.auditSession || null
        this.reviewItems = draft.reviewItems || []
        this.conflictSelections = draft.conflictSelections || {}
          this.chatMessages = this.auditSession
            ? this.ensureSnapshotMessages({ ...this.auditSession, items: this.reviewItems, messages: draft.chatMessages || [] }, this.auditResult || {}, draft.chatMessages || [])
            : (draft.chatMessages || [])
        this.baselineAuditSignature = draft.baselineAuditSignature || ''
        this.documents = (draft.documentSummaries || []).map((item, index) => ({
          id: item.id || `restored_${index}`,
          file: { name: item.name, size: item.size, type: item.type, lastModified: 0 },
          restored: true,
          role: item.role,
          status: item.status || 'done',
          message: item.message || '上次上传的文件记录；如需重新审核请重新选择文件',
          confidence: item.confidence,
          fields: item.fields || {},
          textPreview: item.textPreview || ''
        }))
        this.documentSequence = this.documents.length
      } catch (error) {
        sessionStorage.removeItem(AUDIT_DRAFT_KEY)
      }
    },
    async loadArchiveSelection() {
      this.archiveLoading = true
      try {
        this.archiveProjects = await listArchiveProjects({ keyword: '', includeArchived: false }) || []
        const routeProjectId = String(this.$route.query.projectId || '')
        const routeStageId = String(this.$route.query.stageId || '')
        if (routeProjectId && this.archiveProjects.some(item => item.project_id === routeProjectId)) {
          const project = await getArchiveProject(routeProjectId, false)
          const stage = (project.stages || []).find(item => item.stage_id === routeStageId)
          this.selectedArchiveProjectId = routeProjectId
          this.selectedArchiveProject = project
          this.form.project_name = project.name
          if (stage) {
            this.applyStageValue(stage.name)
            await this.stageNameChanged(stage.name)
          }
        } else if (this.form.project_name) {
          await this.projectNameChanged(this.form.project_name)
        }
      } catch (error) {
        this.$message.error('项目档案加载失败，请刷新页面重试')
      } finally { this.archiveLoading = false }
    },
    async openRouteAuditSession() {
      sessionStorage.removeItem(AUDIT_DRAFT_KEY)
      await this.loadArchiveSelection()
      const sessionId = String(this.$route.query.sessionId || '')
      if (!sessionId) return
      try {
        const session = await getAuditSession(sessionId)
        const metadata = session.metadata || {}
        if (metadata.project_name && !this.form.project_name) this.form.project_name = metadata.project_name
        if (metadata.stage_name && !this.form.project_stage) this.applyStageValue(metadata.stage_name)
        this.auditSession = session
        this.reviewItems = session.items || []
        this.auditResult = {
          audit_session_id: session.session_id,
          audit_session: session,
          review_items: this.reviewItems,
          overall_opinion: metadata.overall_opinion || {},
          latest_result: session.latest_result || {}
        }
        this.chatMessages = this.ensureSnapshotMessages(session, this.auditResult, session.messages || [])
        this.baselineAuditSignature = this.currentAuditSignature
        this.saveAuditDraft()
        this.$nextTick(() => this.scrollToResultPanel())
      } catch (error) {
        this.$message.error('历史审核会话加载失败，请在项目档案中重新进入')
      }
    },
    async refreshArchiveProjects() {
      this.archiveProjects = await listArchiveProjects({ keyword: '', includeArchived: false }) || []
    },
    queryArchiveProjects(queryString, callback) {
      const keyword = String(queryString || '').trim().toLocaleLowerCase()
      const projects = (this.archiveProjects || [])
        .filter(item => !keyword || String(item.name || '').toLocaleLowerCase().includes(keyword))
        .map(item => ({ ...item, value: item.name }))
      callback(projects)
    },
    projectNameInputChanged(value) {
      if (this.projectNameLookupTimer) clearTimeout(this.projectNameLookupTimer)
      this.projectNameLookupTimer = setTimeout(() => {
        this.projectNameChanged(value)
      }, 250)
    },
    projectSuggestionSelected(project) {
      if (this.projectNameLookupTimer) clearTimeout(this.projectNameLookupTimer)
      this.form.project_name = project && project.name ? project.name : this.form.project_name
      this.projectNameChanged(this.form.project_name)
    },
    projectNameInputBlur() {
      if (this.projectNameLookupTimer) clearTimeout(this.projectNameLookupTimer)
      this.projectNameChanged(this.form.project_name)
    },
    async projectNameChanged(projectName) {
      const sequence = ++this.archiveLookupSequence
      this.selectedArchiveStageId = ''
      this.historyPreview = { record_count: 0, records: [] }
      this.inheritedFormSource = null
      const normalized = String(projectName || '').trim().toLocaleLowerCase()
      const summary = this.archiveProjects.find(item => item.name.trim().toLocaleLowerCase() === normalized)
      if (!summary) {
        this.selectedArchiveProjectId = ''
        this.selectedArchiveProject = null
        return
      }
      this.archiveLoading = true
      try {
        const project = await getArchiveProject(summary.project_id, false)
        if (sequence !== this.archiveLookupSequence) return
        this.selectedArchiveProjectId = project.project_id
        this.selectedArchiveProject = project
        await this.stageNameChanged(this.form.project_stage)
      } finally {
        if (sequence === this.archiveLookupSequence) this.archiveLoading = false
      }
    },
    async stageNameChanged(stageName) {
      this.selectedArchiveStageId = ''
      this.historyPreview = { record_count: 0, records: [] }
      this.inheritedFormSource = null
      const stage = this.archiveStages.find(item => this.stageNameEquals(item.name, stageName))
      if (!stage) {
        return
      }
      this.selectedArchiveStageId = stage.stage_id
      try {
        this.historyPreview = await getPreviousStageAudits(stage.stage_id) || { record_count: 0, records: [] }
      } catch (error) {
        this.$message.warning('前序审核记录暂时无法加载，本次提交仍可继续')
      }
    },
    async loadLatestProjectInheritedForm() {
      if (!this.selectedArchiveProjectId) return
      try {
        return
      } catch (error) {
        // 继承参数只是辅助能力，失败时不影响本次人工填写和审核。
      }
    },
    applyInheritedArchiveForm(inherited) {
      return
      const formData = inherited && inherited.form_data
      if (!formData || typeof formData !== 'object' || !Object.keys(formData).length) return
      const skipKeys = new Set(['project_name', 'project_stage', 'incoming_letter_excerpt'])
      let applied = 0
      Object.keys(defaultForm()).forEach(key => {
        if (skipKeys.has(key) || !Object.prototype.hasOwnProperty.call(formData, key)) return
        const current = this.form[key]
        const incoming = formData[key]
        const currentEmpty = Array.isArray(current) ? current.length === 0 : (current === '' || current === null || current === undefined)
        const incomingEmpty = Array.isArray(incoming) ? incoming.length === 0 : (incoming === '' || incoming === null || incoming === undefined)
        if (!currentEmpty || incomingEmpty) return
        this.$set(this.form, key, Array.isArray(incoming) ? [...incoming] : incoming)
        applied += 1
      })
      if (!applied) return
      this.inheritedFormSource = {
        stage_name: inherited.source_stage_name || '',
        audit_id: inherited.source_audit_id || ''
      }
      this.$message.success(`已自动带入上一阶段“${this.inheritedFormSource.stage_name || '已审核阶段'}”的 ${applied} 项参数，可按本阶段情况修改后重新审核`)
      this.saveAuditDraft()
    },
    normalizedStageName(value) {
      return String(value || '').trim().replace(/阶段$/u, '').toLocaleLowerCase()
    },
    stageNameEquals(left, right) {
      return this.normalizedStageName(left) === this.normalizedStageName(right)
    },
    stageSelectionChanged(value) {
      if (value === 'custom') {
        this.form.project_stage = this.customStageName
      } else {
        this.customStageName = ''
        this.form.project_stage = value
      }
      this.stageNameChanged(this.form.project_stage)
    },
    customStageChanged(value) {
      this.form.project_stage = String(value || '').trim()
      this.stageNameChanged(this.form.project_stage)
    },
    applyStageValue(stageName, normalizeRecognized = false) {
      const value = String(stageName || '').trim()
      if (!value) {
        this.stageSelection = ''
        this.customStageName = ''
        this.form.project_stage = ''
        return
      }
      const fixedStages = ['出让', '规划', '设计', '施工']
      let fixed = fixedStages.includes(value) ? value : ''
      if (!fixed && normalizeRecognized) {
        if (value.includes('出让')) fixed = '出让'
        else if (value.includes('规划')) fixed = '规划'
        else if (value.includes('设计')) fixed = '设计'
        else if (value.includes('施工')) fixed = '施工'
      }
      if (fixed) {
        this.stageSelection = fixed
        this.customStageName = ''
        this.form.project_stage = fixed
      } else {
        this.stageSelection = 'custom'
        this.customStageName = value
        this.form.project_stage = value
      }
    },
    async prepareArchiveBindingForAudit() {
      const projectName = String(this.form.project_name || '').trim()
      const stageName = String(this.form.project_stage || '').trim()
      if (!projectName) { this.$message.warning('请填写或选择项目名称'); return false }
      if (!stageName) { this.$message.warning('请填写或选择项目阶段'); return false }
      await this.projectNameChanged(projectName)
      if (this.selectedArchiveProject) await this.stageNameChanged(stageName)
      if (this.archiveStageLocked) {
        this.$message.warning('该项目阶段正在审核，请选择其他阶段')
        return false
      }
      return true
    },
    humanizeAuditText(value) {
      let text = String(value || '')
      const labels = {
        minimum_horizontal_clearance_m: '最小水平净距',
        minimum_vertical_clearance_m: '最小竖向净距',
        pit_depth_m: '基坑深度',
        pit_length_m: '基坑长度',
        buried_depth_m: '轨道结构埋深',
        outer_diameter_or_width_m: '隧道外径或结构宽度',
        is_in_special_protection_zone: '是否位于特别保护区',
        is_in_control_protection_zone: '是否位于控制保护区',
        dewatering_method: '降水方式',
        monitoring_required: '是否需要保护监测',
        impact_level: '影响等级',
        project_type: '项目类型',
        relative_relationship: '相对关系'
      }
      Object.keys(labels).sort((a, b) => b.length - a.length).forEach(key => {
        text = text.replace(new RegExp(key, 'g'), labels[key])
      })
      return text.replace(/\btrue\b/gi, '是').replace(/\bfalse\b/gi, '否')
    },
    normalizedFormPayload() {
      const payload = { ...this.form }
      if (payload.dewatering_method === '其他') {
        const otherValue = String(payload.dewatering_method_other || '').trim()
        payload.dewatering_method = otherValue || '其他'
      }
      delete payload.dewatering_method_other
      const numericFields = [
        'buried_depth_m',
        'outer_diameter_or_width_m',
        'pit_depth_m',
        'pit_length_m',
        'minimum_horizontal_clearance_m',
        'minimum_vertical_clearance_m'
      ]
      numericFields.forEach(key => {
        const value = payload[key]
        if (value === '' || value === null || value === undefined) {
          payload[key] = null
          return
        }
        const numberValue = Number(value)
        payload[key] = Number.isFinite(numberValue) ? numberValue : null
      })
      return payload
    },
    uploadedDocumentPayload() {
      return this.documents.map(item => ({
        name: item.file && item.file.name,
        role: item.role,
        is_primary: item.file === this.caseFile || item.file === this.letterFile,
        fields: item.fields || {},
        text_excerpt: item.textPreview || ''
      }))
    },
    fileIdentity(file) {
      if (!file.__railAuditId) {
        Object.defineProperty(file, '__railAuditId', {
          value: `${Date.now()}-${++this.documentSequence}-${file.name}`,
          enumerable: false
        })
      }
      return file.__railAuditId
    },
    fallbackRole(file) {
      return /函|请示|报审|申请备案|征求意见/.test(file.name) ? 'letter' : 'case'
    },
    async handleDocumentFiles(files) {
      const selected = Array.isArray(files) ? files : (files ? [files] : [])
      if (!selected.length) return
      const existingIds = new Set(this.documents.map(item => item.id))
      const additions = selected.filter(file => !existingIds.has(this.fileIdentity(file))).map(file => ({
        id: this.fileIdentity(file),
        file,
        role: this.fallbackRole(file),
        status: 'identifying',
        message: '等待识别',
        fields: {},
        textPreview: '',
        confidence: null
      }))
      if (!additions.length) {
        this.saveAuditDraft()
        return
      }
      this.documents.push(...additions)
      this.updateLetterExcerpt()
      if (typeof this.markAuditInputChanged === 'function') this.markAuditInputChanged()
      this.saveAuditDraft()
      this.recognizing = true
      await Promise.all(additions.map(record => this.recognizeDocument(record)))
      this.recognizing = this.documents.some(item => item.status === 'identifying')
      this.refreshConflictSelections()
      this.dataDialogMissing = this.collectMissingAuditFields()
      this.uploadDialogVisible = false
      this.dataDialogVisible = true
      this.saveAuditDraft()
    },
    async recognizeDocument(record) {
      record.message = '正在读取内容并判断文件类型'
      try {
        const body = new FormData()
        body.append('file', record.file)
        const result = await recognizeReplyLetter(body)
        record.role = result.document_role || this.fallbackRole(record.file)
        record.fields = result.fields || {}
        record.textPreview = result.text_preview || ''
        record.confidence = result.role_confidence
        record.status = 'done'
        record.message = `${this.roleLabel(record.role)}，识别置信度 ${Math.round(Number(record.confidence || 0) * 100)}%`
        if (record.role === 'letter' || !this.letterRecord) {
          this.applyRecognizedFields(record.fields)
        }
        this.updateLetterExcerpt()
        this.saveAuditDraft()
      } catch (error) {
        record.status = 'failed'
        record.message = `自动识别失败，已按文件名归为${this.roleLabel(record.role)}`
        this.saveAuditDraft()
      }
    },
    roleLabel(role) {
      return { letter: '函件', case: '案例/方案', attachment: '补充附件' }[role] || '项目资料'
    },
    documentRoleChanged(record) {
      record.message = `已人工设为${this.roleLabel(record.role)}`
      if (record.role === 'letter') this.applyRecognizedFields(record.fields || {})
      this.refreshConflictSelections()
      this.updateLetterExcerpt()
      this.saveAuditDraft()
    },
    removeDocument(record) {
      if (this.$refs.documentsPicker && !record.restored) {
        this.$refs.documentsPicker.removeRaw(record.file)
      }
      this.documents = this.documents.filter(item => item.id !== record.id)
      this.updateLetterExcerpt()
      if (typeof this.markAuditInputChanged === 'function') this.markAuditInputChanged()
      this.saveAuditDraft()
    },
    updateLetterExcerpt() {
      this.form.incoming_letter_excerpt = this.letterRecord ? this.letterRecord.textPreview : ''
    },
    applyRecognizedFields(fields) {
      Object.keys(fields).forEach(key => {
        if (key !== 'project_stage' && Object.prototype.hasOwnProperty.call(this.form, key) && fields[key] !== null && fields[key] !== '') this.$set(this.form, key, fields[key])
      })
      if (fields.project_stage) this.applyStageValue(fields.project_stage, true)
      if (fields.land_use_type) {
        this.landUseSelection = this.landUseTypes.includes(fields.land_use_type) ? fields.land_use_type : '其他'
      }
      this.sanitizeAuditOptionValues()
      if (fields.project_name || fields.project_stage) {
        this.$nextTick(() => this.projectNameChanged(this.form.project_name))
      }
    },
    sanitizeAuditOptionValues() {
      if (this.form.relative_relationship && !this.relations.includes(this.form.relative_relationship)) {
        this.form.relative_relationship = ''
      }
      if (Array.isArray(this.form.support_components)) {
        this.form.support_components = this.form.support_components.filter(item => this.supports.includes(item))
      }
    },
    landUseChanged(value) { this.form.land_use_type = value === '其他' ? '' : value },
    syncDiseaseSeverity(condition) {
      if (condition === '较好') {
        this.form.disease_severity = '无明显病害'
      } else if (condition === '较差') {
        if (this.form.disease_severity !== '一般' && this.form.disease_severity !== '严重') {
          this.form.disease_severity = ''
        }
      }
    },
    isBlankAuditValue(value) {
      return value === null || value === undefined || value === ''
    },
    collectMissingAuditFields() {
      const missing = []
      const pushMissing = (key, label, tab = 'project') => missing.push({ key, label, tab })
      const required = [
        ['project_name', '项目名称', 'project'],
        ['project_stage', '项目阶段', 'project']
      ]
      required.forEach(([key, label, tab]) => {
        if (this.isBlankAuditValue(this.form[key])) pushMissing(key, label, tab)
      })
      return missing
    },
    validateLetterInputs() {
      this.sanitizeAuditOptionValues()
      if (!this.ensureConflictsResolved()) return false
      const missing = this.collectMissingAuditFields()
      if (missing.length) {
        this.dataDialogMissing = missing
        this.activeTab = missing[0].tab || 'project'
        this.dataDialogVisible = true
        this.$message.error(`请先确认基础信息：${missing.map(item => item.label).join('、')}`)
        return false
      }
      this.dataDialogMissing = []
      return true
    },
    appendUserChatMessage(content) {
      const text = String(content || '').trim()
      if (!text) return null
      const message = {
        message_id: `local_user_${Date.now()}_${Math.random().toString(16).slice(2)}`,
        role: 'user',
        content: text,
        created_at: new Date().toISOString()
      }
      this.chatMessages.push(message)
      return message
    },
    documentAttachmentPayload(records = []) {
      return (Array.isArray(records) ? records : []).map(record => ({
        id: record.id,
        name: record.file && record.file.name,
        size: record.file && record.file.size,
        role: record.role,
        status: record.status
      })).filter(item => item.name)
    },
    isUploadOnlyChatMessage(message) {
      if (!message || message.role !== 'user') return false
      const content = String(message.content || '').trim()
      const attachments = Array.isArray(message.attachments) ? message.attachments : []
      return Boolean(attachments.length && /^已上传\s*\d+\s*个文件$/.test(content))
    },
    chatMessageKey(message) {
      if (!message) return ''
      if (message.message_id) return String(message.message_id)
      const createdAt = message.created_at || message.createdAt || message.time || ''
      return [message.role || '', createdAt, String(message.content || '').trim()].join('::')
    },
    isLocalUserMessage(message) {
      return Boolean(message && message.role === 'user' && String(message.message_id || '').startsWith('local_'))
    },
    sameUserMessage(left, right) {
      return Boolean(
        left &&
        right &&
        left.role === 'user' &&
        right.role === 'user' &&
        String(left.content || '').trim() === String(right.content || '').trim()
      )
    },
    mergeChatMessages(existing = [], incoming = []) {
      const merged = []
      const indexByKey = {}
      const list = [
        ...(Array.isArray(existing) ? existing : []),
        ...(Array.isArray(incoming) ? incoming : [])
      ]
      list.forEach((message, index) => {
        if (!message) return
        const fallbackId = `local_msg_${Date.now()}_${index}_${Math.random().toString(16).slice(2)}`
        const normalized = {
          ...message,
          message_id: message.message_id || fallbackId
        }
        if (!this.isLocalUserMessage(normalized) && normalized.role === 'user') {
          const localIndex = merged.findIndex(old => this.isLocalUserMessage(old) && this.sameUserMessage(old, normalized))
          if (localIndex >= 0) {
            merged[localIndex] = normalized
            const localKey = this.chatMessageKey(merged[localIndex])
            if (localKey) indexByKey[localKey] = localIndex
            return
          }
        }
        const key = this.chatMessageKey(normalized)
        if (key && indexByKey[key] !== undefined) {
          const old = merged[indexByKey[key]]
          merged[indexByKey[key]] = {
            ...old,
            ...normalized,
            result_snapshot: normalized.result_snapshot || old.result_snapshot
          }
        } else {
          if (key) indexByKey[key] = merged.length
          merged.push(normalized)
        }
      })
      return merged
    },
    mergeUserMessage(messages, userMessage) {
      if (!userMessage) return this.mergeChatMessages([], messages)
      const incoming = Array.isArray(messages) ? messages : []
      const hasServerEcho = incoming.some(message => (
        message &&
        message.role === 'user' &&
        !String(message.message_id || '').startsWith('local_') &&
        String(message.content || '').trim() === String(userMessage.content || '').trim()
      ))
      return this.mergeChatMessages([], hasServerEcho ? incoming : [...incoming, userMessage])
    },
    attachmentRecordsForAudit() {
      const primaryIds = new Set([this.letterRecord && this.letterRecord.id, this.caseRecord && this.caseRecord.id].filter(Boolean))
      return (this.documents || []).filter(item => this.isUploadableDocument(item) && !primaryIds.has(item.id))
    },
    appendAttachmentFiles(body) {
      this.attachmentRecordsForAudit().forEach(record => {
        body.append('attachmentFiles', record.file)
      })
    },
    rerunAuditContext(commandText = '') {
      const attachments = this.attachmentRecordsForAudit().map(record => ({
        name: record.file && record.file.name,
        role: record.role || 'attachment',
        status: record.status || ''
      })).filter(item => item.name)
      return {
        mode: this.auditSession ? '基于已有审核结果和新增附件综合复核' : '首次审核',
        latest_instruction: String(commandText || this.chatInstruction || '').trim(),
        attachment_policy: '新增附件追加进入当前会话，不清空已有文件；重新审核时应结合已有文件、新增附件、当前确认数据、上一版综合评价和全部审核意见形成新的综合审核意见。',
        attachment_count: attachments.length,
        attachment_names: attachments.map(item => item.name),
        attachments
      }
    },
    async startAudit(options = {}) {
      const originalCommandText = String(options.commandText || this.chatInstruction || '').trim()
      if (options.fromChat) {
        const commandText = originalCommandText || (this.auditInputChanged || this.auditSession ? '重新审核' : '开始审核')
        this.appendUserChatMessage(commandText)
        this.chatInstruction = ''
        this.saveAuditDraft()
      }
      if (this.hasOnlyRestoredDocuments) return this.$message.warning('已恢复的是上次文件记录；如需重新审核，请重新选择原始文件')
      if (!this.hasAnyFile) return this.$message.warning('请至少上传函件或案例文件')
      if (!this.letterFile && !this.caseFile) return this.$message.warning('请将至少一个文件设为函件或案例/方案')
      if (!await this.prepareArchiveBindingForAudit()) return
      if (!this.validateLetterInputs()) return
      if (this.auditInputChanged) {
        try {
          await this.$confirm(
            '检测到资料或参数已修改，将基于当前数据重新生成审核意见；新结果生成成功后会替换当前结果。是否继续？',
            '重新审核确认',
            { type: 'warning', confirmButtonText: '重新审核', cancelButtonText: '取消' }
          )
        } catch (error) {
          return
        }
      }
      this.stopAuditPolling()
      this.auditTaskId = ''
      this.expandedSnapshotIds = {}
      this.auditSubmitting = true
      try {
        const body = new FormData()
        const archiveBinding = this.archiveBinding
        const hasArchiveBinding = archiveBinding && archiveBinding.project_id
        let task
        if (this.caseFile) {
          body.append('file', this.caseFile)
          this.appendAttachmentFiles(body)
          const manualContext = {
            ...this.normalizedFormPayload(),
            uploaded_documents: this.uploadedDocumentPayload(),
            latest_review_items: this.auditSession ? this.auditReviewItems.map(item => ({
              order_no: item.order_no,
              title: item.title,
              risk_level: item.risk_level,
              opinion: this.displayReviewOpinion(item)
            })) : [],
            latest_overall_opinion: this.currentOverallOpinion || {},
            rerun_context: this.rerunAuditContext(originalCommandText)
          }
          body.append('options', JSON.stringify({
            top_k: 3,
            rebuild_database: false,
            manual_context: manualContext,
            incoming_letter_name: this.letterFile && this.letterFile.name,
            ...(hasArchiveBinding ? { archive_binding: archiveBinding } : {}),
            manual_archive_only: true
          }))
          task = await createFullTask(body)
        } else {
          if (!/\.pdf$/i.test(this.letterFile.name)) return this.$message.warning('当前复函流水线要求主函件为 PDF，请上传 PDF 函件后再审核')
          body.append('file', this.letterFile)
          this.appendAttachmentFiles(body)
          body.append('payload', JSON.stringify({
            ...this.normalizedFormPayload(),
            uploaded_documents: this.uploadedDocumentPayload(),
            latest_review_items: this.auditSession ? this.auditReviewItems.map(item => ({
              order_no: item.order_no,
              title: item.title,
              risk_level: item.risk_level,
              opinion: this.displayReviewOpinion(item)
            })) : [],
            latest_overall_opinion: this.currentOverallOpinion || {},
            rerun_context: this.rerunAuditContext(originalCommandText),
            ...(hasArchiveBinding ? { archive_binding: archiveBinding } : {}),
            manual_archive_only: true
          }))
          task = await createReplyTask(body)
        }
        this.auditTaskId = task.task_id
        this.startAuditPolling(task.task_id)
      } catch (error) {
        this.auditSubmitting = false
        this.$message.error('审核任务创建失败，请检查服务状态或稍后重试')
      }
    },
    startAuditPolling(taskId) {
      this.stopAuditPolling()
      this.refreshAuditTask(taskId)
      this.auditPollingTimer = setInterval(() => this.refreshAuditTask(taskId), 1500)
    },
    stopAuditPolling() {
      if (this.auditPollingTimer) clearInterval(this.auditPollingTimer)
      this.auditPollingTimer = null
    },
    async refreshAuditTask(taskId) {
      if (!taskId || taskId !== this.auditTaskId) return
      try {
        const task = await getTask(taskId)
        if (taskId !== this.auditTaskId) return
        if (task.status === 'success') {
          this.stopAuditPolling()
          const result = await getTaskResult(taskId)
          if (taskId !== this.auditTaskId) return
          this.auditCompleted(result)
        } else if (task.status === 'failed') {
          this.stopAuditPolling()
          this.auditSubmitting = false
          this.$message.error(task.error_message || '审核失败，请检查资料后重试')
        }
      } catch (error) {
        this.stopAuditPolling()
        this.auditSubmitting = false
        this.$message.error('审核状态获取失败，请检查服务状态')
      }
    },
    ensureSnapshotMessages(session, result = {}, existingMessages = []) {
      const incoming = Array.isArray(session && session.messages) ? [...session.messages] : []
      const items = (session && session.items) || result.review_items || []
      const latest = (session && session.latest_result) || result.latest_result || {}
      const metadata = (session && session.metadata) || {}
      const itemList = Array.isArray(items) ? items : []
      const overall = this.extractOverallOpinion(latest, itemList) ||
        this.extractOverallOpinion(result, itemList) ||
        this.extractOverallOpinion(metadata, itemList)
      const versionNo = Number((session && session.current_version) || latest.version_no || 1) || 1
      const combined = this.mergeChatMessages(existingMessages, incoming)
      const latestSignature = this.snapshotSignatureFromParts(itemList, overall)
      const lastSnapshotIndex = this.lastSnapshotMessageIndex(combined)
      const lastUserIndex = this.lastUserMessageIndex(combined)
      const lastSnapshot = lastSnapshotIndex >= 0 ? combined[lastSnapshotIndex] : null
      const lastSignature = lastSnapshot ? this.messageSnapshotSignature(lastSnapshot) : ''
      const needsBottomSnapshot = Boolean(
        (itemList.length || overall) &&
        latestSignature &&
        (latestSignature !== lastSignature || lastSnapshotIndex < lastUserIndex)
      )
      if (needsBottomSnapshot) {
        incoming.push({
          message_id: `local_snapshot_${(session && session.session_id) || 'session'}_${versionNo}_${Date.now()}`,
          role: 'assistant',
          content: `第 ${versionNo} 版审核意见`,
          version_no: versionNo,
          created_at: new Date().toISOString(),
          result_snapshot: {
            format_version: 'editable_audit_result_v1',
            version_no: versionNo,
            items: itemList,
            review_items: itemList,
            overall_opinion: overall || {},
            snapshot_signature: latestSignature
          }
        })
      }
      return this.mergeChatMessages(existingMessages, incoming)
    },
    hydrateAuditSession(result) {
      const session = result && result.audit_session
      if (!session) {
        this.auditSession = null
        this.reviewItems = []
        this.chatMessages = []
        this.expandedSnapshotIds = {}
        return
      }
      this.auditSession = session
      this.reviewItems = session.items || result.review_items || []
      this.chatMessages = this.ensureSnapshotMessages(session, result, this.chatMessages)
      this.scrollToChatBottom()
    },
    auditCompleted(result) {
      this.auditSubmitting = false
      this.auditResult = result
      this.hydrateAuditSession(result)
      this.baselineAuditSignature = this.currentAuditSignature
      this.saveAuditDraft()
      this.handleArchivedCompletion('案例审核已完成，已生成第一版审核结果')
    },
    async handleArchivedCompletion(message) {
      try {
        await this.refreshArchiveProjects()
        await this.projectNameChanged(this.form.project_name)
      } finally { this.$message.success(message) }
    },
    severityType(value) { return ['重大', '极高', '高'].includes(value) ? 'danger' : (value === '中' ? 'warning' : (value === '低' ? 'success' : 'info')) },
    formatBasis(value) {
      if (!value) return ''
      const list = Array.isArray(value) ? value : [value]
      return list.map(item => {
        if (item == null) return ''
        if (typeof item === 'string') return item
        return [item.document, item.clause, item.quote].filter(Boolean).join(' ')
      }).filter(Boolean).join('；')
    },
    hasMessageSnapshot(message) {
      if (!message || message.role !== 'assistant') return false
      const snapshot = this.messageSnapshot(message)
      const items = snapshot.items || snapshot.review_items
      const overall = this.extractOverallOpinion(snapshot, Array.isArray(items) ? items : [])
      return (Array.isArray(items) && items.length > 0) || Boolean(overall && (overall.conclusion || overall.recommendation))
    },
    lastSnapshotMessage(messages = []) {
      const list = Array.isArray(messages) ? messages : []
      const index = this.lastSnapshotMessageIndex(list)
      if (index >= 0) return list[index]
      return null
    },
    lastSnapshotMessageIndex(messages = []) {
      const list = Array.isArray(messages) ? messages : []
      for (let index = list.length - 1; index >= 0; index -= 1) {
        if (this.hasMessageSnapshot(list[index])) return index
      }
      return -1
    },
    lastUserMessageIndex(messages = []) {
      const list = Array.isArray(messages) ? messages : []
      for (let index = list.length - 1; index >= 0; index -= 1) {
        if (list[index] && list[index].role === 'user') return index
      }
      return -1
    },
    snapshotSignatureFromParts(items = [], overall = null) {
      const normalizedItems = (Array.isArray(items) ? items : [])
        .filter(item => item && !this.isOverallReviewItem(item))
        .map(item => [
          item.order_no,
          item.title,
          item.risk_level,
          item.conclusion,
          item.recommendation
        ].map(value => this.cleanChatMessageContent(value)).join('|'))
        .join('||')
      const normalizedOverall = overall
        ? [
          overall.title,
          overall.conclusion,
          overall.recommendation
        ].map(value => this.cleanChatMessageContent(value)).join('|')
        : ''
      return `${normalizedOverall}::${normalizedItems}`.trim()
    },
    messageSnapshotSignature(message) {
      const snapshot = this.messageSnapshot(message)
      const items = snapshot.items || snapshot.review_items || []
      const overall = this.extractOverallOpinion(snapshot, Array.isArray(items) ? items : [])
      return snapshot.snapshot_signature || this.snapshotSignatureFromParts(items, overall)
    },
    hasHistoricalSnapshot(message) {
      return this.hasMessageSnapshot(message) && message.message_id !== this.latestAssistantSnapshotMessageId
    },
    isLatestSnapshot(message) {
      return this.hasMessageSnapshot(message) && message.message_id === this.latestAssistantSnapshotMessageId
    },
    isSnapshotExpanded(message) {
      return Boolean(message && this.expandedSnapshotIds && this.expandedSnapshotIds[message.message_id])
    },
    toggleSnapshot(message) {
      if (!message || !message.message_id) return
      this.$set(this.expandedSnapshotIds, message.message_id, !this.isSnapshotExpanded(message))
    },
    snapshotSequenceNo(message) {
      const messages = this.visibleChatMessages || []
      let sequence = 0
      for (const item of messages) {
        if (!this.hasMessageSnapshot(item)) continue
        sequence += 1
        if (item && message && item.message_id === message.message_id) return sequence
      }
      return 0
    },
    snapshotVersionLabel(message) {
      const snapshot = this.messageSnapshot(message)
      const version = this.snapshotSequenceNo(message) || Number((snapshot && snapshot.version_no) || (message && message.version_no))
      return version ? `第 ${version} 版` : '历史版本'
    },
    messageReviewItems(message) {
      if (!message || message.role !== 'assistant') return []
      const snapshot = this.messageSnapshot(message)
      const items = snapshot && (snapshot.items || snapshot.review_items)
      return Array.isArray(items)
        ? items.filter(item => !this.isOverallReviewItem(item) && this.displayReviewOpinion(item))
        : []
    },
    messageOverallOpinion(message) {
      if (!message || message.role !== 'assistant') return null
      const snapshot = this.messageSnapshot(message)
      const items = snapshot && (snapshot.items || snapshot.review_items)
      return this.extractOverallOpinion(snapshot, Array.isArray(items) ? items : [])
    },
    messageSnapshot(message) {
      if (!message || message.role !== 'assistant') return {}
      const snapshot = message.result_snapshot || {}
      const items = snapshot.items || snapshot.review_items
      if ((Array.isArray(items) && items.length) || snapshot.overall_opinion) return snapshot
      return this.inferSnapshotFromAssistantText(message.content)
    },
    inferSnapshotFromAssistantText(value) {
      const raw = String(value || '')
      if (!/(order_no|title|conclusion|risk_level|basis|recommendation|修改后的审核意见)/i.test(raw)) return {}
      const text = raw.replace(/\s+/g, ' ').trim()
      const orderMatch = text.match(/order_no["']?\s*[:：]\s*(\d+)/i) || text.match(/第\s*(\d+)\s*(?:条|点|项)/)
      const titleMatch = text.match(/title["']?\s*[:：]\s*["']?([^"'，,。；;]+)["']?/i)
      const conclusionMatch = text.match(/conclusion["']?\s*[:：]\s*([\s\S]*?)(?=\s+["']?(?:risk_level|basis|recommendation)["']?\s*[:：]|$)/i)
      const recommendationMatch = text.match(/recommendation["']?\s*[:：]\s*([\s\S]*?)(?=$)/i)
      const riskMatch = text.match(/risk_level["']?\s*[:：]\s*["']?([高中低]|提示)["']?/i)
      const conclusion = this.cleanChatMessageContent(conclusionMatch && conclusionMatch[1] || recommendationMatch && recommendationMatch[1] || raw)
      if (!conclusion) return {}
      const orderNo = Number(orderMatch && orderMatch[1]) || 1
      const title = this.cleanChatMessageContent(titleMatch && titleMatch[1] || '').slice(0, 34) || `第${orderNo}条审核意见`
      const item = {
        order_no: orderNo,
        title,
        risk_level: riskMatch && riskMatch[1] || '',
        conclusion,
        recommendation: '',
        basis: [],
        source: { kind: 'inferred_from_plain_reply' }
      }
      const overall = this.currentOverallOpinion || {
        title: '综合评价',
        conclusion: this.positiveOverallOpinionText(),
        source: { kind: 'overall_summary' }
      }
      return {
        format_version: 'inferred_audit_result_v1',
        version_no: Number(this.auditSession && this.auditSession.current_version) || 1,
        overall_opinion: overall,
        items: [item],
        review_items: [item]
      }
    },
    isOverallReviewItem(item) {
      const title = String(item && item.title || '').trim()
      const sourceKind = String(item && item.source && item.source.kind || '')
      return sourceKind === 'overall_summary' || title === '综合评价' || title === '综合意见' || title === '综合审核结论'
    },
    extractOverallOpinion(container, items) {
      const direct = container && (container.overall_opinion || container.overallOpinion)
      if (direct && (direct.conclusion || direct.recommendation)) return direct
      const list = Array.isArray(items) ? items : []
      return list.find(item => this.isOverallReviewItem(item) && (item.conclusion || item.recommendation)) || null
    },
    displayOverallOpinion(item) {
      const text = this.cleanChatMessageContent(item && (item.conclusion || item.recommendation) || '')
      if (!text) return ''
      if (!this.overallOpinionNeedsPositiveTone(text)) return text
      return this.positiveOverallOpinionText()
    },
    overallOpinionNeedsPositiveTone(value) {
      return /(不予通过|不同意|不可实施|不得进入|不得实施|多项高风险|高风险及不合规|总体结论为|缺乏|不足|超限|缺陷|缺失|不满足|不符合|严禁|必须严格)/.test(String(value || ''))
    },
    positiveOverallOpinionText() {
      const stage = String(this.form.project_stage || '').trim()
      if (stage.includes('设计')) {
        return '经审查，本次设计资料总体符合基坑项目涉铁保护区审查流程要求，已具备开展设计阶段合规审查和方案完善的基础。后续在落实下列审核意见、补充完善相关资料及控制措施后，可按程序推进施工图深化及备案审查工作。'
      }
      if (stage.includes('施工')) {
        return '经审查，本次施工资料总体符合基坑项目涉铁保护区审查流程要求，已具备开展施工阶段合规审查和现场保护控制的基础。后续在落实下列审核意见、完善施工组织及监测应急措施后，可按程序推进后续施工管理工作。'
      }
      if (stage.includes('出让')) {
        return '经审查，本次资料总体符合基坑项目涉铁保护区前期审查流程要求，已基本具备作为后续规划设计深化依据的合规基础。后续在落实下列审核意见、明确保护区控制条件及报审衔接要求后，可按程序推进后续工作。'
      }
      return '经审查，本次资料总体符合基坑项目涉铁保护区审查流程要求，已具备开展本阶段合规审查和方案深化的基础。后续在落实下列审核意见、补充完善相关资料及安全控制措施后，可按程序推进后续工作。'
    },
    displayReviewTitle(item) {
      const rawTitle = this.cleanChatMessageContent(item && item.title || '')
      const sourceLike = !rawTitle ||
        rawTitle.includes('自动审核意见') ||
        ((rawTitle.toLowerCase().includes('pdf') || rawTitle.includes('规程') || rawTitle.includes('规范') || rawTitle.includes('标准')) && rawTitle.includes('第') && rawTitle.includes('条'))
      const titleLooksEvaluative = this.isEvaluationReviewText(rawTitle)
      if (!sourceLike && !titleLooksEvaluative) return rawTitle
      const text = String(this.displayReviewOpinion(item) || (item && (item.conclusion || item.recommendation)) || '').replace(/\s+/g, ' ').trim()
      if (!text) return rawTitle || '审核事项'
      let title = text.split(/[。；;.!！？?]/)[0].replace(/^(建议|审核意见|结论|意见)[:：\s]*/, '').trim()
      if (!title) title = text
      return title.length > 34 ? `${title.slice(0, 34).replace(/[，,、；;：:\\s]+$/, '')}…` : title
    },
    isActionReviewText(value) {
      return /(应|需|须|建议|请|不得|严禁|禁止|补充|完善|明确|复核|核查|落实|制定|加强|监测|报审|提交|开展|优化|控制|采取|重新|论证|验算|评估|修正|调整)/.test(String(value || ''))
    },
    isEvaluationReviewText(value) {
      return /(符合|满足|风险可控|可控范围|已制定|已落实|严于|低于|有效减少|不构成重大风险|符合.*要求|满足.*要求|判定为|属于|位于|显示|采用|根据规程|根据规范)/.test(String(value || ''))
    },
    isRequirementReviewText(value) {
      return /(不足|缺失|缺少|未明确|未提供|不满足|不符合|超标|风险|隐患|应|需|须|建议|请|不得|严禁|禁止|补充|完善|明确|复核|核查|落实|制定|加强|监测|报审|提交|开展|优化|控制|采取|重新|论证|验算|评估|修正|调整)/.test(String(value || ''))
    },
    isPureEvaluationReviewText(value) {
      const text = String(value || '')
      return this.isEvaluationReviewText(text) && !this.isRequirementReviewText(text)
    },
    displayReviewOpinion(item) {
      const conclusion = this.cleanChatMessageContent(item && item.conclusion || '')
      if (conclusion && !this.isPureEvaluationReviewText(conclusion)) return this.formatReadableText(conclusion)
      const recommendation = this.cleanChatMessageContent(item && item.recommendation || '')
      if (recommendation && !this.isPureEvaluationReviewText(recommendation)) return this.formatReadableText(recommendation)
      return ''
    },
    cleanChatMessageContent(value) {
      let text = String(value || '').trim()
      if (!text) return ''
      text = text
        .replace(/\$+\s*K\s*\$+\s*值/gi, '渗透系数K值')
        .replace(/\$+\s*K\s*\$+/gi, '渗透系数K')
        .replace(/\$+\s*F\s*_\s*s\s*\\?geq\s*([0-9.]+)\s*\$+/gi, '抗突涌安全系数Fs不小于$1')
        .replace(/\$+\s*F\s*_\s*s\s*\$+/gi, '抗突涌安全系数Fs')
        .replace(/\(\s*抗突涌安全系数Fs\s*\)/g, '抗突涌安全系数Fs')
        .replace(/（\s*抗突涌安全系数Fs\s*）/g, '抗突涌安全系数Fs')
        .replace(/\(\s*渗透系数K值\s*\)/g, '渗透系数K值')
        .replace(/（\s*渗透系数K值\s*）/g, '渗透系数K值')
        .replace(/\\geq/g, '不小于')
        .replace(/\\leq/g, '不大于')
        .replace(/\\times/g, '乘以')
        .replace(/\\[a-zA-Z]+/g, '')
        .replace(/\$+/g, '')
        .replace(/\bF\s*_\s*s\b/gi, '抗突涌安全系数Fs')
        .replace(/\bK\s*_\s*([a-zA-Z])\b/g, 'K$1')
        .replace(/```(?:json|markdown|md)?/gi, '')
        .replace(/```/g, '')
        .replace(/^\s{0,3}#{1,6}\s*/gm, '')
        .replace(/^\s*[-*+]\s+/gm, '')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/__(.*?)__/g, '$1')
        .replace(/\*([^*]+)\*/g, '$1')
        .replace(/[*#]+/g, '')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/["']?(order_no|title|conclusion|risk_level|basis|recommendation|reply|items|overall_opinion)["']?\s*[:：]\s*/gi, '')
        .replace(/[{}\[\]]/g, '')
        .replace(/\s+/g, ' ')
        .replace(/^[,，。；;：:\s]+|[,，；;：:\s]+$/g, '')
      return text
    },
    formatReadableText(value) {
      let text = this.cleanChatMessageContent(value)
      if (!text) return ''
      text = text
        .replace(/\s*(第\s*[一二三四五六七八九十\d]+\s*(?:条|点|项)(?:审核意见)?[^：:。；]{0,36}[：:])\s*/g, '$1\n')
        .replace(/\s+(?=\d{1,2}[.、]\s*[\u4e00-\u9fa5])/g, '\n\n')
        .replace(/\s+(?=(?:监测点布置|布点密度与位置|监测项目|监测频率|报警阈值设定|预警值|报警值|控制值|数据共享|信息共享|联合研判|预案启动|黄色预警|橙色预警|红色预警|处置措施|风险提示|备注|提示|建议操作)[：:])/g, '\n')
        .replace(/([。；])\s*(?=(?:监测点布置|布点密度与位置|监测项目|监测频率|报警阈值设定|预警值|报警值|控制值|数据共享|信息共享|联合研判|预案启动|黄色预警|橙色预警|红色预警|处置措施|风险提示|备注|提示|建议操作)[：:])/g, '$1\n')
        .replace(/\n{3,}/g, '\n\n')
        .trim()
      return text
    },
    extractActionReviewOpinion(value) {
      const text = String(value || '').replace(/\s+/g, ' ').trim()
      if (!text) return ''
      const parts = text.split(/[。；;]/).map(part => part.trim()).filter(Boolean)
      const actionParts = parts.filter(part => this.isActionReviewText(part) && !this.isEvaluationReviewText(part))
      if (!actionParts.length) return ''
      return `${actionParts.join('。')}。`
    },
    basisFromText(value) {
      return String(value || '').split(/\n+/).map(item => item.trim()).filter(Boolean)
    },
    openReviewItemDialog(item) {
      this.editingItemId = item && item.item_id || ''
      this.itemForm = {
        title: item && item.title || '',
        risk_level: item && item.risk_level || '',
        conclusion: item && item.conclusion || '',
        recommendation: item && item.recommendation || '',
        basisText: item ? this.formatBasis(item.basis) : ''
      }
      this.itemDialogVisible = true
    },
    applySessionResponse(session) {
      this.auditSession = session
      this.reviewItems = session.items || []
      this.chatMessages = this.ensureSnapshotMessages(session, { review_items: this.reviewItems }, this.chatMessages)
      this.saveAuditDraft()
    },
    async saveReviewItem() {
      if (!this.auditSession) return this.$message.warning('请先完成审核')
      if (!this.itemForm.title || !this.itemForm.conclusion) return this.$message.warning('请填写审核主题和审核结论')
      this.itemSaving = true
      try {
        const payload = {
          title: this.itemForm.title,
          risk_level: this.itemForm.risk_level,
          conclusion: this.itemForm.conclusion,
          recommendation: this.itemForm.recommendation,
          basis: this.basisFromText(this.itemForm.basisText),
          manual_modified: true
        }
        if (this.editingItemId) await updateAuditSessionItem(this.auditSession.session_id, this.editingItemId, payload)
        else await createAuditSessionItem(this.auditSession.session_id, payload)
        this.applySessionResponse(await getAuditSession(this.auditSession.session_id))
        this.itemDialogVisible = false
        this.$message.success('审核条目已保存')
      } catch (error) {
        this.$message.error('保存审核条目失败，请稍后重试')
      } finally {
        this.itemSaving = false
      }
    },
    async removeReviewItem(item) {
      if (!this.auditSession || !item) return
      try {
        await this.$confirm(`确认删除第 ${item.order_no} 条审核结果吗？`, '删除审核条目', { type: 'warning' })
        const result = await deleteAuditSessionItem(this.auditSession.session_id, item.item_id)
        this.applySessionResponse(result.session)
      this.chatMessages.push({
        message_id: `local_${Date.now()}`,
        role: 'assistant',
        content: `已删除第 ${item.order_no} 条审核结果。`,
        created_at: new Date().toISOString()
      })
      this.saveAuditDraft()
      this.$message.success('已删除审核条目')
      } catch (error) {
        if (error !== 'cancel') this.$message.error('删除审核条目失败')
      }
    },
    async sendChatInstruction() {
      if (this.chatSubmitting || this.auditSubmitting) return
      if (!this.canSendComposer) return
      if (!this.chatInstruction && this.hasAnyFile) {
        return this.startAudit({ fromChat: true, commandText: this.auditSession ? '重新审核' : '开始审核' })
      }
      if (this.isStartAuditCommand(this.chatInstruction)) {
        return this.startAudit({ fromChat: true, commandText: this.chatInstruction })
      }
      if (!this.auditSession) return this.$message.warning('请先上传资料并输入“开始审核”')
      const instruction = this.chatInstruction
      const userMessage = this.appendUserChatMessage(instruction)
      this.chatInstruction = ''
      this.saveAuditDraft()
      this.chatSubmitting = true
      this.scrollToChatBottom()
      try {
        const response = await reviseAuditSession(this.auditSession.session_id, instruction)
        const session = {
          ...response.session,
          messages: this.mergeUserMessage(response.session && response.session.messages, userMessage)
        }
        this.applySessionResponse(session)
        this.$message.success('已更新审核结果')
      } catch (error) {
        const detail = error && error.response && error.response.data && (error.response.data.detail || error.response.data.msg)
        this.$message.error(detail || (error && (error.msg || error.message)) || 'AI 修改失败，请检查模型配置或稍后重试')
      } finally {
        this.chatSubmitting = false
      }
    },
    handleComposerKeydown(event) {
      if (!event || event.key !== 'Enter' || event.shiftKey) return
      event.preventDefault()
      this.sendChatInstruction()
    },
    archivePayload(overwrite = false) {
      return {
        project_id: this.selectedArchiveProjectId || '',
        stage_id: this.selectedArchiveStageId || '',
        project_name: String(this.form.project_name || '').trim(),
        stage_name: String(this.form.project_stage || '').trim(),
        form_data: this.normalizedFormPayload(),
        overwrite
      }
    },
    async writeArchive(overwrite = false) {
      if (!this.auditSession) return this.$message.warning('请先完成审核')
      const projectName = String(this.form.project_name || '').trim()
      const stageName = String(this.form.project_stage || '').trim()
      if (!projectName || !stageName) return this.$message.warning('请先填写项目名称和项目阶段')
      this.archiveWriting = true
      try {
        const result = await writeAuditSessionToArchive(this.auditSession.session_id, this.archivePayload(overwrite))
        this.$message.success(result.overwritten ? '已覆盖写入项目档案' : '已写入项目档案')
        await this.refreshArchiveProjects()
        await this.projectNameChanged(projectName)
        this.saveAuditDraft()
      } catch (error) {
        const message = (error && (error.msg || error.message)) || ''
        const needOverwrite = message.includes('已经存在审核记录') || (error && error.response && error.response.status === 409)
        if (!overwrite && needOverwrite) {
          try {
            await this.$confirm('该项目阶段已经有审核记录，是否用当前最新版审核结果覆盖？', '覆盖确认', { type: 'warning', confirmButtonText: '覆盖写入' })
            this.archiveWriting = false
            return this.writeArchive(true)
          } catch (confirmError) {
            if (confirmError !== 'cancel') this.$message.error('写入档案失败')
            return
          }
        }
        this.$message.error(message || '写入档案失败，请稍后重试')
      } finally {
        this.archiveWriting = false
      }
    },
    async generateLatestReply() {
      if (!this.auditSession) return this.$message.warning('请先完成审核')
      if (!this.reviewItems.length) return this.$message.warning('当前没有可生成复函的审核结果')
      this.replySubmitting = true
      try {
        const projectName = String(this.form.project_name || '').trim() || '项目'
        const blob = await generateAuditSessionReply(this.auditSession.session_id, {
          project_name: projectName,
          applicant: String(this.form.applicant || '').trim(),
          project_stage: String(this.form.project_stage || '').trim(),
          form_data: this.normalizedFormPayload()
        })
        const safeName = projectName.replace(/[\\/:*?"<>|]/g, '').slice(0, 80) || '项目'
        saveAs(blob, `${safeName}复函.docx`)
        this.$message.success('已按最新版审核结果生成复函，并保存至案例文件')
      } catch (error) {
        this.$message.error((error && (error.msg || error.message)) || '生成复函失败，请检查服务状态或稍后重试')
      } finally {
        this.replySubmitting = false
      }
    },
    reset() {
      this.stopAuditPolling()
      sessionStorage.removeItem(AUDIT_DRAFT_KEY)
      this.form = defaultForm()
      this.documents = []
      this.auditTaskId = ''
      this.auditResult = null
      this.replyResult = null
      this.auditSession = null
      this.auditSubmitting = false
      this.chatSubmitting = false
      this.reviewItems = []
      this.chatMessages = []
      this.expandedSnapshotIds = {}
      this.chatInstruction = ''
      this.prepPanelExpanded = false
      this.uploadDialogVisible = false
      this.uploadSourceTab = 'library'
      this.libraryLoading = false
      this.libraryAdding = false
      this.libraryKeyword = ''
      this.libraryCases = []
      this.libraryAssets = []
      this.selectedLibraryRows = []
      this.dataDialogVisible = false
      this.dataDialogMissing = []
      this.conflictSelections = {}
      this.baselineAuditSignature = ''
      this.archiveWriting = false
      this.replySubmitting = false
      this.selectedArchiveProjectId = ''
      this.selectedArchiveStageId = ''
      this.selectedArchiveProject = null
      this.historyPreview = { record_count: 0, records: [] }
      this.stageSelection = ''
      this.customStageName = ''
      this.activeTab = 'project'
      this.landUseSelection = ''
      if (this.$refs.documentsPicker) this.$refs.documentsPicker.clear()
    }
  }
}
</script>

<style scoped>
.case-review-page { min-height: calc(100vh - 84px); padding-bottom: 210px; background: #f5f7f8; }
.page-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 18px; }
.page-head h2 { margin: 0 0 7px; font-size: 22px; }.page-head p,.section-heading p { margin: 0; color: #6d7780; }
.input-panel { border: 1px solid #dfe4e8; background: #fff; padding: 16px 18px; }
.result-panel { display: flex; min-height: calc(100vh - 112px); flex-direction: column; margin-top: 16px; padding: 22px 22px 18px; border: 0; background: transparent; }
.review-brief { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.brief-main { display: flex; min-width: 0; align-items: center; gap: 12px; }
.brief-icon { display: inline-flex; width: 38px; height: 38px; flex: 0 0 38px; align-items: center; justify-content: center; border-radius: 12px; background: #e8f5f1; color: #2f7d69; font-size: 20px; }
.brief-main h3 { margin: 0 0 5px; font-size: 17px; }
.brief-main p { margin: 0; overflow: hidden; color: #6d7780; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.brief-actions { display: flex; flex: none; gap: 10px; }
.legacy-config-panel { margin-top: 18px; padding-top: 18px; border-top: 1px solid #edf0f2; }
.section-heading { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }.section-heading h3 { margin: 0 0 5px; font-size: 17px; }.section-heading .el-tag { margin-left: auto; }
.step-number { display: inline-flex; width: 30px; height: 30px; flex: 0 0 30px; align-items: center; justify-content: center; background: #2f7d69; color: #fff; font-weight: 600; }
.archive-field-status { display: flex; min-width: 0; height: 22px; align-items: center; gap: 6px; overflow: hidden; color: #4c7d6f; font-size: 12px; line-height: 22px; }.archive-field-status i { flex: none; font-size: 14px; }.archive-field-status span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.archive-field-status.locked { color: #c56a55; }
.archive-field-status.inherited { color: #2f7d69; }
.unified-upload { margin-bottom: 20px; }
.upload-source-tabs { margin-top: -8px; }
.upload-source-tabs ::v-deep .el-tabs__header { margin-bottom: 14px; }
.upload-source-tabs ::v-deep .el-tabs__item { height: 38px; line-height: 38px; font-size: 15px; }
.library-picker-toolbar { display: grid; grid-template-columns: minmax(0,1fr) auto auto; gap: 10px; margin-bottom: 12px; }
.library-picker-table { border: 1px solid #e4e9ed; border-radius: 8px; overflow: hidden; }
.library-file-cell { display: flex; min-width: 0; align-items: center; gap: 10px; }
.library-file-cell i { display: inline-flex; width: 30px; height: 34px; flex: 0 0 30px; align-items: center; justify-content: center; background: #e7f3ef; color: #2f7d69; font-size: 17px; }
.library-file-cell span { min-width: 0; }
.library-file-cell strong,.library-file-cell small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.library-file-cell strong { color: #1f2c28; font-weight: 600; }
.library-file-cell small { margin-top: 3px; color: #8b949c; font-size: 12px; }
.unified-upload ::v-deep .el-upload-dragger { height: 124px; }
.unified-upload ::v-deep .file-drop .el-icon-upload2 { margin-top: 23px; }
.recognition-alert { margin-top: 12px; }.parameter-area { min-width: 0; border-top: 1px solid #edf0f2; padding-top: 12px; }
.audit-data-dialog ::v-deep .el-dialog__body { max-height: 68vh; overflow: auto; padding-top: 10px; }
.audit-data-dialog .parameter-area { border-top: 0; padding-top: 0; }
.conflict-alert { margin-bottom: 12px; }
.missing-chip-list { display: flex; flex-wrap: wrap; gap: 8px; margin: -2px 0 12px; }
.missing-chip-list .el-tag { cursor: pointer; }
.conflict-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; padding: 12px; border: 1px solid #f3dfbd; border-radius: 8px; background: #fffaf0; }
.conflict-row { display: grid; grid-template-columns: 128px minmax(0,1fr); gap: 12px; align-items: flex-start; }
.conflict-label { color: #6b5a31; font-weight: 600; }
.conflict-row ::v-deep .el-radio-group { display: flex; flex-wrap: wrap; gap: 6px; }
.conflict-row ::v-deep .el-radio-button__inner { border-radius: 4px; border-left: 1px solid #dcdfe6; }
.conflict-options { min-width: 0; }
.conflict-source-list { display: flex; flex-direction: column; gap: 3px; margin-top: 8px; color: #8a8f94; font-size: 12px; line-height: 1.45; }
.conflict-source { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.document-list { margin-top: 12px; border: 1px solid #e5eaed; }
.document-row { display: grid; grid-template-columns: 24px minmax(0,1fr) auto auto 132px 28px; align-items: center; gap: 10px; min-height: 58px; padding: 8px 12px; border-bottom: 1px solid #edf0f2; }
.document-row:last-child { border-bottom: 0; }.document-row > i { color: #2f7d69; font-size: 18px; }
.document-row > .el-icon-warning-outline { color: #d99b32; }.document-name { min-width: 0; }.document-name strong,.document-name small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.document-name small { margin-top: 5px; color: #879199; }.role-select { width: 132px; }.document-remove { color: #8a949c; }
.parameter-form { padding-top: 6px; }.parameter-form ::v-deep .el-select,.parameter-form ::v-deep .el-input-number { width: 100%; }
.project-name-input { width: 100%; }
.custom-stage-input { margin-top: 8px; }
.command-bar { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-top: 22px; padding-top: 18px; border-top: 1px solid #edf0f2; }
.command-bar > span { color: #88919a; font-size: 12px; }.command-bar > div { display: flex; gap: 10px; }
.result-head { display: flex; min-height: 0; align-items: flex-start; justify-content: flex-end; gap: 16px; margin-bottom: 0; }
.reaudit-alert { margin: -4px 0 14px; }
.empty-state { padding: 95px 0; text-align: center; color: #9099a2; }.empty-state i { font-size: 42px; }
.audit-chat-shell { display: flex; min-height: 0; flex: 1; flex-direction: column; }
.audit-chat-scroll { flex: 1; min-height: 300px; overflow: auto; padding: 8px 8px 18px; background: linear-gradient(180deg,#fff 0%,#fbfcfc 100%); }
.chat-row { display: flex; gap: 12px; margin: 14px 0; align-items: flex-start; }
.chat-row.user { flex-direction: row-reverse; }
.chat-avatar { display: inline-flex; width: 34px; height: 34px; flex: 0 0 34px; align-items: center; justify-content: center; border-radius: 50%; background: #e5f2ee; color: #2f7d69; font-size: 12px; font-weight: 700; }
.chat-row.user .chat-avatar { background: #e8f1ff; color: #2b78d4; }
.chat-bubble { max-width: min(980px, calc(100% - 52px)); border: 1px solid #e5ece9; border-radius: 12px; padding: 15px 16px; background: #fff; box-shadow: 0 8px 22px rgba(31, 51, 44, .05); }
.chat-row.user .chat-bubble { border-color: #d8e7fb; background: #eef6ff; }
.chat-bubble p { margin: 0; color: #303b37; line-height: 1.75; white-space: pre-wrap; }
.snapshot-bubble { width: min(980px, calc(100% - 52px)); }
.message-review-list { margin-top: 14px; border-top: 1px solid #edf0f2; padding-top: 12px; }
.message-review-list.latest { margin-top: 0; border-top: 0; padding-top: 0; }
.message-review-list.collapsed { margin-top: 10px; padding-top: 10px; }
.message-review-title { margin-bottom: 10px; color: #2f7d69; font-weight: 700; }
.snapshot-summary-line { display: flex; align-items: center; justify-content: space-between; gap: 12px; color: #2f7d69; font-weight: 700; }
.snapshot-summary-line .el-button { padding: 0; }
.snapshot-detail { margin-top: 12px; }
.thinking-bubble { min-width: 68px; padding: 14px 18px; }
.thinking-text { display: inline-flex; align-items: center; gap: 6px; color: #60736d; }
.thinking-text i.el-icon-loading { margin-right: 6px; color: #2f7d69; }
.thinking-dots { display: inline-flex; align-items: center; gap: 4px; padding-top: 5px; }
.thinking-dots.only-dots { padding-top: 0; }
.thinking-dots i { width: 5px; height: 5px; border-radius: 50%; background: #2f7d69; opacity: .35; animation: thinking-dot 1.15s infinite ease-in-out; }
.thinking-dots i:nth-child(2) { animation-delay: .16s; }
.thinking-dots i:nth-child(3) { animation-delay: .32s; }
@keyframes thinking-dot {
  0%, 80%, 100% { transform: translateY(0); opacity: .35; }
  40% { transform: translateY(-4px); opacity: 1; }
}
.review-bubble { width: min(980px, calc(100% - 52px)); max-width: calc(100% - 52px); }
.review-bubble-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.review-bubble-head strong,.review-bubble-head small { display: block; }.review-bubble-head small { margin-top: 5px; color: #7d8782; font-size: 12px; }
.review-item-card { margin-bottom: 12px; border: 1px solid #e2e9e6; border-radius: 8px; padding: 15px 16px; background: #fff; }
.review-item-card:hover { border-color: #c7ddd5; box-shadow: 0 6px 18px rgba(39, 71, 61, .06); }
.review-item-head { display: grid; grid-template-columns: 34px minmax(0,1fr) auto; gap: 10px; align-items: start; }
.review-order { display: inline-flex; width: 28px; height: 28px; align-items: center; justify-content: center; border: 2px solid #67a897; border-radius: 50%; color: #2f7d69; font-weight: 700; }
.review-item-head h4 { display: inline; margin: 0 8px 0 0; color: #1f2f2b; font-size: 16px; }
.review-actions { display: flex; gap: 8px; }.danger-link { color: #d05f4a; }
.review-item-card.compact { padding: 12px 14px; }
.review-conclusion { margin: 12px 0 0 0; color: #263833; font-weight: 600; line-height: 1.8; white-space: pre-wrap; }
.review-conclusion span { margin-right: 8px; color: #2f7d69; font-weight: 700; }
.review-basis { margin: 9px 0 0 0; color: #76827d; font-size: 12px; line-height: 1.6; }
.overall-review-card { margin-top: 14px; border: 1px solid #d9e9e3; border-left: 4px solid #2f7d69; border-radius: 8px; padding: 14px 16px; background: #f6fbf9; }
.overall-review-card h4 { margin: 0 0 8px; color: #1f4f43; font-size: 15px; }
.overall-review-card p { margin: 0; color: #263833; font-weight: 600; line-height: 1.8; white-space: pre-wrap; }
.overall-review-card.compact { margin-top: 12px; padding: 12px 14px; }
.composer-sticky-zone { position: fixed; right: 24px; bottom: 0; left: 276px; z-index: 1001; padding: 14px 22px 18px; background: linear-gradient(180deg, rgba(245,247,248,0) 0%, #f5f7f8 18%, #f5f7f8 100%); }
.chat-input-bar { margin-top: 0; }
.chat-composer { border: 1px solid #d8dee2; border-radius: 24px; padding: 10px 14px 10px; background: #fff; box-shadow: 0 8px 26px rgba(32, 48, 43, .06); transition: border-color .18s ease, box-shadow .18s ease; }
.chat-composer:focus-within { border-color: #9fbab2; box-shadow: 0 10px 30px rgba(47, 125, 105, .1); }
.composer-input-surface { border-radius: 16px; background: #f7f9fb; padding: 10px 10px 8px; }
.chat-composer-input ::v-deep .el-textarea__inner { min-height: 38px !important; border: 0; padding: 0 2px; resize: none; color: #24312d; font-size: 16px; line-height: 1.55; background: transparent; box-shadow: none; }
.chat-composer-input ::v-deep .el-textarea__inner::placeholder { color: #b9c0c5; }
.composer-file-cards { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 8px; }
.composer-file-card { display: grid; grid-template-columns: 30px minmax(0,1fr) auto 22px; align-items: center; gap: 8px; max-width: 340px; min-width: 230px; padding: 8px 8px 8px 10px; border: 1px solid #e2e8ed; border-radius: 10px; background: #fff; color: #1f2c28; }
.composer-file-icon { display: inline-flex; width: 30px; height: 30px; align-items: center; justify-content: center; border-radius: 8px; background: #e9f2ff; color: #1677ff; font-size: 12px; font-weight: 800; letter-spacing: 0; }
.composer-file-meta { min-width: 0; }
.composer-file-meta strong,.composer-file-meta small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.composer-file-meta strong { color: #1f2c28; font-size: 14px; font-weight: 700; line-height: 1.3; }
.composer-file-meta small { margin-top: 2px; color: #929ba2; font-size: 12px; line-height: 1.25; }
.composer-file-remove { width: 22px; height: 22px; padding: 0; color: #8a949b; }
.composer-file-remove:hover,.composer-file-remove:focus { color: #d05f4a; }
.chat-composer-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 4px; }
.composer-left,.composer-tools { display: flex; align-items: center; gap: 8px; }
.composer-pill { height: 32px; border-radius: 18px; color: #31403b; background: #fff; }
.composer-pill i { margin-right: 4px; color: #2f7d69; }
.composer-icon-btn { width: 34px; height: 34px; border: 0; padding: 0; color: #202a27; background: transparent; font-size: 21px; }
.composer-icon-btn:hover,.composer-icon-btn:focus { color: #2f7d69; background: #edf7f3; }
.composer-send-btn { width: 36px; height: 36px; border: 0; color: #fff; background: #b8bfc5; font-size: 18px; }
.composer-send-btn:not(.is-disabled) { background: #2f7d69; }
.composer-send-btn:not(.is-disabled):hover,.composer-send-btn:not(.is-disabled):focus { background: #286e5d; }
.composer-send-btn.is-disabled { color: #fff; background: #c6ccd1; }
.result-actions { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-top: 10px; padding: 10px 0 0; border-top: 1px solid #edf0f2; }
.result-actions > span { color: #7d8782; font-size: 12px; }.result-actions > div { display: flex; gap: 10px; }
.decision-grid { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); border: 1px solid #e6eaec; }.decision-grid div { display: flex; min-height: 86px; flex-direction: column; justify-content: center; padding: 15px; border-right: 1px solid #e6eaec; }.decision-grid div:last-child { border-right: 0; }.decision-grid span { color: #758089; }.decision-grid strong { margin-top: 8px; color: #2f7d69; }
.overall-summary { margin: 18px 0 0; padding: 18px 0; border-top: 1px solid #e5e9ec; color: #303a40; line-height: 1.85; }
.overall-summary strong { color: #20282d; }.risk-section { padding: 18px 0 2px; border-top: 1px solid #edf0f2; }.risk-section h4 { margin: 0 0 15px; }
.risk-item { margin-bottom: 18px; padding-left: 17px; border-left: 3px solid #2f7d69; }.risk-item > div:first-child { display: flex; align-items: center; gap: 9px; }.risk-item p { margin: 7px 0; line-height: 1.75; }.risk-item small { color: #6f797e; }
.recommendation { margin-top: 9px; padding: 9px 11px; background: #f4f8f7; line-height: 1.65; }.recommendation span { margin-right: 8px; color: #2f7d69; font-weight: 600; }
.opinion-block,.match-block { margin-top: 18px; padding: 17px; border-left: 3px solid #4d7485; background: #f4f7f9; }.opinion-block h4 { margin: 0 0 12px; }.opinion-block p,.match-block p { display: grid; grid-template-columns: 26px 1fr; gap: 8px; line-height: 1.7; }
.opinion-block p span,.match-block p span { color: #2f7d69; font-weight: 600; }.match-block > div { display: flex; flex-direction: column; gap: 5px; }.match-block > .el-tag { float: right; margin-top: -34px; }
@media (max-width: 1100px) { .decision-grid { grid-template-columns: repeat(2,1fr); } }
@media (max-width: 760px) { .document-row { grid-template-columns: 22px minmax(0,1fr) 118px 24px; }.document-row > .el-tag { display: none; }.role-select { width: 118px; } }
@media (max-width: 900px) { .review-brief { align-items: stretch; flex-direction: column; }.brief-actions { display: grid; grid-template-columns: 1fr; } }
@media (max-width: 700px) { .command-bar,.result-actions { align-items: stretch; flex-direction: column; }.command-bar > div,.result-actions > div { display: grid; grid-template-columns: 1fr; }.decision-grid { grid-template-columns: 1fr; }.chat-composer { border-radius: 22px; padding: 12px; }.review-item-head { grid-template-columns: 30px minmax(0,1fr); }.review-actions { grid-column: 2; } }
</style>
