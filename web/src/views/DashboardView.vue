<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import {
  getVulnerabilityStats,
  listApiRisks,
  listAssets,
  listScans,
  type ScanTask,
} from '../api/easm'
import { getErrorMessage } from '../api/client'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
const loading = ref(false)
const latestTasks = ref<ScanTask[]>([])

const stats = reactive({
  totalAssets: 0,
  criticalRisks: 0,
  runningTasks: 0,
  vulnerabilities: 0,
})

function resetStats() {
  stats.totalAssets = 0
  stats.criticalRisks = 0
  stats.runningTasks = 0
  stats.vulnerabilities = 0
  latestTasks.value = []
}

async function loadDashboard() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    resetStats()
    return
  }

  loading.value = true
  try {
    const [assetsPage, vulnStats, apiRiskPage, pendingPage, runningPage, scansPage] =
      await Promise.all([
        listAssets(projectId, { offset: 0, limit: 1 }),
        getVulnerabilityStats(projectId),
        listApiRisks(projectId, { severity: 'critical', limit: 1 }),
        listScans(projectId, { status: 'pending', limit: 1 }),
        listScans(projectId, { status: 'running', limit: 1 }),
        listScans(projectId, { skip: 0, limit: 5 }),
      ])

    stats.totalAssets = assetsPage.total
    stats.criticalRisks = vulnStats.critical + apiRiskPage.total
    stats.runningTasks = pendingPage.total + runningPage.total
    stats.vulnerabilities = vulnStats.total
    latestTasks.value = scansPage.items
  } catch (error) {
    ElMessage.error(`看板数据加载失败：${getErrorMessage(error)}`)
    resetStats()
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await workspace.loadProjects()
  await loadDashboard()
})

watch(
  () => workspace.selectedProjectId,
  async () => {
    await loadDashboard()
  },
)
</script>

<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">核心指标与最近任务状态</p>
      </div>
      <el-tag v-if="workspace.selectedProject" effect="dark">{{ workspace.selectedProject.name }}</el-tag>
      <el-tag type="warning" v-else>请先创建并选择项目</el-tag>
    </div>

    <div class="kpi-grid" v-loading="loading">
      <article class="kpi-card text-[var(--brand)]">
        <div class="kpi-label">资产总数</div>
        <div class="kpi-value kpi-value--brand">{{ stats.totalAssets }}</div>
      </article>
      <article class="kpi-card text-[var(--danger)]">
        <div class="kpi-label">严重风险</div>
        <div class="kpi-value kpi-value--danger">{{ stats.criticalRisks }}</div>
      </article>
      <article class="kpi-card text-[#2f6f7e]">
        <div class="kpi-label">运行中/待执行任务</div>
        <div class="kpi-value kpi-value--neutral">{{ stats.runningTasks }}</div>
      </article>
      <article class="kpi-card text-[var(--accent)]">
        <div class="kpi-label">漏洞总数</div>
        <div class="kpi-value kpi-value--accent">{{ stats.vulnerabilities }}</div>
      </article>
    </div>

    <el-card shadow="never" class="panel-card">
      <template #header>
        <span>最近扫描任务</span>
      </template>
      <el-empty v-if="!latestTasks.length" description="暂无任务数据" />
      <el-table v-else :data="latestTasks" size="small">
        <el-table-column prop="task_type" label="类型" min-width="140" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="priority" label="优先级" width="100" />
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
      </el-table>
    </el-card>
  </div>
</template>
