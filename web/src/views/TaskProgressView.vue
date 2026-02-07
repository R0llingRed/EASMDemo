<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { getErrorMessage } from '../api/client'
import { listScans, type ScanTask } from '../api/easm'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()

const loading = ref(false)
const autoRefresh = ref(true)
const activeTasks = ref<ScanTask[]>([])
const recentTasks = ref<ScanTask[]>([])
const pendingTotal = ref(0)
const runningTotal = ref(0)
let refreshTimer: number | undefined

const activeTotal = computed(() => pendingTotal.value + runningTotal.value)

function formatProgress(task: ScanTask): number {
  return Math.max(0, Math.min(100, task.progress || 0))
}

function progressStatus(task: ScanTask): '' | 'success' | 'exception' {
  if (task.status === 'completed') {
    return 'success'
  }
  if (task.status === 'failed') {
    return 'exception'
  }
  return ''
}

function statusTagType(status: string): '' | 'warning' | 'success' | 'danger' {
  if (status === 'pending') {
    return 'warning'
  }
  if (status === 'completed') {
    return 'success'
  }
  if (status === 'failed') {
    return 'danger'
  }
  return ''
}

async function loadProgress() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    activeTasks.value = []
    recentTasks.value = []
    pendingTotal.value = 0
    runningTotal.value = 0
    return
  }

  loading.value = true
  try {
    const [pendingPage, runningPage, recentPage] = await Promise.all([
      listScans(projectId, { status: 'pending', skip: 0, limit: 100 }),
      listScans(projectId, { status: 'running', skip: 0, limit: 100 }),
      listScans(projectId, { skip: 0, limit: 20 }),
    ])

    pendingTotal.value = pendingPage.total
    runningTotal.value = runningPage.total
    activeTasks.value = [...runningPage.items, ...pendingPage.items]
    recentTasks.value = recentPage.items
  } catch (error) {
    ElMessage.error(`任务进度加载失败：${getErrorMessage(error)}`)
  } finally {
    loading.value = false
  }
}

function setupRefreshTimer(enabled: boolean) {
  if (refreshTimer) {
    window.clearInterval(refreshTimer)
    refreshTimer = undefined
  }
  if (!enabled) {
    return
  }
  refreshTimer = window.setInterval(() => {
    void loadProgress()
  }, 5000)
}

onMounted(async () => {
  await workspace.loadProjects()
  await loadProgress()
  setupRefreshTimer(autoRefresh.value)
})

onBeforeUnmount(() => {
  setupRefreshTimer(false)
})

watch(
  () => workspace.selectedProjectId,
  async () => {
    await loadProgress()
  },
)

watch(
  () => autoRefresh.value,
  (enabled) => {
    setupRefreshTimer(enabled)
  },
)
</script>

<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <h1 class="page-title">Task Progress</h1>
        <p class="page-subtitle">任务执行进度与实时状态</p>
      </div>
      <div class="page-tools">
        <el-button @click="loadProgress" :loading="loading">立即刷新</el-button>
        <el-button :type="autoRefresh ? 'success' : 'default'" @click="autoRefresh = !autoRefresh">
          {{ autoRefresh ? '自动刷新中(5s)' : '开启自动刷新' }}
        </el-button>
      </div>
    </div>

    <div class="kpi-grid">
      <article class="kpi-card text-[#2f6f7e]">
        <div class="kpi-label">活动任务总数</div>
        <div class="kpi-value kpi-value--neutral">{{ activeTotal }}</div>
      </article>
      <article class="kpi-card text-[var(--accent)]">
        <div class="kpi-label">待执行</div>
        <div class="kpi-value kpi-value--accent">{{ pendingTotal }}</div>
      </article>
      <article class="kpi-card text-[var(--brand)]">
        <div class="kpi-label">执行中</div>
        <div class="kpi-value kpi-value--brand">{{ runningTotal }}</div>
      </article>
      <article class="kpi-card text-[var(--danger)]">
        <div class="kpi-label">最近任务数</div>
        <div class="kpi-value kpi-value--danger">{{ recentTasks.length }}</div>
      </article>
    </div>

    <el-card shadow="never" class="panel-card">
      <template #header>
        <span>活动任务（Running + Pending）</span>
      </template>
      <el-empty v-if="!activeTasks.length" description="当前无活动任务" />
      <el-table v-else :data="activeTasks" v-loading="loading">
        <el-table-column prop="task_type" label="类型" min-width="150" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" min-width="220">
          <template #default="{ row }">
            <el-progress
              :percentage="formatProgress(row)"
              :status="progressStatus(row)"
              :stroke-width="14"
            />
          </template>
        </el-table-column>
        <el-table-column label="目标" min-width="130">
          <template #default="{ row }">
            {{ row.completed_targets }}/{{ row.total_targets || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" min-width="240" />
      </el-table>
    </el-card>

    <el-card shadow="never" class="panel-card">
      <template #header>
        <span>最近任务</span>
      </template>
      <el-empty v-if="!recentTasks.length" description="暂无任务记录" />
      <el-table v-else :data="recentTasks" v-loading="loading">
        <el-table-column prop="task_type" label="类型" min-width="150" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="100" />
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
        <el-table-column prop="started_at" label="开始时间" min-width="180" />
        <el-table-column prop="completed_at" label="结束时间" min-width="180" />
      </el-table>
    </el-card>
  </div>
</template>
