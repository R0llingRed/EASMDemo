<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import {
  ArrowLeftBold,
  ArrowRightBold,
  Connection,
  DataAnalysis,
  Monitor,
  Setting,
  Odometer,
  Files,
  WarnTriangleFilled,
  Aim
} from '@element-plus/icons-vue'
import { useWorkspaceStore } from '../stores/workspace'

const route = useRoute()
const workspace = useWorkspaceStore()

const isMobile = ref(false)
const sidebarOpen = ref(true)

type MenuItem = {
  path: string
  label: string
  icon: unknown
  subtitle: string
}

const menuItems: MenuItem[] = [
  { path: '/', label: 'Dashboard', icon: Odometer, subtitle: '资产和任务总览' },
  { path: '/projects', label: 'Projects', icon: Files, subtitle: '项目空间与切换' },
  { path: '/assets', label: 'Assets', icon: Monitor, subtitle: '资产导入与检索' },
  { path: '/risks', label: 'Risks', icon: WarnTriangleFilled, subtitle: '漏洞、API 风险与评分' },
  { path: '/tasks', label: 'Tasks', icon: Aim, subtitle: '扫描任务编排与执行' },
  { path: '/task-progress', label: 'Progress', icon: DataAnalysis, subtitle: '实时任务进度监控' },
  { path: '/automation', label: 'Automation', icon: Connection, subtitle: '资产导入自动化策略' },
  { path: '/settings', label: 'Settings', icon: Setting, subtitle: '连接参数与访问控制' },
]

const defaultMeta: MenuItem = menuItems[0] ?? {
  path: '/',
  label: 'Dashboard',
  icon: Odometer,
  subtitle: '资产和任务总览',
}

const routeMeta = computed(() =>
  menuItems.find((item) => item.path === route.path) ?? defaultMeta,
)

const asideWidth = computed(() => {
  if (isMobile.value) {
    return '280px'
  }
  return sidebarOpen.value ? '270px' : '92px'
})

const menuCollapse = computed(() => !isMobile.value && !sidebarOpen.value)

function syncViewport() {
  isMobile.value = window.innerWidth <= 1024
  if (isMobile.value) {
    sidebarOpen.value = false
  }
}

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function onMenuClick() {
  if (isMobile.value) {
    sidebarOpen.value = false
  }
}

onMounted(() => {
  syncViewport()
  window.addEventListener('resize', syncViewport)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncViewport)
})
</script>

<template>
  <div class="app-shell">
    <div
      v-if="isMobile && sidebarOpen"
      class="app-sidebar-backdrop"
      @click="sidebarOpen = false"
    />
    <el-aside
      :width="asideWidth"
      class="app-sidebar transition-all duration-300"
      :class="{
        'app-sidebar--mobile': isMobile,
        'app-sidebar--mobile-open': isMobile && sidebarOpen,
        'app-sidebar--mobile-closed': isMobile && !sidebarOpen,
      }"
    >
      <div class="app-brand">
        <div class="app-brand-badge">E</div>
        <div v-if="!menuCollapse" class="app-brand-text">
          <p class="app-brand-title">EASM Console</p>
          <p class="app-brand-subtitle">Exposure Operations</p>
        </div>
      </div>

      <el-menu
        class="app-menu"
        :default-active="route.path"
        :collapse="menuCollapse"
        router
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
          @click="onMenuClick"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.label }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <div class="app-main">
      <header class="app-topbar">
        <button class="icon-button" @click="toggleSidebar">
          <el-icon v-if="sidebarOpen"><ArrowLeftBold /></el-icon>
          <el-icon v-else><ArrowRightBold /></el-icon>
        </button>

        <div>
          <h1 class="topbar-title">{{ routeMeta.label }}</h1>
          <p class="topbar-subtitle">{{ routeMeta.subtitle }}</p>
        </div>

        <div class="topbar-status">
          <el-tag v-if="workspace.selectedProject" effect="dark" round>
            {{ workspace.selectedProject.name }}
          </el-tag>
          <el-tag v-else type="warning" round>未选择项目</el-tag>
        </div>
      </header>

      <main class="app-content">
        <RouterView v-slot="{ Component }">
          <transition name="view-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>
