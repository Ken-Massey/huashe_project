<template>
  <div class="patrol-mobile" :class="{ 'has-action': !showLogin && view !== 'list' && canWrite }">
    <header class="topbar">
      <router-link v-if="showLogin" to="/login" class="nav-button">管理平台</router-link>
      <button v-else-if="view !== 'list'" class="nav-button" type="button" :disabled="busy || selectingFiles" @click="goBack"><span aria-hidden="true">‹</span> 返回</button>
      <span v-else class="nav-spacer"></span>
      <h1 class="nav-title">{{ pageTitle }}</h1>
      <button v-if="!showLogin && view === 'list'" class="nav-button" type="button" :disabled="busy" @click="logout">退出</button>
      <button v-else-if="!showLogin && view === 'detail'" class="nav-button" type="button" :disabled="busy" @click="loadTask($route.query.task)">刷新</button>
      <span v-else class="nav-spacer"></span>
    </header>

    <main v-if="showLogin" class="body login-body">
      <section class="card login-card">
        <div class="login-badge" aria-hidden="true"><svg viewBox="0 0 32 32"><rect x="7" y="4" width="18" height="22" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 14h16M11 29l3-4m7 4-3-4" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="20" r="1.5" fill="currentColor"/><circle cx="20" cy="20" r="1.5" fill="currentColor"/></svg></div>
        <div class="eyebrow">现场符合性巡查</div>
        <h1>华设轨道智审</h1>
        <p class="muted login-subtitle">使用巡查账号，查看指派任务并上报现场情况</p>
        <form @submit.prevent="login">
          <fieldset :disabled="loginLoading">
            <label>账号<input v-model="credentials.username" autocomplete="username" placeholder="请输入巡查账号" required @input="loginError = ''"></label>
            <label>密码<span class="password-field"><input v-model="credentials.password" :type="showPassword ? 'text' : 'password'" autocomplete="current-password" placeholder="请输入密码" required @input="loginError = ''"><button type="button" class="password-toggle" :aria-label="showPassword ? '隐藏密码' : '显示密码'" @click="showPassword = !showPassword">{{ showPassword ? '隐藏' : '显示' }}</button></span></label>
            <p v-if="loginError" class="form-error" role="alert">{{ loginError }}</p>
            <button class="primary full login-submit" type="submit" :disabled="loginLoading">{{ loginLoading ? '登录中…' : '登录巡查端' }}</button>
          </fieldset>
        </form>
        <p class="login-footnote">任务查看 · 巡查上报 · 隐患整改 · 现场核查</p>
      </section>
    </main>

    <main v-else class="body">
      <template v-if="view === 'list'">
        <section class="welcome">
          <div class="eyebrow">我的现场任务</div>
          <h2>你好，{{ username || '巡查员' }}</h2>
          <p>及时完成指派任务，上报现场情况</p>
          <div class="stats">
            <div><strong>{{ activeCount }}</strong><span>待办任务</span></div>
            <div><strong>{{ doneCount }}</strong><span>已完成</span></div>
            <div><strong>{{ openHazards }}</strong><span>未闭环隐患</span></div>
          </div>
        </section>
        <div class="section-head">
          <h2>指派任务 <span class="count">{{ total }}</span></h2>
          <button class="text-button" type="button" :disabled="busy" @click="loadTasks(true)">刷新任务</button>
        </div>
        <p v-if="tasks.length < total" class="small muted list-note">统计基于已加载的 {{ tasks.length }} 个任务</p>
        <div v-if="taskListError" class="notice error-notice" role="alert"><strong>任务加载失败</strong><p>{{ taskListError }}</p><button class="link" type="button" :disabled="busy" @click="loadTasks(true)">重新加载</button></div>
        <template v-if="busy && !tasks.length"><div v-for="n in 3" :key="n" class="card skeleton-card" aria-hidden="true"><div class="skeleton"></div><div class="skeleton wide"></div><div class="skeleton"></div></div></template>
        <div v-else-if="!tasks.length && !taskListError" class="card empty"><span class="empty-symbol" aria-hidden="true">✓</span><h3>暂无指派任务</h3><p>有新任务时会显示在这里</p></div>
        <button v-for="item in tasks" :key="item.task_id" class="card task-card" :class="item.status" type="button" :disabled="busy" @click="navigate('detail', item.task_id)">
          <div class="between"><span class="mono">{{ item.task_no }}</span><div><span v-if="overdue(item)" class="pill pending">待处理</span><span class="pill" :class="item.status">{{ taskStatus(item.status) }}</span></div></div>
          <h3>{{ item.name || '巡查任务' }}</h3>
          <p class="task-location">{{ item.line || '未填线路' }}<span v-if="item.location_desc"> · {{ item.location_desc }}</span></p>
          <div class="task-chips"><span>共 {{ item.hazard_count || 0 }} 隐患</span><span v-if="item.open_hazard_count" class="warn">剩 {{ item.open_hazard_count }} 未闭环</span><span>{{ item.record_count || 0 }} 记录</span></div>
          <div class="between small muted"><span>{{ dispatch(item.created_at || item.dispatch_time) }}</span><span class="task-arrow" aria-hidden="true">›</span></div>
        </button>
        <button v-if="tasks.length < total" class="secondary full" type="button" :disabled="busy" @click="loadTasks(false)">{{ busy ? '加载中…' : '加载更多任务' }}</button>
      </template>

      <template v-else-if="view === 'detail'">
        <div v-if="!task" class="card empty">
          <h3>{{ busy ? '正在加载任务…' : '任务加载失败' }}</h3>
          <p v-if="taskError">{{ taskError }}</p>
          <button v-if="!busy" class="secondary" type="button" @click="loadTask($route.query.task)">重新加载</button>
        </div>
        <template v-else>
          <section class="card task-info">
            <div class="between"><span class="mono">{{ task.task_no }}</span><div><span v-if="task.task_type === 'pre_construction'" class="pill">施工前核查</span><span class="pill" :class="task.status">{{ taskStatus(task.status) }}</span></div></div>
            <h2 class="detail-title">{{ task.name }}</h2>
            <p class="meta"><b>线路</b>{{ task.line || '—' }}</p><p class="meta"><b>位置</b>{{ task.location_desc || '—' }}</p><p class="meta"><b>派发人</b>{{ task.dispatcher || '—' }}</p>
          </section>
          <section v-if="task.requirement" class="card accent-card"><h2>巡查要求</h2><p class="preserve">{{ task.requirement }}</p></section>
          <section v-if="task.review_opinion || (task.docs || []).length" class="card">
            <h2>监测方案</h2>
            <template v-if="task.review_opinion"><p class="small muted">监测审查意见</p><p class="preserve">{{ task.review_opinion }}</p></template>
            <div v-for="doc in task.docs || []" :key="doc.doc_id" class="doc-row"><span>{{ doc.file_name }}</span><button class="link" type="button" @click="openDoc(doc, false)">查看</button><button class="link" type="button" @click="openDoc(doc, true)">下载</button></div>
          </section>
          <section v-if="(task.opinions || []).length" class="card">
            <button class="collapse-trigger" type="button" :aria-expanded="opinionsOpen" @click="opinionsOpen = !opinionsOpen">
              <span><strong>审核意见现场核查 <span class="count">{{ task.opinions.length }}</span></strong><span class="summary-counts">完成 {{ opinionSummary.done }} · 待核查 {{ opinionSummary.photo_taken }} · 待拍照 {{ opinionSummary.pending_photo }}<span v-if="opinionSummary.returned"> · 退回 {{ opinionSummary.returned }}</span></span></span>
              <span class="collapse-label">{{ opinionsOpen ? '收起 ▴' : '展开 ▾' }}</span>
            </button>
            <p v-if="opinionSummary.lastTime" class="small muted">更新 {{ fmt(opinionSummary.lastTime) }}</p>
            <template v-if="opinionsOpen">
              <article v-for="op in task.opinions" :key="op.opinion_id" class="opinion">
                <div class="between"><strong>{{ op.title || '审核意见' }}</strong><span class="pill" :class="op.status">{{ opinionStatus(op.status) }}</span></div>
                <p class="small muted">{{ op.stage_name || '' }} {{ fmt(op.check_time || op.created_at) }}</p>
                <p class="preserve">{{ op.opinion_content }}</p>
                <p v-if="op.return_reason" class="notice">退回原因：{{ op.return_reason }}</p>
                <p v-if="op.check_opinion" class="notice">核查意见：{{ op.check_opinion }}</p>
                <div v-if="(op.photos || []).length" class="media-grid">
                  <div v-for="photo in op.photos || []" :key="photo.photo_id" class="media-cell">
                    <button class="preview-thumb" type="button" aria-label="查看现场照片" @click="previewAsset('op:'+photo.photo_id, 'image')"><img v-if="assets['op:'+photo.photo_id]" :src="assets['op:'+photo.photo_id]" alt="现场照片"><span v-else class="media-placeholder">照片</span></button>
                    <button v-if="op.status !== 'done'" class="remove" type="button" aria-label="删除现场照片" :disabled="busy" @click="deleteOpinionPhoto(photo.photo_id)">×</button>
                  </div>
                </div>
                <div v-if="op.status !== 'done'" class="action-row"><button class="secondary" type="button" :disabled="busy" @click="openPicker('opinion', op.opinion_id)">＋上传照片</button><button v-if="op.status === 'pending_photo' || op.status === 'returned'" class="secondary" type="button" :disabled="busy" @click="submitOpinion(op)">提交核查</button></div>
              </article>
            </template>
          </section>
          <section class="card">
            <div class="section-head"><h2>巡查时间线</h2><button v-if="canWrite" class="link" type="button" :disabled="busy" @click="navigate('hazard', task.task_id)">＋添加隐患</button></div>
            <p v-if="!timeline.length" class="muted">暂无巡查记录</p>
            <div v-for="group in timelineGroups" :key="group.key" class="date-group">
              <h3 class="date-heading" :class="{ today: group.label === '今天' }">{{ group.label }}</h3>
              <article v-for="entry in group.entries" :key="entry.key" class="timeline-item">
                <div class="timeline-head"><span class="pill" :class="entry.kind">{{ entry.kind === 'record' ? (entry.data.type === 'rectify' ? '整改反馈' : '日常巡查') : '风险隐患' }}</span><span v-if="entry.data.batchNo" class="batch-chip">第{{ entry.data.batchNo }}批</span><strong v-if="entry.data.title">{{ entry.data.title }}</strong></div>
                <p class="small muted">{{ entry.data.created_by_name || '—' }} · {{ fmt(entry.time) }}</p>
                <p v-if="entry.kind === 'record' && entry.data.note" class="preserve">{{ entry.data.note }}</p>
                <div v-if="entry.kind === 'record' && (entry.data.media || []).length" class="media-grid">
                  <button v-for="media in entry.data.media || []" :key="media.media_id" class="media-cell preview-thumb" type="button" :aria-label="media.kind === 'video' ? '播放巡查视频' : '查看巡查照片'" @click="previewAsset('media:'+media.media_id, media.kind)"><img v-if="media.kind === 'photo' && assets['media:'+media.media_id]" :src="assets['media:'+media.media_id]" alt="巡查照片"><span v-else class="media-placeholder">{{ media.kind === 'video' ? '▶ 视频' : '照片' }}</span></button>
                </div>
                <div v-if="entry.kind === 'record' && entry.data.type === 'patrol' && canWrite" class="action-row"><button class="link" type="button" :disabled="busy" @click="navigate('hazard', task.task_id, { record: entry.data.record_id })">＋添加隐患</button></div>
                <div v-for="hazard in entry.hazards" :key="hazard.hazard_id" class="hazard" :class="{ closed: hazard.status === 'closed' }">
                  <button class="hazard-summary" type="button" :aria-expanded="!!expandedHazards[hazard.hazard_id]" @click="toggleHazard(hazard.hazard_id)">
                    <span><span class="hazard-tags"><span class="pill" :class="hazard.status">{{ hazardStatus(hazard.status) }}</span><span v-if="hazard.hazard_type" class="pill">{{ hazard.hazard_type }}</span><span v-if="hazard.risk_level" class="pill risk">{{ hazard.risk_level }}</span><span v-if="hazard.rectifyRecords.length" class="pill">整改{{ hazard.rectifyRecords.length }}次</span></span><span class="hazard-short">{{ hazard.descShort }}</span></span>
                    <span class="collapse-label">{{ expandedHazards[hazard.hazard_id] ? '收起 ▴' : '详情 ▾' }}</span>
                  </button>
                  <div v-if="expandedHazards[hazard.hazard_id]" class="hazard-detail">
                    <div class="steps"><span v-for="(step, i) in hazardSteps" :key="step" :class="{ reached: i <= hazardSteps.indexOf(hazard.status), current: step === hazard.status }">{{ hazardStatus(step) }}</span></div>
                    <p v-if="hazard.description !== hazard.descShort" class="preserve">{{ hazard.description }}</p>
                    <p v-if="hazard.rectify_requirement" class="notice">整改要求：{{ hazard.rectify_requirement }}</p>
                    <p v-if="hazard.rectify_owner" class="muted small">整改责任人：{{ hazard.rectify_owner }}</p>
                    <div v-if="(hazard.shots || []).length" class="media-grid"><button v-for="shot in hazard.shots || []" :key="shot.shot_id" class="media-cell preview-thumb" type="button" aria-label="查看隐患截图" @click="previewAsset('shot:'+shot.shot_id, 'image')"><img v-if="assets['shot:'+shot.shot_id]" :src="assets['shot:'+shot.shot_id]" alt="隐患截图"><span v-else class="media-placeholder">截图</span></button></div>
                    <div v-for="record in hazard.rectifyRecords" :key="record.record_id" class="rectify">
                      <b>整改记录 · {{ fmt(record.created_at) }}</b><p class="small muted">{{ record.created_by_name || '—' }}</p><p v-if="record.note" class="preserve">{{ record.note }}</p>
                      <div v-if="(record.media || []).length" class="media-grid"><button v-for="media in record.media || []" :key="media.media_id" class="media-cell preview-thumb" type="button" aria-label="查看整改证据" @click="previewAsset('media:'+media.media_id, media.kind)"><img v-if="media.kind === 'photo' && assets['media:'+media.media_id]" :src="assets['media:'+media.media_id]" alt="整改照片"><span v-else class="media-placeholder">{{ media.kind === 'video' ? '▶ 视频' : '照片' }}</span></button></div>
                    </div>
                    <p v-if="hazard.review_comment" class="notice">复核意见：{{ hazard.review_comment }}</p>
                  </div>
                  <div v-if="canWrite" class="action-row hazard-actions"><button v-if="hazard.status === 'pending_rectify' || hazard.status === 'rectifying'" class="secondary" type="button" :disabled="busy" @click="startQuickRectify(hazard)">整改图片上传</button><button v-if="hazard.status === 'rectifying'" class="secondary" type="button" :disabled="busy" @click="submitReview(hazard)">整改完成</button><button v-if="hazard.status === 'pending_confirm'" class="link" type="button" :disabled="busy" @click="navigate('hazard', task.task_id, { hazard: hazard.hazard_id })">修改</button><button v-if="hazard.status === 'pending_confirm'" class="link danger" type="button" :disabled="busy" @click="deleteHazard(hazard)">删除</button></div>
                </div>
              </article>
            </div>
          </section>
          <p v-if="!canWrite" class="notice readonly-notice">任务{{ taskStatus(task.status) }}，可查看巡查记录和附件。</p>
          <div v-if="canWrite" class="bottom-action"><button class="primary full" type="button" :disabled="busy" @click="navigate('upload', task.task_id)">上传照片/视频</button></div>
        </template>
      </template>

      <template v-else-if="view === 'upload' && task">
        <p class="context-label">{{ task.name }}</p>
        <section class="card form-card">
          <fieldset :disabled="busy || selectingFiles">
            <label>上报类型<select v-model="upload.type"><option value="patrol">日常巡查</option><option value="rectify">整改反馈</option></select></label>
            <label v-if="upload.type === 'rectify'"><span class="required">*</span>关联隐患<select v-model="upload.hazardId"><option value="">请选择待整改隐患</option><option v-for="h in rectifiableHazards" :key="h.hazard_id" :value="h.hazard_id">{{ h.description }}</option></select></label>
            <div class="form-item">
              <div class="location-row"><div><b><span class="required">*</span>现场定位</b><p class="small" :class="{ 'form-error': locationError, muted: !locationError }">{{ locating ? '正在定位…' : locationError || locationText }}</p></div><button class="secondary" type="button" :disabled="locating" @click="getLocation">{{ locating ? '定位中…' : location ? '重新定位' : '获取定位' }}</button></div>
              <p v-if="!windowSecure" class="notice">当前地址无法获取定位，请使用 HTTPS 地址访问。</p>
            </div>
            <div class="form-item">
              <h2 class="field-title"><span class="required">*</span>照片/视频 <span class="count">{{ upload.media.length }}</span></h2>
              <p class="small muted">最多 9 张照片、2 段视频；单张 20 MB、视频 50 MB / 60 秒。</p>
              <div class="media-grid">
                <div v-for="(item, i) in upload.media" :key="item.url" class="media-cell"><button class="preview-thumb" type="button" aria-label="预览待上传文件" @click="previewLocal(item)"><img v-if="item.kind === 'photo'" :src="item.url" alt="待上传照片"><span v-else class="media-placeholder">▶ 视频</span></button><button class="remove" type="button" :aria-label="'删除第'+(i+1)+'个文件'" @click="removeLocal('media', i)">×</button><span class="media-index">第{{ i + 1 }}个</span></div>
                <button class="media-cell media-add" type="button" @click="openPicker('media')"><span class="add-plus">＋</span><span>拍照/录视频</span></button>
              </div>
            </div>
            <template v-if="upload.type === 'patrol'">
              <label class="check form-item"><span>本次巡查是否有隐患</span><input v-model="upload.hasHazard" class="switch" type="checkbox"></label>
              <div v-if="upload.hasHazard" class="hazard-fields">
                <label><span class="required">*</span>隐患描述<textarea v-model="upload.hazardDesc" maxlength="2000" rows="4" placeholder="违规施工、超范围施工等现场情况"></textarea></label>
                <label>隐患类型<select v-model="upload.hazardType"><option value="">请选择类型（选填）</option><option v-for="item in hazardTypes" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
                <label>风险等级<select v-model="upload.riskLevel"><option value="">请选择等级（选填）</option><option v-for="item in risks" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
                <div class="form-item"><h2 class="field-title">隐患截图 <span class="small muted">圈注图片，选填</span></h2><div class="media-grid"><div v-for="(item, i) in upload.shots" :key="item.url" class="media-cell"><button class="preview-thumb" type="button" aria-label="预览隐患截图" @click="previewLocal(item)"><img :src="item.url" alt="待上传截图"></button><button class="remove" type="button" aria-label="删除截图" @click="removeLocal('uploadShots', i)">×</button></div><button v-if="upload.shots.length < 9" class="media-cell media-add" type="button" @click="openPicker('uploadShots')"><span class="add-plus">＋</span><span>添加截图</span></button></div></div>
              </div>
            </template>
            <label>本次上传名称 <span class="small muted">选填</span><input v-model.trim="upload.title" maxlength="120" placeholder="如：第2次现场巡查-K10+499核查"></label>
            <label>备注<textarea v-model="upload.note" maxlength="1000" rows="3" placeholder="现场情况说明（选填）"></textarea></label>
          </fieldset>
        </section>
        <div class="bottom-action"><button class="primary full" type="button" :disabled="busy || selectingFiles" @click="submitUpload">{{ busy ? '上报中…' : selectingFiles ? '正在处理照片…' : '提交上报' }}</button></div>
      </template>

      <template v-else-if="view === 'hazard' && task">
        <p class="context-label">{{ task.name }}<span v-if="hazardForm.recordId"> · 关联巡查记录</span></p>
        <section class="card form-card"><fieldset :disabled="busy || selectingFiles">
          <label><span class="required">*</span>隐患描述<textarea v-model="hazardForm.description" maxlength="2000" rows="5" placeholder="请描述现场隐患"></textarea></label>
          <label>隐患类型<select v-model="hazardForm.hazardType"><option value="">请选择类型（选填）</option><option v-for="item in hazardTypes" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label>风险等级<select v-model="hazardForm.riskLevel"><option value="">请选择等级（选填）</option><option v-for="item in risks" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
          <label v-if="!hazardForm.id">整改责任人<input v-model.trim="hazardForm.rectifyOwner" maxlength="120" placeholder="选填"></label>
          <div class="form-item"><h2 class="field-title">隐患截图 <span class="small muted">选填</span></h2><div class="media-grid"><button v-for="shot in existingHazardShots" :key="shot.shot_id" class="media-cell preview-thumb" type="button" aria-label="查看原有隐患截图" @click="previewAsset('shot:'+shot.shot_id, 'image')"><img v-if="assets['shot:'+shot.shot_id]" :src="assets['shot:'+shot.shot_id]" alt="原有隐患截图"><span v-else class="media-placeholder">原有截图</span></button><div v-for="(item, i) in hazardForm.shots" :key="item.url" class="media-cell"><button class="preview-thumb" type="button" aria-label="预览新截图" @click="previewLocal(item)"><img :src="item.url" alt="待上传截图"></button><button class="remove" type="button" aria-label="删除新截图" @click="removeLocal('hazardShots', i)">×</button></div><button v-if="existingHazardShots.length + hazardForm.shots.length < 9" class="media-cell media-add" type="button" @click="openPicker('hazardShots')"><span class="add-plus">＋</span><span>添加截图</span></button></div><p v-if="hazardForm.id" class="small muted">原有截图保留，新选照片追加。</p></div>
        </fieldset></section>
        <div class="bottom-action"><button class="primary full" type="button" :disabled="busy || selectingFiles" @click="submitHazard">{{ busy ? '保存中…' : '保存隐患' }}</button></div>
      </template>
      <div v-else class="card empty"><h3>{{ busy ? '正在加载任务…' : '任务加载失败' }}</h3><p v-if="taskError">{{ taskError }}</p><button v-if="!busy" class="secondary" type="button" @click="routeChanged">重新加载</button></div>
    </main>

    <input ref="photoInput" class="file-input" type="file" accept="image/*" multiple @change="onFiles($event, 'photo')">
    <input ref="cameraInput" class="file-input" type="file" accept="image/*" capture="environment" @change="onFiles($event, 'photo')">
    <input ref="videoInput" class="file-input" type="file" accept="video/mp4,video/quicktime,video/*" multiple @change="onFiles($event, 'video')">
    <input ref="videoCameraInput" class="file-input" type="file" accept="video/*" capture="environment" @change="onFiles($event, 'video')">

    <div v-if="preview" class="preview" role="dialog" aria-modal="true" aria-label="附件预览" @click.self="closePreview"><button type="button" class="preview-close" aria-label="关闭预览" @click="closePreview">×</button><img v-if="preview.kind !== 'video'" :src="preview.url" alt="照片预览"><video v-else :src="preview.url" controls playsinline autoplay></video></div>
    <div v-if="quick.visible" class="dialog-mask" @click.self="closeQuick">
      <section class="dialog card" role="dialog" aria-modal="true" aria-labelledby="rectify-title">
        <div class="between"><h2 id="rectify-title">整改图片上传</h2><span class="small muted">{{ quick.files.length }} 张新照片</span></div>
        <p class="small muted">确认现场照片后填写整改备注；上传后仍需点击“整改完成”。</p>
        <div class="media-grid"><div v-for="(item, i) in quick.files" :key="item.url" class="media-cell"><button class="preview-thumb" type="button" aria-label="预览整改照片" @click="previewLocal(item)"><img :src="item.url" alt="待上传整改照片"></button><button class="remove" type="button" aria-label="删除整改照片" :disabled="busy" @click="removeLocal('quick', i)">×</button></div><button v-if="quick.files.length + quick.existingPhotos < 9" class="media-cell media-add" type="button" :disabled="busy || selectingFiles" @click="openPicker('quick')"><span class="add-plus">＋</span><span>添加照片</span></button></div>
        <label>整改备注 <span class="small muted">选填，默认继承上次</span><textarea v-model="quick.note" rows="3" maxlength="1000" :disabled="busy" placeholder="整改情况说明"></textarea></label>
        <div class="dialog-actions"><button class="secondary" type="button" :disabled="busy" @click="closeQuick">取消</button><button class="primary" type="button" :disabled="busy || selectingFiles || !quick.files.length" @click="submitQuick">{{ busy ? '上传中…' : '确认上传' }}</button></div>
      </section>
    </div>
    <div v-if="sourcePicker" class="picker-mask" @click.self="sourcePicker = null">
      <section class="source-sheet" role="dialog" aria-modal="true" aria-labelledby="source-title">
        <div class="sheet-handle" aria-hidden="true"></div><h2 id="source-title">{{ sourcePicker.scope === 'media' ? '添加照片/视频' : '添加现场照片' }}</h2>
        <div class="source-options">
          <button type="button" @click="selectSource('camera')"><span class="source-icon" aria-hidden="true">◎</span><strong>拍照</strong><small>使用后置摄像头</small></button>
          <button type="button" @click="selectSource('photo')"><span class="source-icon" aria-hidden="true">▧</span><strong>从相册选择</strong><small>支持多张照片</small></button>
          <template v-if="sourcePicker.scope === 'media'"><button type="button" @click="selectSource('videoCamera')"><span class="source-icon" aria-hidden="true">▷</span><strong>录视频</strong><small>最长 60 秒</small></button><button type="button" @click="selectSource('video')"><span class="source-icon" aria-hidden="true">▹</span><strong>选择视频</strong><small>MP4 / MOV</small></button></template>
        </div>
        <button class="sheet-cancel" type="button" @click="sourcePicker = null">取消</button>
      </section>
    </div>
    <div v-if="busy && progressLabel" class="progress-mask" role="dialog" aria-modal="true" aria-label="正在上传"><div class="progress-card"><strong>{{ progressLabel }}</strong><progress :value="progress" max="100"></progress><span>{{ progress }}%</span><p class="small muted">请保持页面开启</p></div></div>
    <div v-if="toast" class="toast" role="status">{{ toast }}</div>
  </div>
