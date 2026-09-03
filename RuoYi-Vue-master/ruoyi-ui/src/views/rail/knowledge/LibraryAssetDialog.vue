<template>
  <el-dialog
    :title="libraryType === 'regulation' ? '上传技术规程与附件' : '上传案例资料'"
    :visible.sync="open"
    width="620px"
    append-to-body
    :close-on-click-modal="false"
    @closed="reset"
  >
    <file-drop-zone
      ref="picker"
      v-model="files"
      multiple
      :limit="20"
      :accept="accept"
      hint="支持 Word、PDF、CAD、BIM、表格、图片和压缩包；一次最多20个文件"
    />
    <p class="recognition-hint">
      <template v-if="libraryType === 'regulation'">PDF、DOCX、TXT、Markdown 将自动尝试识别；其他格式或识别失败的文件将保留原文件。</template>
      <template v-else>PDF、DOC、DOCX 将自动尝试识别为案例；其他格式或识别失败的文件将保留原文件。</template>
    </p>
    <div v-if="files.length" class="selected-files">
      <div v-for="file in files" :key="file.name + file.size">
        <i class="el-icon-document" />
        <span :title="file.name">{{ file.name }}</span>
        <el-input
          v-model.trim="fileNames[fileKey(file)]"
          size="mini"
          clearable
          placeholder="显示名称"
        />
        <button title="移除" @click="remove(file)"><i class="el-icon-close" /></button>
      </div>
    </div>
    <el-form label-position="top" class="asset-form">
      <el-form-item label="所属文件夹">
        <el-cascader
          v-model="folderId"
          :options="folderTreeOptions"
          :props="folderCascaderProps"
          :show-all-levels="false"
          clearable
          filterable
          placeholder="不选择时放在未归类；可选择任意层级文件夹"
          style="width:100%"
        />
      </el-form-item>
    </el-form>
    <div v-if="uploading" class="processing-note">
      <i class="el-icon-loading" /> {{ processingText || '正在处理文件...' }}
    </div>
    <div slot="footer">
      <el-button @click="open=false">取消</el-button>
      <el-button type="primary" :loading="uploading" :disabled="!files.length || hasMissingDisplayName" @click="submit">
        上传 {{ files.length ? `(${files.length})` : '' }}
      </el-button>
    </div>
  </el-dialog>
</template>

<script>
import FileDropZone from '../components/FileDropZone.vue'
import {
  getTask,
  importKnowledge,
  importRegulation,
  uploadLibraryAsset
} from '@/api/rail/audit'

