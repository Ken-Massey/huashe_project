<template>
  <div class="regulation-page">
    <aside class="folder-pane">
      <div class="folder-title">
        <span><i class="el-icon-notebook-2" /> 技术规程库</span>
        <el-button type="text" icon="el-icon-plus" title="新建文件夹" @click="createFolder" />
      </div>
      <button
        :class="['folder-row', { active: selectedFolder === 'all', 'drop-target': dragOverFolder === 'all' }]"
        @click="selectFolder('all')"
        @dragover.prevent="dragOverFolder='all'"
        @dragleave="dragOverFolder=''"
        @drop.prevent.stop="dropToFolder('all', $event)"
      >
        <i class="el-icon-collection-tag" /><span>全部规程</span><em>{{ allRegulations.length }}</em>
      </button>
      <div
        v-for="entry in folderTreeRows"
        :key="entry.folder.folder_id"
        :class="['folder-row custom', { active: selectedFolder === entry.folder.folder_id, 'drop-target': dragOverFolder === entry.folder.folder_id }]"
        :style="{ paddingLeft: (12 + entry.depth * 18) + 'px' }"
        @click="selectFolder(entry.folder.folder_id)"
        @dragover.prevent="dragOverFolder=entry.folder.folder_id"
        @dragleave="dragOverFolder=''"
        @drop.prevent.stop="dropToFolder(entry.folder.folder_id, $event)"
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
        <em>{{ entry.folder.total_count || entry.folder.regulation_count || 0 }}</em>
        <el-dropdown trigger="click" @command="command => manageFolder(command, entry.folder)">
          <button class="folder-more" title="管理文件夹" @click.stop><i class="el-icon-more" /></button>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item command="rename" icon="el-icon-edit">重命名</el-dropdown-item>
            <el-dropdown-item command="delete" icon="el-icon-delete" divided>删除文件夹</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
      <p class="folder-tip">新规程将自动归类，也可手动移动。删除分类不会删除规程原文。</p>
    </aside>

    <section class="reg-list-pane">
      <div class="toolbar">
        <el-input v-model="keyword" clearable prefix-icon="el-icon-search" placeholder="搜索全部技术规程" />
        <el-tooltip :content="selectedFolder === 'all' ? '新建文件夹' : '新建子文件夹'" placement="bottom">
          <el-button class="create-folder-button" icon="el-icon-folder-add" @click="createFolder" />
        </el-tooltip>
        <el-button type="primary" icon="el-icon-upload2" @click="assetUploadOpen=true">上传文件</el-button>
      </div>
      <div class="caption">
        <div class="folder-path">
          <button v-if="selectedFolder!=='all'" class="back-button" title="返回全部技术规程" @click="returnToRoot">
            <i class="el-icon-back" /> 返回上一级
          </button>
          <strong>{{ currentFolderName }}</strong>
        </div>
        <span>{{ visibleRegulations.length + visibleAssets.length }} 个文件</span>
      </div>
      <div v-loading="loading" class="reg-list">
        <div
          v-for="folder in visibleFolders"
          :key="'folder-'+folder.folder_id"
          :class="['reg-row folder-entry', { 'drop-target': dragOverFolder === folder.folder_id }]"
          @click="selectFolder(folder.folder_id)"
          @dragover.prevent="dragOverFolder=folder.folder_id"
          @dragleave="dragOverFolder=''"
          @drop.prevent.stop="dropToFolder(folder.folder_id, $event)"
        >
          <span class="doc-icon folder-icon"><i class="el-icon-folder-opened" /></span>
          <span class="copy"><strong>{{ folder.name }}</strong><small>{{ folder.total_count || folder.regulation_count || 0 }} 个文件</small></span>
          <el-dropdown trigger="click" @command="command => manageFolder(command, folder)">
            <button class="row-more" title="管理文件夹" @click.stop><i class="el-icon-more" /></button>
            <el-dropdown-menu slot="dropdown">
              <el-dropdown-item command="rename" icon="el-icon-edit">重命名</el-dropdown-item>
              <el-dropdown-item command="delete" icon="el-icon-delete" divided>删除文件夹</el-dropdown-item>
            </el-dropdown-menu>
          </el-dropdown>
        </div>
        <div
          v-for="item in visibleRegulations"
          :key="item.regulation_id"
          :class="['reg-row',{selected:selectedId===item.regulation_id}]"
          draggable="true"
          @dragstart="startDrag('regulation', item.regulation_id, item.title, $event)"
          @dragend="endDrag"
          @click="select(item)"
        >
          <span class="doc-icon"><i class="el-icon-document" /></span>
          <span class="copy"><strong>{{ item.title }}</strong><small>{{ item.version || item.original_file_name }}</small></span>
          <el-tag size="mini" :type="item.active ? 'success' : 'info'">{{ item.active ? '启用' : '停用' }}</el-tag>
        </div>
        <div
          v-for="item in visibleAssets"
          :key="item.asset_id"
          :class="['reg-row asset-entry',{selected:selectedAssetId===item.asset_id}]"
          draggable="true"
          @dragstart="startDrag('asset', item.asset_id, item.display_name, $event)"
          @dragend="endDrag"
          @click="selectAsset(item)"
        >
          <span class="doc-icon asset-icon"><i :class="assetIcon(item)" /></span>
          <span class="copy"><strong>{{ item.display_name }}</strong><small>{{ item.original_file_name }} · {{ formatSize(item.file_size) }}</small></span>
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
        <el-empty v-if="!loading&&!visibleFolders.length&&!visibleRegulations.length&&!visibleAssets.length" description="该文件夹暂无文件" :image-size="78" />
      </div>
    </section>

    <section class="detail-pane">
      <div v-if="!detail&&!assetDetail" class="empty"><i class="el-icon-notebook-2" /><p>选择文件查看详情</p></div>
      <template v-else-if="assetDetail">
        <header class="detail-head">
          <div class="title"><span><i :class="assetIcon(assetDetail)" /></span><div><h2>{{ assetDetail.display_name }}</h2><p>{{ assetDetail.original_file_name }} · {{ formatSize(assetDetail.file_size) }}</p></div></div>
          <div class="actions"><el-button icon="el-icon-download" circle title="下载文件" @click="downloadAsset(assetDetail)" /></div>
        </header>
        <div class="asset-preview">
          <iframe v-if="previewUrl&&assetDetail.file_kind==='pdf'" :src="`${previewUrl}#toolbar=1&navpanes=0&view=FitH`" :title="assetDetail.display_name" />
          <img v-else-if="previewUrl&&assetDetail.file_kind==='image'" :src="previewUrl" :alt="assetDetail.display_name">
          <div v-else class="preview-error"><i :class="assetIcon(assetDetail)" /><p>该格式已安全保存在知识库中，请下载后使用对应软件查看。</p><el-button type="primary" plain icon="el-icon-download" @click="downloadAsset(assetDetail)">下载文件</el-button></div>
        </div>
      </template>
      <template v-else>
        <header class="detail-head">
          <div class="title"><span><i class="el-icon-document-checked" /></span><div><h2>{{ detail.title }}</h2><p>{{ detail.original_file_name }}<em v-if="detail.version"> · {{ detail.version }}</em><b>{{ detail.folder_name || '未归入文件夹' }}</b></p></div></div>
          <div class="actions">
            <el-button icon="el-icon-download" circle title="下载原文件" @click="downloadSource" />
            <el-dropdown @command="manage">
              <el-button icon="el-icon-more" circle />
              <el-dropdown-menu slot="dropdown">
                <el-dropdown-item command="rename" icon="el-icon-edit">重命名</el-dropdown-item>
                <el-dropdown-item command="move" icon="el-icon-folder-opened">移动到文件夹</el-dropdown-item>
                <el-dropdown-item :command="detail.active?'disable':'restore'">{{ detail.active ? '停用规程' : '恢复规程' }}</el-dropdown-item>
                <el-dropdown-item command="delete" divided icon="el-icon-delete">彻底删除</el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
          </div>
        </header>
        <div v-loading="contentLoading" class="document-viewer">
          <iframe v-if="previewUrl" :src="`${previewUrl}#toolbar=1&navpanes=0&view=FitH`" :title="detail.title" />
          <pre v-else-if="content" class="content">{{ content }}</pre>
          <div v-else-if="previewError" class="preview-error"><i class="el-icon-warning-outline" /><p>{{ previewError }}</p><el-button @click="downloadSource">下载原文件阅读</el-button></div>
          <div v-else class="preview-loading">正在读取原文件...</div>
        </div>
      </template>
    </section>

    <library-asset-dialog v-model="assetUploadOpen" library-type="regulation" :folders="folderOptions" :default-folder-id="selectedFolder==='all'?'':selectedFolder" @uploaded="reload" />

    <el-dialog title="移动技术规程" :visible.sync="moveOpen" width="430px" append-to-body>
      <el-form label-position="top"><el-form-item label="目标文件夹">
        <el-select v-model="moveFolderId" clearable placeholder="不归入文件夹" style="width:100%">
          <el-option label="不归入文件夹" value="" />
          <el-option v-for="folder in folderOptions" :key="folder.folder_id" :label="folder.path" :value="folder.folder_id" />
        </el-select>
      </el-form-item></el-form>
      <div slot="footer"><el-button @click="moveOpen=false">取消</el-button><el-button type="primary" @click="confirmMove">确定移动</el-button></div>
    </el-dialog>
  </div>
