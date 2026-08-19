<template>
  <div class="knowledge-shell">
      <div class="knowledge-switch">
        <button :class="{active:libraryMode==='regulations'}" @click="libraryMode='regulations'"><i class="el-icon-notebook-2" />技术规程</button>
        <button :class="{active:libraryMode==='cases'}" @click="libraryMode='cases'"><i class="el-icon-folder-opened" />案例文件</button>
      </div>
    <regulation-library v-if="libraryMode==='regulations'" />
    <div v-else class="knowledge-page">
    <aside class="library-nav">
      <div class="library-title">
        <span><i class="el-icon-collection" /> 案例知识库</span>
        <el-button type="text" icon="el-icon-plus" title="新建文件夹" @click="createFolder" />
      </div>
      <button
        :class="['nav-row',{active:filter==='all','drop-target':dragOverFolder==='all'}]"
        @click="chooseFilter('all')"
        @dragover.prevent="dragOverFolder='all'"
        @dragleave="dragOverFolder=''"
        @drop.prevent.stop="dropToFolder('all',$event)"
      >
        <i class="el-icon-collection-tag" /><span>全部案例文件</span><em>{{ cases.length + assets.length }}</em>
      </button>
      <div
        v-for="entry in folderTreeRows"
        :key="entry.folder.folder_id"
        :class="['nav-row custom',{active:filter===entry.folder.folder_id,'drop-target':dragOverFolder===entry.folder.folder_id}]"
        :style="{ paddingLeft: (12 + entry.depth * 18) + 'px' }"
        @click="chooseFilter(entry.folder.folder_id)"
        @dragover.prevent="dragOverFolder=entry.folder.folder_id"
        @dragleave="dragOverFolder=''"
        @drop.prevent.stop="dropToFolder(entry.folder.folder_id,$event)"
      >
        <button
          v-if="entry.hasChildren"
          class="folder-toggle"
          :title="isFolderExpanded(entry.folder.folder_id) ? '收起子文件夹' : '展开子文件夹'"
          @click.stop="toggleFolder(entry.folder.folder_id)"
        >
          <i :class="isFolderExpanded(entry.folder.folder_id) ? 'el-icon-arrow-down' : 'el-icon-arrow-right'" />
        </button>
        <span v-else class="folder-toggle-placeholder" />
        <i class="el-icon-folder-opened" />
        <span :title="entry.folder.name">{{ entry.folder.name }}</span>
        <em>{{ entry.folder.total_count || entry.folder.case_count || 0 }}</em>
        <el-dropdown trigger="click" @command="command => manageFolder(command, entry.folder)">
          <button class="folder-more" title="管理文件夹" @click.stop><i class="el-icon-more" /></button>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item command="rename" icon="el-icon-edit">重命名</el-dropdown-item>
            <el-dropdown-item command="delete" icon="el-icon-delete" divided>删除文件夹</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
      <div class="nav-note">新案例按项目类型自动归类，也可手动移动。删除文件夹不会删除案例原文。</div>
    </aside>

    <main class="case-list-pane">
      <div class="list-toolbar">
        <el-input v-model="keyword" clearable prefix-icon="el-icon-search" placeholder="搜索全部案例文件" />
        <el-tooltip :content="filter === 'all' ? '新建文件夹' : '新建子文件夹'" placement="bottom">
          <el-button class="create-folder-button" icon="el-icon-folder-add" @click="createFolder" />
        </el-tooltip>
        <el-button type="primary" icon="el-icon-upload2" v-hasPermi="['rail:knowledge:import']" @click="assetUploadOpen=true">上传文件</el-button>
      </div>
      <div class="list-caption">
        <div class="folder-path">
          <button v-if="filter!=='all'" class="back-button" title="返回全部案例" @click="returnToRoot">
            <i class="el-icon-back" /> 返回上一级
          </button>
          <el-popover
            v-if="filter!=='all'"
            placement="bottom-start"
            width="280"
            trigger="click"
            popper-class="folder-title-popover"
          >
            <div class="folder-title-full">{{ currentFilterLabel }}</div>
            <button slot="reference" class="folder-title-button" :title="currentFilterLabel">
              <strong>{{ currentFilterLabel }}</strong>
              <i class="el-icon-arrow-down" />
            </button>
          </el-popover>
          <strong v-else class="folder-title-text" :title="currentFilterLabel">{{ currentFilterLabel }}</strong>
        </div>
        <span class="folder-file-count">{{ visibleCases.length + visibleAssets.length }} 个文件</span>
      </div>
      <div v-loading="loading" class="case-list">
        <div
          v-for="folder in visibleFolders"
          :key="'folder-'+folder.folder_id"
          :class="['case-row folder-entry',{'drop-target':dragOverFolder===folder.folder_id}]"
          @click="chooseFilter(folder.folder_id)"
          @dragover.prevent="dragOverFolder=folder.folder_id"
          @dragleave="dragOverFolder=''"
          @drop.prevent.stop="dropToFolder(folder.folder_id,$event)"
        >
          <span class="file-icon folder-icon"><i class="el-icon-folder-opened" /></span>
          <span class="case-copy"><strong>{{ folder.name }}</strong><small>{{ folder.total_count || folder.case_count || 0 }} 个文件</small></span>
          <el-dropdown trigger="click" @command="command => manageFolder(command, folder)">
            <button class="row-more" title="管理文件夹" @click.stop><i class="el-icon-more" /></button>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="rename" icon="el-icon-edit">重命名</el-dropdown-item>
              <el-dropdown-item command="delete" icon="el-icon-delete" divided>删除文件夹</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </div>
        <div
          v-for="item in visibleCases"
          :key="item.case_id"
          :class="['case-row',{selected:selectedId===item.case_id}]"
          draggable="true"
          @dragstart="startDrag('case',item.case_id,item.case_name,$event)"
          @dragend="endDrag"
          @click="selectCase(item)"
        >
          <span class="file-icon"><i class="el-icon-document" /></span>
          <span class="case-copy"><strong>{{ item.case_name }}</strong><small>{{ caseCategory(item) }} · {{ item.original_file_name || '历史案例' }}</small><small>{{ formatDate(item.updated_at) }}</small></span>
          <el-tag size="mini" :type="statusType(item)">{{ statusText(item) }}</el-tag>
        </div>
        <div
          v-for="item in visibleAssets"
          :key="item.asset_id"
          :class="['case-row asset-entry',{selected:selectedAssetId===item.asset_id}]"
          draggable="true"
          @dragstart="startDrag('asset',item.asset_id,item.display_name,$event)"
          @dragend="endDrag"
          @click="selectAsset(item)"
        >
          <span class="file-icon asset-icon"><i :class="assetIcon(item)" /></span>
          <span class="case-copy">
            <strong>{{ item.display_name }}</strong>
            <small>{{ assetLibraryLabel(item) }} · {{ item.original_file_name }} · {{ formatSize(item.file_size) }}</small>
          </span>
          <el-tag v-if="item.library_type === 'reply'" size="mini" type="success">复函</el-tag>
          <el-dropdown trigger="click" @command="command => manageAsset(command, item)">
            <button class="row-more" title="管理资料" @click.stop><i class="el-icon-more" /></button>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="rename" icon="el-icon-edit">重命名</el-dropdown-item>
              <el-dropdown-item command="move" icon="el-icon-folder-opened">移动到文件夹</el-dropdown-item>
              <el-dropdown-item command="download" icon="el-icon-download">下载</el-dropdown-item>
              <el-dropdown-item command="delete" icon="el-icon-delete" divided>删除文件</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </div>
        <div v-if="!loading&&!visibleFolders.length&&!visibleCases.length&&!visibleAssets.length" class="empty-list"><i class="el-icon-folder-opened" /><p>当前文件夹暂无文件</p></div>
      </div>
    </main>

    <section class="case-detail-pane">
      <div v-if="!detail&&!assetDetail" class="empty-detail"><i class="el-icon-chat-dot-square" /><p>选择文件查看详情</p></div>
      <template v-else-if="assetDetail">
        <header class="detail-head asset-head">
          <div><span class="detail-icon"><i :class="assetIcon(assetDetail)" /></span><div><h2>{{ assetDetail.display_name }}</h2><p>{{ assetLibraryLabel(assetDetail) }} · {{ assetDetail.original_file_name }} · {{ formatSize(assetDetail.file_size) }}</p></div></div>
          <div class="commands"><el-button icon="el-icon-download" circle title="下载文件" @click="downloadAsset(assetDetail)" /></div>
        </header>
        <div class="asset-preview">
          <iframe v-if="previewUrl&&assetDetail.file_kind==='pdf'" :src="`${previewUrl}#toolbar=1&navpanes=0&view=FitH`" :title="assetDetail.display_name" />
          <img v-else-if="previewUrl&&assetDetail.file_kind==='image'" :src="previewUrl" :alt="assetDetail.display_name">
          <div v-else class="preview-message"><i :class="assetIcon(assetDetail)" /><p>该格式已保存在知识库中，请下载后使用对应软件查看。</p><el-button type="primary" plain icon="el-icon-download" @click="downloadAsset(assetDetail)">下载文件</el-button></div>
        </div>
      </template>
      <template v-else>
        <header class="detail-head">
          <div><span class="detail-icon"><i class="el-icon-document-checked" /></span><div><h2>{{ detail.case_name }}</h2><p>{{ detail.original_file_name }}</p></div></div>
          <div class="commands">
            <el-tooltip content="下载原文件"><el-button icon="el-icon-download" circle @click="downloadSource" /></el-tooltip>
            <el-dropdown v-hasPermi="['rail:knowledge:remove']" @command="manage">
              <el-button icon="el-icon-more" circle />
              <el-dropdown-menu slot="dropdown">
                 <el-dropdown-item command="rename" icon="el-icon-edit">重命名</el-dropdown-item>
                 <el-dropdown-item command="move" icon="el-icon-folder-opened">移动到文件夹</el-dropdown-item>
                 <el-dropdown-item v-if="detail.active" command="disable" icon="el-icon-circle-close">停用并退出匹配</el-dropdown-item>
                 <el-dropdown-item v-else command="restore" icon="el-icon-refresh-left">恢复参与匹配</el-dropdown-item>
                 <el-dropdown-item command="delete" divided icon="el-icon-delete">彻底删除</el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
          </div>
        </header>
        <el-tabs v-model="detailTab" class="detail-tabs" @tab-click="tabChanged">
          <el-tab-pane label="案例属性" name="features">
            <div class="feature-grid"><div v-for="(value,key) in detail.features" :key="key"><span>{{ key }}</span><strong>{{ displayValue(value) }}</strong></div></div>
          </el-tab-pane>
          <el-tab-pane :label="`评审建议 (${detail.advice_count || 0})`" name="advices">
            <div v-if="detail.advices&&detail.advices.length" class="advice-list"><div v-for="(item,index) in detail.advices" :key="index" class="advice-row"><span>{{ index+1 }}</span><p>{{ item.text || item.opinion || item }}</p></div></div>
            <el-empty v-else description="未可靠识别到评审建议" :image-size="70" />
          </el-tab-pane>
          <el-tab-pane label="原文件" name="content">
            <div v-loading="contentLoading" class="case-document-viewer">
              <iframe v-if="previewUrl" :src="previewUrl" title="案例原文件 PDF 预览" />
              <pre v-else-if="content" class="document-content">{{ content }}</pre>
              <div v-else-if="previewError" class="preview-message">
                <i class="el-icon-warning-outline" />
                <p>{{ previewError }}</p>
                <el-button type="primary" plain icon="el-icon-download" @click="downloadSource">下载原文件</el-button>
              </div>
              <div v-else class="preview-message"><i class="el-icon-document" /><p>切换到本页后读取原文件</p></div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </template>
    </section>

    <library-asset-dialog v-model="assetUploadOpen" library-type="case" :folders="folderOptions" :default-folder-id="filter==='all'?'':filter" @uploaded="reload" />

    <el-dialog title="移动案例" :visible.sync="moveOpen" width="430px" append-to-body>
      <el-form label-position="top"><el-form-item label="目标文件夹">
        <el-select v-model="moveFolderId" clearable placeholder="不归入文件夹" style="width:100%">
          <el-option label="不归入文件夹" value="" />
          <el-option v-for="folder in folderOptions" :key="folder.folder_id" :label="folder.path" :value="folder.folder_id" />
        </el-select>
      </el-form-item></el-form>
      <div slot="footer"><el-button @click="moveOpen=false">取消</el-button><el-button type="primary" @click="confirmMove">确定移动</el-button></div>
    </el-dialog>
    </div>
  </div>
