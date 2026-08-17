<template>
  <div class="reply-page">
    <aside class="reply-nav library-nav">
      <div class="reply-title library-title">
        <span><i class="el-icon-message" /> 回函知识库</span>
        <el-button type="text" icon="el-icon-plus" title="新建项目文件夹" @click="createProjectFolder" />
      </div>

      <button :class="['reply-nav-row nav-row', { active: selectedFolder === 'all' }]" @click="selectFolder('all')">
        <i class="el-icon-collection-tag" />
        <span>全部回函</span>
        <em>{{ assets.length }}</em>
      </button>

      <template v-for="project in projectFolders">
        <button
          :key="project.id"
          :class="['reply-nav-row nav-row custom project-row', { active: selectedFolder === project.id }]"
          @click="selectFolder(project.id)"
        >
          <span class="folder-toggle" @click.stop="toggleProject(project.name)">
            <i :class="isProjectExpanded(project.name) ? 'el-icon-arrow-down' : 'el-icon-arrow-right'" />
          </span>
          <i class="el-icon-folder-opened" />
          <span :title="project.name">{{ project.name }}</span>
          <em>{{ project.count }}</em>
          <el-dropdown trigger="click" @command="command => manageProjectFolder(command, project)">
            <span class="row-more folder-more" title="管理文件夹" @click.stop><i class="el-icon-more" /></span>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="rename" icon="el-icon-edit">重命名</el-dropdown-item>
              <el-dropdown-item command="delete" icon="el-icon-delete" divided>删除文件夹</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </button>

        <template v-if="isProjectExpanded(project.name)">
          <button
            v-for="stage in stageFolders(project.name)"
            :key="stage.id"
            :class="['reply-nav-row nav-row custom stage-row', { active: selectedFolder === stage.id }]"
            @click="selectFolder(stage.id)"
          >
            <span class="folder-toggle-placeholder" />
            <i class="el-icon-folder" />
            <span>{{ stage.name }}</span>
            <em>{{ stage.count }}</em>
          </button>
        </template>
      </template>
    </aside>

    <main class="reply-list-pane">
      <div class="reply-toolbar">
        <el-input v-model="keyword" clearable prefix-icon="el-icon-search" placeholder="搜索全部回函文件" />
        <el-button icon="el-icon-folder-add" title="新建项目文件夹" @click="createProjectFolder" />
        <el-button type="primary" icon="el-icon-upload2" @click="uploadOpen = true">上传回函</el-button>
      </div>

      <div class="reply-caption">
        <div class="folder-path">
          <button v-if="selectedFolder !== 'all'" class="back-button" @click="returnToParent">
            <i class="el-icon-back" /> 返回上一级
          </button>
          <strong>{{ currentFolderName }}</strong>
        </div>
        <span>{{ currentAssetCount }} 个文件</span>
      </div>

      <div v-loading="loading" class="reply-list">
        <div
          v-for="folder in visibleStageFolders"
          :key="folder.id"
          class="reply-row folder-entry"
          @click="selectFolder(folder.id)"
        >
          <span class="reply-file-icon folder-icon"><i class="el-icon-folder-opened" /></span>
          <span class="reply-copy">
            <strong>{{ folder.name }}</strong>
            <small>{{ folder.count }} 个文件</small>
          </span>
          <el-dropdown v-if="isProjectFolder(folder.id)" trigger="click" @command="command => manageProjectFolder(command, folder)">
            <button class="row-more" title="管理文件夹" @click.stop><i class="el-icon-more" /></button>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="rename" icon="el-icon-edit">重命名</el-dropdown-item>
              <el-dropdown-item command="delete" icon="el-icon-delete" divided>删除文件夹</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </div>

        <div
          v-for="item in visibleAssets"
          :key="item.asset_id"
          :class="['reply-row', { selected: selectedAssetId === item.asset_id }]"
          @click="selectAsset(item)"
        >
          <span class="reply-file-icon"><i :class="assetIcon(item)" /></span>
          <span class="reply-copy">
            <strong>{{ item.display_name }}</strong>
            <small>{{ item.original_file_name }} · {{ formatSize(item.file_size) }}</small>
          </span>
          <el-dropdown trigger="click" @command="command => manageAsset(command, item)">
            <button class="row-more" title="管理文件" @click.stop><i class="el-icon-more" /></button>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="rename" icon="el-icon-edit">重命名</el-dropdown-item>
              <el-dropdown-item command="move" icon="el-icon-folder-opened">移动到阶段</el-dropdown-item>
              <el-dropdown-item command="download" icon="el-icon-download">下载</el-dropdown-item>
              <el-dropdown-item command="delete" icon="el-icon-delete" divided>删除文件</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </div>

        <el-empty
          v-if="!loading && !visibleStageFolders.length && !visibleAssets.length"
          description="该文件夹暂无回函"
          :image-size="78"
        />
      </div>
    </main>

    <section class="reply-detail-pane">
      <div v-if="!assetDetail" class="reply-empty">
        <i class="el-icon-document" />
        <p>选择文件查看详情</p>
      </div>
      <template v-else>
        <header class="reply-detail-head">
          <div class="title">
            <span><i :class="assetIcon(assetDetail)" /></span>
            <div>
              <h2>{{ assetDetail.display_name }}</h2>
              <p>{{ assetDetail.original_file_name }} · {{ formatSize(assetDetail.file_size) }}</p>
            </div>
          </div>
          <div class="actions">
            <el-button icon="el-icon-download" circle title="下载文件" @click="downloadAsset(assetDetail)" />
          </div>
        </header>

        <div class="reply-preview">
          <iframe
            v-if="previewUrl && assetDetail.file_kind === 'pdf'"
            :src="`${previewUrl}#toolbar=1&navpanes=0&view=FitH`"
            :title="assetDetail.display_name"
          />
          <div v-else class="preview-message">
            <i :class="assetIcon(assetDetail)" />
            <p>该回函已保存至知识库。Word 文件请下载后查看；PDF 文件可直接预览。</p>
            <el-button type="primary" plain icon="el-icon-download" @click="downloadAsset(assetDetail)">下载文件</el-button>
          </div>
        </div>
      </template>
    </section>

    <el-dialog
      title="上传回函"
      :visible.sync="uploadOpen"
      width="620px"
      append-to-body
      :close-on-click-modal="false"
      @open="initUploadContext"
      @closed="resetUpload"
    >
      <file-drop-zone
        ref="picker"
        v-model="uploadFiles"
        multiple
        show-list
        :limit="20"
        accept=".pdf,.doc,.docx"
        hint="支持 Word、PDF；一次最多 20 个文件"
      />
      <el-form label-position="top" class="upload-form">
        <el-form-item label="上传到文件夹">
          <el-cascader
            v-model="uploadFolderPath"
            :options="replyFolderOptions"
            clearable
            filterable
            placeholder="选择已有项目 / 阶段文件夹"
            style="width:100%"
            @change="handleUploadFolderChange"
          />
          <div class="upload-tip">选择已有文件夹后会自动填入项目名称和阶段；也可以在下方直接输入新项目。</div>
        </el-form-item>
        <el-form-item label="项目名称" required>
          <el-autocomplete
            v-model.trim="uploadProjectName"
            value-key="value"
            clearable
            :fetch-suggestions="queryProjects"
            placeholder="输入或选择项目名称"
            @select="syncUploadFolderPath"
            @blur="syncUploadFolderPath"
          />
        </el-form-item>
        <el-form-item label="项目阶段" required>
          <el-select v-model="uploadStageName" placeholder="请选择阶段" @change="syncUploadFolderPath">
            <el-option v-for="stage in stageNames" :key="stage" :label="stage" :value="stage" />
          </el-select>
        </el-form-item>
      </el-form>
      <div v-if="!canUpload" class="upload-requirement">
        请先选择回函文件，并填写项目名称和项目阶段。
      </div>
      <div v-if="uploading" class="processing-note"><i class="el-icon-loading" /> {{ uploadProgressText }}</div>
      <div slot="footer">
        <el-button @click="uploadOpen = false">取消</el-button>
        <el-button type="primary" :loading="uploading" :disabled="!canUpload" @click="submitUpload">上传</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { saveAs } from 'file-saver'