</template>

<script>
import { saveAs } from 'file-saver'
import LibraryAssetDialog from './LibraryAssetDialog.vue'
import {
  listRegulations, getRegulation, getRegulationContent,
  disableRegulation, restoreRegulation, deleteRegulation, downloadRegulationFile,
  listRegulationFolders, createRegulationFolder, renameRegulationFolder,
  deleteRegulationFolder, moveRegulationToFolder, renameRegulation, listLibraryAssets,
  renameLibraryAsset, moveLibraryAsset, deleteLibraryAsset, downloadLibraryAsset
} from '@/api/rail/audit'

export default {
  name: 'RegulationLibrary',
  components: { LibraryAssetDialog },
  data() {
    return {
      loading: false, keyword: '', allRegulations: [], assets: [], folders: [], selectedFolder: 'all',
      selectedId: '', selectedAssetId: '', detail: null, assetDetail: null, content: '', previewUrl: '', previewError: '',
      contentLoading: false, moveOpen: false, moveFolderId: '', assetUploadOpen: false,
      dragging: null, dragOverFolder: '',
      expandedFolderIds: [], folderTreeInitialized: false
    }
  },
  computed: {
    visibleRegulations() {
      const token = this.keyword.trim().toLowerCase()
      return this.allRegulations.filter(item => {
        const matches = !token || [
          item.title,
          item.version,
          item.original_file_name,
          item.folder_name
        ].filter(Boolean).join(' ').toLowerCase().includes(token)
        if (token) return matches
        const inFolder = this.selectedFolder === 'all'
          ? !item.folder_id
          : item.folder_id === this.selectedFolder
        return inFolder
      })
    },
    visibleFolders() {
      const token = this.keyword.trim().toLowerCase()
      if (token) return []
      const parentId = this.selectedFolder === 'all' ? null : this.selectedFolder
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
        const inFolder = this.selectedFolder === 'all'
          ? !item.folder_id
          : item.folder_id === this.selectedFolder
        return inFolder
      })
    },
    currentFolderName() {
      if (this.selectedFolder === 'all') return '全部技术规程'
      const folder = this.folders.find(item => item.folder_id === this.selectedFolder)
      return folder ? folder.name : '技术规程'
    }
  },
  created() { this.reload() },
  beforeDestroy() { this.releasePreview() },
  methods: {
    async reload() {
      this.loading = true
      try {
        const [rows, folders, assets] = await Promise.all([
          listRegulations({ includeInactive: true }),
          listRegulationFolders(),
          listLibraryAssets({ library_type: 'regulation' })
        ])
        this.allRegulations = rows
        this.folders = folders
        this.assets = assets
        const parentIds = folders
          .filter(folder => folders.some(child => child.parent_id === folder.folder_id))
          .map(folder => folder.folder_id)
        if (!this.folderTreeInitialized) {
          this.expandedFolderIds = parentIds
          this.folderTreeInitialized = true
        } else {
          this.expandedFolderIds = this.expandedFolderIds.filter(folderId => parentIds.includes(folderId))
        }
        if (this.selectedFolder !== 'all' && !folders.some(item => item.folder_id === this.selectedFolder)) this.selectedFolder = 'all'
      } finally { this.loading = false }
    },
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
    selectFolder(folderId) {
      this.selectedFolder = folderId
      this.selectedId = ''
      this.selectedAssetId = ''
      this.detail = null
      this.assetDetail = null
      this.releasePreview()
    },
    returnToRoot() {
      const current = this.folders.find(item => item.folder_id === this.selectedFolder)
      this.selectFolder(current && current.parent_id ? current.parent_id : 'all')
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
      if (!payload || !['regulation', 'asset'].includes(payload.type)) return
      const folderId = target === 'all' ? '' : target
      if (payload.type === 'regulation') {
        await moveRegulationToFolder(payload.id, folderId)
      } else {
        await moveLibraryAsset(payload.id, folderId)
      }
      this.endDrag()
      await this.reload()
      const folder = this.folders.find(item => item.folder_id === folderId)
      this.$message.success(folder ? `已移动到“${folder.name}”` : '已移出文件夹')
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
      const parentId = this.selectedFolder === 'all' ? null : this.selectedFolder
      const parent = parentId ? this.folders.find(item => item.folder_id === parentId) : null
      const title = parent ? `在“${parent.name}”中新建子文件夹` : '新建文件夹'
      const { value } = await this.$prompt('请输入技术规程文件夹名称', title, {
        confirmButtonText: '创建', cancelButtonText: '取消', inputPattern: /\S+/, inputErrorMessage: '文件夹名称不能为空'
      })
      await createRegulationFolder(value.trim(), parentId)
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
        await renameRegulationFolder(folder.folder_id, value.trim())
        await this.reload()
        this.$message.success('文件夹已重命名')
        return
      }
      await this.$confirm(
        `删除“${folder.name}”后，其中的文件和下级文件夹将移到上一级，规程原文不会被删除。`,
        '删除文件夹', { type: 'warning', confirmButtonText: '删除文件夹', cancelButtonText: '取消' }
      )
      const parentId = folder.parent_id || 'all'
      await deleteRegulationFolder(folder.folder_id)
      if (this.selectedFolder === folder.folder_id) this.selectedFolder = parentId
      await this.reload()
      this.$message.success('文件夹已删除，原有内容已移到上一级')
    },
    async select(item) {
      this.selectedAssetId = ''
      this.assetDetail = null
      this.selectedId = item.regulation_id
      this.content = ''
      this.previewError = ''
      this.releasePreview()
      this.contentLoading = true
      try {
        const detail = await getRegulation(item.regulation_id)
        this.detail = detail
        if (/\.pdf$/i.test(detail.original_file_name || '')) {
          const source = await downloadRegulationFile(item.regulation_id)
          this.previewUrl = URL.createObjectURL(new Blob([source], { type: 'application/pdf' }))
        } else {
          const source = await getRegulationContent(item.regulation_id)
          this.content = source.content
        }
      } catch (error) {
        this.previewError = '原文件预览加载失败，请下载后阅读。'
      } finally { this.contentLoading = false }
    },
    async selectAsset(item) {
      this.selectedId = ''
      this.detail = null
      this.selectedAssetId = item.asset_id
      this.assetDetail = item
      this.releasePreview()
      if (!['pdf', 'image'].includes(item.file_kind)) return
      const source = await downloadLibraryAsset(item.asset_id)
      this.previewUrl = URL.createObjectURL(new Blob([source], { type: item.media_type }))
    },
    async manageRegulation(command, item) {
      if (command !== 'rename') return
      const { value } = await this.$prompt('请输入新的技术规程名称', '重命名技术规程', {
        inputValue: item.title,
        inputPattern: /\S+/,
        inputErrorMessage: '名称不能为空'
      })
      await renameRegulation(item.regulation_id, value.trim())
      this.$message.success('技术规程已重命名')
      await this.reload()
      if (this.selectedId === item.regulation_id) await this.select(this.allRegulations.find(row => row.regulation_id === item.regulation_id))
    },
    assetIcon(item) {
      if (item.file_kind === 'cad' || item.file_kind === 'bim') return 'el-icon-copy-document'
      if (item.file_kind === 'image') return 'el-icon-picture-outline'
      if (item.file_kind === 'archive') return 'el-icon-box'
      return 'el-icon-document'
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
        const options = this.folders.map(folder => ({ value: folder.folder_id, label: folder.name }))
        const { value } = await this.$prompt(`输入目标文件夹名称：${options.map(option => option.label).join('、')}`, '移动资料', { inputValue: '' })
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
    async manage(command) {
      if (command === 'rename') {
        await this.manageRegulation(command, this.detail)
        return
      }
      if (command === 'move') {
        this.moveFolderId = this.detail.folder_id || ''
        this.moveOpen = true
        return
      }
      if (command === 'delete') {
        await this.$confirm(`将永久删除“${this.detail.title}”的原文件、规程条文和检索索引，且无法恢复。`, '确认彻底删除', { type: 'warning', confirmButtonText: '彻底删除', cancelButtonText: '取消' })
        await deleteRegulation(this.selectedId)
        this.selectedId = ''
        this.detail = null
        this.content = ''
        this.releasePreview()
        await this.reload()
        this.$message.success('技术规程已彻底删除')
        return
      }
      if (command === 'disable') {
        await this.$confirm('停用后该规程不再参与正式审核，但仍可恢复。', '确认停用')
        await disableRegulation(this.selectedId)
      } else {
        await restoreRegulation(this.selectedId)
      }
      await this.reload()
      this.detail = await getRegulation(this.selectedId)
    },
    async confirmMove() {
      await moveRegulationToFolder(this.selectedId, this.moveFolderId)
      this.moveOpen = false
      await this.reload()
      this.detail = await getRegulation(this.selectedId)
      this.$message.success('技术规程已移动')
    },
    releasePreview() {
      if (this.previewUrl) URL.revokeObjectURL(this.previewUrl)
      this.previewUrl = ''
    },
    async downloadSource() { saveAs(await downloadRegulationFile(this.selectedId), this.detail.original_file_name || `${this.detail.title}.pdf`) }
  }
}
</script>