</template>

<script>
import { saveAs } from 'file-saver'
import RegulationLibrary from './RegulationLibrary.vue'
import LibraryAssetDialog from './LibraryAssetDialog.vue'
import {
  listKnowledge, getKnowledge, getKnowledgeContent,
  disableKnowledge, restoreKnowledge, deleteKnowledge, downloadKnowledgeFile,
  listCaseFolders, createCaseFolder, renameCaseFolder, deleteCaseFolder,
  moveCaseToFolder, renameKnowledgeCase, listLibraryAssets, renameLibraryAsset,
  moveLibraryAsset, deleteLibraryAsset, downloadLibraryAsset
} from '@/api/rail/audit'

export default {
  name: 'RailKnowledge', components: { RegulationLibrary, LibraryAssetDialog },
  data() {
    return {
      libraryMode: 'regulations', loading: false, keyword: '', filter: 'all', cases: [], assets: [], folders: [], selectedId: '', selectedAssetId: '', detail: null, assetDetail: null, detailTab: 'features', content: '', contentLoading: false, previewUrl: '', previewError: '',
      moveOpen: false, moveFolderId: '', assetUploadOpen: false, dragging: null, dragOverFolder: '',
      expandedFolderIds: [], folderTreeInitialized: false
    }
  },
  computed: {
    currentFilterLabel() {
      if (this.filter === 'all') return '全部案例文件'
      const folder = this.folders.find(item => item.folder_id === this.filter)
      return folder ? folder.name : '案例知识库'
    },
    visibleCases() {
      const token = this.keyword.trim().toLowerCase()
      return this.cases.filter(item => {
        const matches = !token || [
          item.case_name,
          item.original_file_name,
          item.category,
          item.folder_name,
          item.features && item.features.category,
          item.features && item.features.project_type,
          item.features && item.features.work_types
        ].filter(Boolean).join(' ').toLowerCase().includes(token)
        if (token) return matches
        return this.filter === 'all' ? !item.folder_id : item.folder_id === this.filter
      })
    },
    visibleFolders() {
      const token = this.keyword.trim().toLowerCase()
      if (token) return []
      const parentId = this.filter === 'all' ? null : this.filter
      return this.folders.filter(item => (item.parent_id || null) === parentId)
    },
    rootFolders() {
      return this.folders.filter(item => !item.parent_id)
    },
    folderTreeRows() {
      const rows = []
      const appendChildren = (parentId, depth) => {
        this.folders
          .filter(item => (item.parent_id || null) === parentId)
          .forEach(folder => {
            const hasChildren = this.folders.some(item => item.parent_id === folder.folder_id)
            rows.push({ folder, depth, hasChildren })
            if (hasChildren && this.isFolderExpanded(folder.folder_id)) {
              appendChildren(folder.folder_id, depth + 1)
            }
          })
      }
      appendChildren(null, 0)
      return rows
    },
    folderOptions() {
      return this.folders.map(item => ({ ...item, path: this.folderPath(item) }))
    },
    visibleAssets() {
      const token = this.keyword.trim().toLowerCase()
      return this.assets.filter(item => {
        const matches = !token || [
          item.display_name,
          item.original_file_name,
          item.folder_name
        ].filter(Boolean).join(' ').toLowerCase().includes(token)
        if (token) return matches
        const displayFolderId = this.assetDisplayFolderId(item)
        const inFolder = this.filter === 'all'
          ? !displayFolderId
          : displayFolderId === this.filter
        return inFolder
      })
    }
  },
  created() { this.reload() },
  beforeDestroy() { this.releasePreview() },
  methods: {
    async reload() {
      this.loading = true
      try {
        const [cases, folders, assets] = await Promise.all([
          listKnowledge({ includeInactive: true }),
          listCaseFolders(),
          listLibraryAssets({ library_type: 'case' })
        ])
        this.cases = cases
        this.folders = folders
        this.assets = assets
        const parentIds = folders
          .filter(folder => folders.some(child => child.parent_id === folder.folder_id))
          .map(folder => folder.folder_id)
        if (!this.folderTreeInitialized) {
          this.expandedFolderIds = []
          this.folderTreeInitialized = true
        } else {
          this.expandedFolderIds = this.expandedFolderIds.filter(folderId => parentIds.includes(folderId))
        }
        if (this.filter !== 'all' && !folders.some(item => item.folder_id === this.filter)) this.filter = 'all'
      } finally { this.loading = false }
    },
    async loadList() { await this.reload() },
    hasFolderChildren(folderId) {
      return this.folders.some(item => item.parent_id === folderId)
    },
    isFolderExpanded(folderId) {
      return this.expandedFolderIds.includes(folderId)
    },
    toggleFolder(folderId) {
      if (!this.hasFolderChildren(folderId)) return
      const index = this.expandedFolderIds.indexOf(folderId)
      if (index >= 0) this.expandedFolderIds.splice(index, 1)
      else this.expandedFolderIds.push(folderId)
    },
    chooseFilter(key) {
      this.releasePreview()
      this.filter = key
      this.selectedId = ''
      this.selectedAssetId = ''
      this.detail = null
      this.assetDetail = null
    },
    returnToRoot() {
      const current = this.folders.find(item => item.folder_id === this.filter)
      this.chooseFilter(current && current.parent_id ? current.parent_id : 'all')
    },
    startDrag(type, id, name, event) {
      this.dragging = { type, id, name }
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('application/json', JSON.stringify(this.dragging))
      event.dataTransfer.setData('text/plain', name || '')
    },
    endDrag() {
      this.dragging = null
      this.dragOverFolder = ''
    },
    async dropToFolder(target, event) {
      this.dragOverFolder = ''
      let payload = this.dragging
      if (!payload) {
        try { payload = JSON.parse(event.dataTransfer.getData('application/json')) } catch (error) { return }
      }
      if (!payload || !['case', 'asset'].includes(payload.type)) return
      const folderId = target === 'all' ? '' : target
      if (payload.type === 'case') {
        await moveCaseToFolder(payload.id, folderId)
      } else {
        await moveLibraryAsset(payload.id, folderId)
      }
      this.endDrag()
      await this.reload()
      const folder = this.folders.find(item => item.folder_id === folderId)
      this.$message.success(folder ? `已移动到“${folder.name}”` : '已移出文件夹')
    },
    caseCategory(item) {
      return (item && (item.folder_name || item.category || (item.features && item.features.category))) || '未归入文件夹'
    },
    folderPath(folder) {
      const names = []
      const visited = new Set()
      let current = folder
      while (current && !visited.has(current.folder_id)) {
        visited.add(current.folder_id)
        names.unshift(current.name)
        current = current.parent_id
          ? this.folders.find(item => item.folder_id === current.parent_id)
          : null
      }
      return names.join(' / ')
    },
    async createFolder() {
      const parentId = this.filter === 'all' ? null : this.filter
      const parent = parentId ? this.folders.find(item => item.folder_id === parentId) : null
      const title = parent ? `在“${parent.name}”中新建子文件夹` : '新建文件夹'
      const { value } = await this.$prompt('请输入案例文件夹名称', title, {
        confirmButtonText: '创建', cancelButtonText: '取消', inputPattern: /\S+/, inputErrorMessage: '文件夹名称不能为空'
      })
      await createCaseFolder(value.trim(), parentId)
      await this.reload()
      this.$message.success(parent
        ? `已在“${parent.name}”中创建子文件夹“${value.trim()}”`
        : `已创建文件夹“${value.trim()}”`)
    },
    async manageFolder(command, folder) {
      if (command === 'rename') {
        const { value } = await this.$prompt('请输入新的文件夹名称', '重命名文件夹', {
          inputValue: folder.name, confirmButtonText: '保存', cancelButtonText: '取消',
          inputPattern: /\S+/, inputErrorMessage: '文件夹名称不能为空'
        })
        await renameCaseFolder(folder.folder_id, value.trim())
        await this.reload()
        this.$message.success('文件夹已重命名')
        return
      }
      await this.$confirm(
        `删除“${folder.name}”后，其中的文件和下级文件夹将移到上一级，案例原文不会被删除。`,
        '删除文件夹', { type: 'warning', confirmButtonText: '删除文件夹', cancelButtonText: '取消' }
      )
      const parentId = folder.parent_id || 'all'
      await deleteCaseFolder(folder.folder_id)
      if (this.filter === folder.folder_id) this.filter = parentId
      await this.reload()
      this.$message.success('文件夹已删除，原有内容已移到上一级')
    },
    async selectCase(item) {
      this.releasePreview()
      this.selectedAssetId = ''
      this.assetDetail = null
      this.selectedId = item.case_id
      this.detail = await getKnowledge(item.case_id)
      this.detailTab = 'features'
      this.content = ''
      this.previewError = ''
    },
    async selectAsset(item) {
      this.releasePreview()
      this.selectedId = ''
      this.detail = null
      this.selectedAssetId = item.asset_id
      this.assetDetail = item
      if (!['pdf', 'image'].includes(item.file_kind)) return
      const source = await downloadLibraryAsset(item.asset_id)
      this.previewUrl = URL.createObjectURL(new Blob([source], { type: item.media_type }))
    },
    async manageCase(command, item) {
      if (command !== 'rename') return
      const { value } = await this.$prompt('请输入新的案例名称', '重命名案例', {
        inputValue: item.case_name,
        inputPattern: /\S+/,
        inputErrorMessage: '名称不能为空'
      })
      await renameKnowledgeCase(item.case_id, value.trim())
      this.$message.success('案例已重命名')
      await this.reload()
      if (this.selectedId === item.case_id) {
        const renamed = this.cases.find(row => row.case_id === item.case_id)
        if (renamed) await this.selectCase(renamed)
      }
    },
    assetIcon(item) {
      if (item.file_kind === 'cad' || item.file_kind === 'bim') return 'el-icon-copy-document'
      if (item.file_kind === 'image') return 'el-icon-picture-outline'
      if (item.file_kind === 'archive') return 'el-icon-box'
      return 'el-icon-document'
    },
    assetLibraryLabel(item) {
      return item && item.library_type === 'reply' ? '复函' : '资料'
    },
    assetDisplayFolderId(item) {
      const folderId = String(item && item.folder_id || '')
      return folderId.startsWith('reply:') || folderId.startsWith('reply-project:') ? '' : folderId
    },
    formatSize(value) {
      if (value < 1024) return `${value} B`
      if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
      return `${(value / 1024 / 1024).toFixed(1)} MB`
    },
    async downloadAsset(item) { saveAs(await downloadLibraryAsset(item.asset_id), item.original_file_name) },
    async manageAsset(command, item) {
      if (command === 'download') return this.downloadAsset(item)
      if (command === 'rename') {
        const { value } = await this.$prompt('请输入新的资料名称', '重命名文件', { inputValue: item.display_name, inputPattern: /\S+/, inputErrorMessage: '名称不能为空' })
        await renameLibraryAsset(item.asset_id, value.trim())
      } else if (command === 'move') {
        const { value } = await this.$prompt(`输入目标文件夹名称：${this.folders.map(folder => folder.name).join('、')}`, '移动资料', { inputValue: '' })
        const folder = this.folders.find(entry => entry.name === value.trim())
        if (!folder) {
          this.$message.error('未找到该文件夹')
          return
        }
        await moveLibraryAsset(item.asset_id, folder.folder_id)
      } else {
        await this.$confirm(`确定删除资料“${item.display_name}”吗？此操作会删除文件且无法恢复。`, '删除资料', { type: 'warning' })
        await deleteLibraryAsset(item.asset_id)
      }
      this.assetDetail = null
      this.selectedAssetId = ''
      this.releasePreview()
      await this.reload()
    },
    statusText(item) { if (!item.active) return '已停用'; return item.status === 'ready' ? '可匹配' : '待复核' },
    statusType(item) { if (!item.active) return 'info'; return item.status === 'ready' ? 'success' : 'warning' },
    formatDate(value) { return value ? value.replace('T', ' ').slice(0, 16) : '' },
    displayValue(value) { if (value == null || value === '') return '-'; if (Array.isArray(value)) return value.join('、') || '-'; if (typeof value === 'object') return JSON.stringify(value, null, 2); return String(value) },
    async tabChanged(tab) {
      if (tab.name !== 'content' || this.previewUrl || this.content || this.contentLoading) return
      this.contentLoading = true
      this.previewError = ''
      try {
        const fileName = (this.detail && this.detail.original_file_name) || ''
        if (/\.pdf$/i.test(fileName)) {
          const source = await downloadKnowledgeFile(this.selectedId)
          const blob = source instanceof Blob ? source : new Blob([source], { type: 'application/pdf' })
          this.previewUrl = `${URL.createObjectURL(blob)}#toolbar=1&navpanes=0&view=FitH`
        } else {
          const value = await getKnowledgeContent(this.selectedId)
          this.content = value.content
        }
      } catch (error) {
        this.previewError = '原文件暂时无法在线预览，请下载后查看。'
      } finally {
        this.contentLoading = false
      }
    },
    releasePreview() {
      if (this.previewUrl) URL.revokeObjectURL(this.previewUrl.split('#')[0])
      this.previewUrl = ''
      this.previewError = ''
    },
    async manage(command) {
      if (command === 'rename') {
        await this.manageCase(command, this.detail)
        return
      }
      if (command === 'move') {
        this.moveFolderId = this.detail.folder_id || ''
        this.moveOpen = true
        return
      }
      if (command === 'delete') {
        await this.$confirm(
          `将永久删除“${this.detail.case_name}”的原文件、解析正文、属性和评审建议，且无法恢复。历史审核报告仍会保留。`,
          '确认彻底删除',
          { type: 'warning', confirmButtonText: '彻底删除', cancelButtonText: '取消' }
        )
        await deleteKnowledge(this.selectedId)
        this.$message.success('案例已彻底删除')
        this.selectedId = ''
        this.detail = null
        this.content = ''
        this.releasePreview()
        await this.reload()
        return
      }
      if (command === 'disable') {
        await this.$confirm('停用后该案例不再参与审核意见匹配，原文件仍保留并可恢复。', '确认停用')
        await disableKnowledge(this.selectedId)
      } else {
        await restoreKnowledge(this.selectedId)
      }
      this.$message.success(command === 'disable' ? '案例已停用' : '案例已恢复')
      await this.reload()
      this.detail = await getKnowledge(this.selectedId)
    },
    async confirmMove() {
      await moveCaseToFolder(this.selectedId, this.moveFolderId)
      this.moveOpen = false
      await this.reload()
      this.detail = await getKnowledge(this.selectedId)
      this.$message.success('案例已移动')
    },
    async downloadSource() { saveAs(await downloadKnowledgeFile(this.selectedId), this.detail.original_file_name || `${this.detail.case_name}.pdf`) }
  }
}
</script>

