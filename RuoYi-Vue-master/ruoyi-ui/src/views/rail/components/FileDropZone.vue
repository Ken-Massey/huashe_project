<template>
  <el-upload
    class="file-drop"
    drag
    action="#"
    :accept="accept"
    :auto-upload="false"
    :multiple="multiple"
    :limit="limit"
    :file-list="files"
    :show-file-list="showList || !multiple"
    :on-change="changed"
    :on-remove="removed"
    :on-exceed="exceeded"
  >
    <i class="el-icon-upload2" />
    <div class="el-upload__text">拖入文件，或<em>点击选择</em></div>
    <div slot="tip" class="el-upload__tip">{{ hint }}</div>
  </el-upload>
</template>

<script>
export default {
  name: 'FileDropZone',
  props: {
    accept: { type: String, default: '.pdf,.doc,.docx,.txt,.json' },
    hint: { type: String, default: '请选择一个文件' },
    multiple: { type: Boolean, default: false },
    limit: { type: Number, default: 1 },
    showList: { type: Boolean, default: false }
  },
  data() { return { files: [] } },
  methods: {
    changed(file, files) {
      this.files = this.multiple ? files.slice(0, this.limit) : files.slice(-1)
      this.$emit('input', this.multiple ? this.files.map(item => item.raw) : file.raw)
    },
    removed(file, files) {
      this.files = files
      this.$emit('input', this.multiple ? files.map(item => item.raw) : null)
    },
    exceeded(files) {
      if (this.multiple) {
        this.$message.warning(`最多上传 ${this.limit} 个文件`)
        return
      }
      this.files = []
      const file = { name: files[0].name, raw: files[0] }
      this.changed(file, [file])
    },
    clear() {
      this.files = []
      this.$emit('input', this.multiple ? [] : null)
    },
    removeRaw(raw) {
      this.files = this.files.filter(item => item.raw !== raw)
      this.$emit('input', this.files.map(item => item.raw))
    }
  }
}
</script>

<style scoped>
.file-drop ::v-deep .el-upload,
.file-drop ::v-deep .el-upload-dragger { width: 100%; }
.file-drop ::v-deep .el-upload-dragger { height: 142px; border-radius: 4px; background: #fafbfc; }
.file-drop .el-icon-upload2 { margin: 31px 0 12px; font-size: 34px; color: #2f7d69; }
.file-drop ::v-deep .el-upload__tip { margin-top: 8px; color: #7a8490; }
</style>
