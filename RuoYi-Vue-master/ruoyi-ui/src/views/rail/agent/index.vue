<template>
  <div class="agent-page">
    <aside class="session-sidebar">
      <div class="session-head">
        <div>
          <h3>AI 智能体</h3>
          <p>历史对话</p>
        </div>
        <el-tooltip content="开启新对话" placement="top">
          <el-button class="new-session" type="primary" icon="el-icon-plus" circle @click="newSession" />
        </el-tooltip>
      </div>
      <div v-loading="sessionsLoading" class="session-list">
        <button
          v-for="item in sessions"
          :key="item.session_id"
          type="button"
          class="session-item"
          :class="{ active: item.session_id === activeSessionId }"
          @click="selectSession(item)"
        >
          <i :class="item.mode === 'knowledge' ? 'el-icon-collection' : 'el-icon-chat-dot-round'" />
          <span class="session-copy">
            <strong :title="item.title">{{ item.title }}</strong>
            <small>{{ modeLabel(item.mode) }}</small>
          </span>
        </button>
        <div v-if="!sessionsLoading && sessions.length === 0" class="empty-sessions">
          <i class="el-icon-chat-dot-square" />
          <span>暂无历史对话</span>
        </div>
      </div>
    </aside>

    <section class="agent-main">
      <header class="agent-head">
        <div class="head-copy">
          <h2>{{ activeSessionTitle || 'AI 智能体' }}</h2>
          <p>通用问答与轨道工程知识检索助手</p>
        </div>
        <div class="agent-state">
          <span class="model-state" :class="{ offline: !configured }">
            <i class="state-dot" />
            {{ configured ? modelDisplayName : '模型未配置' }}
          </span>
          <span class="knowledge-state"><i class="el-icon-collection" /> {{ knowledgeCount }} 个启用案例</span>
        </div>
      </header>

      <div v-if="!configured" class="config-warning">
        <span><i class="el-icon-warning-outline" /> 请先配置硅基流动 API Key，才能使用智能体。</span>
        <el-button type="text" @click="$router.push({ path: '/rail/settings', query: { tab: 'model' } })">前往设置</el-button>
      </div>

      <div class="mode-bar">
        <div class="mode-inner">
          <el-radio-group v-model="mode" size="small">
            <el-radio-button label="general"><i class="el-icon-chat-dot-round" /> 通用对话</el-radio-button>
            <el-radio-button label="knowledge"><i class="el-icon-collection" /> 知识库问答</el-radio-button>
          </el-radio-group>
          <div class="mode-actions">
            <span>{{ mode === 'knowledge' ? '结合知识库原文回答' : '与当前模型连续对话' }}</span>
            <el-button type="text" icon="el-icon-plus" @click="newSession">新对话</el-button>
          </div>
        </div>
      </div>

      <main ref="conversation" class="conversation">
        <div v-if="messages.length === 0" class="welcome">
          <div class="welcome-mark"><i :class="mode === 'knowledge' ? 'el-icon-collection' : 'el-icon-chat-dot-round'" /></div>
          <h3>{{ mode === 'knowledge' ? '从知识库中查找答案' : '今天想了解什么？' }}</h3>
          <p>{{ mode === 'knowledge' ? '可询问历史案例、技术要求和评审建议' : '可以进行工程咨询、内容整理或自由问答' }}</p>
          <div class="suggestions">
            <button v-for="item in currentSuggestions" :key="item" type="button" @click="useSuggestion(item)">
              <span>{{ item }}</span><i class="el-icon-right" />
            </button>
          </div>
        </div>

        <article v-for="message in messages" :key="message.message_id || `${message.role}-${message.created_at}-${message.content}`" class="message-row" :class="message.role">
          <div v-if="message.role === 'assistant'" class="assistant-avatar"><i class="el-icon-chat-dot-round" /></div>
          <div class="message-content">
            <div class="message-label">
              {{ message.role === 'user' ? '你' : '智能体' }}
              <span v-if="message.model">{{ compactModelName(message.model) }}</span>
            </div>
            <div v-if="message.role === 'assistant'" class="message-body markdown-body" v-html="renderMarkdown(message.content)" />
            <div v-else class="message-body">{{ message.content }}</div>
            <details v-if="message.sources && message.sources.length" class="sources">
              <summary><i class="el-icon-document" /> 查看 {{ message.sources.length }} 条知识库依据</summary>
              <div v-for="(source, sourceIndex) in message.sources" :key="`${source.case_id || source.regulation_id || 'source'}-${sourceIndex}`" class="source-item">
                <strong>[{{ sourceIndex + 1 }}] {{ source.case_name || source.title || source.original_file_name || '知识库材料' }}</strong>
                <span>{{ source.excerpt }}</span>
              </div>
            </details>
          </div>
        </article>

        <div v-if="loading" class="message-row assistant thinking-row">
          <div class="assistant-avatar"><i class="el-icon-chat-dot-round" /></div>
          <div class="message-content">
            <div class="message-label">智能体</div>
            <div class="thinking">
              <i class="el-icon-loading" />
              {{ mode === 'knowledge' ? '正在检索知识库并组织回答' : '正在思考' }}
            </div>
          </div>
        </div>
      </main>

      <footer class="composer">
        <div class="composer-inner">
          <div class="composer-box">
            <el-input
              v-model="question"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 6 }"
              maxlength="2000"
              resize="none"
              :placeholder="mode === 'knowledge' ? '询问知识库中的案例、技术要求或评审建议' : '输入消息'"
              @keydown.native="handleKeydown"
            />
            <div class="composer-actions">
              <span><i :class="mode === 'knowledge' ? 'el-icon-collection' : 'el-icon-chat-dot-round'" /> {{ modeLabel(mode) }}</span>
              <el-tooltip content="发送（Enter）" placement="top">
                <el-button
                  class="send-button"
                  type="primary"
                  icon="el-icon-top"
                  circle
                  :loading="loading"
                  :disabled="!question.trim() || !configured"
                  @click="send"
                />
              </el-tooltip>
            </div>
          </div>
          <p class="composer-tip">内容由 AI 生成，请结合技术规程与项目资料核验。Shift + Enter 换行</p>
        </div>
      </footer>
    </section>
  </div>