<style scoped>
.regulation-page { display: grid; height: calc(100vh - 64px); min-height: 0; grid-template-columns: 292px minmax(360px,420px) minmax(560px,1fr); overflow: hidden; background: #fff; }
.folder-pane { position: relative; min-width: 0; min-height: 0; overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; border-right: 1px solid #e1e5e8; padding: 20px 14px 84px; background: #f8faf9; }
.folder-title { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; padding: 0 10px; color: #263f39; font-size: 20px; font-weight: 600; }
.folder-title i { margin-right: 8px; color: #2f7d69; }
.folder-row { position: relative; display: grid; width: 100%; min-height: 48px; grid-template-columns: 22px minmax(0,1fr) auto; gap: 8px; align-items: center; border: 0; border-radius: 5px; padding: 0 12px; background: transparent; color: #56636a; text-align: left; cursor: pointer; }
.folder-row:hover,.folder-row.active { background: #e6f2ee; color: #27725f; }
.folder-row.drop-target,.reg-row.folder-entry.drop-target { outline: 2px solid #3b927a; outline-offset: -2px; background: #dcefe8; color: #236a57; }
.folder-row span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.folder-row em { color: #87929a; font-style: normal; }
.folder-row.custom { grid-template-columns: 18px 22px minmax(0,1fr) auto 28px; }
.folder-toggle,.folder-toggle-placeholder { width: 18px; height: 28px; }
.folder-toggle { display: inline-flex; align-items: center; justify-content: center; border: 0; border-radius: 3px; padding: 0; background: transparent; color: #6f7c79; cursor: pointer; }
.folder-toggle:hover { background: #d7e8e2; color: #27725f; }
.folder-toggle-placeholder { display: block; }
.folder-more { width: 26px; height: 28px; border: 0; border-radius: 4px; background: transparent; color: #748078; cursor: pointer; opacity: 0; }
.folder-row:hover .folder-more,.folder-row.active .folder-more { opacity: 1; }
.folder-tip { position: absolute; right: 20px; bottom: 20px; left: 20px; margin: 0; color: #97a09f; font-size: 12px; line-height: 1.6; }
.reg-list-pane { display: flex; min-width: 0; min-height: 0; flex-direction: column; overflow: hidden; border-right: 1px solid #e1e5e8; }
.toolbar { display: grid; flex: none; grid-template-columns: minmax(0,1fr) 40px auto; gap: 10px; padding: 20px 18px 14px; }
.create-folder-button { width: 40px; padding-right: 0; padding-left: 0; }
.caption { display: flex; min-height: 43px; flex: none; align-items: center; justify-content: space-between; border-bottom: 1px solid #e8ebed; padding: 6px 20px; color: #68727b; font-size: 13px; }
.folder-path { display: flex; min-width: 0; align-items: center; gap: 10px; }
.back-button { display: inline-flex; height: 30px; align-items: center; gap: 5px; border: 0; border-radius: 4px; padding: 0 8px; background: #edf4f1; color: #317764; cursor: pointer; }
.back-button:hover { background: #dcece6; }
.reg-list { min-height: 0; flex: 1 1 auto; overflow-x: hidden; overflow-y: auto; overscroll-behavior: contain; scrollbar-gutter: stable; }
.reg-row { display: grid; width: 100%; min-height: 92px; grid-template-columns: 42px minmax(0,1fr) auto; gap: 10px; align-items: center; border: 0; border-bottom: 1px solid #edf0f2; padding: 13px 16px; background: #fff; text-align: left; cursor: pointer; }
.reg-row:hover,.reg-row.selected { background: #f0f6f4; }
.reg-row[draggable="true"] { user-select: none; }
.reg-row[draggable="true"]:active { cursor: grabbing; }
.folder-entry,.asset-entry { cursor: pointer; }
.folder-icon { background: #eef3f1; color: #60756f; }
.asset-icon { background: #edf4f2; color: #437b6d; }
.row-more { width: 30px; height: 32px; border: 0; border-radius: 4px; background: transparent; color: #7a858d; cursor: pointer; }
.row-more:hover { background: #e4ece9; color: #2f7d69; }
.doc-icon { display: flex; width: 36px; height: 43px; align-items: center; justify-content: center; background: #dff0ea; color: #2f7d69; font-size: 19px; }
.copy { display: flex; min-width: 0; flex-direction: column; gap: 5px; }
.copy strong,.copy small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.copy small { color: #89929a; font-size: 12px; }
.detail-pane { min-width: 0; min-height: 0; overflow: hidden; }
.empty { padding-top: 190px; color: #929aa3; text-align: center; }
.empty i { font-size: 42px; }
.detail-head { display: flex; min-height: 104px; align-items: center; justify-content: space-between; border-bottom: 1px solid #e2e6e9; padding: 16px 28px; }
.title { display: flex; min-width: 0; align-items: center; gap: 14px; }
.title>span { display: flex; width: 52px; height: 58px; flex: none; align-items: center; justify-content: center; background: #dcefe8; color: #2f7d69; font-size: 25px; }
.title h2 { overflow: hidden; margin: 0 0 7px; font-size: 20px; text-overflow: ellipsis; white-space: nowrap; letter-spacing: 0; }
.title p { margin: 0; color: #858e96; }
.title em { font-style: normal; }
.title b { margin-left: 10px; border-radius: 3px; padding: 2px 7px; background: #edf5f2; color: #4a8173; font-size: 12px; font-weight: 400; }
.actions { display: flex; gap: 8px; }
.document-viewer { height: calc(100% - 104px); min-height: 0; overflow: hidden; background: #eef1f3; }
.document-viewer iframe { width: 100%; height: 100%; border: 0; background: #fff; }
.asset-preview { display: flex; height: calc(100% - 104px); min-height: 0; align-items: center; justify-content: center; overflow: auto; background: #eef1f3; }
.asset-preview iframe { width: 100%; height: 100%; border: 0; background: #fff; }
.asset-preview img { display: block; max-width: 96%; max-height: 96%; object-fit: contain; }
.asset-preview .preview-error { width: 100%; padding-top: 0; }
.content { height: 100%; margin: 0; overflow: auto; padding: 24px 28px; background: #f7f8f9; font: inherit; line-height: 1.8; white-space: pre-wrap; word-break: break-word; }
.preview-error,.preview-loading { padding-top: 160px; color: #8a939b; text-align: center; }
.preview-error i { font-size: 36px; }
.upload-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; margin-top: 16px; }
.upload-fields .el-form-item:last-child { grid-column: 1 / -1; }
.upload-fields .el-select { width: 100%; }
.detail-pane ::v-deep .task-panel { margin: 12px 28px 0; }
@media (max-width: 1250px) {
  .regulation-page { grid-template-columns: 260px 360px minmax(500px,1fr); }
}
</style>