import FileDropZone from '../components/FileDropZone.vue'
import {
  listLibraryAssets,
  uploadLibraryAsset,
  renameLibraryAsset,
  moveLibraryAsset,
  deleteLibraryAsset,
  downloadLibraryAsset
} from '@/api/rail/audit'

const STAGE_NAMES = ['规划阶段', '设计阶段', '施工阶段']
const REPLY_FOLDER_STORAGE_KEY = 'rail_reply_library_folders_v1'
const STAGE_CODE_MAP = {
  规划阶段: 'plan',
  设计阶段: 'design',
  施工阶段: 'build'
}
const CODE_STAGE_MAP = Object.keys(STAGE_CODE_MAP).reduce((result, name) => {
  result[STAGE_CODE_MAP[name]] = name
  return result
}, {})

function stableProjectKey(value) {
  const text = String(value || '').trim()
  let hash = 5381
  for (let index = 0; index < text.length; index += 1) {
    hash = ((hash << 5) + hash) ^ text.charCodeAt(index)
  }
  return `p${(hash >>> 0).toString(36)}`
}

function readReplyFolders() {
  try {
    const parsed = JSON.parse(localStorage.getItem(REPLY_FOLDER_STORAGE_KEY) || '[]')
    if (!Array.isArray(parsed)) return []
    return parsed
      .map(item => ({
        projectName: String(item.projectName || '').trim(),
        folderKey: String(item.folderKey || '').trim(),
        stages: Array.isArray(item.stages) ? item.stages.map(stage => String(stage || '').trim()).filter(Boolean) : []
      }))
      .filter(item => item.projectName)
      .map(item => ({
        ...item,
        folderKey: item.folderKey || stableProjectKey(item.projectName)
      }))
  } catch (error) {
    return []
  }
}

