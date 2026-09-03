<template>
  <aside class="rail-navigation" aria-label="轨道保护业务导航">
    <div class="brand-mark" title="华设轨道智审系统">
      <i class="el-icon-office-building" />
      <span>华设轨道智审系统</span>
    </div>
    <nav class="business-links">
      <router-link
        v-for="item in visibleItems"
        :key="item.path"
        :to="item.path"
        class="business-link"
        :class="{ active: isActive(item) }"
      >
        <i :class="item.icon" />
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
    <router-link to="/rail/settings" class="settings-link" :class="{ active: isActive('/rail/settings') }">
      <i class="el-icon-setting" /><span>设置</span>
    </router-link>
  </aside>
</template>

<script>
export default {
  name: 'RailNavigation',
  data() {
    return {
      items: [
        { path: '/rail/audit', label: '案例审核', icon: 'el-icon-finished' },
        { path: '/rail/workflow', label: '审核流转', icon: 'el-icon-s-claim', permission: 'rail:audit:workflow:list' },
        { path: '/rail/patrol', label: '现场符合性巡查', icon: 'el-icon-location-outline' },
        { path: '/rail/knowledge', label: '知识库', icon: 'el-icon-collection' },
        { path: '/rail/agent', label: 'AI智能体', icon: 'el-icon-chat-dot-square' },
        { path: '/rail/archive', label: '项目档案', icon: 'el-icon-document-copy' },
        { path: '/rail/general', label: '通用管理', icon: 'el-icon-s-data', permissions: ['rail:general:list', 'rail:general:query'] },
        // 账号管理：进入用户管理页，需管理员权限
        { path: '/system/user', label: '账号管理', icon: 'el-icon-s-tools', permission: 'system:user:list' }
      ]
    }
  },
  computed: {
    visibleItems() {
      const perms = this.$store.getters.permissions || []
      return this.items.filter(item => {
        if (!item.permission && !item.permissions) return true
        if (perms.includes('*:*:*')) return true
        if (item.permissions) return item.permissions.some(permission => perms.includes(permission))
        return perms.includes(item.permission)
      })
    }
  },
  methods: {
    isActive(item) {
      const path = typeof item === 'string' ? item : item.path
      // 系统管理：/system/ 下任意页面均高亮
      if (path === '/system/user') {
        return this.$route.path.startsWith('/system/')
      }
      return this.$route.path === path || this.$route.path.startsWith(`${path}/`)
    }
  }
}
</script>

<style lang="scss" scoped>
.rail-navigation {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 20;
  display: flex;
  width: 208px;
  flex-direction: column;
  align-items: center;
  border-right: 1px solid #e3e7e6;
  background: #f2f4f3;
}
.brand-mark {
  display: grid;
  width: 174px;
  min-height: 58px;
  margin: 22px 0 24px;
  place-items: center;
  border: 1px solid #d6dfdc;
  border-radius: 8px;
  background: #fff;
  color: #267663;
  font-size: 25px;
  gap: 10px;
  grid-template-columns: 28px 1fr;
  padding: 0 14px;
}
.brand-mark span { color: #34433e; font-size: 13px; font-weight: 600; line-height: 1.35; }
.business-links { width: 100%; }
.business-link {
  position: relative;
  display: flex;
  width: 100%;
  min-height: 64px;
  flex-direction: row;
  align-items: center;
  justify-content: flex-start;
  gap: 13px;
  padding: 10px 22px;
  color: #626b68;
  font-size: 13px;
  line-height: 1.35;
  text-align: left;
  transition: color .18s ease, background-color .18s ease;
}
.business-link i { width: 24px; font-size: 22px; text-align: center; }
.business-link span,
.settings-link span { white-space: nowrap; }
.business-link:hover,
.business-link.active { background: #e5efeb; color: #246f5d; }
.business-link.active::before {
  position: absolute;
  top: 12px;
  bottom: 12px;
  left: 0;
  width: 3px;
  background: #2f806b;
  content: '';
}
.settings-link {
  display: flex;
  width: 100%;
  height: 58px;
  margin-top: auto;
  align-items: center;
  gap: 13px;
  padding: 0 22px;
  border-top: 1px solid #dde3e1;
  color: #626b68;
  font-size: 13px;
}
.settings-link i { width: 24px; font-size: 21px; text-align: center; }
.settings-link:hover,.settings-link.active { background: #e5efeb; color: #246f5d; }
@media (max-width: 760px) {
  .rail-navigation {
    top: auto;
    right: 0;
    width: auto;
    height: 68px;
    flex-direction: row;
    border-top: 1px solid #e3e7e6;
    border-right: 0;
  }
  .brand-mark { display: none; }
  .business-links { display: grid; height: 100%; grid-template-columns: repeat(auto-fit, minmax(52px, 1fr)); }
  .business-link { min-height: 68px; gap: 4px; padding: 5px 3px; font-size: 11px; }
  .business-link i { font-size: 20px; }
  .business-link.active::before { inset: 0 12px auto; width: auto; height: 3px; }
  .settings-link { width: 62px; height: 68px; flex-direction: column; justify-content: center; gap: 4px; padding: 4px; border-top: 0; border-left: 1px solid #dde3e1; font-size: 11px; }
}
</style>