</template>

<script>
import MarkdownIt from 'markdown-it'
import {
  askAgent,
  createAgentSession,
  getAgentConfig,
  getAgentSession,
  getKnowledgeStats,
  listAgentSessions
} from '@/api/rail/audit'

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: false
})

const defaultLinkOpen = markdown.renderer.rules.link_open || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options)
}
markdown.renderer.rules.link_open = function(tokens, idx, options, env, self) {
  tokens[idx].attrSet('target', '_blank')
  tokens[idx].attrSet('rel', 'noopener noreferrer')
  return defaultLinkOpen(tokens, idx, options, env, self)
}

export default {
  name: 'RailAgent',
  data() {
    return {
      question: '',
      loading: false,
      sessionsLoading: false,
      messages: [],
      sessions: [],
      activeSessionId: '',
      knowledgeCount: 0,
      mode: 'general',
      configured: false,
      provider: 'siliconflow',
      providerLabel: '硅基流动 Qwen3.5 快速模型',
      model: 'Qwen/Qwen3.5-35B-A3B',
      generalSuggestions: ['帮我概括一下基坑工程安全评估的主要思路', '解释一下欧氏距离和余弦相似度的区别', '帮我整理一份项目会议提纲'],
      knowledgeSuggestions: ['哪些案例涉及基坑降水？', '知识库中对变形监测有哪些建议？', '哪些案例位于特别保护区？']
    }
  },
  computed: {
    currentSuggestions() { return this.mode === 'knowledge' ? this.knowledgeSuggestions : this.generalSuggestions },
    modelDisplayName() {
      const name = this.model ? this.model.split('/').pop() : ''
      return name || this.providerLabel
    },
    activeSessionTitle() {
      const current = this.sessions.find(item => item.session_id === this.activeSessionId)
      return current && current.title !== '新对话' ? current.title : ''
    }
  },
  created() {
    this.loadState()
    this.loadSessions()
  },
  methods: {
    async loadState() {
      try { const value = await getKnowledgeStats(); this.knowledgeCount = value.active || 0 } catch (_) { this.knowledgeCount = 0 }
      try {
        const value = await getAgentConfig()
        this.configured = Boolean(value.configured)
        this.provider = value.provider || 'siliconflow'
        this.providerLabel = value.provider_label || '硅基流动 Qwen3.5 快速模型'
        this.model = value.model || 'Qwen/Qwen3.5-35B-A3B'
      } catch (_) { this.configured = false }
    },
    async loadSessions() {
      this.sessionsLoading = true
      try {
        const rows = await listAgentSessions(50)
        this.sessions = Array.isArray(rows) ? rows : []
        if (this.sessions.length && !this.activeSessionId) {
          await this.selectSession(this.sessions[0])
        }
      } finally {
        this.sessionsLoading = false
      }
    },
    async ensureSession() {
      if (this.activeSessionId) return this.activeSessionId
      const session = await createAgentSession({ mode: this.mode })
      this.activeSessionId = session.session_id
      this.messages = session.messages || []
      this.upsertSession(session)
      return this.activeSessionId
    },
    async newSession() {
      if (this.loading) return
      const session = await createAgentSession({ mode: this.mode })
      this.activeSessionId = session.session_id
      this.messages = []
      this.upsertSession(session)
      this.scrollBottom()
    },
    async selectSession(item) {
      if (!item || !item.session_id || item.session_id === this.activeSessionId) return
      const session = await getAgentSession(item.session_id)
      this.activeSessionId = session.session_id
      this.mode = session.mode || this.mode
      this.messages = this.normalizeMessages(session.messages || [])
      this.upsertSession(session)
      this.scrollBottom()
    },
    upsertSession(session) {
      if (!session || !session.session_id) return
      const summary = {
        session_id: session.session_id,
        title: session.title || '新对话',
        mode: session.mode || this.mode,
        message_count: session.message_count || 0,
        created_at: session.created_at,
        updated_at: session.updated_at,
        last_message_at: session.last_message_at
      }
      const index = this.sessions.findIndex(item => item.session_id === summary.session_id)
      if (index >= 0) this.$set(this.sessions, index, { ...this.sessions[index], ...summary })
      else this.sessions.unshift(summary)
      this.sessions.sort((a, b) => String(b.last_message_at || b.updated_at || '').localeCompare(String(a.last_message_at || a.updated_at || '')))
    },
    normalizeMessages(values) {
      return values.map(item => ({
        message_id: item.message_id,
        role: item.role,
        content: item.content,
        model: item.model,
        sources: item.sources || [],
        created_at: item.created_at
      }))
    },
    useSuggestion(value) { this.question = value; this.send() },
    compactModelName(value) { return value ? value.split('/').pop() : '' },
    renderMarkdown(value) { return markdown.render(value || '') },
    modeLabel(value) { return value === 'knowledge' ? '知识库问答' : '通用对话' },
    handleKeydown(event) {
      if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
        event.preventDefault()
        this.send()
      }
    },
    async send() {
      const value = this.question.trim()
      if (!value || this.loading || !this.configured) return
      this.loading = true
      this.question = ''
      try {
        const sessionId = await this.ensureSession()
        this.messages.push({ role: 'user', content: value, created_at: new Date().toISOString() })
        this.scrollBottom()
        const result = await askAgent({ question: value, top_k: 5, mode: this.mode, session_id: sessionId })
        if (Array.isArray(result.messages)) this.messages = this.normalizeMessages(result.messages)
        else this.messages.push({ role: 'assistant', content: result.answer, model: result.model, sources: result.sources || [] })
        this.upsertSession(result.session)
        this.knowledgeCount = result.knowledge_stats ? result.knowledge_stats.active : this.knowledgeCount
      } catch (error) {
        this.messages.push({ role: 'assistant', content: `暂时无法完成回答：${error.msg || error.message || '服务异常'}`, sources: [] })
      } finally {
        this.loading = false
        this.scrollBottom()
      }
    },
    scrollBottom() { this.$nextTick(() => { const el = this.$refs.conversation; if (el) el.scrollTop = el.scrollHeight }) }
  }
}
</script>