function writeReplyFolders(folders) {
  localStorage.setItem(REPLY_FOLDER_STORAGE_KEY, JSON.stringify(folders.map(item => ({
    projectName: item.projectName,
    folderKey: item.folderKey || stableProjectKey(item.projectName),
    stages: item.stages
  }))))
}

function projectKeyFor(projectName) {
  const name = String(projectName || '').trim()
  const stored = readReplyFolders().find(item => item.projectName === name)
  return (stored && stored.folderKey) || stableProjectKey(name)
}

function projectNameForKey(folderKey) {
  const key = String(folderKey || '').trim()
  const stored = readReplyFolders().find(item => item.folderKey === key)
  return (stored && stored.projectName) || ''
}

function folderIdFromKey(folderKey, stageName = '') {
  const key = String(folderKey || '').trim()
  if (!stageName) return `rpk:${key}`
  return `rp:${key}:${STAGE_CODE_MAP[stageName] || encodeURIComponent(stageName)}`
}

function folderId(projectName, stageName = '') {
  const project = encodeURIComponent(String(projectName || '').trim())
  if (!stageName) return `reply-project:${project}`
  return `reply:${project}:${encodeURIComponent(String(stageName || '').trim())}`
}

function parseFolderId(value) {
  const text = String(value || '')
  if (text.startsWith('rpk:')) {
    const folderKey = text.slice('rpk:'.length)
    return { projectName: projectNameForKey(folderKey), stageName: '', folderKey }
  }
  if (text.startsWith('rp:')) {
    const [, folderKey = '', stageCode = ''] = text.split(':')
    return {
      projectName: projectNameForKey(folderKey),
      stageName: CODE_STAGE_MAP[stageCode] || decodeURIComponent(stageCode),
      folderKey
    }
  }
  if (text.startsWith('reply-project:')) {
    const projectName = decodeURIComponent(text.slice('reply-project:'.length))
    return { projectName, stageName: '', folderKey: projectKeyFor(projectName) }
  }
  if (text.startsWith('reply:')) {
    const [, project = '', stage = ''] = text.split(':')
    const projectName = decodeURIComponent(project)
    return { projectName, stageName: decodeURIComponent(stage), folderKey: projectKeyFor(projectName) }
  }
  return { projectName: '', stageName: '', folderKey: '' }
}

