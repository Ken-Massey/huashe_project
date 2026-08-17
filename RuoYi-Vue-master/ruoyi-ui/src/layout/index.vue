<template>
  <div class="rail-shell">
    <rail-navigation />
    <main class="rail-workspace">
      <app-main />
    </main>
  </div>
</template>

<script>
import { AppMain } from './components'
import RailNavigation from './components/RailNavigation'

export default {
  name: 'Layout',
  components: { AppMain, RailNavigation },
  mounted() {
    const value = localStorage.getItem('rail-font-size') || 'standard'
    document.body.classList.remove('font-size-small', 'font-size-standard', 'font-size-large')
    document.body.classList.add(`font-size-${value}`)
  }
}
</script>

<style lang="scss" scoped>
.rail-shell {
  min-height: 100vh;
  background: #f5f7f8;
}
.rail-workspace {
  min-height: 100vh;
  margin-left: 208px;
}
@media (max-width: 760px) {
  .rail-workspace {
    margin-left: 0;
    padding-bottom: 68px;
  }
}
</style>