<style lang="scss" scoped>
.agent-page {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  height: 100vh;
  max-height: 100vh;
  min-height: 620px;
  overflow: hidden;
  background: #fff;
  color: #202724;
}
.session-sidebar { display: flex; flex-direction: column; min-width: 0; border-right: 1px solid #e5ebe8; background: #f7faf9; }
.session-head {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  padding: 19px 18px 14px;
  border-bottom: 1px solid #e2e9e6;
}
.session-head h3 { margin: 0 0 4px; font-size: 18px; font-weight: 600; letter-spacing: 0; }
.session-head p { margin: 0; color: #86928e; font-size: 12px; }
.new-session { width: 34px; height: 34px; padding: 0; }
.session-list { flex: 1 1 0; min-height: 0; overflow-y: auto; padding: 10px; }
.session-item {
  display: flex;
  width: 100%;
  min-height: 58px;
  gap: 10px;
  align-items: flex-start;
  padding: 10px;
  border: 1px solid transparent;
  border-radius: 7px;
  background: transparent;
  color: #35413d;
  cursor: pointer;
  text-align: left;
}
.session-item i {
  flex: 0 0 26px;
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  background: #e7f2ee;
  color: #2f8168;
  font-size: 15px;
}
.session-item:hover { background: #fff; border-color: #dce6e2; }
.session-item.active { background: #e7f3ef; border-color: #bad8ce; }
.session-copy { display: grid; min-width: 0; gap: 4px; }
.session-copy strong { overflow: hidden; color: #24302c; font-size: 13px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.session-copy small { color: #89938f; font-size: 11px; }
.empty-sessions { display: grid; gap: 8px; place-items: center; padding: 58px 14px; color: #9aa4a0; font-size: 13px; }
.empty-sessions i { font-size: 26px; }
.agent-main { display: flex; flex-direction: column; min-width: 0; min-height: 0; overflow: hidden; }
.agent-head {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  min-height: 78px;
  padding: 18px 34px;
  border-bottom: 1px solid #e8ecea;
}
.agent-head h2 { margin: 0 0 5px; font-size: 22px; font-weight: 600; letter-spacing: 0; }
.agent-head p { margin: 0; color: #7d8783; font-size: 13px; }
.agent-state { display: flex; align-items: center; gap: 16px; color: #63706b; font-size: 12px; }
.model-state {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  border: 1px solid #cde6dc;
  border-radius: 6px;
  background: #eff9f5;
  color: #26735d;
}
.model-state.offline { border-color: #ecd9b3; background: #fff8e9; color: #8d6628; }
.state-dot { width: 6px; height: 6px; border-radius: 50%; background: #2ba879; }
.offline .state-dot { background: #d19b3e; }
.knowledge-state i { margin-right: 4px; }
.config-warning { display: flex; flex: 0 0 auto; align-items: center; justify-content: space-between; padding: 9px 34px; background: #fff8e9; color: #865f24; font-size: 13px; }
.mode-bar { flex: 0 0 auto; border-bottom: 1px solid #e8ecea; background: #fff; }
.mode-inner { display: flex; align-items: center; justify-content: space-between; width: min(960px, calc(100% - 48px)); margin: 0 auto; padding: 11px 0; }
.mode-actions { display: flex; align-items: center; gap: 16px; color: #8a928f; font-size: 12px; }
.mode-actions .el-button { padding: 4px 0; color: #727d79; }
.conversation {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 34px max(24px, calc((100% - 960px) / 2)) 56px;
  background: #fbfcfc;
  scroll-behavior: smooth;
}
.welcome { max-width: 700px; margin: 0 auto; padding-top: 54px; text-align: center; }
.welcome-mark {
  display: grid;
  width: 54px;
  height: 54px;
  margin: 0 auto;
  place-items: center;
  border: 1px solid #d9e7e2;
  border-radius: 8px;
  background: #eef7f4;
  color: #317d67;
  font-size: 25px;
}
.welcome h3 { margin: 18px 0 8px; font-size: 22px; font-weight: 600; }
.welcome > p { margin: 0 0 28px; color: #7e8884; font-size: 13px; }
.suggestions { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; text-align: left; }
.suggestions button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 72px;
  padding: 14px 15px;
  border: 1px solid #dfe6e3;
  border-radius: 7px;
  background: #fff;
  color: #3f4b47;
  cursor: pointer;
  line-height: 1.5;
  text-align: left;
}
.suggestions button i { margin-left: 10px; color: #a2aaa7; }
.suggestions button:hover { border-color: #8dbbad; background: #f8fbfa; color: #246d58; }
.message-row { display: flex; width: min(900px, 100%); margin: 0 auto 30px; gap: 12px; }
.message-row.user { justify-content: flex-end; }
.message-content { min-width: 0; max-width: calc(100% - 50px); }
.message-row.user .message-content { width: auto; max-width: 72%; }
.assistant-avatar {
  display: grid;
  flex: 0 0 34px;
  width: 34px;
  height: 34px;
  margin-top: 21px;
  place-items: center;
  border: 1px solid #d2e4de;
  border-radius: 7px;
  background: #eaf5f1;
  color: #2c7c65;
  font-size: 17px;
}
.message-label { margin: 0 0 7px 2px; color: #78827e; font-size: 12px; }
.message-row.user .message-label { text-align: right; }
.message-label span { margin-left: 8px; color: #a0a8a5; }
.message-body { border-radius: 8px; color: #242b28; font-size: 15px; line-height: 1.8; }
.message-row.user .message-body { padding: 11px 16px; background: #e6f1ed; white-space: pre-wrap; }
.message-row.assistant .message-body { padding: 2px 4px 0; }
.markdown-body ::v-deep > :first-child { margin-top: 0; }
.markdown-body ::v-deep > :last-child { margin-bottom: 0; }
.markdown-body ::v-deep h1,
.markdown-body ::v-deep h2,
.markdown-body ::v-deep h3,
.markdown-body ::v-deep h4 { margin: 24px 0 10px; color: #1d2522; font-weight: 600; line-height: 1.45; }
.markdown-body ::v-deep h1 { font-size: 21px; }
.markdown-body ::v-deep h2 { font-size: 19px; }
.markdown-body ::v-deep h3 { font-size: 17px; }
.markdown-body ::v-deep h4 { font-size: 15px; }
.markdown-body ::v-deep p { margin: 0 0 13px; }
.markdown-body ::v-deep ul,
.markdown-body ::v-deep ol { margin: 8px 0 15px; padding-left: 25px; }
.markdown-body ::v-deep li { margin: 5px 0; padding-left: 2px; }
.markdown-body ::v-deep strong { color: #17201d; font-weight: 600; }
.markdown-body ::v-deep blockquote { margin: 14px 0; padding: 9px 14px; border-left: 3px solid #68a692; background: #f2f7f5; color: #53615c; }
.markdown-body ::v-deep code { padding: 2px 5px; border-radius: 4px; background: #edf1ef; color: #b04a3f; font-family: Consolas, Monaco, monospace; font-size: 13px; }
.markdown-body ::v-deep pre { overflow-x: auto; margin: 14px 0; padding: 15px; border-radius: 7px; background: #202724; color: #ecf1ef; }
.markdown-body ::v-deep pre code { padding: 0; background: transparent; color: inherit; }
.markdown-body ::v-deep table { width: 100%; margin: 14px 0; border-collapse: collapse; font-size: 14px; }
.markdown-body ::v-deep th,
.markdown-body ::v-deep td { padding: 9px 11px; border: 1px solid #dfe5e2; text-align: left; }
.markdown-body ::v-deep th { background: #f3f6f5; font-weight: 600; }
.markdown-body ::v-deep a { color: #267d64; text-decoration: none; }
.markdown-body ::v-deep a:hover { text-decoration: underline; }
.sources { margin-top: 15px; border: 1px solid #dfe8e4; border-radius: 7px; background: #f7faf9; }
.sources summary { padding: 10px 13px; color: #4d6f64; cursor: pointer; font-size: 12px; list-style: none; }
.sources summary::-webkit-details-marker { display: none; }
.sources summary i { margin-right: 6px; }
.source-item { display: grid; gap: 5px; padding: 10px 13px; border-top: 1px solid #e1e8e5; }
.source-item strong { font-size: 13px; }
.source-item span { color: #64706b; font-size: 12px; line-height: 1.65; }
.thinking-row { margin-bottom: 12px; }
.thinking { padding: 8px 4px; color: #55786d; font-size: 14px; }
.thinking i { margin-right: 7px; }
.composer { position: relative; z-index: 5; flex: 0 0 auto; padding: 12px 24px 14px; border-top: 1px solid #e7ebe9; background: rgba(255, 255, 255, 0.98); }
.composer-inner { width: min(900px, 100%); margin: 0 auto; }
.composer-box {
  padding: 10px 12px 8px 16px;
  border: 1px solid #d7dfdc;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 7px 24px rgba(47, 75, 66, 0.08);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.composer-box:focus-within { border-color: #73a995; box-shadow: 0 8px 28px rgba(47, 98, 80, 0.12); }
.composer ::v-deep .el-textarea__inner { padding: 3px 0 6px; border: 0; background: transparent; box-shadow: none; color: #27302d; font-size: 14px; line-height: 1.65; }
.composer-actions { display: flex; align-items: center; justify-content: space-between; min-height: 34px; }
.composer-actions > span { color: #7c8883; font-size: 12px; }
.composer-actions > span i { margin-right: 5px; }
.send-button { width: 34px; height: 34px; padding: 0; background: #2f856b; border-color: #2f856b; }
.send-button:hover,
.send-button:focus { background: #28745e; border-color: #28745e; }
.composer-tip { margin: 7px 0 0; color: #a0a7a4; font-size: 11px; text-align: center; }
@media (max-width: 920px) {
  .agent-page { grid-template-columns: 1fr; }
  .session-sidebar { display: none; }
}
@media (max-width: 820px) {
  .agent-head { padding: 16px 20px; }
  .agent-head p,
  .knowledge-state,
  .mode-actions > span { display: none; }
  .config-warning { padding-right: 20px; padding-left: 20px; }
  .mode-inner { width: calc(100% - 32px); }
  .conversation { padding-right: 16px; padding-left: 16px; }
  .suggestions { grid-template-columns: 1fr; }
  .welcome { padding-top: 25px; }
  .message-row.user .message-content { max-width: 88%; }
  .composer { padding-right: 12px; padding-left: 12px; }
}
</style>