export default {
  name: 'ReplyLibrary',
  components: { FileDropZone },
  data() {
    return {
      loading: false,
      keyword: '',
      selectedFolder: 'all',
      assets: [],
      selectedAssetId: '',
      assetDetail: null,
      previewUrl: '',
      uploadOpen: false,
      uploadFiles: [],
      uploadProjectName: '',
      uploadStageName: '规划阶段',
      uploadFolderPath: [],
      uploading: false,
      uploadProgressText: '',
      stageNames: STAGE_NAMES,
      replyFolders: readReplyFolders(),
      expandedProjects: {}
    }
  },
  computed: {
    projectFolders() {
      const map = new Map()
      this.replyFolders.forEach(item => {
        if (!item.projectName) return
        map.set(item.projectName, { count: 0, folderKey: item.folderKey || stableProjectKey(item.projectName) })
      })
      this.assets.forEach(item => {
        const { projectName, folderKey } = parseFolderId(item.folder_id)
        if (!projectName) return
        const current = map.get(projectName) || { count: 0, folderKey: folderKey || stableProjectKey(projectName) }
        current.count += 1
        map.set(projectName, current)
      })
      return [...map.entries()]
        .sort((a, b) => a[0].localeCompare(b[0], 'zh-Hans-CN'))
        .map(([name, meta]) => ({ id: folderId(name), name, count: meta.count, folderKey: meta.folderKey }))
    },
    visibleStageFolders() {
      if (this.keyword.trim()) return []
      if (this.selectedFolder === 'all') return this.projectFolders
      const { projectName, stageName } = parseFolderId(this.selectedFolder)
      if (!projectName || stageName) return []
      return this.stageFolders(projectName)
    },
    visibleAssets() {
      const token = this.keyword.trim().toLowerCase()
      return this.assets.filter(item => {
        const { projectName, stageName } = parseFolderId(item.folder_id)
        const matches = !token || [
          item.display_name,
          item.original_file_name,
          projectName,
          stageName
        ].filter(Boolean).join(' ').toLowerCase().includes(token)
        if (!matches) return false
        if (token) return true
        if (this.selectedFolder === 'all') return false
        const current = parseFolderId(this.selectedFolder)
        if (current.projectName && !current.stageName) return projectName === current.projectName && !stageName
        return projectName === current.projectName && stageName === current.stageName
      })
    },
    currentAssetCount() {
      const token = this.keyword.trim().toLowerCase()
      if (token) return this.visibleAssets.length
      if (this.selectedFolder === 'all') return this.assets.length
      const current = parseFolderId(this.selectedFolder)
      if (!current.projectName) return this.assets.length
      if (!current.stageName) {
        return this.assets.filter(item => parseFolderId(item.folder_id).projectName === current.projectName).length
      }
      return this.visibleAssets.length
    },
    currentFolderName() {
      if (this.selectedFolder === 'all') return '全部回函'
      const { projectName, stageName } = parseFolderId(this.selectedFolder)
      return stageName ? stageName : (projectName || '回函知识库')
    },
    replyFolderOptions() {
      return this.projectFolders.map(project => ({
        value: project.name,
        label: project.name,
        children: this.stageFolders(project.name).map(stage => ({
          value: stage.name,
          label: `${stage.name}（${stage.count}）`
        }))
      }))
    },
    canUpload() {
      return this.uploadFiles.length && this.uploadProjectName.trim() && this.uploadStageName
    }
  },
  created() {
    this.reload()
  },
  beforeDestroy() {
    this.releasePreview()
  },
  methods: {
    async reload() {
      this.loading = true
      try {
        this.assets = await listLibraryAssets({ library_type: 'reply' }) || []
      } finally {
        this.loading = false
      }
    },
    stageFolders(projectName) {
      const stored = this.replyFolders.find(item => item.projectName === projectName)
      const names = [...new Set([...STAGE_NAMES, ...((stored && stored.stages) || [])])]
      return names.map(name => {
        const id = folderId(projectName, name)
        const count = this.assets.filter(item => {
          const parsed = parseFolderId(item.folder_id)
          return parsed.projectName === projectName && parsed.stageName === name
        }).length
        return { id, name, count }
      })
    },
    persistReplyFolders() {
      writeReplyFolders(this.replyFolders)
    },
    ensureReplyFolder(projectName, stageName = '') {
      const name = String(projectName || '').trim()
      if (!name) return
      const stage = String(stageName || '').trim()
      let folder = this.replyFolders.find(item => item.projectName === name)
      if (!folder) {
        folder = { projectName: name, folderKey: stableProjectKey(name), stages: [...STAGE_NAMES] }
        this.replyFolders.push(folder)
      }
      if (!folder.folderKey) folder.folderKey = stableProjectKey(name)
      if (stage && !folder.stages.includes(stage)) folder.stages.push(stage)
      this.persistReplyFolders()
    },
    isProjectExpanded(projectName) {
      return this.expandedProjects[projectName] === true
    },
    isProjectFolder(id) {
      const { projectName, stageName } = parseFolderId(id)
      return !!projectName && !stageName
    },
    toggleProject(projectName) {
      this.$set(this.expandedProjects, projectName, !this.isProjectExpanded(projectName))
    },
    async createProjectFolder() {
      const { value } = await this.$prompt('请输入项目名称', '新建回函文件夹', {
        inputPattern: /\S+/,
        inputErrorMessage: '项目名称不能为空',
        confirmButtonText: '新建',
        cancelButtonText: '取消'
      })
      const projectName = String(value || '').trim()
      if (!projectName) return
      const existed = this.projectFolders.some(item => item.name === projectName)
      this.ensureReplyFolder(projectName)
      this.selectFolder(folderId(projectName))
      this.$message.success(existed ? '项目文件夹已存在，已为你打开' : '已新建项目文件夹')
    },
    async manageProjectFolder(command, project) {
      if (command === 'rename') return this.renameProjectFolder(project)
      if (command === 'delete') return this.deleteProjectFolder(project)
    },
    async renameProjectFolder(project) {
      const oldName = String(project.name || '').trim()
      if (!oldName) return
      const { value } = await this.$prompt('请输入新的项目文件夹名称', '重命名文件夹', {
        inputValue: oldName,
        inputPattern: /\S+/,
        inputErrorMessage: '项目名称不能为空',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      })
      const newName = String(value || '').trim()
      if (!newName || newName === oldName) return
      if (this.projectFolders.some(item => item.name === newName)) {
        return this.$message.warning('已存在同名项目文件夹')
      }
      const stored = this.replyFolders.find(item => item.projectName === oldName)
      const folderKey = (stored && stored.folderKey) || (project.folderKey || stableProjectKey(oldName))
      const affected = this.assets.filter(item => parseFolderId(item.folder_id).projectName === oldName)
      for (const item of affected) {
        const { stageName } = parseFolderId(item.folder_id)
        await moveLibraryAsset(item.asset_id, folderId(newName, stageName || STAGE_NAMES[0]))
      }
      if (stored) {
        stored.projectName = newName
        stored.folderKey = folderKey
      } else {
        this.replyFolders.push({ projectName: newName, folderKey, stages: [...STAGE_NAMES] })
      }
      delete this.expandedProjects[oldName]
      this.$set(this.expandedProjects, newName, true)
      const selected = parseFolderId(this.selectedFolder)
      if (selected.projectName === oldName) this.selectedFolder = folderId(newName, selected.stageName)
      this.persistReplyFolders()
      await this.reload()
      this.$message.success('文件夹已重命名')
    },
    async deleteProjectFolder(project) {
      const projectName = String(project.name || '').trim()
      if (!projectName) return
      const affected = this.assets.filter(item => parseFolderId(item.folder_id).projectName === projectName)
      const message = affected.length
        ? `确定删除项目文件夹“${projectName}”吗？该文件夹下 ${affected.length} 个回函文件也会被删除，且无法恢复。`
        : `确定删除项目文件夹“${projectName}”吗？`
      await this.$confirm(message, '删除文件夹', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      })
      for (const item of affected) {
        await deleteLibraryAsset(item.asset_id)
      }
      this.replyFolders = this.replyFolders.filter(item => item.projectName !== projectName)
      delete this.expandedProjects[projectName]
      const selected = parseFolderId(this.selectedFolder)
      if (selected.projectName === projectName) this.selectFolder('all')
      if (this.assetDetail && affected.some(item => item.asset_id === this.assetDetail.asset_id)) {
        this.selectedAssetId = ''
        this.assetDetail = null
        this.releasePreview()
      }
      this.persistReplyFolders()
      await this.reload()
      this.$message.success('文件夹已删除')
    },
    initUploadContext() {
      const { projectName, stageName } = parseFolderId(this.selectedFolder)
      if (projectName && !this.uploadProjectName) this.uploadProjectName = projectName
      if (stageName) this.uploadStageName = stageName
      if (!this.uploadStageName) this.uploadStageName = '规划阶段'
      this.syncUploadFolderPath()
    },
    syncUploadFolderPath() {
      const projectName = String(this.uploadProjectName || '').trim()
      const stageName = String(this.uploadStageName || '').trim()
      if (!projectName || !stageName) {
        this.uploadFolderPath = []
        return
      }
      const project = this.projectFolders.find(item => item.name === projectName)
      if (!project) {
        this.uploadFolderPath = []
        return
      }
      const hasStage = this.stageFolders(projectName).some(item => item.name === stageName)
      this.uploadFolderPath = hasStage ? [projectName, stageName] : []
    },
    handleUploadFolderChange(value) {
      const path = Array.isArray(value) ? value : []
      if (path.length >= 1) this.uploadProjectName = path[0] || ''
      if (path.length >= 2) this.uploadStageName = path[1] || '规划阶段'
    },
    selectFolder(id) {
      this.releasePreview()
      this.selectedFolder = id
      const { projectName } = parseFolderId(id)
      if (projectName) this.$set(this.expandedProjects, projectName, true)
      this.selectedAssetId = ''
      this.assetDetail = null
    },
    returnToParent() {
      const { projectName, stageName } = parseFolderId(this.selectedFolder)
      this.selectFolder(stageName ? folderId(projectName) : 'all')
    },
    queryProjects(queryString, callback) {
      const token = String(queryString || '').trim().toLowerCase()
      callback(this.projectFolders
        .filter(item => !token || item.name.toLowerCase().includes(token))
        .map(item => ({ value: item.name })))
    },
    async selectAsset(item) {
      this.releasePreview()
      this.selectedAssetId = item.asset_id
      this.assetDetail = item
      if (item.file_kind !== 'pdf') return
      const source = await downloadLibraryAsset(item.asset_id)
      this.previewUrl = URL.createObjectURL(new Blob([source], { type: item.media_type || 'application/pdf' }))
    },
    assetIcon(item) {
      if (item.file_kind === 'pdf') return 'el-icon-document'
      if (item.file_kind === 'word') return 'el-icon-document-copy'
      return 'el-icon-document'
    },
    formatSize(value) {
      if (!value) return '0 B'
      if (value < 1024) return `${value} B`
      if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
      return `${(value / 1024 / 1024).toFixed(1)} MB`
    },
    releasePreview() {
      if (this.previewUrl) URL.revokeObjectURL(this.previewUrl)
      this.previewUrl = ''
    },
    async downloadAsset(item) {
      saveAs(await downloadLibraryAsset(item.asset_id), item.original_file_name)
    },
    async manageAsset(command, item) {
      if (command === 'download') return this.downloadAsset(item)
      if (command === 'rename') {
        const { value } = await this.$prompt('请输入新的文件名称', '重命名文件', {
          inputValue: item.display_name,
          inputPattern: /\S+/,
          inputErrorMessage: '名称不能为空'
        })
        await renameLibraryAsset(item.asset_id, value.trim())
      } else if (command === 'move') {
        const current = parseFolderId(item.folder_id)
        const { value: projectName } = await this.$prompt('请输入项目名称', '移动回函', {
          inputValue: current.projectName,
          inputPattern: /\S+/,
          inputErrorMessage: '项目名称不能为空'
        })
        const { value: stageName } = await this.$prompt('请输入阶段名称：规划阶段、设计阶段或施工阶段', '移动回函', {
          inputValue: current.stageName || '规划阶段',
          inputPattern: /^(规划阶段|设计阶段|施工阶段)$/,
          inputErrorMessage: '阶段只能为规划阶段、设计阶段或施工阶段'
        })
        this.ensureReplyFolder(projectName, stageName)
        await moveLibraryAsset(item.asset_id, folderId(projectName, stageName))
      } else if (command === 'delete') {
        await this.$confirm(`确定删除回函“${item.display_name}”吗？此操作会删除文件且无法恢复。`, '删除回函', { type: 'warning' })
        await deleteLibraryAsset(item.asset_id)
        if (this.selectedAssetId === item.asset_id) {
          this.selectedAssetId = ''
          this.assetDetail = null
          this.releasePreview()
        }
      }
      await this.reload()
      this.$message.success('操作已完成')
    },
    resetUpload() {
      this.uploadFiles = []
      this.uploadProjectName = ''
      this.uploadStageName = '规划阶段'
      this.uploadFolderPath = []
      this.uploading = false
      this.uploadProgressText = ''
      if (this.$refs.picker) this.$refs.picker.clear()
    },
    async submitUpload() {
      if (!this.canUpload) return
      this.uploading = true
      try {
        this.ensureReplyFolder(this.uploadProjectName, this.uploadStageName)
        const files = [...this.uploadFiles]
        for (let index = 0; index < files.length; index += 1) {
          const file = files[index]
          this.uploadProgressText = `正在上传 ${index + 1}/${files.length}：${file.name}`
          const body = new FormData()
          body.append('file', file)
          body.append('library_type', 'reply')
          body.append('folder_id', folderId(this.uploadProjectName, this.uploadStageName))
          await uploadLibraryAsset(body)
        }
        this.$message.success(`已上传 ${files.length} 个回函文件`)
        this.uploadOpen = false
        await this.reload()
      } catch (error) {
        this.$message.error(`上传失败：${error.message || '请稍后重试'}`)
      } finally {
        this.uploading = false
        this.uploadProgressText = ''
      }
    }
  }
}
</script>

