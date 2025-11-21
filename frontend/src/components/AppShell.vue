<template>
  <el-container class="app-shell">
    <el-header height="64px" class="app-shell__header">
      <div class="app-shell__brand">
        <span class="app-shell__logo">Financial Manager</span>
      </div>
      <el-menu mode="horizontal" :default-active="activePath" :ellipsis="false" router class="app-shell__menu"
        background-color="transparent" text-color="#ffffff" active-text-color="#ffffff">
        <el-menu-item index="/dashboard">
          <el-icon>
            <Monitor />
          </el-icon>
          <span>总览</span>
        </el-menu-item>
        <el-menu-item index="/purchases">
          <el-icon>
            <ShoppingCart />
          </el-icon>
          <span>采购</span>
        </el-menu-item>
        <el-menu-item index="/sales">
          <el-icon>
            <TrendCharts />
          </el-icon>
          <span>销售</span>
        </el-menu-item>
        <el-menu-item index="/business">
          <el-icon>
            <Briefcase />
          </el-icon>
          <span>业务</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon>
            <Setting />
          </el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
      <div class="app-shell__actions">
        <el-tooltip placement="bottom" :content="tooltipContent">
          <el-tag class="app-shell__user" effect="dark" type="info">
            {{ userLabel }}
          </el-tag>
        </el-tooltip>
        <el-button size="small" plain @click="handleLogout">退出</el-button>
      </div>
    </el-header>
    <el-main class="app-shell__main">
      <slot />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Briefcase, Monitor, Setting, ShoppingCart, TrendCharts } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const activePath = computed(() => route.meta?.activePath || route.path)
const userLabel = computed(() => auth.email || '未登录')
const tooltipContent = computed(() => (auth.email ? `当前账号：${auth.email}` : '尚未登录账号'))

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.app-shell__header {
  display: flex;
  align-items: center;
  background: linear-gradient(120deg, #4b8b79, #3c6c60);
  color: #ffffff;
  padding: 0 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  gap: 24px;
}

.app-shell__brand {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 18px;
}

.app-shell__logo {
  letter-spacing: 0.5px;
}

.app-shell__menu {
  flex: 1;
  border-bottom: none;
}

.app-shell__menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.75);
}

/* .app-shell__menu :deep(.is-active) {
  background: rgba(255, 255, 255, 0.15) !important;
  border-radius: 8px;
  margin-top: 10px;
} */

.app-shell__menu :deep(.el-menu-item span) {
  margin-left: 6px;
}

.app-shell__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-shell__user {
  background: rgba(255, 255, 255, 0.18);
  border: none;
}

.app-shell__main {
  padding: 32px;
  background: transparent;
}
</style>