<style scoped>
.knowledge-shell { height: 100vh; overflow: hidden; background: #fff; }.knowledge-switch { display: flex; height: 64px; align-items: center; gap: 8px; border-bottom: 1px solid #e1e5e8; padding: 0 24px; }.knowledge-switch button { display: flex; height: 36px; align-items: center; gap: 7px; border: 1px solid #dfe4e2; border-radius: 4px; padding: 0 16px; background: #fff; color: #54605d; cursor: pointer; }.knowledge-switch button.active { border-color: #31806c; background: #e6f1ed; color: #276b59; }
.knowledge-page { display: grid; grid-template-columns: 292px minmax(360px,420px) minmax(560px,1fr); height: calc(100vh - 64px); overflow: hidden; background: #fff; }
.library-nav,.case-list-pane { border-right: 1px solid #e1e5e8; }
.library-nav { position: relative; min-width: 0; overflow: auto; padding: 20px 14px 84px; background: #f8faf9; }
.library-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; padding: 0 10px; color: #263f39; font-size: 20px; font-weight: 600; }
.library-title>span { display: flex; align-items: center; }
.library-title i { margin-right: 8px; color: #2f7d69; }
.nav-row { position: relative; display: grid; width: 100%; min-height: 48px; grid-template-columns: 22px minmax(0,1fr) auto; gap: 8px; align-items: center; border: 0; border-radius: 5px; padding: 0 12px; background: transparent; color: #56636a; text-align: left; cursor: pointer; }
.nav-row:hover,.nav-row.active { background: #e6f2ee; color: #27725f; }
.nav-row.drop-target,.case-row.folder-entry.drop-target { outline: 2px solid #3b927a; outline-offset: -2px; background: #dcefe8; color: #236a57; }
.nav-row span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.nav-row em { color: #87929a; font-size: 12px; font-style: normal; }
.nav-row.custom { grid-template-columns: 18px 22px minmax(0,1fr) auto 28px; }
.folder-toggle,.folder-toggle-placeholder { width: 18px; height: 28px; }
.folder-toggle { display: inline-flex; align-items: center; justify-content: center; border: 0; border-radius: 3px; padding: 0; background: transparent; color: #6f7c79; cursor: pointer; }
.folder-toggle:hover { background: #d7e8e2; color: #27725f; }
.folder-toggle-placeholder { display: block; }
.folder-more { width: 26px; height: 28px; border: 0; border-radius: 4px; background: transparent; color: #748078; cursor: pointer; opacity: 0; }
.nav-row:hover .folder-more,.nav-row.active .folder-more { opacity: 1; }
.nav-note { position: absolute; right: 20px; bottom: 20px; left: 20px; margin: 0; color: #97a09f; font-size: 12px; line-height: 1.6; }
.case-list-pane { display: flex; min-width: 0; min-height: 0; flex-direction: column; overflow: hidden; }.list-toolbar { display: grid; flex: none; grid-template-columns: minmax(0,1fr) 40px auto; gap: 10px; padding: 20px 18px 14px; }.create-folder-button { width: 40px; padding-right: 0; padding-left: 0; }.list-caption { display: flex; min-height: 43px; flex: none; align-items: center; justify-content: space-between; padding: 6px 20px; border-bottom: 1px solid #e8ebed; color: #68727b; font-size: 13px; }.folder-path { display: flex; min-width: 0; align-items: center; gap: 10px; }.back-button { display: inline-flex; height: 30px; align-items: center; gap: 5px; border: 0; border-radius: 4px; padding: 0 8px; background: #edf4f1; color: #317764; cursor: pointer; }.back-button:hover { background: #dcece6; }.case-list { min-height: 0; flex: 1 1 auto; overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; scrollbar-gutter: stable; }.case-row { display: grid; width: 100%; min-height: 92px; grid-template-columns: 42px minmax(0,1fr) auto; gap: 10px; align-items: center; border: 0; border-bottom: 1px solid #edf0f2; padding: 13px 16px; background: #fff; text-align: left; cursor: pointer; }.case-row:hover,.case-row.selected { background: #f0f6f4; }.case-row[draggable="true"] { user-select: none; }.case-row[draggable="true"]:active { cursor: grabbing; }.folder-entry,.asset-entry { cursor: pointer; }.file-icon { display: flex; width: 36px; height: 42px; align-items: center; justify-content: center; background: #dff0ea; color: #2f7d69; font-size: 19px; }.folder-icon { background: #eef3f1; color: #60756f; }.asset-icon { background: #edf4f2; color: #437b6d; }.row-more { width: 30px; height: 32px; border: 0; border-radius: 4px; background: transparent; color: #7a858d; cursor: pointer; }.row-more:hover { background: #e4ece9; color: #2f7d69; }.case-copy { display: flex; min-width: 0; flex-direction: column; gap: 5px; }.case-copy strong,.case-copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.case-copy small { color: #89929a; font-size: 12px; }.empty-list,.empty-detail { padding-top: 130px; text-align: center; color: #929aa3; }.empty-list i,.empty-detail i { font-size: 40px; }
.case-detail-pane { min-width: 0; min-height: 0; overflow: hidden; }.detail-head { display: flex; min-height: 104px; align-items: center; justify-content: space-between; border-bottom: 1px solid #e2e6e9; padding: 18px 28px; }.detail-head>div:first-child { display: flex; min-width: 0; align-items: center; gap: 15px; }.detail-icon { display: flex; width: 52px; height: 60px; flex: none; align-items: center; justify-content: center; background: #dcefe8; color: #2f7d69; font-size: 26px; }.detail-head h2 { overflow: hidden; margin: 0 0 7px; font-size: 20px; text-overflow: ellipsis; white-space: nowrap; letter-spacing: 0; }.detail-head p { overflow: hidden; margin: 0; color: #858e96; text-overflow: ellipsis; white-space: nowrap; }.commands { display: flex; gap: 8px; }.detail-tabs { height: calc(100% - 104px); padding: 0 28px; }.detail-tabs ::v-deep .el-tabs__content { height: calc(100% - 55px); overflow: auto; }.feature-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 0 28px; }.feature-grid>div { display: grid; grid-template-columns: minmax(130px, 42%) 1fr; gap: 12px; border-bottom: 1px solid #edf0f2; padding: 13px 0; }.feature-grid span { overflow-wrap: anywhere; color: #78818a; }.feature-grid strong { overflow-wrap: anywhere; font-weight: 500; white-space: pre-wrap; }.advice-row { display: grid; grid-template-columns: 28px 1fr; gap: 10px; border-bottom: 1px solid #edf0f2; padding: 15px 0; }.advice-row>span { display: flex; width: 24px; height: 24px; align-items: center; justify-content: center; background: #e5f1ed; color: #2f7d69; }.advice-row p { margin: 0; line-height: 1.75; }.case-document-viewer { height: 100%; min-height: 520px; overflow: hidden; background: #f5f6f7; }.case-document-viewer iframe { width: 100%; height: 100%; min-height: 620px; border: 0; background: #fff; }.asset-preview { display: flex; height: calc(100% - 104px); min-height: 0; align-items: center; justify-content: center; overflow: auto; background: #eef1f3; }.asset-preview iframe { width: 100%; height: 100%; border: 0; background: #fff; }.asset-preview img { display: block; max-width: 96%; max-height: 96%; object-fit: contain; }.asset-preview .preview-message { width: 100%; }.document-content { min-height: 100%; margin: 0; padding: 18px; background: #f7f8f9; color: #3f4850; font-family: inherit; line-height: 1.8; white-space: pre-wrap; word-break: break-word; }.preview-message { display: flex; min-height: 420px; flex-direction: column; align-items: center; justify-content: center; color: #8b949c; }.preview-message i { margin-bottom: 12px; font-size: 40px; }.upload-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; margin-top: 16px; }.upload-fields .el-form-item:last-child { grid-column: 1 / -1; }.upload-fields ::v-deep .el-select { width: 100%; }
.list-caption { gap: 12px; }
.folder-path { flex: 1 1 auto; overflow: hidden; }
.back-button { flex: 0 0 auto; white-space: nowrap; }
.folder-title-button { display: inline-flex; min-width: 0; max-width: 100%; flex: 1 1 auto; align-items: center; gap: 4px; border: 0; padding: 0; background: transparent; color: inherit; cursor: pointer; text-align: left; }
.folder-title-button strong,.folder-title-text { display: block; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.folder-title-button i,.folder-file-count { flex: 0 0 auto; }
.folder-file-count { white-space: nowrap; }
.folder-title-full { color: #263f39; line-height: 1.6; word-break: break-word; }
@media (max-width: 1250px) {
  .knowledge-page { grid-template-columns: 260px 360px minmax(500px,1fr); }
  .feature-grid { grid-template-columns: 1fr; }
}
</style>