<style scoped>
.reply-page { display: grid; grid-template-columns: 292px minmax(360px,420px) minmax(560px,1fr); height: calc(100vh - 64px); overflow: hidden; background: #fff; }
.reply-nav,.reply-list-pane { border-right: 1px solid #e1e5e8; }
.reply-nav { min-width: 0; overflow: auto; padding: 20px 14px; background: #f8faf9; }
.reply-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; padding: 0 10px; color: #263f39; font-size: 20px; font-weight: 600; line-height: 1.4; }
.reply-title>span { display: flex; align-items: center; }
.reply-title i { margin-right: 8px; color: #2f7d69; }
.reply-icon-button { width: 32px; height: 32px; border: 0; border-radius: 5px; background: transparent; color: #409EFF; font-size: 18px; cursor: pointer; }
.reply-icon-button:hover { background: #e6f2ee; }
.reply-icon-button i { margin-right: 0; color: inherit; }
.reply-nav-row { position: relative; display: grid; width: 100%; min-height: 48px; grid-template-columns: 22px minmax(0,1fr) auto; gap: 8px; align-items: center; border: 0; border-radius: 5px; padding: 0 12px; background: transparent; color: #56636a; font-size: 14px; font-weight: 400; text-align: left; cursor: pointer; }
.reply-nav-row:hover,.reply-nav-row.active { background: #e6f2ee; color: #27725f; }
.reply-nav-row.custom { grid-template-columns: 18px 22px minmax(0,1fr) auto; }
.reply-nav-row.project-row { grid-template-columns: 18px 22px minmax(0,1fr) auto 28px; }
.reply-nav-row.stage-row { padding-left: 34px; }
.reply-nav-row span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.reply-nav-row em { color: #87929a; font-size: 12px; font-style: normal; }
.folder-toggle-placeholder { display: block; width: 18px; height: 28px; }
.folder-toggle { display: inline-flex; width: 18px; height: 28px; align-items: center; justify-content: center; color: #7f8b92; }
.folder-toggle:hover { color: #2f7d69; }
.library-nav { position: relative; min-width: 0; overflow: auto; padding: 20px 14px 84px; background: #f8faf9; }
.library-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; padding: 0 10px; color: #263f39; font-size: 20px; font-weight: 600; line-height: 1.4; }
.library-title>span { display: flex; align-items: center; }
.library-title i { margin-right: 8px; color: #2f7d69; }
.library-title ::v-deep .el-button { padding: 0; color: #409EFF; font-size: 18px; }
.library-title ::v-deep .el-button i { margin-right: 0; color: inherit; }
.nav-row { position: relative; display: grid; width: 100%; min-height: 48px; grid-template-columns: 22px minmax(0,1fr) auto; gap: 8px; align-items: center; border: 0; border-radius: 5px; padding: 0 12px; background: transparent; color: #56636a; font-size: 14px; font-weight: 400; text-align: left; cursor: pointer; }
.nav-row:hover,.nav-row.active { background: #e6f2ee; color: #27725f; }
.nav-row span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nav-row em { color: #87929a; font-size: 12px; font-style: normal; }
.nav-row.custom { grid-template-columns: 18px 22px minmax(0,1fr) auto 28px; }
.nav-row .folder-more { width: 26px; height: 28px; border: 0; border-radius: 4px; background: transparent; color: #748078; cursor: pointer; opacity: 0; }
.nav-row:hover .folder-more,.nav-row.active .folder-more { opacity: 1; }
.reply-list-pane { display: flex; min-width: 0; min-height: 0; flex-direction: column; overflow: hidden; }
.reply-toolbar { display: grid; flex: none; grid-template-columns: minmax(0,1fr) auto auto; gap: 10px; padding: 20px 18px 14px; }
.reply-caption { display: flex; min-height: 43px; flex: none; align-items: center; justify-content: space-between; padding: 6px 20px; border-bottom: 1px solid #e8ebed; color: #68727b; font-size: 13px; }
.folder-path { display: flex; min-width: 0; align-items: center; gap: 10px; }
.back-button { display: inline-flex; height: 30px; align-items: center; gap: 5px; border: 0; border-radius: 4px; padding: 0 8px; background: #edf4f1; color: #317764; cursor: pointer; }
.reply-list { min-height: 0; flex: 1 1 auto; overflow-x: hidden; overflow-y: auto; }
.reply-row { display: grid; width: 100%; min-height: 92px; grid-template-columns: 42px minmax(0,1fr) auto; gap: 10px; align-items: center; border: 0; border-bottom: 1px solid #edf0f2; padding: 13px 16px; background: #fff; text-align: left; cursor: pointer; }
.reply-row:hover,.reply-row.selected { background: #f0f6f4; }
.reply-file-icon { display: flex; width: 36px; height: 42px; align-items: center; justify-content: center; background: #dff0ea; color: #2f7d69; font-size: 19px; }
.folder-icon { background: #eef3f1; color: #60756f; }
.reply-copy { display: flex; min-width: 0; flex-direction: column; gap: 5px; }
.reply-copy strong,.reply-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.reply-copy strong { font-size: 16px; font-weight: 600; line-height: 1.35; }
.reply-copy small { color: #89929a; font-size: 12px; }
.folder-more { width: 26px; height: 28px; border: 0; border-radius: 4px; background: transparent; color: #748078; cursor: pointer; opacity: 0; }
.reply-nav-row:hover .folder-more,.reply-nav-row.active .folder-more { opacity: 1; }
.row-more { width: 30px; height: 32px; border: 0; border-radius: 4px; background: transparent; color: #7a858d; cursor: pointer; }
.row-more:hover { background: #e4ece9; color: #2f7d69; }
.folder-more { display: inline-flex; align-items: center; justify-content: center; }
.reply-detail-pane { min-width: 0; min-height: 0; overflow: hidden; }
.reply-empty { padding-top: 210px; text-align: center; color: #929aa3; }
.reply-empty i { font-size: 40px; }
.reply-detail-head { display: flex; min-height: 104px; align-items: center; justify-content: space-between; border-bottom: 1px solid #e2e6e9; padding: 18px 28px; }
.reply-detail-head .title { display: flex; min-width: 0; align-items: center; gap: 15px; }
.reply-detail-head .title>span { display: flex; width: 52px; height: 60px; flex: none; align-items: center; justify-content: center; background: #dcefe8; color: #2f7d69; font-size: 26px; }
.reply-detail-head h2 { overflow: hidden; margin: 0 0 7px; font-size: 20px; text-overflow: ellipsis; white-space: nowrap; }
.reply-detail-head p { overflow: hidden; margin: 0; color: #858e96; text-overflow: ellipsis; white-space: nowrap; }
.reply-preview { display: flex; height: calc(100% - 104px); min-height: 0; align-items: center; justify-content: center; overflow: auto; background: #eef1f3; }
.reply-preview iframe { width: 100%; height: 100%; border: 0; background: #fff; }
.preview-message { display: flex; min-height: 420px; flex-direction: column; align-items: center; justify-content: center; color: #8b949c; }
.preview-message i { margin-bottom: 12px; font-size: 40px; }
.upload-form { margin-top: 16px; }
.upload-form ::v-deep .el-autocomplete,.upload-form ::v-deep .el-select { width: 100%; }
.upload-tip { margin-top: 6px; color: #8b949c; font-size: 12px; line-height: 1.5; }
.upload-requirement { margin-top: 10px; color: #8b949c; font-size: 13px; }
.processing-note { margin-top: 12px; color: #317764; font-size: 13px; }
@media (max-width: 1250px) {
  .reply-page { grid-template-columns: 260px 360px minmax(500px,1fr); }
}
</style>