export default {
  name: 'LibraryAssetDialog',
  components: { FileDropZone },
  props: {
    value: { type: Boolean, default: false },
    libraryType: { type: String, required: true },
    folders: { type: Array, default: () => [] },
    defaultFolderId: { type: String, default: '' }
  },
  data() {
    return {
      files: [],
      fileNames: {},
      folderId: '',
      uploading: false,
      processingText: '',
      folderCascaderProps: {
        value: 'folder_id',
        label: 'name',
        children: 'children',
        checkStrictly: true,
        emitPath: false
      },
      accept: '.pdf,.doc,.docx,.txt,.md,.xls,.xlsx,.csv,.ppt,.pptx,.dwg,.dxf,.dwt,.rvt,.ifc,.png,.jpg,.jpeg,.tif,.tiff,.bmp,.zip,.rar,.7z'
    }
  },
  computed: {
    open: {
      get() { return this.value },
      set(value) { this.$emit('input', value) }
    },
    folderMap() {
      const source = Array.isArray(this.folders) ? this.folders : []
      return new Map(source.map(item => [item.folder_id, item]))
    },
    folderTreeOptions() {
      const source = Array.isArray(this.folders) ? this.folders : []
      const childrenMap = new Map()
      source.forEach(folder => {
        const parentId = folder.parent_id || ''
        if (!childrenMap.has(parentId)) childrenMap.set(parentId, [])
        childrenMap.get(parentId).push(folder)
      })
      const build = parentId => (childrenMap.get(parentId || '') || [])
        .sort((left, right) => String(left.name || '').localeCompare(String(right.name || ''), 'zh-Hans-CN'))
        .map(folder => {
          const children = build(folder.folder_id)
          const option = { ...folder }
          if (children.length) option.children = children
          return option
        })
      return build('')
    },
    selectedFolderId() {
      return this.folderId || ''
    },
    hasMissingDisplayName() {
      return this.files.some(file => !this.displayName(file))
    }
  },
  watch: {
    value(value) {
      if (value) this.applyDefaultFolder()
    },
    files: {
      handler(files) {
        const next = {}
        ;(files || []).forEach(file => {
          const key = this.fileKey(file)
          next[key] = this.fileNames[key] || this.defaultDisplayName(file)
        })
        this.fileNames = next
      },
      deep: false
    }
  },
  methods: {
    fileKey(file) {
      return `${file.name || ''}_${file.size || 0}_${file.lastModified || 0}`
    },
    defaultDisplayName(file) {
      return String(file.name || '').replace(/\.[^.]+$/, '') || '未命名文件'
    },
    displayName(file) {
      return (this.fileNames[this.fileKey(file)] || this.defaultDisplayName(file)).trim()
    },
    remove(file) {
      if (this.$refs.picker) this.$refs.picker.removeRaw(file)
    },
    reset() {
      this.files = []
      this.fileNames = {}
      this.folderId = ''
      this.uploading = false
      this.processingText = ''
      if (this.$refs.picker) this.$refs.picker.clear()
    },
    applyDefaultFolder() {
      const folderId = this.defaultFolderId || ''
      this.folderId = folderId && this.folderMap.has(folderId) ? folderId : ''
    },
    extension(file) {
      const parts = String(file.name || '').toLowerCase().split('.')
      return parts.length > 1 ? parts.pop() : ''
    },
    canRecognize(file) {
      const extension = this.extension(file)
      return this.libraryType === 'regulation'
        ? ['pdf', 'docx', 'txt', 'md'].includes(extension)
        : ['pdf', 'doc', 'docx'].includes(extension)
    },
    async waitForTask(taskId) {
      for (let index = 0; index < 800; index += 1) {
        const task = await getTask(taskId)
        if (task.status === 'success') return
        if (task.status === 'failed') throw new Error(task.error_message || '文件识别失败')
        await new Promise(resolve => setTimeout(resolve, 1500))
      }
      throw new Error('文件识别超时')
    },
    async recognizeRegulation(file) {
      const body = new FormData()
      body.append('file', file)
      body.append('title', this.displayName(file))
      if (this.selectedFolderId) body.append('folder_id', this.selectedFolderId)
      const result = await importRegulation(body)
      await this.waitForTask(result.task_id)
    },
    async recognizeCase(file) {
      const body = new FormData()
      body.append('file', file)
      body.append('case_name', this.displayName(file))
      if (this.selectedFolderId) body.append('folder_id', this.selectedFolderId)
      const result = await importKnowledge(body)
      await this.waitForTask(result.task_id)
    },
    async preserveOriginal(file) {
      const body = new FormData()
      body.append('file', file)
      body.append('library_type', this.libraryType)
      body.append('display_name', this.displayName(file))
      if (this.selectedFolderId) body.append('folder_id', this.selectedFolderId)
      await uploadLibraryAsset(body)
    },
    async submit() {
      if (this.hasMissingDisplayName) {
        this.$message.warning('请填写每个文件的文件名称')
        return
      }
      this.uploading = true
      let recognized = 0
      let preserved = 0
      try {
        const files = [...this.files]
        for (let index = 0; index < files.length; index += 1) {
          const file = files[index]
          this.processingText = `正在处理 ${index + 1}/${files.length}：${file.name}`
          if (this.canRecognize(file)) {
            try {
              if (this.libraryType === 'regulation') {
                await this.recognizeRegulation(file)
              } else {
                await this.recognizeCase(file)
              }
              recognized += 1
              continue
            } catch (error) {
              if (this.libraryType === 'regulation') {
                throw new Error(`${file.name} 解析规程失败：${error.message || '请检查文件是否可复制文字，或补充MinerU/OCR配置后重试'}`)
              }
              // 案例库允许保留原文件；技术规程必须完成正文入库后才能参与检索和启用。
            }
          }
          await this.preserveOriginal(file)
          preserved += 1
        }
        const parts = []
        if (recognized) parts.push(`自动识别 ${recognized} 个`)
        if (preserved) parts.push(`原文件保存 ${preserved} 个`)
        this.$message.success(parts.length ? parts.join('，') : `已上传 ${files.length} 个文件`)
        this.$emit('uploaded')
        this.open = false
      } catch (error) {
        this.$message.error(`上传失败：${error.message || '请稍后重试'}`)
      } finally {
        this.uploading = false
        this.processingText = ''
      }
    }
  }
}
</script>

<style scoped>
.selected-files { max-height: 180px; margin-top: 14px; overflow: auto; border: 1px solid #e6eaed; }
.selected-files>div { display: grid; grid-template-columns: 22px minmax(0,1.1fr) minmax(160px,1fr) 30px; gap: 8px; align-items: center; padding: 9px 12px; border-bottom: 1px solid #eef1f3; }
.selected-files>div:last-child { border-bottom: 0; }
.selected-files span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.selected-files button { border: 0; background: transparent; color: #87919a; cursor: pointer; }
.recognition-hint { margin: 10px 0 0; color: #7f898f; font-size: 13px; line-height: 1.6; }
.asset-form { margin-top: 16px; }
.asset-form ::v-deep .el-select { width: 100%; }
.processing-note { margin-top: 12px; color: #317764; font-size: 13px; }
.processing-note i { margin-right: 6px; }
</style>