</template>

<script>
import { clearMobileSession, getMobileToken, getMobileUser, mobileBlob, mobileDelete, mobileGet, mobileLogin, mobilePost, mobileUpload, saveMobileSession } from './api'
import { locate } from './geo'
import { buildPatrolTimeline, dispatchTime, groupTimeline, isOverdue, summarizeOpinions } from './flow'

const TASK_STATUS = { pending: '待执行', executing: '执行中', completed: '已完成', closed: '已关闭' }
const HAZARD_STATUS = { pending_confirm: '待确认', pending_rectify: '待整改', rectifying: '整改中', pending_review: '待复核', closed: '已闭环' }
const OPINION_STATUS = { pending_photo: '待拍照', photo_taken: '已拍照·待核查', done: '已完成', returned: '退回重拍' }
const HAZARD_STEPS = ['pending_confirm', 'pending_rectify', 'rectifying', 'pending_review', 'closed']
const PHOTO_LIMIT = 20 * 1024 * 1024
const VIDEO_LIMIT = 50 * 1024 * 1024
const nowText = () => { const d = new Date(); const pad = n => String(n).padStart(2, '0'); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}` }
const parseTime = value => new Date(String(value || '').replace(' ', 'T')).getTime() || 0
const newUpload = () => ({ type: 'patrol', hazardId: '', title: '', note: '', media: [], hasHazard: false, hazardDesc: '', hazardType: '', riskLevel: '', shots: [] })
const newHazard = () => ({ id: '', recordId: '', description: '', hazardType: '', riskLevel: '', rectifyOwner: '', shots: [] })

export default {
  name: 'PatrolMobile',
  data() {
    return {
      credentials: { username: '', password: '' }, loggedIn: !!getMobileToken(), username: getMobileUser(),
      loginLoading: false, loginError: '', showPassword: false,
      tasks: [], total: 0, page: 1, task: null, timeline: [], taskListError: '', taskError: '',
      assets: {}, urls: [], assetGeneration: 0, loadSequence: 0, busy: false,
      locating: false, location: null, locationError: '', selectingFiles: false,
      toast: '', toastTimer: null, progress: 0, progressLabel: '',
      upload: newUpload(), hazardForm: newHazard(), hazardTypes: [], risks: [],
      opinionsOpen: false, expandedHazards: {}, preview: null, picker: null, sourcePicker: null,
      quick: { visible: false, hazardId: '', recordId: '', existingPhotos: 0, note: '', files: [] },
      hazardSteps: HAZARD_STEPS
    }
  },
  computed: {
    view() { const view = this.$route.query.view; return ['list', 'login', 'detail', 'upload', 'hazard'].includes(view) ? view : 'list' },
    showLogin() { return !this.loggedIn || this.view === 'login' },
    pageTitle() { return this.showLogin ? '巡查端' : ({ list: '我的任务', detail: '任务详情', upload: '上报', hazard: this.hazardForm.id ? '修改隐患' : '添加隐患' })[this.view] },
    doneCount() { return this.tasks.filter(t => ['completed', 'closed'].includes(t.status)).length },
    timelineGroups() { return groupTimeline(this.timeline) },
    opinionSummary() { return summarizeOpinions(this.task && this.task.opinions) },
    existingHazardShots() { const hazard = (this.task && this.task.hazards || []).find(h => String(h.hazard_id) === String(this.hazardForm.id)); return hazard && hazard.shots || [] },
    windowSecure() { return window.isSecureContext },
    canWrite() { return this.task && ['pending', 'executing'].includes(this.task.status) },
    activeCount() { return this.tasks.filter(t => ['pending', 'executing'].includes(t.status)).length },
    openHazards() { return this.tasks.reduce((sum, t) => sum + Number(t.open_hazard_count || 0), 0) },
    rectifiableHazards() { return (this.task && this.task.hazards || []).filter(h => ['pending_rectify', 'rectifying'].includes(h.status)) },
    locationText() { return this.location ? `${this.location.latitude.toFixed(6)}, ${this.location.longitude.toFixed(6)} · 精度约 ${Math.round(this.location.accuracy)} 米` : '尚未获取定位' }
  },
  watch: {
    '$route.query': {
      handler(to, from) {
        this.sourcePicker = null
        this.picker = null
        this.closePreview()
        this.releaseLocal(this.quick.files); this.quick.visible = false; this.quick.files = []
        if (from && from.view === 'upload' && to.view !== 'upload') {
          this.releaseLocal(this.upload.media); this.releaseLocal(this.upload.shots); this.upload = newUpload()
        }
        if (from && from.view === 'hazard' && to.view !== 'hazard') {
          this.releaseLocal(this.hazardForm.shots); this.hazardForm = newHazard()
        }
        if (this.loggedIn && !this.loginLoading && to.view !== 'login') this.routeChanged()
      },
      deep: true
    }
  },
  created() { window.addEventListener('patrol-mobile-unauthorized', this.unauthorized); if (!this.showLogin) this.bootstrap() },
  beforeDestroy() { window.removeEventListener('patrol-mobile-unauthorized', this.unauthorized); this.revokeAssets(); this.releaseLocal(this.upload.media); this.releaseLocal(this.upload.shots); this.releaseLocal(this.hazardForm.shots); this.releaseLocal(this.quick.files); clearTimeout(this.toastTimer) },
  methods: {
    taskStatus: value => TASK_STATUS[value] || value || '—', hazardStatus: value => HAZARD_STATUS[value] || value || '—', opinionStatus: value => OPINION_STATUS[value] || value || '—',
    dispatch: dispatchTime,
    overdue: isOverdue,
    fmt(value) { return value ? String(value).replace('T', ' ').slice(0, 16) : '—' },
    flash(message) { this.toast = message; clearTimeout(this.toastTimer); this.toastTimer = setTimeout(() => { this.toast = '' }, message.length > 35 ? 7000 : 3600) },
    fail(error) { this.flash(error && error.message || '操作失败') },
    async login() {
      if (this.loginLoading) return
      const username = this.credentials.username.trim()
      if (!username || !this.credentials.password) { this.loginError = '请输入账号和密码'; return }
      this.loginLoading = true
      this.loginError = ''
      try {
        const result = await mobileLogin(username, this.credentials.password)
        if (!result.token) throw new Error('登录未返回令牌')
        saveMobileSession(result.token, username)
        this.username = username
        this.loggedIn = true
        this.credentials.password = ''
        await this.$router.replace({ path: '/rail/patrol-mobile' }).catch(() => {})
        await this.bootstrap()
      } catch (error) {
        this.loginError = error && error.message || '登录失败，请稍后重试'
      } finally { this.loginLoading = false }
    },
    logout() { if (!window.confirm('确定退出登录吗？')) return; this.unauthorized() },
    unauthorized() {
      clearMobileSession()
      this.loadSequence++
      this.loggedIn = false; this.task = null; this.tasks = []; this.total = 0; this.timeline = []
      this.revokeAssets()
      this.releaseLocal(this.upload.media); this.releaseLocal(this.upload.shots)
      this.releaseLocal(this.hazardForm.shots); this.releaseLocal(this.quick.files)
      this.upload = newUpload(); this.hazardForm = newHazard()
      this.quick.visible = false; this.quick.files = []; this.sourcePicker = null; this.picker = null; this.preview = null
      this.busy = false; this.progressLabel = ''; this.taskListError = ''; this.taskError = ''
      this.$router.replace({ path: '/rail/patrol-mobile', query: { view: 'login' } }).catch(() => {})
    },
    async bootstrap() { await Promise.all([this.loadDicts(), this.routeChanged()]) },
    navigate(view, taskId, extra = {}, replace = false) {
      const query = view === 'list' ? {} : { view, task: taskId, ...extra }
      return this.$router[replace ? 'replace' : 'push']({ path: '/rail/patrol-mobile', query }).catch(() => {})
    },
    goBack() { if (this.busy || this.selectingFiles) return; this.navigate(this.view === 'detail' ? 'list' : 'detail', this.$route.query.task, {}, true) },
    async routeChanged() {
      if (this.showLogin) return
      const taskId = this.$route.query.task
      if (this.view === 'list') { await this.loadTasks(true); return }
      if (!taskId) { this.navigate('list', null, {}, true); return }
      if (!this.task || String(this.task.task_id) !== String(taskId) || this.view === 'detail') await this.loadTask(taskId)
      if (!this.task || String(this.task.task_id) !== String(taskId)) return
      if (['upload', 'hazard'].includes(this.view) && !this.canWrite) {
        this.flash('该任务已结束，仅可查看记录')
        this.navigate('detail', taskId, {}, true); return
      }
      if (this.view === 'upload') {
        this.releaseLocal(this.upload.media); this.releaseLocal(this.upload.shots)
        this.upload = newUpload(); this.location = null; this.locationError = ''
      }
      if (this.view === 'hazard') {
        this.releaseLocal(this.hazardForm.shots); this.hazardForm = newHazard()
        const id = this.$route.query.hazard
        if (id) {
          const hazard = (this.task.hazards || []).find(item => String(item.hazard_id) === String(id))
          if (!hazard || hazard.status !== 'pending_confirm') {
            this.flash('该隐患当前不可修改'); this.navigate('detail', taskId, {}, true); return
          }
          this.hazardForm = { id: hazard.hazard_id, recordId: hazard.record_id || '', description: hazard.description || '', hazardType: hazard.hazard_type || '', riskLevel: hazard.risk_level || '', rectifyOwner: hazard.rectify_owner || '', shots: [] }
        } else this.hazardForm.recordId = this.$route.query.record || ''
      }
    },
    async loadTasks(reset) {
      if (this.busy && !reset) return
      const sequence = ++this.loadSequence
      this.busy = true; this.taskListError = ''; this.progressLabel = ''
      try {
        const page = reset ? 1 : this.page + 1
        const result = await mobileGet('/rail/patrol/tasks', { page, size: 30 })
        if (sequence !== this.loadSequence) return
        this.tasks = reset ? (result.items || []) : this.tasks.concat(result.items || [])
        this.total = Number(result.total == null ? this.tasks.length : result.total); this.page = page
      } catch (error) {
        if (sequence === this.loadSequence) this.taskListError = error && error.message || '请检查网络后重试'
      } finally { if (sequence === this.loadSequence) this.busy = false }
    },
    async loadDicts() { try { const [types, risks] = await Promise.all([mobileGet('/rail/patrol/dicts', { dictType: 'hazard_type' }), mobileGet('/rail/patrol/dicts', { dictType: 'hazard_risk' })]); this.hazardTypes = types || []; this.risks = risks || [] } catch (error) { this.fail(error) } },
    async loadTask(id) {
      const sequence = ++this.loadSequence
      this.busy = true; this.taskError = ''; this.progressLabel = ''
      try {
        const task = await mobileGet(`/rail/patrol/tasks/${encodeURIComponent(id)}`)
        if (sequence !== this.loadSequence) return
        const differentTask = !this.task || this.task.task_id !== task.task_id
        this.task = task; this.buildTimeline(task); this.revokeAssets()
        if (differentTask) { this.opinionsOpen = false; this.expandedHazards = {} }
        const jobs = []
        ;(task.records || []).forEach(r => (r.media || []).filter(m => m.kind === 'photo').forEach(m => jobs.push([`media:${m.media_id}`, `/rail/patrol/media/${m.media_id}/file`])))
        ;(task.hazards || []).forEach(h => (h.shots || []).forEach(s => jobs.push([`shot:${s.shot_id}`, `/rail/patrol/shots/${s.shot_id}/file`])))
        ;(task.opinions || []).forEach(o => (o.photos || []).forEach(p => jobs.push([`op:${p.photo_id}`, `/rail/patrol/opinion-photos/${p.photo_id}/file`])))
        this.primeAssets(jobs, this.assetGeneration)
      } catch (error) {
        if (sequence === this.loadSequence) { this.task = null; this.taskError = error && error.message || '请检查网络后重试' }
      } finally { if (sequence === this.loadSequence) this.busy = false }
    },
    buildTimeline(task) { this.timeline = buildPatrolTimeline(task) },
    toggleHazard(id) { this.$set(this.expandedHazards, id, !this.expandedHazards[id]) },
    async primeAssets(jobs, generation) { let next = 0; const worker = async () => { while (next < jobs.length && generation === this.assetGeneration) { const [key, path] = jobs[next++]; await this.fetchAsset(key, path, generation) } }; await Promise.all(Array.from({ length: Math.min(4, jobs.length) }, worker)) },
    async fetchAsset(key, path, generation = this.assetGeneration) { try { const blob = await mobileBlob(path); if (generation !== this.assetGeneration) return; const url = URL.createObjectURL(blob); this.$set(this.assets, key, url); this.urls.push(url) } catch (error) { /* 单张资源失败不影响任务阅读 */ } },
    revokeAssets() { this.assetGeneration++; this.urls.forEach(url => URL.revokeObjectURL(url)); this.urls = []; this.assets = {} },
    async previewAsset(key, kind) { try { if (!this.assets[key]) { const [type, id] = key.split(':'); const path = type === 'media' ? `/rail/patrol/media/${id}/file` : type === 'shot' ? `/rail/patrol/shots/${id}/file` : `/rail/patrol/opinion-photos/${id}/file`; await this.fetchAsset(key, path) } if (this.assets[key]) this.preview = { url: this.assets[key], kind } } catch (error) { this.fail(error) } },
    previewLocal(item) { this.preview = { url: item.url, kind: item.kind } }, closePreview() { this.preview = null },
    async openDoc(doc, download) { const tab = !download && doc.kind !== 'word' ? window.open('', '_blank') : null; try { const blob = await mobileBlob(`/rail/patrol/docs/${doc.doc_id}/file`); const url = URL.createObjectURL(blob); if (download || doc.kind === 'word' || !tab) { const anchor = document.createElement('a'); anchor.href = url; anchor.download = doc.file_name || '监测方案'; document.body.appendChild(anchor); anchor.click(); anchor.remove() } else tab.location.href = url; setTimeout(() => URL.revokeObjectURL(url), 60000) } catch (error) { if (tab) tab.close(); this.fail(error) } },
    async getLocation() {
      if (this.locating) return
      this.locating = true; this.locationError = ''
      try { this.location = await locate(); this.flash('定位成功') }
      catch (error) { this.locationError = error && error.message || '定位失败，请重试' }
      finally { this.locating = false }
    },
    openPicker(scope, id = '') {
      if (this.busy || this.selectingFiles) return
      this.sourcePicker = { scope, id }
    },
    selectSource(kind) {
      if (!this.sourcePicker || this.busy || this.selectingFiles) return
      const { scope, id } = this.sourcePicker
      this.sourcePicker = null
      this.choose(scope, kind, id)
    },
    choose(scope, kind, id = '') {
      this.picker = { scope, id }
      const ref = { camera: 'cameraInput', video: 'videoInput', videoCamera: 'videoCameraInput', photo: 'photoInput' }[kind] || 'photoInput'
      this.$refs[ref].click()
    },
    async onFiles(event, kind) {
      const files = Array.from(event.target.files || [])
      event.target.value = ''
      const picker = this.picker
      this.picker = null
      if (!files.length || !picker || this.busy || this.selectingFiles) return
      const { scope, id } = picker
      if (scope === 'opinion') { await this.uploadOpinionPhotos(id, files); return }
      const target = scope === 'media' ? this.upload.media : scope === 'uploadShots' ? this.upload.shots : scope === 'hazardShots' ? this.hazardForm.shots : this.quick.files
      this.selectingFiles = true
      try {
        for (let file of files) {
          const photo = kind === 'photo'
          const limit = scope === 'media' && !photo ? 2 : 9
          const existing = scope === 'quick' ? this.quick.existingPhotos : scope === 'hazardShots' ? this.existingHazardShots.length : 0
          const count = scope === 'media' ? target.filter(item => item.kind === kind).length : target.length + existing
          if (count >= limit) { this.flash(`每条记录最多 ${limit} ${photo ? '张照片' : '段视频'}`); break }
          try {
            if (photo) file = await this.preparePhoto(file)
            else {
              if (!/\.(mp4|mov)$/i.test(file.name)) throw new Error('仅支持 MP4 或 MOV 视频')
              if (file.size > VIDEO_LIMIT) throw new Error('单段视频不能超过 50 MB')
              if (await this.videoTooLong(file)) throw new Error('视频不能超过 60 秒')
            }
            if (!this.loggedIn) break
            target.push({ file, url: URL.createObjectURL(file), kind })
          } catch (error) { this.fail(error) }
        }
        if (scope === 'quick' && target.length && this.loggedIn) this.quick.visible = true
      } finally { this.selectingFiles = false }
    },
    preparePhoto(file) { if (/\.(jpe?g|png|webp|bmp)$/i.test(file.name) && file.size <= PHOTO_LIMIT) return Promise.resolve(file); return new Promise((resolve, reject) => { const image = new Image(); const url = URL.createObjectURL(file); image.onload = () => { URL.revokeObjectURL(url); const scale = Math.min(1, 2400 / Math.max(image.width, image.height)); const canvas = document.createElement('canvas'); canvas.width = Math.max(1, Math.round(image.width * scale)); canvas.height = Math.max(1, Math.round(image.height * scale)); canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height); canvas.toBlob(blob => { if (!blob || blob.size > PHOTO_LIMIT) return reject(new Error('照片无法压缩到 20 MB 以下')); resolve(new File([blob], file.name.replace(/\.[^.]+$/, '') + '.jpg', { type: 'image/jpeg' })) }, 'image/jpeg', 0.85) }; image.onerror = () => { URL.revokeObjectURL(url); reject(new Error('浏览器不支持此照片格式，请选择 JPG 或 PNG')) }; image.src = url }) },
    videoTooLong(file) { return new Promise(resolve => { const video = document.createElement('video'); const url = URL.createObjectURL(file); let settled = false; const done = tooLong => { if (settled) return; settled = true; clearTimeout(timer); URL.revokeObjectURL(url); resolve(tooLong) }; const timer = setTimeout(() => done(false), 8000); video.preload = 'metadata'; video.onloadedmetadata = () => done(video.duration > 60); video.onerror = () => done(false); video.src = url }) },
    removeLocal(scope, index) { const target = scope === 'media' ? this.upload.media : scope === 'uploadShots' ? this.upload.shots : scope === 'hazardShots' ? this.hazardForm.shots : this.quick.files; const [item] = target.splice(index, 1); if (item) URL.revokeObjectURL(item.url) }, releaseLocal(items) { (items || []).forEach(item => URL.revokeObjectURL(item.url)) },
    setProgress(label, done, total, partial = 0) { this.progressLabel = label; this.progress = Math.round((done + partial / 100) / Math.max(total, 1) * 100) },
    async sendFiles(path, items, fields, start, total) { let done = start; for (const item of items) { this.setProgress(`正在上传 ${done + 1}/${total}`, done, total); await mobileUpload(path, item.file, { ...fields, ...(path.includes('/media') ? { kind: item.kind } : {}) }, p => this.setProgress(`正在上传 ${done + 1}/${total}`, done, total, p)); done++; this.setProgress(`已上传 ${done}/${total}`, done, total) } return done },
    async submitUpload() {
      if (this.busy || this.selectingFiles || !this.canWrite) return
      const form = this.upload
      if (!form.media.length) return this.flash('请先选择照片或视频')
      if (!this.location) return this.flash('请先获取定位')
      if (form.type === 'rectify' && !form.hazardId) return this.flash('请选择关联隐患')
      if (form.type === 'patrol' && form.hasHazard && !form.hazardDesc.trim()) return this.flash('请填写隐患描述')
      this.busy = true; this.progressLabel = ''; this.progress = 0
      let created = false; let success = false
      const taskId = this.task.task_id
      try {
        const record = await mobilePost(`/rail/patrol/tasks/${taskId}/records`, { type: form.type, hazard_id: form.type === 'rectify' ? form.hazardId : '', title: form.title.trim(), note: form.note.trim(), ...this.location })
        created = true
        const total = form.media.length + (form.type === 'patrol' && form.hasHazard ? form.shots.length : 0)
        const done = await this.sendFiles(`/rail/patrol/records/${record.record_id}/media`, form.media, { takenAt: nowText() }, 0, total)
        if (form.type === 'patrol' && form.hasHazard) {
          const hazard = await mobilePost(`/rail/patrol/tasks/${taskId}/hazards`, { record_id: record.record_id, description: form.hazardDesc.trim(), hazard_type: form.hazardType, risk_level: form.riskLevel })
          await this.sendFiles(`/rail/patrol/hazards/${hazard.hazard_id}/shots`, form.shots, {}, done, total)
        }
        success = true; this.flash('上报成功')
      } catch (error) {
        this.flash(`${error.message}${created ? '；部分数据可能已保存，请先返回任务详情核对，避免重复上报。' : ''}`)
      } finally { this.busy = false; this.progressLabel = '' }
      if (success) this.navigate('detail', taskId, {}, true)
    },
    async submitHazard() {
      if (this.busy || this.selectingFiles || !this.canWrite) return
      const form = this.hazardForm
      if (!form.description.trim()) return this.flash('请填写隐患描述')
      this.busy = true; this.progressLabel = ''; this.progress = 0
      let saved = false; let success = false
      const taskId = this.task.task_id
      try {
        const payload = { description: form.description.trim(), hazard_type: form.hazardType, risk_level: form.riskLevel }
        const hazard = form.id
          ? await mobilePost(`/rail/patrol/hazards/${form.id}`, payload)
          : await mobilePost(`/rail/patrol/tasks/${taskId}/hazards`, { ...payload, record_id: form.recordId, rectify_owner: form.rectifyOwner })
        saved = true
        await this.sendFiles(`/rail/patrol/hazards/${hazard.hazard_id}/shots`, form.shots, {}, 0, form.shots.length)
        success = true; this.flash('隐患已保存')
      } catch (error) {
        this.flash(`${error.message}${saved ? '；隐患可能已保存，请先返回任务详情核对。' : ''}`)
      } finally { this.busy = false; this.progressLabel = '' }
      if (success) this.navigate('detail', taskId, {}, true)
    },
    async deleteHazard(hazard) { if (!window.confirm('确认删除该隐患？')) return; try { await mobileDelete(`/rail/patrol/hazards/${hazard.hazard_id}`); this.flash('已删除'); await this.loadTask(this.task.task_id) } catch (error) { this.fail(error) } },
    currentRectifyRecord(hazard) { return (this.task.records || []).filter(r => r.type === 'rectify' && r.hazard_id === hazard.hazard_id && (!hazard.review_time || parseTime(r.created_at) > parseTime(hazard.review_time))).sort((a, b) => parseTime(b.created_at) - parseTime(a.created_at))[0] },
    startQuickRectify(hazard) {
      if (this.busy || this.selectingFiles || !this.canWrite) return
      if (!['pending_rectify', 'rectifying'].includes(hazard.status)) return
      const record = this.currentRectifyRecord(hazard)
      this.releaseLocal(this.quick.files)
      this.quick = { visible: false, hazardId: hazard.hazard_id, recordId: record && record.record_id || '', existingPhotos: record ? (record.media || []).filter(m => m.kind === 'photo').length : 0, note: record && record.note || '', files: [] }
      if (this.quick.existingPhotos >= 9) return this.flash('本轮整改已有 9 张照片，请在详情中核对')
      this.openPicker('quick')
    },
    closeQuick() { if (this.busy || this.selectingFiles) return; this.releaseLocal(this.quick.files); this.quick.visible = false; this.quick.files = [] },
    async submitQuick() {
      if (this.busy || this.selectingFiles || !this.quick.files.length || !this.canWrite) return
      this.busy = true; this.progressLabel = ''; this.progress = 0
      let success = false
      try {
        let id = this.quick.recordId
        if (id) await mobilePost(`/rail/patrol/records/${id}`, { note: this.quick.note.trim() })
        else {
          let position = null
          try { position = await locate() } catch (error) { /* 快速整改允许无坐标，保持小程序规则。 */ }
          const record = await mobilePost(`/rail/patrol/tasks/${this.task.task_id}/records`, {
            type: 'rectify', hazard_id: this.quick.hazardId, note: this.quick.note.trim(),
            longitude: position && position.longitude, latitude: position && position.latitude, accuracy: position && position.accuracy
          })
          id = record.record_id
          this.quick.recordId = id
        }
        const total = this.quick.files.length
        // 成功文件移出待上传队列；重试只续传剩余照片，不另建整改记录。
        for (let i = 0; this.quick.files.length; i++) {
          const item = this.quick.files[0]
          this.setProgress(`正在上传整改照片 ${i + 1}/${total}`, i, total)
          await mobileUpload(`/rail/patrol/records/${id}/media`, item.file, { kind: 'photo', takenAt: nowText() }, p => this.setProgress(`正在上传整改照片 ${i + 1}/${total}`, i, total, p))
          URL.revokeObjectURL(item.url); this.quick.files.shift(); this.quick.existingPhotos++
        }
        success = true; this.quick.visible = false; this.flash('整改照片已上传')
      } catch (error) {
        this.flash(`${error.message}${this.quick.recordId ? '；已上传照片会保留，请核对后继续上传剩余照片。' : ''}`)
      } finally { this.busy = false; this.progressLabel = '' }
      if (success) await this.loadTask(this.task.task_id)
    },
    async submitReview(hazard) { if (!window.confirm('确认整改已完成，提交平台复核？')) return; try { await mobilePost(`/rail/patrol/hazards/${hazard.hazard_id}/submit`); this.flash('已提交复核'); await this.loadTask(this.task.task_id) } catch (error) { this.fail(error) } },
    async uploadOpinionPhotos(id, files) {
      const opinion = (this.task && this.task.opinions || []).find(o => o.opinion_id === id)
      if (this.busy || !opinion || opinion.status === 'done') return
      if ((opinion.photos || []).length + files.length > 9) return this.flash('每条意见最多 9 张照片')
      this.busy = true; this.progressLabel = ''; this.progress = 0
      try {
        for (let i = 0; i < files.length; i++) {
          const file = await this.preparePhoto(files[i])
          this.setProgress(`上传现场照片 ${i + 1}/${files.length}`, i, files.length)
          await mobileUpload(`/rail/patrol/opinions/${id}/photos`, file, { takenAt: nowText() }, p => this.setProgress(`上传现场照片 ${i + 1}/${files.length}`, i, files.length, p))
        }
        this.flash('照片已上传')
      } catch (error) { this.flash(`${error.message}；请核对已保存的照片，避免重复上传。`) }
      finally { this.busy = false; this.progressLabel = '' }
      await this.loadTask(this.task.task_id)
    },
    async deleteOpinionPhoto(id) { if (!window.confirm('确认删除该现场照片？')) return; try { await mobileDelete(`/rail/patrol/opinion-photos/${id}`); this.flash('照片已删除'); await this.loadTask(this.task.task_id) } catch (error) { this.fail(error) } },
    async submitOpinion(opinion) { if (!window.confirm('确认现场照片已拍好并提交平台核查？')) return; try { await mobilePost(`/rail/patrol/opinions/${opinion.opinion_id}/submit`); this.flash('已提交核查'); await this.loadTask(this.task.task_id) } catch (error) { this.fail(error) } }
  }
}
</script>

<style scoped>
.patrol-mobile {
  --primary: #2563eb;
  --ink: #20334d;
  --muted: #738198;
  --line: #e5eaf2;
  min-height: 100vh;
  min-height: 100dvh;
  background: #f5f7fb;
  color: var(--ink);
  font: 15px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
  padding-bottom: env(safe-area-inset-bottom);
}
.patrol-mobile *, .patrol-mobile *::before, .patrol-mobile *::after { box-sizing: border-box; }
.patrol-mobile button, .patrol-mobile input, .patrol-mobile textarea, .patrol-mobile select { font: inherit; }
.patrol-mobile button { cursor: pointer; -webkit-tap-highlight-color: transparent; }
.patrol-mobile button:disabled { opacity: .55; cursor: default; }
.patrol-mobile button:focus-visible, .patrol-mobile a:focus-visible { outline: 3px solid #93b8fb; outline-offset: 3px; }
.topbar { height: calc(58px + env(safe-area-inset-top)); padding: env(safe-area-inset-top) max(12px, env(safe-area-inset-right)) 0 max(12px, env(safe-area-inset-left)); background: #1b3a67; color: #fff; display: grid; grid-template-columns: 80px 1fr 80px; align-items: center; position: sticky; top: 0; z-index: 5; box-shadow: 0 2px 8px #17375f12; }
.nav-title { margin: 0; text-align: center; font-size: 17px; line-height: 1.4; font-weight: 600; }
.nav-button { display: flex; align-items: center; justify-content: center; gap: 5px; min-height: 44px; border: 0; background: none; color: #fff; text-decoration: none; font-size: 14px !important; }
.nav-button > span { font-size: 26px; line-height: 1; }
.nav-spacer { width: 80px; }
.body { max-width: 680px; margin: 0 auto; padding: 20px 16px 32px; }
.has-action .body { padding-bottom: calc(106px + env(safe-area-inset-bottom)); }
.card { display: block; width: 100%; text-align: left; background: #fff; color: inherit; border: 1px solid var(--line); border-radius: 12px; padding: 18px; margin-bottom: 14px; box-shadow: 0 3px 12px #183b6810; }
.card h2, .section-head h2 { font-size: 17px; margin: 0 0 12px; font-weight: 600; }
.card h3 { font-size: 17px; margin: 8px 0; }
.card p { margin: 8px 0; }
.eyebrow { color: #54759f; font-size: 12px; font-weight: 600; letter-spacing: .07em; }
.login-body { min-height: calc(100vh - 58px); min-height: calc(100dvh - 58px); display: flex; align-items: center; justify-content: center; padding-top: 32px; padding-bottom: 32px; }
.login-card { max-width: 450px; padding: 28px 26px; margin: 0; }
.login-badge { width: 54px; height: 54px; display: grid; place-items: center; background: #ecf2fd; color: #1b3a67; border: 1px solid #dce7fb; border-radius: 15px; margin-bottom: 20px; }
.login-badge svg { width: 32px; height: 32px; }
.login-card h1 { font-size: 25px; margin: 6px 0 10px; font-weight: 600; }
.login-subtitle { font-size: 13px; line-height: 1.8; }
.login-card form { margin-top: 24px; }
.login-card form label { margin: 16px 0 0; }
.password-field { display: block; position: relative; }
.card .password-field input { padding-right: 64px; }
.password-toggle { position: absolute; right: 6px; top: 0; height: 46px; padding: 0 10px; border: 0; background: none; color: #587395; font-size: 12px !important; }
.login-submit { margin-top: 24px; }
.login-footnote { margin: 20px 0 0 !important; padding-top: 18px; border-top: 1px solid var(--line); font-size: 11px; color: var(--muted); text-align: center; }
.welcome { padding: 2px 2px 4px; }
.welcome h2 { font-size: 24px; font-weight: 600; margin: 5px 0; }
.welcome > p { font-size: 13px; margin: 0 0 18px; color: var(--muted); }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
.stats > div { background: #fff; border: 1px solid var(--line); border-radius: 11px; padding: 12px 6px; text-align: center; }
.stats strong { display: block; color: #244b80; font-size: 25px; line-height: 1.4; font-weight: 600; }
.stats span { font-size: 12px; color: var(--muted); }
.section-head, .between, .location-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.section-head { margin: 12px 0; }
.section-head h2 { margin: 0; }
.count { display: inline-block; vertical-align: middle; padding: 1px 7px; border-radius: 6px; background: #eef2f8; color: #627895; font-size: 12px; font-weight: 500; }
.list-note { margin: -4px 0 12px; }
.task-card { border-left: 3px solid #b9c6d8; transition: border-color .15s, box-shadow .15s; }
.task-card.pending { border-left-color: #dba34d; }
.task-card.executing { border-left-color: #4c84d9; }
.task-card.completed, .task-card.closed { border-left-color: #80b2a0; }
.task-card:not(:disabled):active { border-color: #779eeb; background: #fafcff; }
.task-card h3 { margin: 11px 0 5px; font-weight: 600; }
.task-card .task-location { color: #65768d; font-size: 13px; margin: 0 0 12px; }
.task-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.task-chips > span { padding: 2px 7px; background: #f2f5f9; border-radius: 5px; color: #6b7b90; font-size: 11px; }
.task-chips > .warn { color: #9e6a24; background: #fff4e4; }
.task-arrow { font-size: 22px; color: #8c9db5; line-height: 1; }
.mono { font: 12px Consolas, monospace; color: #74859c; overflow-wrap: anywhere; }
.pill { display: inline-block; padding: 2px 8px; background: #edf2f8; color: #5b708d; border-radius: 5px; font-size: 11px; font-weight: 500; white-space: nowrap; }
.pill.pending, .pill.pending_confirm, .pill.pending_rectify, .pill.rectifying, .pill.pending_photo { background: #fff2dc; color: #93601d; }
.pill.executing, .pill.pending_review, .pill.photo_taken { background: #e8f0fe; color: #3664a6; }
.pill.completed, .pill.closed, .pill.done { background: #e5f4ed; color: #378165; }
.pill.risk, .pill.returned { background: #fff0ed; color: #b35844; }
.pill.record { background: #eef2f8; color: #526b8d; }
.small { font-size: 12px; }
.muted { color: var(--muted); }
.full { width: 100%; }
.primary, .secondary { min-height: 44px; border-radius: 8px; padding: 10px 15px; font-weight: 600 !important; }
.primary { background: var(--primary); border: 1px solid var(--primary); color: #fff; box-shadow: 0 3px 8px #2563eb14; }
.primary:not(:disabled):active { background: #1d4ed8; }
.secondary { background: #fff; border: 1px solid #ccd9ec; color: #365f97; }
.secondary:not(:disabled):active { background: #eff5fe; }
.text-button, .link { min-height: 40px; padding: 6px 4px; background: none; border: 0; color: #3269ba; font-size: 13px !important; }
.danger { color: #b75555; }
.empty { text-align: center; color: var(--muted); padding: 38px 18px; }
.empty h3 { font-size: 16px; color: #657b95; }
.empty p { font-size: 13px; }
.empty-symbol { width: 46px; height: 46px; margin: 0 auto 14px; border-radius: 50%; display: grid; place-items: center; color: #7297c0; background: #f0f5fc; font-size: 23px; }
.skeleton { height: 12px; background: #edf1f7; border-radius: 5px; margin: 10px 0; width: 45%; animation: shimmer 1.4s ease-in-out infinite alternate; }
.skeleton.wide { width: 85%; height: 18px; margin: 18px 0; }
@keyframes shimmer { to { opacity: .5; } }
.detail-title { font-size: 21px !important; margin: 14px 0 !important; }
.task-info .meta { display: flex; gap: 15px; font-size: 13px; }
.meta b { color: var(--muted); min-width: 48px; font-weight: 400; }
.accent-card { border-left: 3px solid #6d92c7; background: #fcfdff; }
.preserve { white-space: pre-wrap; overflow-wrap: anywhere; }
.doc-row { display: flex; align-items: center; gap: 10px; border-top: 1px solid var(--line); padding: 6px 0; font-size: 13px; }
.doc-row > span { flex: 1; min-width: 0; overflow-wrap: anywhere; }
.collapse-trigger, .hazard-summary { display: flex; justify-content: space-between; align-items: center; gap: 10px; width: 100%; padding: 0; text-align: left; border: 0; background: none; color: inherit; min-height: 44px; }
.collapse-trigger strong { font-size: 16px; font-weight: 600; }
.collapse-trigger > span:first-child, .hazard-summary > span:first-child { min-width: 0; }
.summary-counts { display: block; font-size: 11px; color: var(--muted); margin-top: 6px; }
.collapse-label { flex-shrink: 0; font-size: 11px; color: #6d86a7; }
.opinion { border-top: 1px solid var(--line); padding: 16px 0 4px; margin-top: 12px; }
.notice { background: #fff6e7; color: #8b692f; border: 1px solid #f5e5c6; border-radius: 8px; padding: 10px 12px; font-size: 12px; overflow-wrap: anywhere; }
.error-notice { margin-bottom: 16px; background: #fff3f1; color: #a44c40; border-color: #f4dbd5; }
.error-notice p { margin: 5px 0 0; }
.readonly-notice { background: #eef3fa; border-color: #e0e8f3; color: #627996; }
.date-group { margin-top: 20px; }
.date-heading { font-size: 13px !important; font-weight: 600; color: #72839b; display: flex; align-items: center; gap: 10px; }
.date-heading::after { content: ""; flex: 1; height: 1px; background: var(--line); }
.date-heading.today { color: #365f97; }
.timeline-item { padding: 10px 0 16px; border-bottom: 1px solid var(--line); }
.timeline-item:last-child { border: 0; padding-bottom: 0; }
.timeline-head { display: flex; flex-wrap: wrap; align-items: center; gap: 7px; font-size: 14px; }
.batch-chip { font-size: 11px; color: #6e83a0; }
.hazard { margin: 12px 0 0; padding: 12px; border: 1px solid #f0e4d0; border-radius: 9px; background: #fffcf7; }
.hazard.closed { background: #f9fcfb; border-color: #dcece5; }
.hazard-tags { display: flex; flex-wrap: wrap; gap: 5px; }
.hazard-short { display: block; margin-top: 8px; font-size: 13px; overflow-wrap: anywhere; }
.hazard-detail { margin-top: 12px; padding-top: 10px; border-top: 1px solid #ece5db; font-size: 13px; }
.steps { display: flex; gap: 4px; overflow-x: auto; padding: 3px 0 10px; }
.steps span { flex: 1; min-width: max-content; text-align: center; color: #a0a9b4; font-size: 10px; border-bottom: 2px solid #e5e8ed; padding: 3px 4px; }
.steps span.reached { color: #608d78; border-color: #8db6a2; }
.steps span.current { font-weight: 600; }
.rectify { background: #f4f8fc; border-left: 2px solid #8eaed5; padding: 8px 10px; margin: 12px 0; border-radius: 0 6px 6px 0; }
.rectify b { font-size: 12px; font-weight: 600; }
.action-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 12px; }
.action-row .secondary { font-size: 12px !important; min-height: 40px; padding: 8px 11px; }
.hazard-actions { padding-top: 8px; border-top: 1px solid #ece5db; }
.media-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }
.media-cell { aspect-ratio: 1; min-width: 0; position: relative; overflow: hidden; background: #eef2f7; border: 0; border-radius: 8px; padding: 0; }
.preview-thumb { display: block; border: 0; width: 100%; height: 100%; padding: 0; background: none; }
.media-cell img { width: 100%; height: 100%; object-fit: cover; display: block; }
.media-placeholder { display: grid; place-items: center; width: 100%; height: 100%; color: #6b819e; font-size: 13px; }
.remove { position: absolute; top: 0; right: 0; width: 30px; height: 30px; border: 0; border-radius: 0 0 0 10px; background: #25374cc4; color: #fff; font-size: 22px !important; line-height: 1; padding: 0; }
.media-index { position: absolute; left: 0; bottom: 0; right: 0; background: #23374b80; color: #fff; padding: 2px 6px; font-size: 10px; pointer-events: none; }
.media-add { border: 1px dashed #c1cfe2; background: #f8faff; color: #7087a8; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 12px !important; gap: 4px; }
.add-plus { font-size: 28px; line-height: 1.3; color: #7d99bd; }
.bottom-action { position: fixed; z-index: 6; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 680px; padding: 12px 16px calc(12px + env(safe-area-inset-bottom)); background: #fffffff5; border-top: 1px solid var(--line); box-shadow: 0 -3px 12px #1b3a6708; }
fieldset { border: 0; padding: 0; margin: 0; min-width: 0; }
.card label { display: block; margin: 20px 0 6px; font-size: 14px; font-weight: 500; }
.form-card fieldset > label:first-child { margin-top: 0; }
.card input:not([type=checkbox]), .card select, .card textarea { display: block; width: 100%; border: 1px solid #d6dfec; border-radius: 8px; background: #fff; padding: 11px 12px; margin-top: 8px; color: var(--ink); outline: none; font-size: 16px; font-weight: 400; min-height: 46px; }
.card input:focus, .card select:focus, .card textarea:focus { border-color: #76a1ed; box-shadow: 0 0 0 3px #eaf1fe; }
.card input::placeholder, .card textarea::placeholder { color: #a0acbe; font-size: 13px; }
.card textarea { resize: vertical; }
.context-label { font-size: 13px; color: #71839c; margin: 0 3px 12px; overflow-wrap: anywhere; }
.form-item { margin-top: 22px; }
.field-title { font-size: 14px !important; font-weight: 500 !important; margin: 0 0 4px !important; }
.field-title + p { margin-top: 3px; font-size: 11px; }
.required { color: #bd695c; margin-right: 5px; }
.location-row { border: 1px solid #e2eaf5; background: #f6f9fe; border-radius: 8px; padding: 12px; align-items: flex-start; }
.location-row > div { min-width: 0; flex: 1; }
.location-row b { font-size: 13px; font-weight: 500; }
.location-row p { margin: 5px 0 0; line-height: 1.7; overflow-wrap: anywhere; }
.location-row button { flex-shrink: 0; padding: 8px 10px; font-size: 12px !important; min-height: 40px; }
.check { display: flex !important; align-items: center; justify-content: space-between; gap: 12px; padding-top: 20px; border-top: 1px solid var(--line); }
.switch { appearance: none; -webkit-appearance: none; flex-shrink: 0; width: 44px; height: 26px; border-radius: 16px; background: #cbd5e3; position: relative; cursor: pointer; transition: background .15s; }
.switch::after { content: ""; position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px #20334d25; transition: transform .15s; }
.switch:checked { background: #477fe3; }
.switch:checked::after { transform: translateX(18px); }
.switch:focus-visible { outline: 3px solid #93b8fb; outline-offset: 3px; }
.hazard-fields { padding: 0 12px 16px; margin-top: 12px; background: #fffcf6; border: 1px solid #f0e5cf; border-radius: 8px; }
.form-error { color: #b65044 !important; font-size: 12px; }
.file-input { display: none; }
.preview, .dialog-mask, .picker-mask, .progress-mask { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; padding: 20px; background: #14294299; }
.dialog-mask { z-index: 20; }
.preview { z-index: 40; background: #0a1627ed; }
.preview img, .preview video { max-width: 100%; max-height: 85vh; object-fit: contain; }
.preview-close { position: absolute; right: max(12px, env(safe-area-inset-right)); top: max(12px, env(safe-area-inset-top)); width: 44px; height: 44px; background: none; border: 0; color: #fff; font-size: 36px !important; }
.dialog { width: 100%; max-width: 500px; margin: 0; max-height: 85vh; max-height: 85dvh; overflow-y: auto; padding: 20px; }
.dialog .between h2 { margin: 0; }
.dialog-actions { display: grid; grid-template-columns: 1fr 1.3fr; gap: 10px; margin-top: 22px; }
.picker-mask { z-index: 30; align-items: flex-end; padding: 0; }
.source-sheet { width: 100%; max-width: 680px; border-radius: 18px 18px 0 0; background: #fff; padding: 10px 18px calc(14px + env(safe-area-inset-bottom)); box-shadow: 0 -8px 30px #1328401a; }
.sheet-handle { width: 34px; height: 4px; border-radius: 5px; background: #d8dfea; margin: 0 auto 17px; }
.source-sheet h2 { margin: 0 0 18px; text-align: center; font-size: 16px; font-weight: 600; }
.source-options { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.source-options button { display: flex; flex-direction: column; align-items: center; gap: 3px; padding: 14px 8px; border: 1px solid #e5ecf7; border-radius: 10px; background: #f8faff; color: #345b8d; }
.source-options strong { font-size: 13px; font-weight: 500; }
.source-options small { color: #8a9ab0; font-size: 11px; }
.source-icon { display: grid; place-items: center; width: 32px; height: 32px; color: #6089c0; font-size: 27px; line-height: 1; margin-bottom: 4px; }
.sheet-cancel { width: 100%; min-height: 44px; padding: 12px; margin-top: 12px; color: #6c7d92; background: #fff; border: 0; border-top: 1px solid var(--line); }
.progress-mask { z-index: 45; }
.progress-card { max-width: 340px; width: 100%; padding: 24px; border-radius: 12px; background: #fff; text-align: center; }
.progress-card strong { font-size: 15px; font-weight: 500; }
.progress-card progress { display: block; width: 100%; height: 7px; border: 0; border-radius: 8px; overflow: hidden; margin: 18px 0 8px; accent-color: #477fe3; }
.progress-card progress::-webkit-progress-bar { background: #eaf0f9; }
.progress-card progress::-webkit-progress-value { background: #477fe3; }
.progress-card > span { color: #5379ad; font-size: 12px; }
.toast { position: fixed; z-index: 50; left: 50%; bottom: calc(92px + env(safe-area-inset-bottom)); transform: translateX(-50%); width: max-content; max-width: min(88%, 560px); padding: 12px 16px; background: #243a54ed; color: #fff; border-radius: 9px; text-align: center; font-size: 13px; overflow-wrap: anywhere; box-shadow: 0 4px 18px #172e4526; }
@media (min-width: 681px) { .body { padding-top: 26px; } .task-card:hover { box-shadow: 0 5px 18px #183b6817; } }
@media (max-width: 360px) {
  .body { padding: 16px 12px 28px; }
  .has-action .body { padding-bottom: calc(100px + env(safe-area-inset-bottom)); }
  .card { padding: 15px; }
  .media-grid { gap: 6px; }
  .location-row { padding: 10px; }
  .login-card { padding: 24px 20px; }
  .collapse-trigger { align-items: flex-start; }
  .summary-counts { font-size: 10px; }
}
@media (prefers-reduced-motion: reduce) { .skeleton { animation: none; } .task-card, .switch, .switch::after { transition: none; } }
</style>
