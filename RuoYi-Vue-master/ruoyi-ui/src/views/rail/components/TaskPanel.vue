<template>
  <section v-if="taskId" class="task-panel">
    <div class="task-head">
      <div>
        <strong>{{ title }}</strong>
      </div>
      <el-tag size="small" :type="tagType">{{ statusLabel }}</el-tag>
    </div>
    <el-progress :percentage="progress" :status="status === 'failed' ? 'exception' : undefined" :format="formatProgress" />
    <el-alert v-if="task.error_message" :title="task.error_message" type="error" :closable="false" show-icon />
    <div v-if="showFiles && files.length" class="result-files">
      <div class="section-label">结果文件</div>
      <div v-for="file in files" :key="file.file_id" class="file-row">
        <span><i class="el-icon-document" /> {{ file.name }}</span>
        <el-button type="text" icon="el-icon-download" @click="download(file)">下载</el-button>
      </div>
    </div>
  </section>
</template>

<script>
import { saveAs } from 'file-saver'
import { getTask, getTaskResult, getTaskFiles, downloadTaskFile } from '@/api/rail/audit'

export default {
  name: 'TaskPanel',
  props: {
    taskId: { type: String, default: '' },
    title: { type: String, default: '处理进度' },
    showFiles: { type: Boolean, default: true }
  },
  data() {
    return {
      task: {}, files: [], timer: null, progressTimer: null,
      displayedProgress: 0, serverProgress: 0, progressStartedAt: 0
    }
  },
  computed: {
    progress() { return Math.max(0, Math.min(100, Math.floor(this.displayedProgress))) },
    status() { return this.task.status || 'queued' },
    statusLabel() { return ({ queued: '排队中', running: '处理中', success: '已完成', failed: '失败' })[this.status] || this.status },
    tagType() { return ({ queued: 'info', running: 'warning', success: 'success', failed: 'danger' })[this.status] || 'info' }
  },
  watch: {
    taskId: {
      immediate: true,
      handler(value) {
        if (value) {
          this.start()
          return
        }
        this.stop()
        this.task = {}
        this.files = []
        this.resetProgress()
      }
    }
  },
  beforeDestroy() { this.stop() },
  methods: {
    start() {
      this.stop()
      this.resetProgress()
      this.progressStartedAt = Date.now()
      this.refresh()
      this.timer = setInterval(this.refresh, 1500)
      this.progressTimer = setInterval(this.tickProgress, 450)
    },
    stop() {
      if (this.timer) clearInterval(this.timer)
      if (this.progressTimer) clearInterval(this.progressTimer)
      this.timer = null
      this.progressTimer = null
    },
    resetProgress() {
      this.displayedProgress = 0
      this.serverProgress = 0
      this.progressStartedAt = 0
    },
    formatProgress(percentage) { return `${percentage}%` },
    syncProgress(task) {
      const raw = Number(task.progress || 0)
      if (task.status === 'success') {
        this.displayedProgress = 100
        this.serverProgress = 100
        return
      }
      if (task.status === 'failed') {
        this.serverProgress = Math.max(this.serverProgress, Math.min(raw, 100))
        this.displayedProgress = Math.max(this.displayedProgress, this.serverProgress)
        return
      }
      this.serverProgress = Math.max(this.serverProgress, Math.min(raw, 99))
      if (!this.progressStartedAt) this.progressStartedAt = Date.now()
    },
    tickProgress() {
      if (!this.taskId || this.displayedProgress >= 100) return
      const active = ['queued', 'running'].includes(this.status)
      if (!active) return
      const elapsedSeconds = Math.max(0, (Date.now() - (this.progressStartedAt || Date.now())) / 1000)
      const timeProgress = Math.min(99, 6 + elapsedSeconds * 1.1)
      const target = Math.max(this.serverProgress, timeProgress)
      if (target <= this.displayedProgress) return
      const delta = target - this.displayedProgress
      this.displayedProgress = Math.min(99, this.displayedProgress + Math.max(0.35, Math.min(1.2, delta * 0.18)))
    },
    async refresh() {
      if (!this.taskId) return
      const taskId = this.taskId
      try {
        const task = await getTask(taskId)
        if (taskId !== this.taskId) return
        this.task = task
        this.syncProgress(task)
        if (this.status === 'success') {
          this.stop()
          const [result, files] = await Promise.all([getTaskResult(taskId), getTaskFiles(taskId)])
          if (taskId !== this.taskId) return
          this.files = files || []
          this.$emit('success', result)
        } else if (this.status === 'failed') {
          this.stop()
          this.$emit('failed', this.task)
        }
      } catch (error) { this.stop() }
    },
    async download(file) { saveAs(await downloadTaskFile(this.taskId, file.file_id), file.name) }
  }
}
</script>

<style scoped>
.task-panel { margin-top: 20px; padding: 18px 20px; border: 1px solid #dfe4e8; border-radius: 4px; background: #fff; }
.task-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px; }
.result-files { margin-top: 18px; border-top: 1px solid #edf0f2; padding-top: 12px; }
.section-label { margin-bottom: 5px; color: #606a75; font-size: 13px; }
.file-row { display: flex; align-items: center; justify-content: space-between; min-height: 34px; }
</style>
